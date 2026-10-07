# Báo cáo chất lượng dữ liệu và quá tải công việc: `{đường dẫn CSV}`

Công cụ: `skills/csv-quality/scripts/check_csv.py` | Ngưỡng giờ tối đa: {max_hours} | exit code: {exit_code}

## Tổng quan khối lượng công việc
| Owner | Tổng giờ hợp lệ | Tình trạng |
|---|---|---|
| {owner} | {total_hours} | {Quá tải / Bình thường} |

## Danh sách người quá tải (> {max_hours} giờ)
- {owner}: {total_hours} giờ (vượt {total_hours - max_hours} giờ)
(Nếu không có ai quá tải: "Không có nhân sự nào vượt ngưỡng.")

## Các dòng bị loại trừ
| Line | task_id | Lý do loại trừ |
|---|---|---|
| {line} | {task_id} | {reasons} |

## Thống kê chất lượng dữ liệu
| Chỉ số | Giá trị |
|---|---|
| Số dòng dữ liệu (không tính header) | {row_count} |
| Dòng thiếu owner | {missing_owner_count} |
| Dòng hours không hợp lệ | {invalid_hours_count} |
| Số task_id bị lặp (distinct) | {duplicate_id_count} ({duplicate_ids}) |

## Chi tiết lỗi dữ liệu
| Line | Cột | Loại | task_id | Mô tả |
|---|---|---|---|---|
| {line} | {column} | {type} | {task_id} | {message} |

## Đánh giá và Khuyến nghị
- Đánh giá tính hợp lệ của dữ liệu và các dòng bị loại.
- Khuyến nghị xử lý công việc cho nhân sự bị quá tải (nếu có).
- Khuyến nghị chuẩn hóa dữ liệu đầu vào.
