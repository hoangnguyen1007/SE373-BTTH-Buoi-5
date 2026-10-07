---
name: csv-quality
description: Kiểm tra chất lượng file CSV công việc (task_id, owner, hours), tính tổng giờ và xác định người quá tải theo ngưỡng giờ bằng script có sẵn, rồi ghi báo cáo Markdown dưới output/. Dùng khi người dùng yêu cầu kiểm tra dữ liệu công việc, tính tổng giờ theo người hoặc tìm người quá tải.
---

# CSV quality & workload analysis

Kiểm tra chất lượng CSV công việc và tính tổng giờ theo người bằng script, không tự tính bằng mắt hay phán đoán.

## Chạy script

Dùng tool `bash` (cwd là workspace). Lệnh đầy đủ:

```
python skills/csv-quality/scripts/check_csv.py --input <đường dẫn CSV> --max-hours <ngưỡng giờ>
```

Ví dụ: `python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8`

- Tham số `--max-hours` là bắt buộc, nhận số hữu hạn không âm.
- **Quan trọng**: Nếu người dùng yêu cầu kiểm tra quá tải hoặc tính giờ mà **chưa cung cấp ngưỡng giờ**, hãy **hỏi lại người dùng** để nhận ngưỡng trước khi thực hiện hoặc kết luận. Không dùng ngưỡng từ cuộc trò chuyện cũ hoặc tự ý chọn giá trị mặc định.
- Khi người dùng đã cung cấp ngưỡng, truyền đúng giá trị đó vào `--max-hours`.
- Không cần đọc source script để chạy.

## Kiểm tra kết quả

- `exit_code` 0: Phân tích thành công. `stdout` là JSON gồm:
  - Thống kê chất lượng: `row_count`, `missing_owner_count`, `invalid_hours_count`, `duplicate_id_count`, `duplicate_ids`, `issues`.
  - Phân tích giờ & quá tải: `max_hours`, `hours_by_owner` (chỉ gồm owner có dòng hợp lệ được cộng), `overloaded_owners` (những người có tổng giờ > `max_hours`, sắp xếp theo tên), `excluded_rows` (các dòng bị loại kèm danh sách mã lý do).
- `exit_code` 1 hoặc khác 0: **Lỗi thực thi** (file không tồn tại, thiếu cột bắt buộc, lỗi parse CSV, thiếu hoặc sai tham số `--max-hours`). Đọc `stderr`, báo lỗi cho người dùng. Tuyệt đối không đưa ra tổng giờ, không suy đoán kết quả hay ghi báo cáo như thể đã phân tích thành công.
- `timed_out` true hoặc `ok` false: Lệnh không chạy xong; báo lỗi, không suy đoán kết quả.

## Viết báo cáo

1. Đọc template `references/report-template.md` trong thư mục skill này (`skills/csv-quality/references/report-template.md`).
2. Lấy mọi con số từ JSON của script. Điền đủ ngưỡng giờ, bảng tổng giờ theo người, danh sách người quá tải, bảng dòng bị loại trừ kèm lý do, và chi tiết lỗi chất lượng.
3. Không tự sửa file CSV nguồn. Có thể đề xuất hướng xử lý trong mục khuyến nghị.
4. Ghi báo cáo bằng `write_file` vào đường dẫn người dùng yêu cầu (ví dụ `output/workload.md` hoặc `output/csv-quality.md`), rồi trả lời đường dẫn kèm tóm tắt kết quả chính.
