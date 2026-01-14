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
