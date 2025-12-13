import os
from decouple import config

# Database
DATABASE_URL = config("DATABASE_URL", default="postgresql://localhost/streamfix_dev")

# Upstream provider
UPSTREAM_PROVIDER = config("UPSTREAM_PROVIDER", default="openrouter")
OPENROUTER_API_KEY = config("OPENROUTER_API_KEY", default="")
OPENROUTER_BASE_URL = config("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

# Security
STREAMFIX_MASTER_KEY = config("STREAMFIX_MASTER_KEY", default="dev-key-change-in-production")
STREAMFIX_ADMIN_TOKEN = config("STREAMFIX_ADMIN_TOKEN", default="admin-dev-token")

# App settings
ENV = config("ENV", default="dev")
LOG_LEVEL = config("LOG_LEVEL", default="info")
MAX_JSON_CHARS = config("MAX_JSON_CHARS", default=200000, cast=int)
MAX_STREAM_SECONDS = config("MAX_STREAM_SECONDS", default=90, cast=int)
MAX_CONCURRENT_STREAMS = config("MAX_CONCURRENT_STREAMS", default=50, cast=int)
MAX_RPM = config("MAX_RPM", default=120, cast=int)
DEFAULT_RULE_PACK = config("DEFAULT_RULE_PACK", default="default")

# Railway deployment
PORT = config("PORT", default=8000, cast=int)