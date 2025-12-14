# Contributing to StreamFix

Thanks for your interest in contributing to StreamFix! 🎉

## Quick Start

1. **Fork & Clone**
   ```bash
   git clone https://github.com/your-username/streamfix.git
   cd streamfix
   ```

2. **Development Setup**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
   pip install -e .
   ```

3. **Run Tests**
   ```bash
   python -m pytest tests/
   ```

4. **Start Development Server**
   ```bash
   streamfix serve --port 8000
   ```
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