"""
Data loader for the Detection Latency conversation dataset.

Loads the 13-conversation synthetic dataset (10 adversarial, 3 benign)
with phase annotations and monitor evaluation results.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

DATA_PATH = Path(__file__).parent.parent / "data" / "conversations.json"


def load_dataset() -> Dict:
    """Load the full conversation dataset with metadata."""
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def get_conversations() -> List[Dict]:
    """Return list of all conversations."""
    return load_dataset()["conversations"]


def get_adversarial() -> List[Dict]:
    """Return only adversarial conversations."""
    return [c for c in get_conversations() if c["type"] == "adversarial"]


def get_benign() -> List[Dict]:
    """Return only benign control conversations."""
    return [c for c in get_conversations() if c["type"] == "benign"]


def get_conversation_by_id(conv_id: str) -> Optional[Dict]:
    """Look up a conversation by its ID."""
    for c in get_conversations():
        if c["id"] == conv_id:
            return c
    return None


def to_message_list(conversation: Dict) -> List[Dict]:
    """Convert a conversation dict to the message format expected by the scoring engine.
    
    Maps 'USER' role to 'YOU' for backward compatibility with the app display.
    """
    return [
        {"role": "BOT" if t["role"] == "BOT" else "YOU", "text": t["text"]}
        for t in conversation["turns"]
    ]


def get_monitor_results_table() -> List[Dict]:
    """Generate the paper's Table 1: detection pattern across conditions.
    
    Returns data suitable for display as the core results table.
    """
    results = []
    adversarial = get_adversarial()
    benign = get_benign()
    
    # Adversarial at turns 1-5
    early_normal = sum(1 for c in adversarial[:3] if c["monitor_result_early"] == "NORMAL")
    early_uncertain = sum(1 for c in adversarial[:3] if c["monitor_result_early"] == "UNCERTAIN")
    early_suspicious = sum(1 for c in adversarial[:3] if c["monitor_result_early"] == "SUSPICIOUS")
    
    results.append({
        "condition": "Adversarial, turns 1-5",
        "n": 3,
        "NORMAL": early_normal,
        "UNCERTAIN": early_uncertain,
        "SUSPICIOUS": early_suspicious
    })
    
    # Adversarial at full trajectory
    full_normal = sum(1 for c in adversarial[:3] if c["monitor_result_full"] == "NORMAL")
    full_uncertain = sum(1 for c in adversarial[:3] if c["monitor_result_full"] == "UNCERTAIN")
    full_suspicious = sum(1 for c in adversarial[:3] if c["monitor_result_full"] == "SUSPICIOUS")
    
    results.append({
        "condition": "Adversarial, full trajectory",
        "n": 3,
        "NORMAL": full_normal,
        "UNCERTAIN": full_uncertain,
        "SUSPICIOUS": full_suspicious
    })
    
    # Benign at full trajectory
    results.append({
        "condition": "Benign, full trajectory",
        "n": 3,
        "NORMAL": 3,
        "UNCERTAIN": 0,
        "SUSPICIOUS": 0
    })
    
    return results
