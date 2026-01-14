# Phác thảo cấu trúc dự án

Mục tiêu của cấu trúc là hỗ trợ pipeline dữ liệu lớn, dễ mở rộng và tái sử dụng. Hiện tại repo đang có các thư mục sau:

```
social-network-data/
  configs/
    sensitive_words.txt     # danh sách từ nhạy cảm
  data/
    raw/                    # nơi chứa các file crawl (nếu muốn gom về đây)
    processed/              # dữ liệu đã lọc/chuẩn hóa
  docs/
    PROJECT_STRUCTURE.md
    PIPELINE_STEPS.md
    INTERMEDIATE_SCHEMA.md
  scripts/
    run_filter_sensitive.ps1
  src/
    filter_sensitive.py
  *.csv                     # dữ liệu crawl hiện có (tweets, reddit, ...)
```

Kiến trúc mở rộng đề xuất (multi-tier):

```
data_crawler/               # thu thập dữ liệu từ X, Threads, Reddit
etl_pipeline/               # chuẩn hóa, làm sạch, loại trùng, lọc nhạy cảm
storage/                    # cấu hình lưu trữ (ClickHouse)
analysis_engine/            # xử lý batch/stream (Spark)
dashboard/                  # dashboard hiển thị xu hướng, cảnh báo
```

Gợi ý: Có thể tạo thêm các thư mục đề xuất khi bắt đầu triển khai các bước tương ứng.
