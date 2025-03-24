import json
import sys
from datetime import datetime

def get_conversation_ids():
    """Load conversation IDs from a text or YAML file.
    
    By default, attempts to load IDs from 'conversation_ids.txt' where each line contains one ID.
    If that fails or the file is empty, it attempts to load from 'config.yaml' using the key 'conversation_ids'.
    """
    ids = []
    # Attempt to load from conversation_ids.txt
    try:
        with open("conversation_ids.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            ids = [int(line.strip()) for line in lines if line.strip()]
    except Exception as e:
        sys.stderr.write("Warning: Could not read conversation_ids.txt: " + str(e) + "\n")
    
    # If no IDs found, attempt to load from config.yaml
    if not ids:
        try:
            import yaml
            with open("config.yaml", "r", encoding="utf-8") as f_yaml:
                config_data = yaml.safe_load(f_yaml)
                if config_data and "conversation_ids" in config_data:
                    ids = [int(x) for x in config_data["conversation_ids"]]
        except Exception as e:
            sys.stderr.write("Warning: Could not load conversation_ids from config.yaml: " + str(e) + "\n")
    
    if not ids:
        sys.stderr.write("Error: No conversation IDs provided.\n")
    
    return ids

def format_conversation(conversation):
    """Format a conversation into clean, structured markdown for LLM analysis"""
    conv_id = conversation['id']
    created_at = datetime.fromtimestamp(conversation['created_at']).strftime('%Y-%m-%d %H:%M:%S')
    
    md_content = f"\n---\n\n"
    md_content += f"# Conversation {conv_id}\n\n"
    md_content += "## Metadata\n\n"
    md_content += f"- **Conversation ID:** {conv_id}\n"
    md_content += f"- **Created At:** {created_at}\n"
    if conversation.get("custom_attributes", {}).get("support_specialist"):
         specialist = conversation["custom_attributes"]["support_specialist"]
         md_content += f"- **User Support Specialist:** {specialist}\n"
    md_content += "\n"
    
    if 'custom_attributes' in conversation:
        md_content += "### Custom Attributes\n\n"
        custom_attrs = conversation['custom_attributes']
        for key, value in custom_attrs.items():
            if value:
                md_content += f"- **{key}:** {value}\n"
        md_content += "\n"
    
    md_content += "## Messages\n\n"
    for part in conversation.get('conversation_parts', {}).get('conversation_parts', []):
        if not isinstance(part, dict):
            continue
        if part.get('part_type') in ['comment', 'assignment', 'note']:
            timestamp = datetime.fromtimestamp(part['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            author_type = part['author'].get('type', '')
            author_name = part['author'].get('name', '')
            body = (part.get('body') or '').replace('<p class="no-margin">', '').replace('</p>', '\n').strip()
            
            if body:
                md_content += f"### {timestamp}\n\n"
                md_content += f"**Author:** {author_name} ({author_type})\n\n"
                md_content += f"{body}\n\n"
    
    md_content += "---\n\n"
    return md_content

def process_conversations():
    conversation_ids = get_conversation_ids()
    if not conversation_ids:
        sys.stderr.write("No conversation IDs loaded. Please check conversation_ids.txt\n")
        return
    import os
    if not os.path.exists('raw_conversations.json'):
        with open('raw_conversations.json', 'w', encoding='utf-8') as f:
            f.write("[]")
    import subprocess
    try:
        with open('raw_conversations.json', 'r', encoding='utf-8') as f_json:
            all_conversations = json.load(f_json)
    except Exception as e:
        sys.stderr.write("Error reading raw_conversations.json: " + str(e) + "\n")
        return
    if not all_conversations:
        print("raw_conversations.json is empty. Fetching raw conversation data using export_conversations.py...")
        try:
            subprocess.run(["python3", "export_conversations.py", "--export-only"], check=True)
        except Exception as e:
            sys.stderr.write("Error running export_conversations.py: " + str(e) + "\n")
            sys.exit(1)
        try:
            with open('raw_conversations.json', 'r', encoding='utf-8') as f_json:
                all_conversations = json.load(f_json)
        except Exception as e:
            sys.stderr.write("Error reading raw_conversations.json after export: " + str(e) + "\n")
            sys.exit(1)
        if not all_conversations:
            sys.stderr.write("Error: No raw conversations loaded from raw_conversations.json after export.\n")
            sys.exit(1)
    with open(f"conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", 'w', encoding='utf-8') as f_out:
        for conversation in all_conversations:
            if str(conversation.get('id')) in [str(x) for x in conversation_ids]:
                try:
                    md_content = format_conversation(conversation)
                    f_out.write(md_content)
                except Exception as e:
                    sys.stderr.write(f"Error processing conversation {conversation.get('id')}: {str(e)}\n")
                    continue

if __name__ == "__main__":
    conv_ids = get_conversation_ids()
    if not conv_ids:
        sys.stderr.write("Error: No conversation IDs provided.\n")
        sys.exit(1)
    process_conversations()
