#!/usr/bin/env python3
import sys
import json
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "src"))
import logging
logging.basicConfig(level=logging.DEBUG)
from process_conversations import process_conversations, format_conversation

def process_single_conversation(convo_id):
    import os
    if not os.path.exists('raw_conversations.json'):
        with open('raw_conversations.json', 'w', encoding='utf-8') as f:
            f.write("[]")
    try:
        with open('raw_conversations.json', 'r', encoding='utf-8') as f:
            all_conversations = json.load(f)
    except Exception as e:
        sys.stderr.write("Error reading raw_conversations.json: " + str(e) + "\n")
        sys.exit(1)
    found = None
    for conversation in all_conversations:
        if str(conversation.get('id')) == str(convo_id):
            found = conversation
            break
    if found:
        print(format_conversation(found))
    else:
        from intercom_export.api.client import IntercomClient
        import os
        import yaml
        config_data = {}
        # Try to get token from environment first
        env_token = os.environ.get("INTERCOM_API_TOKEN")
        if env_token:
            config_data["api_token"] = env_token
        try:
            with open("config.yaml", "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                intercom_cfg = cfg.get("intercom", {})
                # Set api_token from config if not already set
                config_data.setdefault("api_token", intercom_cfg.get("api_token"))
                # Also set api_version and base_url from config with defaults
                config_data["api_version"] = intercom_cfg.get("api_version", "2.8")
                config_data["base_url"] = intercom_cfg.get("base_url", "https://api.intercom.io")
        except Exception as e:
            # If config.yaml can't be opened, set default values
            config_data["api_version"] = "2.8"
            config_data["base_url"] = "https://api.intercom.io"
        if not config_data.get("api_token"):
            sys.stderr.write("INTERCOM_API_TOKEN not set and not found in config.yaml. Cannot fetch from API.\n")
            sys.exit(1)
        config_obj = type("Config", (object,), config_data)()
        client = IntercomClient(config_obj)
        fetched = client.get_conversation(convo_id)
        if fetched:
            # Append fetched conversation to raw_conversations.json with robust handling
            try:
                with open('raw_conversations.json', 'r', encoding='utf-8') as raw_file:
                    try:
                        raw_data = json.load(raw_file)
                        if not isinstance(raw_data, list):
                            raw_data = []
                    except Exception:
                        raw_data = []
            except Exception:
                raw_data = []
            raw_data.append(fetched)
            with open('raw_conversations.json', 'w', encoding='utf-8') as raw_file:
                json.dump(raw_data, raw_file, indent=2)
            sys.stderr.write("Raw conversation data updated.\n")
            
            # Append formatted conversation to conversations.md with robust handling
            formatted = format_conversation(fetched)
            try:
                with open('conversations.md', 'a', encoding='utf-8') as md_file:
                    md_file.write(formatted)
            except Exception as write_err:
                sys.stderr.write("Error writing to conversations.md: " + str(write_err) + "\n")
                with open('conversations.md', 'w', encoding='utf-8') as md_file:
                    md_file.write(formatted)
            sys.stderr.write("Formatted conversation appended to conversations.md.\n")
            print(formatted)
        else:
            sys.stderr.write(f"Conversation {convo_id} not found by API.\n")
            sys.exit(1)

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--export-only":
            from process_conversations import get_conversation_ids
            conversation_ids = get_conversation_ids()
            for convo_id in conversation_ids:
                process_single_conversation(convo_id)
        elif sys.argv[1].isdigit():
            conversation_id = sys.argv[1]
            process_single_conversation(conversation_id)
        else:
            sys.stderr.write("Invalid argument. Provide a numeric conversation id or '--export-only'.\n")
            sys.exit(1)
    else:
        process_conversations()

if __name__ == "__main__":
    main()
