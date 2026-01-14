# Schema trung gian (chuẩn hóa)

Schema trung gian được tổng hợp từ header các file CSV hiện có. Danh sách cột chuẩn hóa:

```
categories, collectDate, content, createDate, description, docId, docType, domain,
fromCrawler, link, logoLink, numComments, numDislikes, numLikes, numShares, numViews,
pictures, postId, postLink, provinces, reactions, source, sourceId, sourceName, tags,
title, type, userId, userName
```

## Mô tả chi tiết từng trường

Bảng mô tả dưới đây dùng để chuẩn hóa kiểu dữ liệu và ý nghĩa:

| Cột | Nhóm | Kiểu dữ liệu gợi ý | Mô tả |
| --- | --- | --- | --- |
| docId | Định danh | string | Định danh tài liệu do hệ thống crawl tạo. |
| postId | Định danh | string | ID gốc của bài viết trên nền tảng. |
| source | Nguồn | string | Tên nền tảng (X, Threads, Reddit...). |
| sourceId | Nguồn | string | ID nguồn/nhóm dữ liệu bên crawler. |
| sourceName | Nguồn | string | Tên nguồn/nhóm dữ liệu bên crawler. |
| docType | Nguồn | string | Loại tài liệu (post, comment, ...). |
| type | Nguồn | string | Kiểu bài viết (tùy nền tảng). |
| fromCrawler | Nguồn | string | Tên crawler hoặc phiên bản crawler. |
| userId | Người dùng | string | ID người dùng. |
| userName | Người dùng | string | Tên hiển thị. |
| title | Nội dung | string | Tiêu đề (nếu có). |
| content | Nội dung | string | Nội dung chính. |
| description | Nội dung | string | Mô tả ngắn (nếu có). |
| tags | Nội dung | string | Tag/hashtag liên quan. |
| pictures | Nội dung | string | Danh sách URL ảnh (nếu có). |
| logoLink | Nội dung | string | Logo hoặc ảnh đại diện nguồn. |
| link | Nội dung | string | Liên kết gốc của bài viết. |
| postLink | Nội dung | string | Liên kết bài viết (khác link nếu có). |
| domain | Nội dung | string | Domain nguồn liên kết. |
| numLikes | Tương tác | long | Số lượt thích. |
| numDislikes | Tương tác | long | Số lượt không thích. |
| numComments | Tương tác | long | Số bình luận. |
| numShares | Tương tác | long | Số chia sẻ/repost. |
| numViews | Tương tác | long | Số lượt xem. |
| reactions | Tương tác | string | Các loại phản ứng khác. |
| createDate | Thời gian | datetime | Thời điểm bài viết được tạo. |
| collectDate | Thời gian | datetime | Thời điểm crawler thu thập. |
| provinces | Vùng miền | string | Tỉnh/thành (nếu suy luận được). |
| categories | Chủ đề | string | Nhãn chủ đề (nếu có). |

## Nhóm trường chính

1. Nhóm nội dung
   - title, content, description, tags, pictures, logoLink, link, postLink, domain

2. Nhóm tương tác
   - numLikes, numDislikes, numComments, numShares, numViews, reactions

3. Nhóm thời gian
   - createDate, collectDate

4. Nhóm người dùng & ngữ cảnh
   - userId, userName, sourceId, sourceName, source, docType, type, fromCrawler

5. Nhóm vùng miền & chủ đề
   - provinces, categories

6. Nhóm định danh
   - docId, postId

## Quy ước chuẩn hóa

- Các trường số tương tác nên chuyển sang kiểu số nguyên 64-bit, thiếu dữ liệu để null hoặc 0 tùy chiến lược.
- Thời gian cần chuẩn ISO-8601 và thống nhất timezone (khuyến nghị UTC).
- Các trường URL nên giữ nguyên để truy vết và dedup.
