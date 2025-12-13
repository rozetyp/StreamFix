---
name: Bug Report
about: Report a bug or issue with StreamFix Gateway
title: '[BUG] '
labels: bug
assignees: ''

---

## Bug Description
A clear and concise description of what the bug is.

## Reproduction Steps
1. Request details (model, parameters)
2. Expected JSON output
3. Actual behavior

## Example Request
```bash
curl -X POST https://streamfix.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3-haiku",
    "messages": [{"role": "user", "content": "Your prompt here"}]
  }'
```

## Request ID
If available, include the `x-streamfix-request-id` from response headers.

## Environment
- Client library/language:
- StreamFix endpoint: 
- Model used:

## Additional Context
Any other relevant information about the issue.