# 📖 Deployment Guide

## Production Deployment

### Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker & Docker Compose
- 16GB+ RAM
- 100GB+ SSD storage
- Python 3.9+
- SSL certificates (for HTTPS)

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Python
sudo apt install python3.9 python3.9-venv python3-pip -y
```

### 2. Application Deployment

```bash
# Create app directory
sudo mkdir -p /opt/social-analytics
cd /opt/social-analytics

# Clone repository
git clone <repository-url> .

# Create production environment
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup production config
cp .env.example .env.production
nano .env.production  # Edit with production values
```

### 3. Production Configuration

Edit `.env.production`:

```bash
# Production mode
ENV=production
LOG_LEVEL=WARNING

# Strong passwords
ELASTICSEARCH_PASSWORD=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Resource allocation
SPARK_DRIVER_MEMORY=8g
SPARK_EXECUTOR_MEMORY=8g
BATCH_SIZE=5000
MAX_WORKERS=8

# Security
API_SECRET_KEY=$(openssl rand -hex 32)
```

### 4. Docker Production Setup

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.1
    environment:
      - "ES_JAVA_OPTS=-Xms8g -Xmx8g"
      - xpack.security.enabled=true
    deploy:
      resources:
        limits:
          memory: 16g
    restart: always
    
  # ... other services with production settings
```

Start services:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Nginx Reverse Proxy

Install Nginx:

```bash
sudo apt install nginx -y
```

Create config `/etc/nginx/sites-available/social-analytics`:

```nginx
upstream api_backend {
    server 127.0.0.1:8000;
}

upstream dashboard_backend {
    server 127.0.0.1:8050;
}

server {
    listen 80;
    server_name analytics.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name analytics.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/analytics.crt;
    ssl_certificate_key /etc/ssl/private/analytics.key;
    
    # API
    location /api/ {
        proxy_pass http://api_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Dashboard
    location / {
        proxy_pass http://dashboard_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable and start:

```bash
sudo ln -s /etc/nginx/sites-available/social-analytics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Systemd Services

Create `/etc/systemd/system/social-analytics-api.service`:

```ini
[Unit]
Description=Social Analytics API
After=network.target docker.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/social-analytics
Environment="PATH=/opt/social-analytics/venv/bin"
ExecStart=/opt/social-analytics/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/social-analytics-dashboard.service`:

```ini
[Unit]
Description=Social Analytics Dashboard
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/social-analytics
Environment="PATH=/opt/social-analytics/venv/bin"
ExecStart=/opt/social-analytics/venv/bin/python src/dashboard/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable social-analytics-api
sudo systemctl enable social-analytics-dashboard
sudo systemctl start social-analytics-api
sudo systemctl start social-analytics-dashboard
```

### 7. Cron Jobs

Setup ETL cron job:

```bash
sudo crontab -e
```

Add:

```cron
# Run ETL every hour
0 * * * * cd /opt/social-analytics && /opt/social-analytics/venv/bin/python src/main_etl.py >> /var/log/social-analytics/etl.log 2>&1

# Backup daily at 2 AM
0 2 * * * /opt/social-analytics/scripts/backup.sh
```

### 8. Monitoring Setup

Install monitoring stack:

```bash
# Already included in docker-compose
# Access at:
# - Grafana: https://analytics.yourdomain.com:3000
# - Prometheus: https://analytics.yourdomain.com:9090
```

### 9. Backup Strategy

Create `/opt/social-analytics/scripts/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backup/social-analytics"
DATE=$(date +%Y%m%d_%H%M%S)

# Elasticsearch snapshot
curl -X PUT "localhost:9200/_snapshot/my_backup/snapshot_$DATE?wait_for_completion=true"

# ClickHouse backup
docker exec social_clickhouse clickhouse-client --query "BACKUP DATABASE social_analytics TO Disk('backups', 'backup_$DATE')"

# PostgreSQL backup
docker exec social_postgres pg_dump -U postgres social_metadata > $BACKUP_DIR/postgres_$DATE.sql

# Compress and upload to S3 (optional)
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/*_$DATE.*
# aws s3 cp $BACKUP_DIR/backup_$DATE.tar.gz s3://your-bucket/backups/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

Make executable:

```bash
chmod +x /opt/social-analytics/scripts/backup.sh
```

### 10. Security Hardening

```bash
# Firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Automatic updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### 11. Monitoring & Alerts

Setup alerting in Prometheus (`configs/prometheus.yml`):

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - 'alerts.yml'
```

Create `configs/alerts.yml`:

```yaml
groups:
  - name: social_analytics
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.05
        for: 10m
        annotations:
          summary: "High error rate detected"
          
      - alert: HighMemoryUsage
        expr: memory_usage_percent > 90
        for: 5m
        annotations:
          summary: "High memory usage"
```

### 12. Scaling

#### Horizontal Scaling

Add more API workers:

```bash
# In systemd service
ExecStart=/opt/social-analytics/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 8
```

#### Elasticsearch Cluster

Update `docker-compose.prod.yml`:

```yaml
elasticsearch-node1:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.1
  environment:
    - node.name=es-node1
    - cluster.name=social-analytics
    - discovery.seed_hosts=es-node2,es-node3
    - cluster.initial_master_nodes=es-node1,es-node2,es-node3

elasticsearch-node2:
  # Similar config
  
elasticsearch-node3:
  # Similar config
```

### 13. Health Checks

Create monitoring script:

```bash
#!/bin/bash
# /opt/social-analytics/scripts/health_check.sh

# Check API
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "API is down, restarting..."
    systemctl restart social-analytics-api
fi

# Check Elasticsearch
if ! curl -f http://localhost:9200 > /dev/null 2>&1; then
    echo "Elasticsearch is down"
    docker-compose restart elasticsearch
fi

# Check ClickHouse
if ! docker exec social_clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
    echo "ClickHouse is down"
    docker-compose restart clickhouse
fi
```

Add to cron:

```cron
*/5 * * * * /opt/social-analytics/scripts/health_check.sh
```

### 14. SSL/TLS Setup

Using Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d analytics.yourdomain.com
```

### 15. Performance Tuning

System tuning for production:

```bash
# Increase file descriptors
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Network tuning
echo "net.core.somaxconn=65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog=8192" >> /etc/sysctl.conf
sysctl -p
```

### Checklist

- [ ] Server setup complete
- [ ] Docker services running
- [ ] Production configs applied
- [ ] Nginx configured with SSL
- [ ] Systemd services enabled
- [ ] Cron jobs scheduled
- [ ] Backups configured
- [ ] Monitoring setup
- [ ] Firewall configured
- [ ] Health checks running
- [ ] Logs rotating
- [ ] Alerts configured
