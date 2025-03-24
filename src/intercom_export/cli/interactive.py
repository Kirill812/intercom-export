from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from typing import List, Dict, Any

def interactive_conversation_selector(conversations: List[Dict[str, Any]]) -> List[str]:
    """
    Provides an interactive CLI interface for selecting conversations.
    
    Args:
        conversations: List of conversation dictionaries. Each conversation should have an 'id',
                       and optionally 'subject' and 'updated_at' keys for display.
                       
    Returns:
        List of selected conversation IDs as strings.
    """
    # Build a mapping of conversation IDs to a preview string.
    preview_map = {}
    for conv in conversations:
        conv_id = str(conv.get("id", "N/A"))
        subject = conv.get("subject", "No subject")
        updated_at = conv.get("updated_at", "Unknown date")
        preview_map[conv_id] = f"{conv_id} - {subject} - {updated_at}"
    
    # Create an autocompleter using the conversation IDs.
    conv_completer = WordCompleter(list(preview_map.keys()), sentence=True)
    
    style = Style.from_dict({
        'prompt': 'ansicyan bold',
        'selected': 'ansigreen'
    })
    
    selected_ids = []
    
    while True:
        if selected_ids:
            print("\nSelected conversations:")
            for cid in selected_ids:
                print(f"  * {preview_map.get(cid, cid)}")
        
        print("\nEnter conversation ID to toggle selection.")
        print("Commands: 'all' to select all, 'none' to clear selection, 'done' to finish.")
        user_input = prompt(HTML("<prompt>Select conversation >>> </prompt>"), completer=conv_completer, style=style).strip()
        
        if user_input.lower() == 'done':
            break
        elif user_input.lower() == 'all':
            selected_ids = list(preview_map.keys())
            print(f"All {len(selected_ids)} conversations selected.")
        elif user_input.lower() == 'none':
            selected_ids = []
            print("All selections cleared.")
        elif user_input in preview_map:
            if user_input in selected_ids:
                selected_ids.remove(user_input)
                print(f"Removed: {preview_map[user_input]}")
            else:
                selected_ids.append(user_input)
                print(f"Added: {preview_map[user_input]}")
        else:
            print("Invalid input. Please try again.")
    
    return selected_ids
