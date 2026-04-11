<div align="center">

# 🔍 Detection Latency in Conversational AI Monitoring

### _A system that detects only after exploitation begins is not a safety system — it is a logging system._

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-TrajAudit-FF4B4B?style=for-the-badge)](https://kxibsjdcufwvh5kvh2hyqc.streamlit.app)
[![Paper](https://img.shields.io/badge/📄_Research_Paper-PDF-blue?style=for-the-badge)](docs/trajectory_blindness_paper.pdf)
[![Tests](https://img.shields.io/badge/Tests-12%2F12_Passing-brightgreen?style=for-the-badge)](#testing)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

</div>

---

## The Problem

Standard safety monitors evaluate individual messages. Adversarial conversational agents distribute their intent across many turns. Early turns look **completely normal**. The harmful objective only becomes visible at the **CAPTURE → CONVERSION** phase transition.

By then, the victim is already emotionally invested.

This structural gap is **Detection Latency**.

> Adversarial conversational agents are undetectable in early turns — not because monitors fail, but because the adversarial objective hasn't produced observable evidence yet.

---

## Key Results

A blind **Gemini 3.1 Pro** monitor evaluated 13 synthetic conversations under identical prompts at two context lengths:

| Condition | n | NORMAL | UNCERTAIN | SUSPICIOUS |
|-----------|---|--------|-----------|------------|
| Adversarial, turns 1–5 | 3 | 2 | 1 | **0** |
| Adversarial, full trajectory | 3 | 0 | 0 | **3** |
| Benign, full trajectory | 3 | **3** | 0 | 0 |

**Zero false positives.** Detection activates only after the CAPTURE phase — when the victim is already trapped.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TrajAudit Pipeline                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Input: Multi-turn conversation                                │
│     │                                                           │
│     ▼                                                           │
│   ┌──────────────────────────────────────┐                      │
│   │  Signal Extraction Layer             │                      │
│   │  ├── Financial signals    (w=0.15)   │                      │
│   │  ├── Urgency signals      (w=0.10)   │                      │
│   │  ├── Authority signals    (w=0.08)   │                      │
│   │  ├── Rapport signals      (w=0.04)   │                      │
│   │  └── Extraction signals   (w=0.18)   │                      │
│   └──────────────┬───────────────────────┘                      │
│                  │                                               │
│                  ▼                                               │
│   ┌──────────────────────────────────────┐                      │
│   │  Trajectory Accumulation Engine      │                      │
│   │  score(t) = score(t-1) + s*(1-0.3c) │                      │
│   │  Cumulative risk with decay          │                      │
│   └──────────────┬───────────────────────┘                      │
│                  │                                               │
│                  ▼                                               │
│   ┌──────────────────────────────────────┐                      │
│   │  Phase Classification                │                      │
│   │  🟢 Opening    (0.00 – 0.15)        │                      │
│   │  🟡 Rapport    (0.15 – 0.35)        │                      │
│   │  🟠 Capture    (0.35 – 0.60)        │                      │
│   │  🔴 Conversion (0.60+)              │                      │
│   └──────────────┬───────────────────────┘                      │
│                  │                                               │
│                  ▼                                               │
│   ┌──────────────────────────────────────┐                      │
│   │  Detection Gap Analysis              │                      │
│   │  Compares trajectory vs single-turn  │                      │
│   │  Quantifies # turns of early warning │                      │
│   └──────────────────────────────────────┘                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## The 4 Adversarial Phases

Grounded in **6 months of empirical observation** of 4 real deployed hybrid human-bot scam pipelines on Snapchat:

```
Phase           │ Behavior                                    │ Monitor Response
────────────────┼─────────────────────────────────────────────┼─────────────────
🟢 RAPPORT      │ Normal social interaction, reciprocal chat  │ NORMAL ✓
🟡 EXTRACTION   │ Curiosity, shared interests, flattery       │ NORMAL ✓
🟠 CAPTURE      │ Authority, social proof, platform redirect  │ UNCERTAIN
🔴 CONVERSION   │ Payment request, wallet, subscription       │ SUSPICIOUS
```

The monitor's classification at each phase is **correct** — the adversarial signal genuinely isn't present in early turns. The problem is structural: by CONVERSION, the victim is already invested.

---

## The Handoff Signature

A novel **content-agnostic detection primitive** undocumented in published literature:

| Layer | Latency | Trigger |
|-------|---------|---------|
| Scripted automation | ~5 seconds | Routine conversational turns |
| Human operator | 90–120 minutes | Edge cases (bot accusations, resistance) |

This latency discontinuity, co-occurring with sentence-boundary style shifts, provides a complementary detection channel requiring **no NLP, no classifier, and no conversation content**.

---

## Dataset

**13 synthetic conversations** (10 adversarial, 3 benign) in [`data/conversations.json`](data/conversations.json):

- Phase-annotated at every turn
- Each adversarial conversation instantiates distinct policy variant combinations
- Generated by Claude Sonnet 4.6 using the empirically documented phase structure
- No real conversation text, usernames, or explicit content

### Policy Variants Covered:
- Geographic personalization
- Accelerated intimacy
- DARVO defense (on bot accusation)
- Platform redirect
- Vulnerability exploit
- Social proof / authority
- Urgency pressure

### Scam Types:
Sports betting, crypto investment, romance-investment hybrid, tech job scam, charity/donation scam, giveaway/raffle scam, subscription trap, sextortion setup

---

## Quick Start

### Run Locally
```bash
git clone https://github.com/aamish-ahmad/detection-latency.git
cd detection-latency
pip install -r requirements.txt
streamlit run app.py
```

### Use the Scoring Engine
```python
from src.scoring import trajectory_score, single_turn_baseline, detection_gap

conversation = [
    {"role": "BOT", "text": "Hey! How are you?"},
    {"role": "YOU", "text": "Good thanks!"},
    {"role": "BOT", "text": "Want to join my crypto trading group? 300% returns."},
    {"role": "BOT", "text": "Deposit 500 USDT to this wallet address."},
]

# Trajectory-aware score
risk = trajectory_score(conversation)
print(f"Trajectory Risk: {risk}")

# Compare with single-turn baseline
traj_scores = [trajectory_score(conversation[:i+1]) for i in range(len(conversation))]
baseline = single_turn_baseline(conversation)
gap = detection_gap(traj_scores, baseline)
print(f"Detection gap: {gap['description']}")
```

---

## Project Structure

```
detection-latency/
├── app.py                      # Streamlit interactive demo (live at Streamlit Cloud)
├── requirements.txt            # Dependencies
├── LICENSE                     # MIT License
├── CONTRIBUTING.md             # Contribution guidelines
├── data/
│   └── conversations.json      # 13 phase-annotated conversations (10 adv, 3 benign)
├── src/
│   ├── __init__.py
│   ├── scoring.py              # TrajAudit scoring engine
│   └── data_loader.py          # Dataset loader utilities
├── tests/
│   ├── __init__.py
│   └── test_scoring.py         # 12 tests — scoring, gap detection, zero FP
├── docs/
│   └── trajectory_blindness_paper.pdf  # Research paper
└── .devcontainer/
    └── devcontainer.json       # GitHub Codespace config
```

---

## Testing

```bash
python -m pytest tests/ -v
```

```
tests/test_scoring.py::TestScoreMessage::test_innocent_message_scores_low PASSED
tests/test_scoring.py::TestScoreMessage::test_financial_message_scores_high PASSED
tests/test_scoring.py::TestScoreMessage::test_rapport_message_scores_moderate PASSED
tests/test_scoring.py::TestScoreMessage::test_score_bounded PASSED
tests/test_scoring.py::TestTrajectoryScore::test_empty_conversation PASSED
tests/test_scoring.py::TestTrajectoryScore::test_benign_conversation_below_threshold PASSED
tests/test_scoring.py::TestTrajectoryScore::test_adversarial_conversation_above_threshold PASSED
tests/test_scoring.py::TestTrajectoryScore::test_zero_false_positives PASSED
tests/test_scoring.py::TestTrajectoryScore::test_score_monotonically_increases PASSED
tests/test_scoring.py::TestDetectionGap::test_trajectory_detects_earlier PASSED
tests/test_scoring.py::TestClassifyRisk::test_safe_classification PASSED
tests/test_scoring.py::TestClassifyRisk::test_high_classification PASSED

12 passed in 0.07s
```

---

## Live Demo

🔗 **[TrajAudit — Interactive Demo](https://kxibsjdcufwvh5kvh2hyqc.streamlit.app)**

Features:
- Browse all 13 conversations with phase annotations
- Real-time trajectory scoring visualization
- Side-by-side comparison: TrajAudit vs single-turn classifier
- Optional Gemini API integration for live LLM comparison
- Test your own conversations

---

## Contributions & Future Work

- Expand evaluation to more LLM monitors (Opus 4.6, GPT-5)
- Quantify detection latency per-turn with confidence scoring
- Integrate the Handoff Signature as a multi-channel detection system
- Larger-scale benchmark with 100+ synthetic conversations
- Real-time integration with messaging platform APIs

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Research Paper

**"Trajectory Blindness as Detection Latency in Conversational Monitoring"**

Aamish Ahmad · VIT Vellore · MSc Data Science 2026

📄 [Read the full paper](docs/trajectory_blindness_paper.pdf)

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Visualization | Plotly |
| Scoring Engine | Python (custom trajectory accumulation) |
| LLM Integration | Google Gemini API (optional) |
| Dataset | JSON (phase-annotated synthetic conversations) |
| Testing | pytest |
| Deployment | Streamlit Cloud |

---

## Author

**Aamish Ahmad**  
MSc Data Science, VIT Vellore · 2026  
📧 aamish.ahmad99@gmail.com  
🔗 [GitHub](https://github.com/aamish-ahmad)

---

## License

MIT License — see [LICENSE](LICENSE) for details.
