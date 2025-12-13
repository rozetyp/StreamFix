# Contributing to StreamFix Gateway

Thank you for your interest in contributing! StreamFix is designed to be a reliable, simple JSON repair proxy for AI applications.

## Quick Start

1. **Fork the repository**
2. **Clone your fork**: `git clone https://github.com/YOUR-USERNAME/StreamFix.git`
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Run tests**: `python -m pytest tests/`
5. **Start development server**: `python -m app.main`

## Development Guidelines

### Core Principles
- **Reliability first**: Changes must not break existing functionality
- **Simple maintenance**: Avoid complex dependencies or storage requirements
- **Deterministic repair**: JSON fixes should be predictable and safe

### Before Submitting
- [ ] Tests pass: `python -m pytest tests/`
- [ ] Manual testing with known cases from `KNOWN_CASES.md`
- [ ] Documentation updated if needed

## Testing Your Changes

```bash
# Run core FSM tests
python -m pytest tests/test_fsm_fixtures.py -v

# Test specific repair cases
python -m pytest tests/ -k "repair" -v

# Manual end-to-end test
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": "Return: {\"test\": true,}"}]}'
```

## Pull Request Process

1. **Small, focused changes** - One feature/fix per PR
2. **Clear description** - Explain what and why
3. **Test coverage** - Include tests for new functionality
4. **Documentation** - Update relevant docs

## Areas for Contribution

- **Additional repair patterns** (with tests)
- **Performance optimizations** for streaming
- **Better error messages** and debugging
- **Client libraries** in other languages

## Questions?

- Check existing [issues](https://github.com/rozetyp/StreamFix/issues)
- Review [KNOWN_CASES.md](KNOWN_CASES.md) for current scope
- Open a discussion for feature ideas

We appreciate your contributions! 🚀