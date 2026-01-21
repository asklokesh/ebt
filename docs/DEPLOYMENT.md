# EBT Eligibility Classification System - Deployment Guide

## Deployment Options

1. **Local Development** - For development and testing
2. **Docker Compose** - For local production-like environment
3. **Render** - Cloud deployment with Blueprint
4. **Manual Cloud Deployment** - AWS, GCP, Azure

---

## Local Development

### Prerequisites

- Python 3.11+
- pip or uv package manager
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/asklokesh/ebt.git
cd ebt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### Run API

```bash
# Development mode with auto-reload
uvicorn src.main:app --reload --port 8000

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Run UI

```bash
# In a separate terminal
streamlit run ui/app.py
```

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_rule_validator.py -v
```

---

## Docker Compose Deployment

### Prerequisites

- Docker
- Docker Compose

### Quick Start

```bash
# Build and start services
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Access Points

- API: http://localhost:8000
- UI: http://localhost:8501
- API Docs: http://localhost:8000/docs

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required for AI reasoning (optional without it)
GOOGLE_API_KEY=your_google_api_key

# Optional for enhanced product lookup
USDA_API_KEY=your_usda_api_key
```

### Data Persistence

Docker volumes are used for data persistence:

- `ebt-data`: SQLite database
- `chromadb-data`: ChromaDB vector store

To reset data:
```bash
docker-compose down -v  # Remove volumes
docker-compose up --build
```

---

## Render Deployment

### Prerequisites

- Render account (https://render.com)
- GitHub repository with the code

### Steps

1. **Fork Repository**
   - Fork https://github.com/asklokesh/ebt to your account

2. **Create Blueprint**
   - Go to Render Dashboard
   - Click "New" -> "Blueprint"
   - Connect your GitHub account
   - Select the forked repository

3. **Configure Services**

   The `render.yaml` file defines two services:
   - `ebt-api`: FastAPI backend
   - `ebt-ui`: Streamlit frontend

4. **Set Environment Variables**

   In Render dashboard, add:
   - `GOOGLE_API_KEY`: Your Google API key
   - `USDA_API_KEY`: Your USDA API key (optional)

5. **Deploy**
   - Click "Apply" to deploy
   - Wait for build and deployment
   - Access your services at provided URLs

### Custom Domain

1. Go to service settings
2. Add custom domain
3. Update DNS records as instructed

---

## AWS Deployment

### Using Elastic Container Service (ECS)

1. **Build and Push Images**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

   # Build and tag
   docker build -t ebt-api .
   docker tag ebt-api:latest <account>.dkr.ecr.us-east-1.amazonaws.com/ebt-api:latest

   # Push
   docker push <account>.dkr.ecr.us-east-1.amazonaws.com/ebt-api:latest
   ```

2. **Create ECS Task Definition**
   - Define container settings
   - Set environment variables
   - Configure resource limits

3. **Create ECS Service**
   - Select task definition
   - Configure load balancer
   - Set auto-scaling rules

### Using EC2

1. **Launch EC2 Instance**
   - Amazon Linux 2 or Ubuntu
   - t3.medium or larger
   - Configure security groups (ports 8000, 8501)

2. **Install Dependencies**
   ```bash
   sudo yum install -y python3.11 python3.11-pip
   # or for Ubuntu
   sudo apt install -y python3.11 python3.11-venv
   ```

3. **Deploy Application**
   ```bash
   git clone https://github.com/asklokesh/ebt.git
   cd ebt
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Use systemd for Process Management**

   Create `/etc/systemd/system/ebt-api.service`:
   ```ini
   [Unit]
   Description=EBT Classification API
   After=network.target

   [Service]
   User=ec2-user
   WorkingDirectory=/home/ec2-user/ebt
   ExecStart=/home/ec2-user/ebt/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
   Restart=always
   Environment="GOOGLE_API_KEY=your_key"

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   sudo systemctl enable ebt-api
   sudo systemctl start ebt-api
   ```

---

## Production Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ENV` | No | Environment (development/production) |
| `LOG_LEVEL` | No | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `DATABASE_PATH` | No | Path to SQLite database |
| `CHROMADB_PATH` | No | Path to ChromaDB storage |
| `GOOGLE_API_KEY` | No* | Google Gemini API key |
| `USDA_API_KEY` | No | USDA FoodData API key |
| `API_URL` | No | API URL for UI (default: http://localhost:8000) |

*Required for AI reasoning; system falls back to rule-based only without it.

### Recommended Production Settings

```bash
# .env.production
ENV=production
LOG_LEVEL=INFO
DATABASE_PATH=/data/ebt/ebt_classification.db
CHROMADB_PATH=/data/ebt/chromadb

# Security
# Add these in production
SECRET_KEY=your_secret_key
API_KEY_HEADER=X-API-Key
CORS_ORIGINS=https://yourdomain.com
```

### Nginx Configuration (Optional)

```nginx
upstream ebt_api {
    server 127.0.0.1:8000;
}

upstream ebt_ui {
    server 127.0.0.1:8501;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://ebt_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name ui.yourdomain.com;

    location / {
        proxy_pass http://ebt_ui;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Monitoring

### Health Checks

API health endpoint: `GET /health`

```bash
curl http://localhost:8000/health
```

### Logging

Logs are in JSON format for easy parsing:

```json
{
  "event": "classification_completed",
  "product_id": "SKU-123",
  "is_eligible": true,
  "confidence": 0.95,
  "timestamp": "2026-01-21T15:30:00Z"
}
```

### Recommended Monitoring Stack

1. **Logs**: ELK Stack or CloudWatch Logs
2. **Metrics**: Prometheus + Grafana
3. **Tracing**: Jaeger or AWS X-Ray
4. **Alerts**: PagerDuty or OpsGenie

---

## Troubleshooting

### Common Issues

**API won't start**
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip install -r requirements.txt

# Check environment variables
printenv | grep -E "(GOOGLE|USDA|DATABASE)"
```

**ChromaDB errors**
```bash
# Reset vector store
rm -rf data/chromadb
# Restart API
```

**Database locked**
```bash
# Check for zombie processes
ps aux | grep uvicorn
kill <pid>
```

**High memory usage**
- Reduce ChromaDB batch sizes
- Lower max_concurrent in bulk classification
- Use smaller embedding model

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG uvicorn src.main:app --reload
```
