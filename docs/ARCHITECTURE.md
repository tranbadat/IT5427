# 🎓 Architecture & Design Document

## System Overview

Hệ thống phân tích dữ liệu mạng xã hội với khả năng xử lý hàng triệu bài viết, phát hiện sự kiện, và cung cấp insights thời gian thực.

## Architecture Layers

### 1. Data Ingestion Layer

**Components:**
- CSV File Readers
- Data Validators
- Schema Mappers

**Responsibilities:**
- Read from multiple data sources
- Validate data integrity
- Map to unified schema

**Technologies:**
- Pandas for batch processing
- Pydantic for validation
- Custom parsers for each platform

### 2. ETL Processing Layer

**Components:**
- Data Cleaner
- Deduplicator
- Text Analyzer
- Engagement Calculator

**Workflow:**
```
Raw Data → Clean → Deduplicate → Analyze → Enrich → Store
```

**Key Features:**
- Multi-stage cleaning pipeline
- Similarity-based deduplication (TF-IDF + Cosine Similarity)
- NLP processing (spaCy, NLTK)
- Engagement scoring algorithm

### 3. Storage Layer

**Elasticsearch:**
- **Purpose:** Full-text search, aggregations
- **Data:** Processed posts with text analysis
- **Indices:** posts, processed, events, metrics
- **Access Pattern:** Search queries, trending analysis

**ClickHouse:**
- **Purpose:** OLAP analytics, time-series
- **Data:** Structured post data, metrics
- **Tables:** posts, metrics_hourly, events, user_analytics
- **Access Pattern:** Aggregations, time-series queries

**PostgreSQL:**
- **Purpose:** Metadata, configurations
- **Data:** Job status, system state
- **Access Pattern:** Transactional

**Redis:**
- **Purpose:** Caching, rate limiting
- **Data:** API cache, session data
- **Access Pattern:** Key-value lookups

### 4. Analysis Layer

**Text Analysis:**
- Sentiment analysis (TextBlob)
- Language detection (LangDetect)
- Named Entity Recognition (spaCy)
- Keyword extraction (TF-IDF)

**Event Detection:**
- Volume spike detection (Z-score)
- Keyword burst detection
- Event clustering (temporal + keyword overlap)
- Anomaly detection

**Metrics:**
- Engagement scoring: `likes*1 + shares*3 + comments*2 + views*0.01`
- Virality detection: engagement threshold + growth rate
- Trend scoring: statistical analysis of time-series

### 5. Streaming Layer

**Spark Structured Streaming:**
- Real-time data ingestion
- Window-based aggregations
- Watermarking for late data
- Stateful processing

**Features:**
- File stream monitoring
- Cross-platform data joining
- Real-time trending detection
- Viral post alerts

### 6. API Layer

**FastAPI:**
- RESTful endpoints
- Async request handling
- Automatic OpenAPI docs
- CORS support

**Endpoints:**
- Search & filter
- Statistics & metrics
- Trending analysis
- Event detection
- Time-series data

### 7. Visualization Layer

**Dash Dashboard:**
- Real-time charts
- Platform comparisons
- Trending keywords
- Viral posts feed
- Event timeline

**Components:**
- Time-series plots (Plotly)
- Distribution charts
- Top N lists
- Interactive filters

### 8. Monitoring Layer

**Prometheus:**
- Metrics collection
- Time-series storage
- Alerting rules

**Grafana:**
- Dashboard visualization
- Alert management
- Multi-source data

## Data Flow

### Batch Processing Flow

```
CSV Files (data/)
    ↓
DataLoader
    ↓
SocialMediaPost (unified schema)
    ↓
DataCleaner (clean text, normalize)
    ↓
Deduplicator (find & mark duplicates)
    ↓
TextAnalyzer (NLP, sentiment, entities)
    ↓
EngagementCalculator (scores, viral detection)
    ↓
ProcessedPost
    ↓
    ├→ Elasticsearch (search index)
    └→ ClickHouse (analytics)
    ↓
EventDetector
    ↓
Events → Elasticsearch events index
```

### Streaming Flow

```
File Stream (new CSV)
    ↓
Spark Structured Streaming
    ↓
Schema Validation
    ↓
Transformations (engagement calc, etc.)
    ↓
Window Aggregations (1h, 6h, 1d)
    ↓
Parquet Output / Memory Table
    ↓
Query by Dashboard/API
```

### Query Flow

```
User Request (API/Dashboard)
    ↓
FastAPI Endpoint
    ↓
    ├→ Elasticsearch (text search, trending)
    ├→ ClickHouse (analytics, time-series)
    └→ Redis (cache check)
    ↓
Data Aggregation
    ↓
Response (JSON)
    ↓
Dashboard Visualization
```

## Design Patterns

