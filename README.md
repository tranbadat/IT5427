# 📊 Hệ thống Phân tích Dữ liệu Mạng Xã hội và Phát hiện Sự kiện

## 🎯 Tổng quan

Dự án phân tích dữ liệu mạng xã hội đa nền tảng (X/Twitter, Threads, Reddit) với khả năng phát hiện bùng phát sự kiện theo thời gian thực. Hệ thống tích hợp công nghệ Big Data hiện đại bao gồm Elasticsearch, ClickHouse, Spark Streaming, và các thuật toán NLP/ML tiên tiến.

### ✨ Tính năng chính

- 🔄 **ETL Pipeline**: Thu thập, làm sạch, chuẩn hóa dữ liệu từ nhiều nền tảng
- 🔍 **Elasticsearch**: Tìm kiếm và phân tích văn bản toàn diện
- 📈 **ClickHouse**: Phân tích OLAP hiệu suất cao
- ⚡ **Spark Streaming**: Xử lý dữ liệu thời gian thực
- 🤖 **NLP & ML**: Phân tích sentiment, trích xuất entities, phát hiện sự kiện
- 🚨 **Event Detection**: Phát hiện bùng phát, trending topics, viral content
- 📊 **Dashboard**: Trực quan hóa dữ liệu real-time
- 🔌 **REST API**: Truy vấn và tích hợp dữ liệu

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐
│  Data Sources   │  (CSV files from X, Threads, Reddit)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ETL Pipeline   │  (Extract, Transform, Load)
│  - Data Loader  │
│  - Cleaner      │
│  - Deduplicator │
│  - NLP Analyzer │
└────────┬────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌────────────┐
│Elasticsearch │ │ ClickHouse  │ │   Spark    │
│   (Search)   │ │  (Analytics)│ │(Streaming) │
└──────┬───────┘ └──────┬──────┘ └─────┬──────┘
       │                │               │
       └────────┬───────┴───────────────┘
                ▼
       ┌────────────────┐
       │   FastAPI      │
       │  (REST API)    │
       └────────┬───────┘
                │
       ┌────────┴───────┐
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│ Dash Board  │  │  Grafana    │
│ (Analytics) │  │(Monitoring) │
└─────────────┘  └─────────────┘
```

## 📁 Cấu trúc dự án

```
IT5427/
├── configs/                 # Cấu hình
│   ├── sensitive_words.txt  # Từ nhạy cảm
│   ├── prometheus.yml       # Monitoring config
│   └── clickhouse/          # ClickHouse configs
├── data/                    # Dữ liệu
│   ├── raw/                 # Dữ liệu thô
│   ├── processed/           # Dữ liệu đã xử lý
│   └── output/              # Kết quả phân tích
├── src/                     # Source code
│   ├── etl/                 # ETL pipeline
│   │   ├── data_loader.py
│   │   ├── data_cleaner.py
│   │   └── deduplicator.py
│   ├── analysis/            # Phân tích dữ liệu
│   │   ├── text_analyzer.py
│   │   └── event_detector.py
│   ├── storage/             # Lưu trữ
│   │   ├── elasticsearch_client.py
│   │   └── clickhouse_client.py
│   ├── streaming/           # Xử lý streaming
│   │   └── stream_processor.py
│   ├── api/                 # REST API
│   │   └── main.py
│   ├── dashboard/           # Dashboard
│   │   └── app.py
│   ├── config.py            # Cấu hình
│   ├── models.py            # Data models
│   ├── filter_sensitive.py  # Lọc nội dung nhạy cảm
│   └── main_etl.py          # ETL orchestrator
├── scripts/                 # Scripts tiện ích
│   ├── init_databases.py
│   └── run_filter_sensitive.ps1
├── docs/                    # Tài liệu
│   ├── PIPELINE_STEPS.md
│   ├── INTERMEDIATE_SCHEMA.md
│   └── PROJECT_STRUCTURE.md
├── tests/                   # Unit tests
├── docker-compose.yml       # Docker setup
├── requirements.txt         # Python dependencies
├── Makefile                # Build commands
├── .env.example            # Environment template
└── README.md               # Tài liệu này
```

## 🚀 Cài đặt và Chạy

### Yêu cầu hệ thống

- Python 3.9+
- Docker & Docker Compose
- 8GB RAM minimum (16GB recommended)
- 10GB disk space

### 1. Clone và cài đặt

```bash
# Clone repository
git clone <repository-url>
cd IT5427

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows

