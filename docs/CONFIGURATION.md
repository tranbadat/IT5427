# ⚙️ Configuration Guide

## Environment Variables

File `.env` chứa tất cả cấu hình hệ thống.

### Application Settings

```bash
# Environment: development, staging, production
ENV=development

# Logging
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json         # json, text
LOG_FILE=./logs/app.log
```

### Elasticsearch Configuration

```bash
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=changeme
ELASTICSEARCH_INDEX_PREFIX=social_media
```

**Production Settings:**
- Enable authentication
- Use HTTPS
- Configure replicas for high availability
- Set up index lifecycle management (ILM)

### ClickHouse Configuration

```bash
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=social_analytics
```

**Production Settings:**
- Enable authentication
- Configure replication
- Set up partitioning strategy
- Optimize compression

### PostgreSQL Configuration

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=social_metadata
```

### Redis Configuration

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

**Use Cases:**
- Caching API responses
- Rate limiting
- Session storage
- Queue management

### Spark Configuration

```bash
SPARK_MASTER=local[*]           # local[*] for local, spark://host:port for cluster
SPARK_APP_NAME=SocialMediaAnalytics
SPARK_DRIVER_MEMORY=4g
SPARK_EXECUTOR_MEMORY=4g
```

**Cluster Settings:**
```bash
SPARK_MASTER=spark://master:7077
SPARK_DRIVER_MEMORY=8g
SPARK_EXECUTOR_MEMORY=8g
SPARK_EXECUTOR_CORES=4
```

### API Configuration

```bash
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True             # False in production
```

### Processing Configuration

```bash
# Batch processing
BATCH_SIZE=1000             # Records per batch
MAX_WORKERS=4               # Parallel workers

# Deduplication
DEDUP_THRESHOLD=0.85        # Similarity threshold (0-1)

# Alert thresholds
SPIKE_DETECTION_THRESHOLD=2.5    # Z-score threshold
VIRAL_THRESHOLD=10000            # Engagement threshold
ANOMALY_ZSCORE=3.0              # Anomaly detection
```

### Data Paths

```bash
RAW_DATA_PATH=./data/raw
PROCESSED_DATA_PATH=./data/processed
OUTPUT_DATA_PATH=./data/output
SENSITIVE_WORDS_PATH=./configs/sensitive_words.txt
```

### Monitoring

```bash
PROMETHEUS_PORT=9090
SENTRY_DSN=                 # Add your Sentry DSN for error tracking
```

## Docker Compose Configuration

### Resource Limits

Adjust trong `docker-compose.yml`:

```yaml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms2g -Xmx2g"  # Increase for production
  deploy:
    resources:
      limits:
        memory: 4g
```

### Volumes

```yaml
volumes:
  es_data:              # Elasticsearch data
  clickhouse_data:      # ClickHouse data
  postgres_data:        # PostgreSQL data
  redis_data:           # Redis data
  prometheus_data:      # Prometheus metrics
  grafana_data:         # Grafana dashboards
```

### Networks

```yaml
networks:
  social_network:
    driver: bridge
```

## Performance Tuning

### Elasticsearch

```bash
# Increase heap size
ES_JAVA_OPTS=-Xms4g -Xmx4g

# Optimize for search
index.refresh_interval=5s
index.number_of_shards=2
index.number_of_replicas=1
```

### ClickHouse

```bash
# Increase cache
max_memory_usage=10000000000
max_bytes_before_external_group_by=5000000000
```

### Spark

```bash
# Optimize for large datasets
spark.sql.shuffle.partitions=200
spark.default.parallelism=100
spark.sql.adaptive.enabled=true
```

## Security Best Practices

### Production Checklist

- [ ] Change all default passwords
- [ ] Enable HTTPS/TLS
- [ ] Set up firewall rules
- [ ] Enable authentication on all services
- [ ] Use secrets management (Vault, AWS Secrets Manager)
- [ ] Regular security updates
- [ ] Enable audit logging
- [ ] Implement rate limiting
- [ ] Add input validation
- [ ] Use environment-specific configs

### Example Secure Configuration

```bash
# .env.production
ENV=production
LOG_LEVEL=WARNING

# Use strong passwords
ELASTICSEARCH_PASSWORD=<strong-password>
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>

# Enable TLS
ELASTICSEARCH_USE_SSL=true
POSTGRES_SSL_MODE=require

# Add authentication
API_SECRET_KEY=<random-secret-key>
JWT_SECRET=<jwt-secret>
```

## Backup Configuration

### Elasticsearch Snapshots

```bash
# Configure snapshot repository
curl -X PUT "localhost:9200/_snapshot/my_backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/backup/elasticsearch"
  }
}
```

### ClickHouse Backups

```bash
# Backup database
clickhouse-client --query "BACKUP TABLE posts TO Disk('backups', 'posts_backup')"
```

## Monitoring Configuration

### Prometheus Targets

Edit `configs/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['api:8000']
  
  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch:9200']
```

### Grafana Dashboards

Import dashboards:
1. Login to Grafana (http://localhost:3000)
2. Add Prometheus datasource
3. Import dashboard ID: 
   - Elasticsearch: 266
   - ClickHouse: 882
