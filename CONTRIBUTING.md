# Contributing to soul-avatar-matcher

Thank you for your interest in contributing! This document outlines the process.

## Development Setup

```bash
git clone https://github.com/soul-avatar-matcher/soul-avatar-matcher.git
cd soul-avatar-matcher
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and configure your local settings.

## Code Style

- Python 3.11+, type hints throughout
- Line length: 100 characters
- Linting: `ruff check src/ config/ scripts/`
- Type checking: `mypy src/ config/ scripts/ --ignore-missing-imports`
- Formatting: `ruff format src/`

Run both before submitting a PR:

```bash
ruff check src/ config/ scripts/
ruff format --check src/ config/ scripts/
```

## Testing

Tests are written with pytest:

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Pull Request Process

1. Create a feature branch from `develop`
2. Make your changes with clear commit messages
3. Ensure linting and type checks pass
4. Add or update tests as needed
5. Open a PR against `develop` with a clear description
6. CI must pass before merge

## Architecture

See [CLAUDE.md](CLAUDE.md) for project identity and architecture overview.
See [PROJECT-detail.md](PROJECT-detail.md) for full technical specification.
See [SECURITY.md](SECURITY.md) for security audit and guidelines.

## Questions?

Open an issue on GitHub.
