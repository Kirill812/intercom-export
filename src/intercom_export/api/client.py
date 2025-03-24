"""
Intercom API client for fetching conversations and related data.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Callable
try:
    import requests
except ModuleNotFoundError:
    import sys
    sys.stderr.write("Error: The 'requests' module is not installed. Please run 'pip install requests' to install it.\n")
    raise
from ..config import IntercomConfig

logger = logging.getLogger(__name__)

class IntercomAPIError(Exception):
    """Base exception for Intercom API errors."""
    def __init__(self, message: str, response: Optional[requests.Response] = None):
        super().__init__(message)
        self.response = response

class RateLimitError(IntercomAPIError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, message: str, response: Optional[requests.Response] = None, retry_after: Optional[int] = None):
        super().__init__(message, response)
        self.retry_after = retry_after

class AuthenticationError(IntercomAPIError):
    """Raised when API authentication fails."""
    pass

class IntercomClient:
    """Client for interacting with the Intercom API."""
    
    def __init__(self, config):
        """Initialize the client with configuration."""
        if isinstance(config, (tuple, list)):
            config = config[0]
        if isinstance(config, dict):
            from ..config import IntercomConfig
            config = IntercomConfig(config)
        # If a nested 'intercom' configuration exists, use it.
        if getattr(config, 'intercom', None) is not None:
            intercom_config = config.intercom
            if isinstance(intercom_config, dict):
                from ..config import IntercomConfig
                config = IntercomConfig(intercom_config)
            else:
                config = intercom_config
        self.config = config
        # Standardize base_url from configuration: remove trailing slash and any endpoint path
        base_url = self.config.base_url.rstrip('/')
        if base_url.endswith('/conversation') or base_url.endswith('/conversations'):
            base_url = base_url.rsplit('/', 1)[0]
        self.config.base_url = base_url
        self.session = requests.Session()
        import os
        env_token = os.getenv("INTERCOM_API_TOKEN", "") or ""
        if env_token:
            auth_token = env_token
        else:
            auth_token = getattr(config, 'api_token', '') or ''
        if auth_token.startswith("Bearer "):
            token = auth_token[len("Bearer "):]
        else:
            token = auth_token
        self.session.headers.update({
            'Authorization': f"Bearer {token}",
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Intercom-Version': config.api_version
        })
        
        # Configure retry parameters
        self.max_retries = getattr(config, 'max_retries', 5)
        self.initial_backoff = getattr(config, 'initial_backoff', 1)
        self.backoff_factor = getattr(config, 'backoff_factor', 2)
        self.max_backoff = getattr(config, 'max_backoff', 60)
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        logger.debug(f"Raw API response ({response.status_code}): {response.text}")
        if response.ok:
            return response.json()
        
        error_msg = f"API request failed: {response.status_code}"
        try:
            error_data = response.json()
            if isinstance(error_data, dict) and error_data.get("message"):
                error_msg += f" - {error_data.get('message')}"
            elif response.text:
                error_msg += f" - {response.text}"
        except ValueError:
            if response.text:
                error_msg += f" - {response.text}"
        if response.status_code == 401:
            raise AuthenticationError("Invalid API token", response)
        elif response.status_code == 429:
            retry_after = None
            if 'Retry-After' in response.headers:
                try:
                    retry_after = int(response.headers['Retry-After'])
                except (ValueError, TypeError):
                    pass
            raise RateLimitError("Rate limit exceeded", response, retry_after)
        else:
            raise IntercomAPIError(error_msg, response)

    def _determine_batch_size(self, total_items: int) -> int:
        """Determine optimal batch size based on system resources and total items."""
        import os
        configured_batch = getattr(self.config, 'batch_size', None)
        if configured_batch is not None:
            return configured_batch
        cpu_count = os.cpu_count() or 4
        suggested_size = max(10, min(50, total_items // (cpu_count * 2) or 10))
        return suggested_size

    def get_conversations(self, conversation_ids: list, batch_size: int = None) -> list:
        """Fetch conversations for given IDs using intelligent batching."""
        if batch_size is None:
            batch_size = self._determine_batch_size(len(conversation_ids))
            logger.info(f"Using intelligent batch size of {batch_size} for {len(conversation_ids)} conversations")
        all_conversations = []
        for i in range(0, len(conversation_ids), batch_size):
            batch = conversation_ids[i:i+batch_size]
            payload = {"display_as": "plaintext", "expand": ["conversation_message"], "query": {"value": [{"value": batch}]}}
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    response = self.session.post(f"{self.config.base_url}/conversations", json=payload)
                    data = self._handle_response(response)
                    convs = data.get("conversations", [])
                    if not convs and len(batch) == 1:
                        raise IntercomAPIError(f"Conversation {batch[0]} not found", response)
                    all_conversations.extend(convs)
                    break
                except RateLimitError as e:
                    if attempt < max_attempts - 1:
                        wait_time = e.retry_after or (2 ** attempt)
                        logger.warning(f"Rate limit hit, waiting {wait_time}s before retrying...")
                        time.sleep(wait_time)
                        if len(batch) > 1:
                            half_batch = len(batch) // 2
                            batch = batch[:half_batch]
                            logger.info(f"Reducing batch size to {len(batch)} for retry")
                    else:
                        raise
            logger.info(f"Processed {min(i + batch_size, len(conversation_ids))}/{len(conversation_ids)} conversations")
        return all_conversations

    def get_conversation(self, conversation_id) -> dict:
        """Fetch a single conversation by ID.
        Attempts a GET request first; if it does not yield a conversation matching the provided ID, falls back to a POST request with a query payload."""
        # Attempt GET request.
        try:
            response = self.session.get(f"{self.config.base_url}/conversations/{conversation_id}")
            data = self._handle_response(response)
        except IntercomAPIError:
            data = None

        # Check if the GET response is a conversation object by verifying it has an "id" that matches.
        if data and data.get("id") and str(data.get("id")) == str(conversation_id):
            return data

        # Fallback to POST request if GET did not return the expected conversation.
        payload = {"display_as": "plaintext", "expand": ["conversation_message"], "query": {"value": [{"value": [conversation_id]}]}}
        response = self.session.post(f"{self.config.base_url}/conversations", json=payload)
        data = self._handle_response(response)
        convs = data.get("conversations", [])
        if convs:
            return convs[0]
        else:
            raise IntercomAPIError(f"Conversation {conversation_id} not found via fallback", response)
