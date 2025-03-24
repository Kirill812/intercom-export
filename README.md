# Intercom Conversation Exporter

A Python tool for exporting and formatting Intercom conversations. This tool provides a flexible and maintainable way to export conversations from Intercom in various formats, with support for customization, filtering, and direct API integration.

## Features

- Export conversations in multiple formats (Markdown, JSON)
- Fetch conversation data directly from the Intercom API using your API token
- Configurable via environment variables, config files, or CLI arguments
- Batch processing with customizable batch sizes
- Robust error handling and logging
- Type-safe with full type annotations
- Extensible formatter system

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/intercom-export.git
cd intercom-export

# Install in development mode
pip install -e .
```

### Requirements

- Python 3.7 or higher
- Required packages are listed in requirements.txt

## Configuration

The tool can be configured in multiple ways (in order of precedence):

1. Command-line arguments
2. Environment variables
3. Configuration file (YAML)

### Environment Variables

- `INTERCOM_API_TOKEN`: Your Intercom API token (required for fetching conversation data)
- `INTERCOM_BASE_URL`: API base URL (default: https://api.intercom.io)
- `EXPORT_FORMAT`: Output format (markdown/json)
- `EXPORT_DIR`: Output directory for exported files
- `BATCH_SIZE`: Number of conversations per batch (default: 10)
- `DEBUG`: Enable debug logging

### Configuration File

Create a `config.yaml` file:

```yaml
intercom:
  api_token: "your-api-token"
  base_url: "https://api.intercom.io"
  api_version: "2.8"

export:
  output_format: "markdown"
  output_dir: "exports"
  batch_size: 15
  include_metadata: true
  include_context: true

debug: false
```

## Usage

### Basic Usage

Run the export script to fetch conversation data directly from the Intercom API. Make sure you have set the required environment variables (especially `INTERCOM_API_TOKEN`) and that your conversation IDs are listed in a text file (one ID per line).

```bash
python3 export_conversations.py
```

Additionally, you can pass an optional conversation ID as a command-line argument to process only that conversation. For example:

```bash
python3 export_conversations.py 57976
```

This command will:

- Read conversation IDs from `conversation_ids.txt`
- Fetch each conversation from the Intercom API
- Format the conversations into Markdown
- Write the formatted output to `conversations.md`

### Input Files

The tool supports reading conversation IDs from:
- A text file (one ID per line), default: `conversation_ids.txt`
- A YAML file (e.g., with a `conversation_ids` section)

## Output Formats

### Markdown

The Markdown format is optimized for readability and analysis:

```markdown
## Conversation 123456

**Created:** 2023-01-01 12:00:00

### Context
- **State:** open
- **Tags:** support, urgent
- **Platform:** iOS
- **Version:** 1.2.3

### Conversation

**2023-01-01 12:00:00 - John Doe (user):**
Having trouble with login...

**2023-01-01 12:05:00 - Support Agent (admin):**
Let me help you with that...
```

### JSON

The JSON format includes all conversation data in a structured format:

```json
{
  "id": "123456",
  "created_at": "2023-01-01T12:00:00Z",
  "state": "open",
  "messages": [
    {
      "author": {
        "name": "John Doe",
        "type": "user"
      },
      "body": "Having trouble with login...",
      "created_at": "2023-01-01T12:00:00Z"
    }
  ]
}
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run type checker
mypy src

# Format code
black src tests

# Run linter
flake8 src tests
```

### Project Structure

```
intercom_export/
├── api/
│   └── client.py          # Intercom API client
├── models/
│   └── conversation.py    # Data models
├── formatters/
│   ├── base.py            # Base formatter interface
│   └── markdown.py        # Markdown formatter
├── config.py              # Configuration management
└── cli.py                 # Command-line interface
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details
