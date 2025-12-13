# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in StreamFix Gateway, please report it privately.

**Do not create public GitHub issues for security vulnerabilities.**

### How to Report

1. **Email**: Create a new issue and tag it as [SECURITY]
2. **Include**: 
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Assessment**: Within 1 week  
- **Fix timeline**: Depends on severity, typically within 2 weeks
- **Disclosure**: Coordinated disclosure after fix is deployed

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x.x   | ✅        |
| < 1.0   | ❌        |

## Security Considerations

### By Design
- **No persistent storage**: Reduces data exposure risk
- **Stateless operation**: No user data retention
- **Input validation**: JSON parsing with bounds checking
- **Proxy architecture**: Minimal attack surface

### Known Limitations
- **OpenRouter API key**: Required for operation, protect appropriately
- **Memory artifacts**: Request data temporarily stored in memory
- **No authentication**: Suitable for internal/trusted environments

### Deployment Security

```bash
# Environment variables (never commit)
OPENROUTER_API_KEY=your-key-here

# Railway deployment
railway variables set OPENROUTER_API_KEY=your-key-here

# Docker security
docker run --env-file .env streamfix-gateway
```

### Best Practices

1. **API key protection**: Use environment variables, never hardcode
2. **Network security**: Deploy behind HTTPS/VPN for sensitive use
3. **Monitoring**: Watch for unusual request patterns
4. **Updates**: Keep dependencies current

Thank you for helping keep StreamFix secure! 🔒