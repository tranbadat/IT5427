# 📡 API Documentation

## Overview

FastAPI REST API cho phép truy vấn và phân tích dữ liệu mạng xã hội.

**Base URL**: `http://localhost:8000`

**Interactive Docs**: `http://localhost:8000/docs`

## Authentication

Currently no authentication required (add JWT/OAuth in production)

## Endpoints

### 1. Health Check

**GET** `/health`

Kiểm tra trạng thái services

**Response:**
```json
{
  "status": "healthy",
  "elasticsearch": true,
  "clickhouse": true
}
```

### 2. Search Posts

**POST** `/search`

Tìm kiếm bài viết với filters

**Request Body:**
```json
{
  "query": "climate change",
  "platform": "threads",
  "start_date": "2026-01-01T00:00:00",
  "end_date": "2026-01-20T23:59:59",
  "limit": 100
}
```

**Response:**
```json
{
  "total": 1523,
  "posts": [
    {
      "doc_id": "...",
      "content": "...",
      "user_name": "...",
      "engagement_score": 1250.5
    }
  ]
}
```

### 3. Get Statistics

**GET** `/stats?start_date=2026-01-01&end_date=2026-01-20`

Lấy thống kê tổng quan

**Response:**
```json
{
  "total_posts": 125000,
  "unique_users": 45000,
  "total_likes": 5000000,
  "total_shares": 250000,
  "total_comments": 180000,
  "avg_engagement": 125.5
}
```

### 4. Trending Keywords

**GET** `/trending/keywords?limit=20`

Lấy keywords đang trending

**Response:**
```json
{
  "keywords": [
    {"keyword": "AI", "count": 1523},
    {"keyword": "climate", "count": 982}
  ]
}
```

### 5. Trending Tags

**GET** `/trending/tags?start_date=2026-01-19&limit=50`

Lấy tags trending từ ClickHouse

**Response:**
```json
{
  "tags": [
    {"tag": "technology", "frequency": 2341, "engagement": 125000},
    {"tag": "news", "frequency": 1892, "engagement": 98000}
  ]
}
```

### 6. Viral Posts

**GET** `/viral?threshold=10000&limit=50`

Lấy các bài viết viral

**Response:**
```json
{
  "viral_posts": [
    {
      "doc_id": "...",
      "title": "...",
      "engagement_score": 25000,
      "num_likes": 15000,
      "num_shares": 5000
    }
  ]
}
```

### 7. Activity Spikes

**GET** `/events/spikes?window_hours=24&threshold=2.5`

Phát hiện các đợt tăng đột biến hoạt động

**Response:**
```json
{
  "spikes": [
    {
      "hour": "2026-01-20T15:00:00",
      "source": "threads",
      "count": 1523,
      "z_score": 3.5
    }
  ]
}
```

### 8. Time Series

**GET** `/timeseries?interval=1 HOUR&platform=threads`

Lấy dữ liệu time series

**Parameters:**
- `start_date`: ISO datetime
- `end_date`: ISO datetime
- `platform`: x, threads, reddit (optional)
- `interval`: 1 HOUR, 1 DAY, 1 WEEK

**Response:**
```json
{
  "data": [
    {
      "time_bucket": "2026-01-20T15:00:00",
      "platform": "threads",
      "post_count": 523,
      "total_likes": 12500,
      "avg_engagement": 125.5
    }
  ]
}
```

### 9. Top Users

**GET** `/users/top?limit=100`

Lấy top users theo engagement

**Response:**
```json
{
  "users": [
    {
      "user_id": "123",
      "user_name": "john_doe",
      "platform": "threads",
      "post_count": 150,
      "total_engagement": 25000
    }
  ]
}
```

### 10. Aggregated Data

**GET** `/aggregate?interval=1h`

Lấy dữ liệu tổng hợp theo khoảng thời gian

**Response:**
```json
{
  "aggregations": [
    {
      "timestamp": "2026-01-20T15:00:00",
      "count": 523,
      "total_engagement": 12500
    }
  ]
}
```

## Error Handling

API trả về standard HTTP status codes:

- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

**Error Response:**
```json
{
  "detail": "Error message here"
}
```

## Rate Limiting

Currently no rate limiting (add in production)

## Examples

### Python

```python
import requests

# Search posts
response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "technology",
        "platform": "threads",
        "limit": 10
    }
)
data = response.json()
print(f"Found {data['total']} posts")
```

### cURL

```bash
# Get statistics
curl -X GET "http://localhost:8000/stats"

# Search posts
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "AI", "limit": 10}'
```

### JavaScript

```javascript
// Fetch trending keywords
fetch('http://localhost:8000/trending/keywords?limit=20')
  .then(response => response.json())
  .then(data => console.log(data.keywords));
```