### 1. Repository Pattern
- `ElasticsearchClient`, `ClickHouseClient` abstract storage
- Centralized data access logic
- Easy to swap implementations

### 2. Pipeline Pattern
- ETL as series of transformations
- Each stage is independent
- Easy to add/remove stages

### 3. Strategy Pattern
- Different analyzers (sentiment, entity, etc.)
- Pluggable analysis strategies
- Easy to extend

### 4. Observer Pattern
- Event detection triggers alerts
- Monitoring publishes metrics
- Decoupled components

## Scalability Considerations

### Horizontal Scaling

**API:**
- Stateless design
- Load balancer (Nginx)
- Multiple workers

**Elasticsearch:**
- Cluster setup (3+ nodes)
- Sharding strategy
- Replica sets

**ClickHouse:**
- Distributed tables
- Replication
- Cluster configuration

**Spark:**
- Cluster mode
- Dynamic resource allocation
- Partition optimization

### Vertical Scaling

**Memory:**
- Increase JVM heap (ES, Spark)
- Buffer sizes
- Cache sizes

**CPU:**
- More workers
- Parallel processing
- Async operations

**Storage:**
- SSD for hot data
- Tiered storage
- Compression

## Performance Optimizations

### Database
- Index optimization
- Partitioning by date
- Compression (ZSTD)
- Aggregation caching

### Processing
- Batch processing (1000 records)
- Parallel workers (4-8)
- Lazy evaluation
- Memory-efficient generators

### API
- Response caching (Redis)
- Query result caching
- Pagination
- Field filtering

### Network
- Connection pooling
- Keep-alive
- Compression (gzip)
- CDN for static assets

## Security Measures

### Authentication & Authorization
- API keys
- JWT tokens
- Role-based access control
- OAuth integration (future)

### Data Security
- Encryption at rest
- Encryption in transit (TLS)
- Sensitive data filtering
- PII anonymization

### Network Security
- Firewall rules
- VPC isolation
- Rate limiting
- DDoS protection

### Application Security
- Input validation
- SQL injection prevention
- XSS protection
- CSRF tokens

## Monitoring & Observability

### Metrics
- Request rate, latency
- Error rate
- Resource usage (CPU, memory, disk)
- Queue depths
- Cache hit rates

### Logging
- Structured logging (JSON)
- Log levels (DEBUG → ERROR)
- Centralized logging
- Log rotation

### Tracing
- Request tracing
- Performance profiling
- Bottleneck identification

### Alerting
- Threshold alerts
- Anomaly detection
- On-call rotation
- Escalation policies

## Future Enhancements

### Short Term
- [ ] Implement authentication
- [ ] Add more data sources
- [ ] Improve ML models
- [ ] Enhanced visualization

### Medium Term
- [ ] Real-time streaming from APIs
- [ ] Advanced topic modeling (LDA)
- [ ] Sentiment trend prediction
- [ ] Automated reporting

### Long Term
- [ ] Deep learning for classification
- [ ] Graph analysis (influence networks)
- [ ] Predictive analytics
- [ ] Multi-language support

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Data Processing | Python, Pandas, NumPy | ETL, analysis |
| Search | Elasticsearch | Full-text search |
| Analytics | ClickHouse | OLAP, time-series |
| Streaming | Spark | Real-time processing |
| API | FastAPI | REST endpoints |
| Visualization | Dash, Plotly | Dashboards |
| NLP | spaCy, NLTK, TextBlob | Text analysis |
| ML | scikit-learn, SciPy | Clustering, statistics |
| Storage | PostgreSQL, Redis | Metadata, cache |
| Monitoring | Prometheus, Grafana | Metrics, alerts |
| Container | Docker, Docker Compose | Deployment |

## Performance Benchmarks

### Expected Performance (16GB RAM, 8 cores)

| Operation | Throughput | Latency |
|-----------|-----------|---------|
| CSV ingestion | 10K posts/sec | - |
| Text cleaning | 5K posts/sec | - |
| NLP analysis | 1K posts/sec | - |
| ES indexing | 5K posts/sec | - |
| ClickHouse insert | 10K posts/sec | - |
| API search | - | 50ms p95 |
| API aggregation | - | 200ms p95 |
| Dashboard refresh | - | 1-2 sec |

### Optimization Tips

1. **Batch size**: 1000-5000 for best throughput
2. **Workers**: CPU cores - 1 for CPU-bound tasks
3. **ES shards**: 1-2 per node for small clusters
4. **CH partitions**: By month for time-series data
5. **Spark partitions**: 2-3x number of cores

## Conclusion

This architecture provides:
- ✅ Scalability (horizontal & vertical)
- ✅ High availability (replication, failover)
- ✅ Performance (caching, optimization)
- ✅ Flexibility (modular design)
- ✅ Observability (monitoring, logging)
- ✅ Maintainability (clean code, documentation)
