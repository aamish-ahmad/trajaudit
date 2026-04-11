# Contributing to Detection Latency / TrajAudit

Thank you for your interest in contributing to this research project.

## How to Contribute

### Reporting Issues
- Use the [GitHub Issues](https://github.com/aamish-ahmad/detection-latency/issues) tab
- Include conversation examples if reporting detection failures
- Describe expected vs. observed behavior

### Adding Conversations
- Follow the schema in `data/conversations.json`
- Include phase annotations for each turn
- Adversarial conversations must follow the RAPPORT → EXTRACTION → CAPTURE → CONVERSION structure
- Benign conversations should model realistic social interactions

### Extending the Scoring Engine
- The scoring engine lives in `src/scoring.py`
- New signal categories must include empirical justification
- Maintain backward compatibility with existing conversations

### Testing
```bash
python -m pytest tests/
```

## Code Style
- Python 3.11+
- Type hints for all function signatures
- Docstrings for all public functions

## Research Ethics
- No real conversation data, usernames, or PII
- All synthetic conversations must be clearly labeled
- Follow responsible disclosure for any new adversarial patterns discovered

## Contact
Aamish Ahmad — aamish.ahmad99@gmail.com
