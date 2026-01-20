# 🚀 Quick Start Guide

## Bắt đầu nhanh trong 5 phút

### 1. Setup môi trường (2 phút)

```bash
# Clone project
cd IT5427

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Download NLP models
python -m spacy download en_core_web_sm
python -m nltk.downloader punkt stopwords vader_lexicon
```

### 2. Khởi động services (2 phút)

```bash
# Copy environment file
cp .env.example .env

# Start Docker services
docker-compose up -d

# Wait for services (30 seconds)
sleep 30

# Initialize databases
python scripts/init_databases.py
```

### 3. Chạy pipeline (1 phút)

```bash
# Run ETL pipeline
python src/main_etl.py

# Start API (new terminal)
uvicorn src.api.main:app --reload

# Start Dashboard (new terminal)
python src/dashboard/app.py
```

### 4. Truy cập services

- **API**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8050
- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601
- **ClickHouse**: http://localhost:8123
- **Grafana**: http://localhost:3000 (admin/admin)

## 📋 Checklist hoàn thành setup

- [ ] Python 3.9+ đã cài đặt
- [ ] Docker & Docker Compose đã cài đặt
- [ ] Virtual environment đã tạo
- [ ] Dependencies đã cài đặt
- [ ] Docker services đang chạy
- [ ] Databases đã khởi tạo
- [ ] ETL pipeline chạy thành công
- [ ] API đang chạy
- [ ] Dashboard đang hiển thị

## 🐛 Troubleshooting

### Lỗi kết nối Elasticsearch

```bash
# Kiểm tra Elasticsearch
curl http://localhost:9200

# Restart service
docker-compose restart elasticsearch
```

### Lỗi import module

```bash
# Đảm bảo virtual environment active
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Lỗi port đã sử dụng

```bash
# Tìm process sử dụng port
lsof -i :8000  # API port
lsof -i :8050  # Dashboard port

# Kill process
kill -9 <PID>
```

## 📚 Bước tiếp theo

1. Đọc [API Documentation](API.md)
2. Xem [Dashboard Guide](DASHBOARD.md)
3. Tìm hiểu [Data Pipeline](../docs/PIPELINE_STEPS.md)
4. Customize [Configuration](CONFIGURATION.md)
