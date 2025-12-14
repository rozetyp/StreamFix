# Deployment Guide

Quick deployment options for StreamFix.

## Railway (Recommended)
```bash
git clone https://github.com/your-org/streamfix
cd streamfix
railway login
railway link
railway up
```

**One-click**: [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/streamfix)

## Docker
```bash
docker run -p 8000:8000 -e OPENROUTER_API_KEY=your-key streamfix/gateway
```

## Environment Variables
- `UPSTREAM_BASE_URL` - API endpoint (default: localhost:1234) 
- `OPENROUTER_API_KEY` / `OPENAI_API_KEY` - API keys
- `PORT` - Server port (default: 8000)

## Other Platforms

**Vercel**: Use `vercel deploy`
**Heroku**: Standard Python app deployment
**AWS/GCP**: Deploy as containerized service
**Local**: `streamfix serve` for development
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Add nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - streamfix
```

Run with:
```bash
docker-compose up -d
```

## Railway Deployment

### One-Click Deploy
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/streamfix)

### Manual Railway Deploy

1. **Create Railway project**:
   ```bash
   npm install -g @railway/cli
   railway login
   railway init
   ```

2. **Configure environment**:
   ```bash
   railway variables set OPENROUTER_API_KEY=your-key
   railway variables set UPSTREAM_BASE_URL=https://openrouter.ai/api/v1
   ```

3. **Deploy**:
   ```bash
   railway deploy
   ```

### Railway Configuration Files

Create `railway.toml`:
```toml
[build]
builder = "NIXPACKS"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[env]
PORT = "8000"
```

Create `nixpacks.toml`:
```toml
[phases.install]
cmds = ["pip install -e ."]

[start]
cmd = "streamfix serve --host 0.0.0.0 --port $PORT"
```

## Vercel Deployment

For serverless deployment on Vercel:

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Create `vercel.json`**:
   ```json
   {
     "functions": {
       "app/vercel_app.py": {
         "runtime": "python3.9"
       }
     },
     "routes": [
       {
         "src": "/(.*)",
         "dest": "/app/vercel_app.py"
       }
     ],
     "env": {
       "OPENROUTER_API_KEY": "@openrouter_api_key"
     }
   }
   ```

3. **Create `app/vercel_app.py`**:
   ```python
   from app.main import app
   
   # Vercel expects an ASGI app
   handler = app
   ```

4. **Deploy**:
   ```bash
   vercel --prod
   ```

## AWS Lambda

Deploy as a serverless function:

1. **Install dependencies**:
   ```bash
   pip install mangum
   ```

2. **Create `lambda_function.py`**:
   ```python
   from mangum import Mangum
   from app.main import app
   
   handler = Mangum(app)
   ```

3. **Package deployment**:
   ```bash
   zip -r streamfix-lambda.zip app/ lambda_function.py
   ```

4. **Deploy via AWS CLI**:
   ```bash
   aws lambda create-function \
     --function-name streamfix \
     --runtime python3.9 \
     --role arn:aws:iam::account:role/lambda-role \
     --handler lambda_function.handler \
     --zip-file fileb://streamfix-lambda.zip
   ```

## Google Cloud Run

1. **Create `Dockerfile`**:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY . .
   
   RUN pip install -e .
   
   EXPOSE 8080
   CMD ["streamfix", "serve", "--host", "0.0.0.0", "--port", "8080"]
   ```

2. **Deploy**:
   ```bash
   gcloud run deploy streamfix \
     --source . \
     --platform managed \
     --region us-central1 \
     --set-env-vars OPENROUTER_API_KEY=your-key
   ```

## Kubernetes

Create Kubernetes manifests:

`deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: streamfix
spec:
  replicas: 3
  selector:
    matchLabels:
      app: streamfix
  template:
    metadata:
      labels:
        app: streamfix
    spec:
      containers:
      - name: streamfix
        image: streamfix:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: streamfix-secrets
              key: api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
```

`service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: streamfix-service
spec:
  selector:
    app: streamfix
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | None |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `ANTHROPIC_API_KEY` | Anthropic API key | None |
| `UPSTREAM_BASE_URL` | Custom upstream API URL | Auto-detected |
| `PORT` | Server port | 8000 |
| `HOST` | Server host | 127.0.0.1 |
| `LOG_LEVEL` | Logging level | info |
| `DISABLE_CORS` | Disable CORS headers | false |

## Performance Tuning

### Uvicorn Configuration
```bash
# Production settings
streamfix serve \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --access-log \
  --proxy-headers
```

### Memory Management
- Artifact retention: 100 requests (configurable)
- Request timeout: 60 seconds (configurable)
- Connection pooling: Enabled by default

### Load Balancing
For high-traffic deployments, use a reverse proxy:

`nginx.conf`:
```nginx
upstream streamfix {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name api.yourcompany.com;
    
    location / {
        proxy_pass http://streamfix;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
    }
}
```

## Security Considerations

### API Key Management
- **Never commit API keys** to version control
- Use **environment variables** or **secret management** services
- **Rotate keys regularly**
- Consider **BYOK (Bring Your Own Key)** for hosted deployments

### Network Security
- **Use HTTPS** in production
- **Implement rate limiting** at the reverse proxy level
- **Restrict access** to admin endpoints
- **Monitor and log** all requests

### Data Privacy
- StreamFix **does not store** request/response data by default
- Artifacts are kept **in memory only** and expire automatically
- Consider **disabling logging** for sensitive deployments

## Monitoring

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed metrics
curl http://localhost:8000/metrics
```

### Logging
Configure structured logging:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
```

### Metrics Integration
StreamFix exposes metrics that can be scraped by Prometheus:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'streamfix'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**
   - Check upstream API connectivity
   - Verify API keys are set correctly
   - Check firewall/network settings

2. **High Memory Usage**
   - Reduce artifact retention limit
   - Monitor request patterns
   - Consider request size limits

3. **Slow Response Times**
   - Check upstream API latency
   - Monitor CPU/memory usage
   - Consider adding more workers

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=debug streamfix serve

# Check configuration
streamfix serve --dry-run
```