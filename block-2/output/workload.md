# Báo cáo chất lượng dữ liệu và quá tải công việc: `data/workload.csv`

Công cụ: `skills/csv-quality/scripts/check_csv.py` | Ngưỡng giờ tối đa: 8.0 | exit code: 0

## Tổng quan khối lượng công việc
| Owner | Tổng giờ hợp lệ | Tình trạng |
|---|---|---|
| Lan | 9.0 | Quá tải |
| Minh | 3.0 | Bình thường |

## Danh sách người quá tải (> 8.0 giờ)
- Lan: 9.0 giờ (vượt 1.0 giờ)

## Các dòng bị loại trừ
| Line | task_id | Lý do loại trừ |
|---|---|---|
| 5 | T04 | invalid_hours |
| 6 | T02 | duplicate_id |
| 7 | T05 | missing_owner |

## Thống kê chất lượng dữ liệu
| Chỉ số | Giá trị |
|---|---|
| Số dòng dữ liệu (không tính header) | 6 |
| Dòng thiếu owner | 1 |
| Dòng hours không hợp lệ | 1 |
| Số task_id bị lặp (distinct) | 1 (T02) |

## Chi tiết lỗi dữ liệu
| Line | Cột | Loại | task_id | Mô tả |
|---|---|---|---|---|
| 5 | hours | invalid_hours | T04 | hours 'abc' không phải số hữu hạn không âm. |
| 6 | task_id | duplicate_id | T02 | task_id T02 đã xuất hiện ở line 3. |
| 7 | owner | missing_owner | T05 | owner trống. |

## Đánh giá và Khuyến nghị
- Lan có tổng 9.0 giờ hợp lệ (từ T01: 4h và T02: 5h), vượt ngưỡng 8.0 giờ (vượt 1.0 giờ). Dòng 6 (T02 lặp lại) đã bị loại trừ đúng quy tắc chỉ giữ lần xuất hiện đầu tiên trong file.
- Minh có tổng 3.0 giờ hợp lệ (từ T03: 3h). Dòng 5 (T04) bị loại do hours không hợp lệ ('abc').
- Dòng 7 (T05) bị loại do thiếu thông tin owner.
- Cần phân bổ lại 1.0 giờ công việc của Lan sang nhân sự khác để đảm bảo không vượt ngưỡng cho phép.
- Cần chuẩn hóa dữ liệu đầu vào: bổ sung owner cho task T05, sửa giá trị số cho task T04, loại bỏ task_id trùng lặp T02.
