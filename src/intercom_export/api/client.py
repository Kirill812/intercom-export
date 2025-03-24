"""
Intercom API client for fetching conversations and related data.
"""

import logging
from typing import List, Dict, Any, Optional
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
    pass

class AuthenticationError(IntercomAPIError):
    """Raised when API authentication fails."""
    pass

class IntercomClient:
    """Client for interacting with the Intercom API."""
    
    def __init__(self, config: IntercomConfig):
        """Initialize the client with configuration."""
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.api_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Intercom-Version': config.api_version
        })
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        # Log the raw API response for debugging purposes
        logger.debug(f"Raw API response ({response.status_code}): {response.text}")
        if response.ok:
            return response.json()
        
        error_msg = f"API request failed: {response.status_code}"
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                error_msg = f"{error_msg} - {error_data.get('message', '')}"
        except ValueError:
            error_msg = f"{error_msg} - {response.text}"
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API token", response)
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded", response)
        else:
            raise IntercomAPIError(error_msg, response)
    
    def get_conversations(
        self,
        conversation_ids: List[int],
        batch_size: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Fetch conversations in batches.
        
        Args:
            conversation_ids: List of conversation IDs to fetch
            batch_size: Number of conversations to fetch per request
        
        Returns:
            List of conversation data dictionaries
        """
        conversations = []
        total_batches = (len(conversation_ids) + batch_size - 1) // batch_size
        
        for i in range(0, len(conversation_ids), batch_size):
            batch = conversation_ids[i:i + batch_size]
            logger.info(
                f"Fetching batch {i//batch_size + 1}/{total_batches} "
                f"({len(batch)} conversations)"
            )
            
            try:
                response = self.session.post(
                    f'{self.config.base_url}/conversations/search',
                    json={
                        'query': {
                            'operator': 'OR',
                            'value': [{'field': 'id', 'operator': 'IN', 'value': batch}]
                        },
                        'display_as': 'plaintext',
                        'sort_field': 'created_at',
                        'sort_order': 'desc',
                        'include_messages': True,
                        'include_message_parts': True,
                        'expand': [
                            'conversation_message',
                            'conversation_parts',
                            'contact',
                            'assignee'
                        ]
                    }
                )
                
                data = self._handle_response(response)
                logger.debug(f"Fetched conversation data: {data}")
                conversations.extend(data.get('conversations', []))
                
            except RateLimitError:
                logger.warning("Rate limit hit, implementing backoff...")
                # TODO: Implement exponential backoff retry
                raise
            except Exception as e:
                logger.error(f"Error fetching batch: {str(e)}")
                raise
        
        return conversations
    
    def get_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """
        Fetch a single conversation by ID. If the conversation data returned by the search endpoint 
        is incomplete, a fallback GET request is performed to retrieve detailed data.
        
        Args:
            conversation_id: ID of the conversation to fetch
        
        Returns:
            Conversation data dictionary with complete details.
        """
        conversations = self.get_conversations([conversation_id])
        if not conversations:
            raise IntercomAPIError(f"Conversation {conversation_id} not found")
        conversation = conversations[0]
        # Check if the conversation data appears incomplete (e.g., missing conversation_message)
        if 'conversation_message' not in conversation:
            logger.debug(f"Incomplete conversation data received for ID {conversation_id}. Fetching detailed data via GET request.")
            detailed_response = self.session.get(f'{self.config.base_url}/conversations/{conversation_id}')
            detailed_data = self._handle_response(detailed_response)
            logger.debug(f"Detailed conversation data: {detailed_data}")
            conversation = detailed_data
        return conversation
