"""
TrajAudit Scoring Engine — Trajectory-aware risk accumulation for conversational monitoring.

The core insight: adversarial conversations distribute malicious intent across turns.
Single-turn classifiers miss this because each turn in isolation scores low. The trajectory
score accumulates evidence across the full conversation, detecting the phase-structured
manipulation pattern that defines real-world hybrid human-bot scam pipelines.

Phase Model:
    RAPPORT     → Behaviorally indistinguishable from normal social interaction
    EXTRACTION  → Curiosity, shared interests, flattery, information gathering
    CAPTURE     → Authority signals, social proof, platform redirect, urgency
    CONVERSION  → Payment request, wallet address, subscription, credential harvesting
"""

from typing import List, Dict, Optional, Tuple

# ── Signal Taxonomy ──────────────────────────────────────────────────────────
# Derived from 6 months of empirical observation of 4 deployed adversarial
# pipelines on Snapchat. Each category maps to observable behavioral patterns
# in the RAPPORT → EXTRACTION → CAPTURE → CONVERSION phase structure.

SIGNAL_WEIGHTS = {
    "financial": {
        "weight": 0.15,
        "keywords": [
            "invest", "crypto", "money", "profit", "deposit", "trading", "$",
            "usdt", "cashapp", "paypal", "betting", "winnings", "bet", "30%",
            "70%", "payout", "earn", "win", "risk-free", "forex", "returns",
            "wallet", "transfer", "200", "500", "1000", "4200", "bitcoin",
            "zelle", "fee", "refundable", "paycheck", "shipping"
        ],
        "description": "Financial terms indicating extraction/conversion intent"
    },
    "urgency": {
        "weight": 0.10,
        "keywords": [
            "hurry", "closing", "now", "quick", "limited", "first time",
            "last chance", "tonight", "immediately", "clockwork", "deadline",
            "tomorrow", "before midnight", "spots fill", "before friday"
        ],
        "description": "Temporal pressure signals to accelerate decision-making"
    },
    "authority": {
        "weight": 0.08,
        "keywords": [
            "mentor", "team", "expert", "years", "reliable", "uncle", "analyst",
            "presidents", "clubs", "uk", "tipico", "settlement", "singapore",
            "algorithm", "signals", "whale", "goldman", "coach", "recruiter",
            "global", "200+", "300+", "500+", "2000+"
        ],
        "description": "Social proof and authority indicators used in CAPTURE phase"
    },
    "rapport": {
        "weight": 0.04,
        "keywords": [
            "interesting", "noticed", "usually", "something told me", "honestly",
            "nervous too", "totally understand", "life changing", "genuine",
            "different", "impressive", "cutie", "vibe", "click"
        ],
        "description": "Rapport-building language — low weight individually, contextualizes trajectory"
    },
    "extraction": {
        "weight": 0.18,
        "keywords": [
            "platform", "register", "sign up", "join", "link", "code", "referral",
            "stake", "upfront", "deposit", "wallet", "send me", "cashapp",
            "bit.ly", "binance", "telegram", "verify", "age verification",
            "card info", "protonmail"
        ],
        "description": "Direct extraction signals — highest weight, marks CONVERSION phase"
    }
}


def score_message(text: str) -> float:
    """Score a single message for adversarial signal density.
    
    Returns a float [0, 1] representing how many adversarial signals
    are present in this individual message.
    """
    t = text.lower()
    score = 0.0
    for category, config in SIGNAL_WEIGHTS.items():
        weight = config["weight"]
        for keyword in config["keywords"]:
            if keyword in t:
                score += weight
    return min(round(score, 3), 1.0)


def trajectory_score(messages: List[Dict]) -> float:
    """Compute cumulative trajectory risk score across all BOT messages.
    
    This is the core algorithm: risk accumulates across turns with
    diminishing returns (the 0.3 decay factor prevents saturation).
    The trajectory score captures the behavioral arc — from innocent
    RAPPORT through progressive EXTRACTION to CONVERSION.
    
    Args:
        messages: List of message dicts with 'role' and 'text' keys
        
    Returns:
        Cumulative risk score [0, 0.99]
    """
    cumulative = 0.0
    for msg in messages:
        if msg["role"] in ("BOT", "bot"):
            signal = score_message(msg["text"])
            # Accumulate with decay to model trajectory arc
            cumulative = min(cumulative + signal * (1 - cumulative * 0.3), 0.99)
    return round(cumulative, 3)


def single_turn_baseline(messages: List[Dict]) -> List[float]:
    """Simulate a single-turn classifier (peak score across individual messages).
    
    This represents the standard approach: evaluate each message independently
    and take the maximum observed score. Demonstrates the Detection Latency
    gap — early messages score near zero because adversarial intent is not
    yet present in the text.
    
    Args:
        messages: List of message dicts with 'role' and 'text' keys
        
    Returns:
        List of peak single-turn scores at each conversation position
    """
    scores = []
    peak = 0.0
    for msg in messages:
        if msg["role"] in ("BOT", "bot"):
            peak = max(peak, score_message(msg["text"]) * 1.1)
        scores.append(round(min(peak, 0.99), 2))
    return scores


def trajectory_scores_over_turns(messages: List[Dict]) -> List[float]:
    """Compute trajectory score at each turn position.
    
    Returns a list where index i is the trajectory score using
    messages[0:i+1], enabling visualization of the risk accumulation
    curve alongside the single-turn baseline.
    """
    return [trajectory_score(messages[:i+1]) for i in range(len(messages))]


def classify_risk(score: float) -> Tuple[str, str]:
    """Map a risk score to a phase label and severity.
    
    Returns:
        Tuple of (phase_label, severity) where severity is one of
        'safe', 'low', 'medium', 'high'
    """
    if score >= 0.6:
        return "🔴 Extraction", "high"
    elif score >= 0.35:
        return "🟠 Trust Building", "medium"
    elif score >= 0.15:
        return "🟡 Rapport", "low"
    else:
        return "🟢 Opening", "safe"


def detection_gap(
    traj_scores: List[float],
    baseline_scores: List[float],
    threshold: float = 0.75
) -> Dict:
    """Compute the detection latency gap between trajectory and baseline scoring.
    
    This quantifies the paper's core finding: how many turns earlier does
    trajectory-aware monitoring detect adversarial behavior compared to
    single-turn classification?
    
    Returns:
        Dict with 'traj_flag_turn', 'baseline_flag_turn', 'gap_turns',
        and 'description' explaining the gap
    """
    traj_flag = next((i+1 for i, s in enumerate(traj_scores) if s >= threshold), None)
    base_flag = next((i+1 for i, s in enumerate(baseline_scores) if s >= threshold), None)
    
    gap = None
    if traj_flag and base_flag:
        gap = base_flag - traj_flag
    
    return {
        "traj_flag_turn": traj_flag,
        "baseline_flag_turn": base_flag,
        "gap_turns": gap,
        "description": _describe_gap(traj_flag, base_flag, gap)
    }


def _describe_gap(traj_flag, base_flag, gap):
    if traj_flag and not base_flag:
        return f"TrajAudit flagged at turn {traj_flag}. Single-turn baseline never reached threshold."
    elif traj_flag and base_flag and gap and gap > 0:
        return f"TrajAudit flagged {gap} turns earlier (turn {traj_flag} vs turn {base_flag})."
    elif traj_flag and base_flag and gap == 0:
        return "Both methods flagged at the same turn."
    elif not traj_flag:
        return "Conversation classified as safe by both methods."
    return "Unable to compute gap."
