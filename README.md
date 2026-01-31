# Phân tích dữ liệu mạng xã hội để phát hiện bùng phát sự kiện xã hội

## Tổng quan

Dự án tập trung vào việc thu thập, chuẩn hóa và phân tích dữ liệu mạng xã hội đa nền tảng (X, Threads, Reddit) nhằm phát hiện bùng phát sự kiện theo thời gian thực. Hệ thống áp dụng quy trình ETL, lưu trữ dữ liệu lớn, và phân tích xu hướng bằng các kỹ thuật thống kê/streaming.

## Nguồn dữ liệu

- X (Twitter): chỉ số lan truyền mạnh (like, repost, reply, view).
- Threads: nội dung dài, thiên về thảo luận cộng đồng.
- Reddit: dữ liệu dạng thảo luận theo chủ đề (subreddit), công khai, phù hợp nghiên cứu học thuật.

## Cấu trúc dự án

Xem chi tiết tại [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md). Tóm tắt:

- `configs/`: cấu hình, danh sách từ nhạy cảm.
- `data/`: dữ liệu raw và dữ liệu đã xử lý.
- `src/`: các module xử lý (lọc nhạy cảm).
- `docs/`: tài liệu pipeline và schema trung gian.
- `scripts/`: script tiện ích.

Kiến trúc mở rộng đề xuất:

- `data_crawler/`: thu thập dữ liệu.
- `etl_pipeline/`: làm sạch, chuẩn hóa, loại trùng.
- `storage/`: cấu hình ClickHouse.
- `analysis_engine/`: Spark batch/stream.
- `dashboard/`: hiển thị và cảnh báo.

## Schema trung gian
[docs/INTERMEDIATE_SCHEMA.md](docs/INTERMEDIATE_SCHEMA.md)

Các nhóm trường chính:

- Nội dung: title, content, description, tags, pictures, link, postLink, domain.
- Tương tác: numLikes, numDislikes, numComments, numShares, numViews, reactions.
- Thời gian: createDate, collectDate.
- Người dùng & ngữ cảnh: userId, userName, sourceId, sourceName, source, docType, type, fromCrawler.

## Pipeline triển khai

Quy trình chi tiết tại  [docs/PIPELINE_STEPS.md](docs/PIPELINE_STEPS.md). Tóm tắt:

1. Mô hình hóa nguồn dữ liệu và xây dựng schema trung gian.
2. ETL: chuẩn hóa, xử lý trùng lặp, lọc nhiễu.
3. Lưu trữ vào ClickHouse để truy vấn OLAP.
4. Phân tích bùng phát bằng Spark và các chỉ số thống kê.
5. Dashboard hiển thị xu hướng và cảnh báo.

## Module lọc từ nhạy cảm

Module `src/filter_sensitive.py` loại bỏ bài viết chứa từ nhạy cảm theo các cột:
`title, content, description, tags`.

Cách chạy:

```powershell
python src\filter_sensitive.py --input data\raw --output data\processed --words configs\sensitive_words.txt
```

## Ghi chú về ClickHouse

ClickHouse đóng vai trò OLAP server để tăng tốc truy vấn cho dashboard. Có thể thiết kế bảng phân vùng theo `createDate`/`collectDate` và chỉ mục theo `source`, `categories`.


## Huong dan streaming + kiem tra ghi ClickHouse (Ubuntu/macOS)

Luu y quan trong: Spark Structured Streaming voi file source chi doc **file moi** sau khi stream da chay. Neu file da ton tai truoc do hoac da duoc checkpoint ghi nhan, Spark se bo qua.

### 1) Reset checkpoint (neu can)
```bash
rm -rf ./checkpoints/social_burst
```

### 2) Khoi dong lai stack
```bash
docker compose down
docker compose up -d --force-recreate
```

### 3) Copy file moi sau khi stream da chay
```bash
cp ./data/raw/twitter/tweets.csv ./data/raw/twitter/tweets_$(date +%Y%m%d%H%M%S).csv
```

### 4) Xem log
```bash
docker logs -f spark-runner
docker logs -f clickhouse
```

### 5) Kiem tra ClickHouse nhanh
```bash
docker exec -it clickhouse clickhouse-client -u admin --password admin123
```
```sql
SELECT count(*) FROM social_time_series;
SELECT count(*) FROM social_burst_events;
```

## Huong dan streaming + kiem tra ghi ClickHouse (Windows PowerShell)

### 1) Reset checkpoint (neu can)
```powershell
Remove-Item -Recurse -Force .\checkpoints\social_burst
```

### 2) Khoi dong lai stack
```powershell
docker compose down
docker compose up -d --force-recreate
```

### 3) Copy file moi sau khi stream da chay
```powershell
Copy-Item .\data\raw\twitter\tweets.csv .\data\raw\twitter\tweets_$(Get-Date -Format yyyyMMddHHmmss).csv
```

### 4) Xem log
```powershell
docker logs -f spark-runner
docker logs -f clickhouse
```

### 5) Kiem tra ClickHouse nhanh
```powershell
docker exec -it clickhouse clickhouse-client -u admin --password admin123
```
```sql
SELECT count(*) FROM social_time_series;
SELECT count(*) FROM social_burst_events;
```
