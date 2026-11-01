# Contributing

Thanks for your interest in RADIANT. The project is experimental research software.

## Before contributing

- Keep reference labels out of tutor prompts.
- Add tests for scoring and data-validation changes.
- Document metric assumptions and failure modes.
- Do not add real student data or identifiable learner information.
- Do not claim educational effectiveness from synthetic scenarios or model-only scores.

## Development

```bash
python -m pip install -e ".[test]"
pytest
```

## Pull requests

Describe the scientific motivation, implementation change, tests, and any impact on reproducibility or interpretation of metrics.
