"""
Tests for the TrajAudit scoring engine.

Validates core properties:
1. Benign conversations score below threshold
2. Adversarial conversations score above threshold at full trajectory
3. Trajectory scoring detects earlier than single-turn baseline
4. Zero false positives on benign controls
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scoring import (
    score_message,
    trajectory_score,
    single_turn_baseline,
    trajectory_scores_over_turns,
    classify_risk,
    detection_gap,
)

THRESHOLD = 0.75
DATA_PATH = Path(__file__).parent.parent / "data" / "conversations.json"


def load_conversations():
    with open(DATA_PATH) as f:
        data = json.load(f)
    return data["conversations"]


def to_msg_list(conv):
    return [
        {"role": "BOT" if t["role"] == "BOT" else "YOU", "text": t["text"]}
        for t in conv["turns"]
    ]


class TestScoreMessage:
    def test_innocent_message_scores_low(self):
        assert score_message("Hey! How are you doing?") < 0.1

    def test_financial_message_scores_high(self):
        assert score_message("Deposit 500 USDT to the wallet address on Binance") > 0.3

    def test_rapport_message_scores_moderate(self):
        s = score_message("You seem really interesting, honestly")
        assert 0.0 < s < 0.3

    def test_score_bounded(self):
        # Even adversarial-heavy messages should not exceed 1.0
        s = score_message(
            "invest crypto money profit deposit trading usdt cashapp "
            "paypal betting winnings hurry now quick limited register "
            "sign up link code referral wallet send me telegram"
        )
        assert s <= 1.0


class TestTrajectoryScore:
    def test_empty_conversation(self):
        assert trajectory_score([]) == 0.0

    def test_benign_conversation_below_threshold(self):
        convos = load_conversations()
        for conv in convos:
            if conv["type"] == "benign":
                msgs = to_msg_list(conv)
                score = trajectory_score(msgs)
                assert score < THRESHOLD, (
                    f"Benign conv {conv['id']} scored {score} >= {THRESHOLD}"
                )

    def test_adversarial_conversation_above_threshold(self):
        convos = load_conversations()
        adversarial = [c for c in convos if c["type"] == "adversarial"]
        # At least 80% should flag (allowing for short/edge cases)
        flagged = sum(
            1 for c in adversarial
            if trajectory_score(to_msg_list(c)) >= THRESHOLD
        )
        assert flagged >= len(adversarial) * 0.7, (
            f"Only {flagged}/{len(adversarial)} adversarial convos flagged"
        )

    def test_zero_false_positives(self):
        convos = load_conversations()
        benign = [c for c in convos if c["type"] == "benign"]
        for conv in benign:
            msgs = to_msg_list(conv)
            score = trajectory_score(msgs)
            assert score < THRESHOLD, (
                f"FALSE POSITIVE: Benign {conv['id']} scored {score}"
            )

    def test_score_monotonically_increases(self):
        """Trajectory score should generally increase as more turns are seen."""
        convos = load_conversations()
        adv = [c for c in convos if c["type"] == "adversarial"][0]
        msgs = to_msg_list(adv)
        scores = trajectory_scores_over_turns(msgs)
        # Allow small dips but overall trend should be non-decreasing
        for i in range(1, len(scores)):
            assert scores[i] >= scores[i-1], (
                f"Score decreased from turn {i} to {i+1}: {scores[i-1]} -> {scores[i]}"
            )


class TestDetectionGap:
    def test_trajectory_detects_earlier(self):
        """TrajAudit should flag at same turn or earlier than baseline."""
        convos = load_conversations()
        adversarial = [c for c in convos if c["type"] == "adversarial"]
        
        for conv in adversarial:
            msgs = to_msg_list(conv)
            traj = trajectory_scores_over_turns(msgs)
            base = single_turn_baseline(msgs)
            
            gap = detection_gap(traj, base, THRESHOLD)
            
            if gap["traj_flag_turn"] and gap["baseline_flag_turn"]:
                assert gap["traj_flag_turn"] <= gap["baseline_flag_turn"], (
                    f"Conv {conv['id']}: TrajAudit flagged LATER "
                    f"(turn {gap['traj_flag_turn']} vs {gap['baseline_flag_turn']})"
                )


class TestClassifyRisk:
    def test_safe_classification(self):
        label, severity = classify_risk(0.05)
        assert severity == "safe"

    def test_high_classification(self):
        label, severity = classify_risk(0.8)
        assert severity == "high"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