# Cài đặt dependencies
make install
# hoặc
pip install -r requirements.txt

# Thiết lập dự án
make setup
```

### 2. Cấu hình

```bash
# Copy file cấu hình
cp .env.example .env

# Chỉnh sửa .env theo môi trường của bạn
nano .env
```

### 3. Khởi động services

```bash
# Khởi động tất cả Docker services
make docker-up

# Chờ services khởi động (30 giây)
# Services bao gồm:
# - Elasticsearch (port 9200)
# - Kibana (port 5601)
# - ClickHouse (port 8123, 9000)
# - PostgreSQL (port 5432)
# - Redis (port 6379)
# - Prometheus (port 9090)
# - Grafana (port 3000)
```

### 4. Chạy ETL Pipeline

```bash
# Chạy ETL pipeline để xử lý dữ liệu
make run-etl
# hoặc
python src/main_etl.py
```

### 5. Khởi động API

```bash
# Khởi động FastAPI server
make run-api
# hoặc
python -m uvicorn src.api.main:app --reload

# API sẽ chạy tại: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 6. Khởi động Dashboard

```bash
# Khởi động Dash dashboard
make run-dashboard
# hoặc
python src/dashboard/app.py

# Dashboard tại: http://localhost:8050
```

### 7. Chạy Streaming (Optional)

```bash
# Xử lý dữ liệu streaming
make run-stream
# hoặc
python src/streaming/stream_processor.py
```

## 📊 Sử dụng

### ETL Pipeline

ETL pipeline tự động:
1. Đọc dữ liệu từ CSV files trong `data/`
2. Làm sạch và chuẩn hóa dữ liệu
3. Phát hiện và loại bỏ duplicate
4. Phân tích sentiment và trích xuất keywords
5. Tính engagement score
6. Phát hiện viral posts
7. Lưu vào Elasticsearch và ClickHouse

### REST API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `POST /search` - Tìm kiếm posts
- `GET /stats` - Thống kê tổng quan
- `GET /trending/keywords` - Keywords trending
- `GET /trending/tags` - Tags trending
- `GET /viral` - Viral posts
- `GET /events/spikes` - Activity spikes
- `GET /timeseries` - Time series data
- `GET /users/top` - Top users

### Dashboard Features

- 📈 Real-time activity charts
- 🌐 Platform distribution
- ⚡ Engagement metrics
- 🔥 Trending keywords
- 👤 Top users
- 🔥 Viral posts
- 🚨 Event detection

## 🔧 Phát triển

### Chạy tests

```bash
make test
```

### Code formatting

```bash
make format
```

### Linting

```bash
make lint
```

### Clean up

```bash
# Dọn dẹp temporary files
make clean

# Tắt Docker services
make docker-down
```

## 📚 Tài liệu chi tiết

- [Pipeline Steps](docs/PIPELINE_STEPS.md) - Quy trình xử lý chi tiết
- [Schema Documentation](docs/INTERMEDIATE_SCHEMA.md) - Cấu trúc dữ liệu
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Kiến trúc dự án

## 🔍 Chi tiết công nghệ

### Data Processing
- **Pandas**: Data manipulation
- **NumPy**: Numerical computing
- **Spark**: Distributed processing

### Storage
- **Elasticsearch**: Full-text search, aggregations
- **ClickHouse**: OLAP analytics
- **PostgreSQL**: Metadata storage
- **Redis**: Caching

### Analysis
- **NLTK**: Text processing
- **spaCy**: NLP, NER
- **TextBlob**: Sentiment analysis
- **scikit-learn**: ML, clustering
- **LangDetect**: Language detection

### API & Visualization
- **FastAPI**: REST API
- **Dash**: Interactive dashboards
- **Plotly**: Data visualization
- **Prometheus**: Monitoring
- **Grafana**: Metrics visualization

## 🤝 Đóng góp

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👥 Team

Social Media Analytics Team - VNPT IT5427

## Module lọc từ nhạy cảm

Module `src/filter_sensitive.py` loại bỏ bài viết chứa từ nhạy cảm theo các cột:
`title, content, description, tags`.

Cách chạy:

```powershell
python src\filter_sensitive.py --input data\raw --output data\processed --words configs\sensitive_words.txt
```

## Ghi chú về ClickHouse

ClickHouse đóng vai trò OLAP server để tăng tốc truy vấn cho dashboard. Có thể thiết kế bảng phân vùng theo `createDate`/`collectDate` và chỉ mục theo `source`, `categories`.
