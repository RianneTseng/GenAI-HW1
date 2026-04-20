import json
import os

MEMORY_FILE = "user_memory.json"
HISTORY_FILE = "chat_history.json"

def load_memory():
    """Load long-term user memories from JSON."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_memory(memories):
    """Save current memories to user_memory.json."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=4)

def load_chat_history():
    """Load all chat sessions and history."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"Session 1": []} # Default initial state

def save_chat_history(sessions):
    """Save all active chat sessions to chat_history.json."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=4)