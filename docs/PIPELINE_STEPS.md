# Các bước triển khai chi tiết

Tài liệu này mô tả quy trình tích hợp dữ liệu và phát hiện bùng phát sự kiện theo từng giai đoạn.

## 1. Mô hình hóa nguồn dữ liệu

- Xác định cấu trúc dữ liệu của X, Threads, Reddit.
- Ghi nhận khác biệt ngữ nghĩa (semantic heterogeneity): cách đặt tên trường, định nghĩa tương tác, thời gian.
- Xây dựng lược đồ trung gian để cung cấp một cái nhìn thống nhất (`docs/INTERMEDIATE_SCHEMA.md`).

## 2. Xây dựng ETL và tích hợp dữ liệu

- Áp dụng mô hình Global-as-View (GAV) để ánh xạ nguồn về schema trung gian.
- Chuẩn hóa kiểu dữ liệu, timezone, cách biểu diễn tags/hashtag.
- Tạo bước lọc nội dung nhạy cảm trước khi phân tích.

## 3. Làm sạch, loại trùng và lan truyền chéo

- Dedup theo `postId/docId/link` kết hợp normalize nội dung.
- Phát hiện lan truyền chéo giữa nền tảng (share/repost/cross-post).
- Loại bỏ spam, nội dung không thuộc chủ đề nghiên cứu.

## 4. Lưu trữ và xử lý

- Lưu dữ liệu chuẩn hóa vào ClickHouse để truy vấn nhanh.
- Thiết kế bảng phân vùng theo thời gian để tối ưu truy vấn OLAP.
- Dùng Spark (batch/stream) để tổng hợp theo cửa sổ thời gian.

## 5. Phát hiện bùng phát sự kiện

- Tính chỉ số tăng trưởng theo thời gian (moving average, z-score).
- Thiết lập ngưỡng phát hiện đột biến (spike) cho từng chủ đề.
- Có thể dùng clustering để gom nhóm bài viết theo sự kiện.

## 6. Trực quan hóa và cảnh báo

- Dashboard hiển thị trend, mức độ lan truyền, phân bố theo nguồn.
- Cảnh báo khi vượt ngưỡng bùng phát hoặc tăng trưởng bất thường.

## 7. Đánh giá và tinh chỉnh

- Đánh giá false positive/false negative.
- Cập nhật danh sách từ nhạy cảm và bộ lọc chủ đề theo thực tế.
