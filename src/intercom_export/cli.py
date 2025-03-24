"""
Command-line interface for Intercom conversation exports.
"""

import argparse
import logging
import os
import sys
from typing import List, Optional
import yaml

from .config import create_config, Config
from .api.client import IntercomClient, IntercomAPIError
from .models.conversation import Conversation
from .formatters.factory import create_formatter, get_available_formats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_argparser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Export Intercom conversations to various formats"
    )
    
    parser.add_argument(
        "conversation_ids",
        nargs="*",
        type=int,
        help="Specific conversation IDs to export"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--format",
        choices=get_available_formats(),
        default="markdown",
        help="Output format (default: markdown)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: conversations.<format>)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=15,
        help="Number of conversations to fetch per batch (default: 15)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser

def load_conversation_ids(path: str) -> List[int]:
    """Load conversation IDs from a file."""
    with open(path) as f:
        if path.endswith('.yaml') or path.endswith('.yml'):
            data = yaml.safe_load(f)
            return [int(id_) for id_ in data.get('conversation_ids', [])]
        return [int(line.strip()) for line in f if line.strip()]

def export_conversations(config: Config, args: argparse.Namespace) -> None:
    """Export conversations using the specified configuration."""
    try:
        # Set up API client
        client = IntercomClient(config.intercom)
        
        # Get conversation IDs
        conversation_ids = args.conversation_ids
        if not conversation_ids and os.path.exists('conversation_ids.txt'):
            conversation_ids = load_conversation_ids('conversation_ids.txt')
        
        if not conversation_ids:
            logger.error("No conversation IDs provided")
            sys.exit(1)
        
        logger.info(f"Exporting {len(conversation_ids)} conversations...")
        
        # Fetch conversations
        raw_conversations = client.get_conversations(
            conversation_ids,
            batch_size=args.batch_size
        )
        
        # Convert to model instances
        conversations = [
            Conversation.from_api_data(conv)
            for conv in raw_conversations
        ]
        
        # Determine output path
        if not args.output:
            ext = ".md" if args.format == "markdown" else f".{args.format}"
            args.output = f"conversations{ext}"
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        
        # Create formatter and format conversations
        with open(args.output, 'w', encoding='utf-8') as f:
            formatter = create_formatter(
                args.format,
                f,
                indent=2 if args.format == 'json' else None
            )
            formatter.format_conversations(conversations)
        
        logger.info(f"Exported {len(conversations)} conversations to {args.output}")
        
    except IntercomAPIError as e:
        logger.error(f"API Error: {str(e)}")
        if args.verbose and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.verbose:
            logger.exception("Detailed error:")
        sys.exit(1)

def main() -> None:
    """Main entry point for the CLI."""
    parser = setup_argparser()
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    try:
        config = create_config(
            config_file=args.config,
            env_vars=True,
            export={
                'output_format': args.format,
                'batch_size': args.batch_size
            }
        )
    except Exception as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)
    
    # Run export
    export_conversations(config, args)

if __name__ == "__main__":
    main()
