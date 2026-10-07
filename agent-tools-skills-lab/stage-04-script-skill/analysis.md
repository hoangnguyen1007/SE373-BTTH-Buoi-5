# Báo cáo phân tích Block 2: Kiểm tra quá tải theo người (Stage 03 → Stage 04)

## 1. Tổng quan các thay đổi đã thực hiện

### 1.1. Mở rộng script kiểm tra dữ liệu (`scripts/check_csv.py`)
- **Tham số CLI bắt buộc `--max-hours`**:
  - Bổ sung `parser.add_argument("--max-hours", type=float, required=True)`.
  - Kiểm tra điều kiện số hữu hạn không âm: nếu thiếu tham số hoặc giá trị `< 0` / không phải số hữu hạn (`NaN`, `inf`), script in thông báo lỗi ra `stderr` và kết thúc với mã thoát khác 0 (`sys.exit(1)` hoặc `sys.exit(2)`).
- **Chuẩn hóa dữ liệu (Whitespace Normalization)**:
  - Loại bỏ khoảng trắng đầu/cuối của các trường `task_id`, `owner`, `hours` trước khi xử lý.
  - Phân biệt chữ hoa/thường đối với `owner` (không gộp hai tên khác hoa/thường).
- **Quy tắc khử trùng lặp nghiêm ngặt (First Occurrence Rule)**:
  - Mỗi `task_id` không rỗng chỉ giữ **lần xuất hiện đầu tiên trong file**.
  - Các lần xuất hiện sau đều bị loại trừ với lý do `duplicate_id`, kể cả khi lần xuất hiện đầu tiên có dữ liệu không hợp lệ. Tuyệt đối không thay thế bằng "lần hợp lệ đầu tiên".
- **Tính toán tổng giờ làm việc (`hours_by_owner`)**:
  - Chỉ cộng các dòng thỏa mãn toàn bộ tiêu chí: đúng số trường, `task_id` không rỗng, `owner` không rỗng, `hours` là số hữu hạn không âm (chấp nhận giá trị `0`).
  - Owner chỉ xuất hiện trong `hours_by_owner` khi có ít nhất một dòng hợp lệ được cộng giờ.
- **Xác định danh sách nhân sự quá tải (`overloaded_owners`)**:
  - So sánh điều kiện nghiêm ngặt: `total_hours > max_hours`. Trường hợp tổng giờ bằng đúng ngưỡng (`total_hours == max_hours`) không tính là quá tải.
  - Danh sách được sắp xếp tăng dần theo tên `owner`.
- **Tổng hợp danh sách dòng bị loại trừ (`excluded_rows`)**:
  - Mỗi dòng dữ liệu bị loại xuất hiện duy nhất 1 lần trong `excluded_rows`, sắp xếp theo số thứ tự dòng (`line`).
  - Danh sách lý do (`reasons`) được chuẩn hóa và sắp xếp theo thứ tự quy định: `wrong_field_count`, `missing_task_id`, `duplicate_id`, `missing_owner`, `invalid_hours`.
- **Bảo toàn và đồng bộ hóa**:
  - Giữ nguyên toàn bộ các thống kê chất lượng dữ liệu cũ (`row_count`, `missing_owner_count`, `invalid_hours_count`, `duplicate_id_count`, `issues`).
  - Đồng bộ mã nguồn hoàn toàn giữa `workspace/skills/csv-quality/scripts/check_csv.py` và `fixtures/skills/csv-quality/scripts/check_csv.py`.

### 1.2. Cập nhật chỉ dẫn Skill (`SKILL.md`)
- Hướng dẫn Agent phân tích yêu cầu: trích xuất đường dẫn file CSV và ngưỡng giờ `--max-hours`.
- **Quy tắc an toàn khi thiếu ngưỡng**: Nếu người dùng không cung cấp ngưỡng giờ trong câu hỏi, Agent **bắt buộc phải hỏi lại người dùng** trước khi thực hiện phân tích; tuyệt đối không tự ý giả định hay sử dụng ngưỡng từ các lượt hội thoại trước.
- Cập nhật cú pháp lệnh thực thi qua tool `bash`: `python skills/csv-quality/scripts/check_csv.py --input <path> --max-hours <threshold>`.

### 1.3. Cập nhật tài liệu tham khảo báo cáo (`references/report-template.md`)
- Cấu trúc lại mẫu báo cáo theo chuẩn Markdown chuyên nghiệp:
  - Header: đường dẫn file, script thực thi, ngưỡng giờ tối đa `{max_hours}`, mã thoát `{exit_code}`.
  - Bảng "Tổng quan khối lượng công việc": Liệt kê từng owner, tổng giờ hợp lệ và trạng thái (Quá tải / Bình thường).
  - Mục "Danh sách người quá tải": Chi tiết số giờ vượt ngưỡng hoặc xác nhận không có ai vượt ngưỡng.
  - Bảng "Các dòng bị loại trừ": Số dòng, `task_id`, và tất cả các lý do loại trừ tương ứng.
  - Bảng "Thống kê chất lượng dữ liệu" & "Chi tiết lỗi dữ liệu".
  - Đánh giá và khuyến nghị nghiệp vụ.

### 1.4. Bổ sung kiểm thử tự động (`tests/test_check_csv.py`)
- Cập nhật hàm `run(path, max_hours=8.0)` hỗ trợ truyền tham số linh hoạt.
- Thêm test case `test_missing_max_hours_exit_nonzero` và `test_invalid_max_hours_exit_nonzero`.
- Thêm test case kiểm tra `workload.csv` với ngưỡng 8 (`test_workload_threshold_8`) và ngưỡng 9 (`test_workload_threshold_9`).
- Thêm test case kiểm tra trường hợp đặc biệt (`test_edge_case_first_occurrence_invalid_hours` với `workload-edge.csv` và ngưỡng 0). Toàn bộ 17 test cases đều vượt qua 100%.

---

## 2. Kết quả kiểm tra từng trường hợp

### Bảng tổng hợp đối chiếu kết quả
| Kịch bản kiểm thử | Đầu vào | Ngưỡng (`max-hours`) | Kết quả tính toán & Phân tích | Trạng thái |
|---|---|:---:|---|:---:|
| **1. CSV chuẩn, ngưỡng 8** | `data/workload.csv` | `8.0` | - Lan: 9.0h (Quá tải, vượt 1.0h)<br>- Minh: 3.0h (Bình thường)<br>- Loại dòng: 5 (`invalid_hours`), 6 (`duplicate_id`), 7 (`missing_owner`) | ĐẠT 100% |
| **2. CSV chuẩn, ngưỡng 9** | `data/workload.csv` | `9.0` | - Lan: 9.0h (Bình thường, 9.0h = 9.0h không vượt)<br>- Minh: 3.0h (Bình thường)<br>- Không có nhân sự nào bị quá tải | ĐẠT 100% |
| **3. Không cung cấp ngưỡng** | `data/workload.csv` | *Không có* | Agent không chạy script với ngưỡng tùy tiện mà phản hồi hỏi lại người dùng để cung cấp ngưỡng cụ thể | ĐẠT 100% |
| **4. File không tồn tại** | `data/khong-co.csv` | `8.0` | Script trả mã thoát 1, ghi lỗi ra stderr. Agent thông báo không tìm thấy file, dừng xử lý an toàn | ĐẠT 100% |
| **5. Edge case (ID đầu tiên lỗi)** | `data/workload-edge.csv` | `0.0` | - Minh: 0.0h (Bình thường)<br>- Lan: 0.0h (không có trong `hours_by_owner`)<br>- Dòng 2 loại vì `invalid_hours`, dòng 3 loại vì `duplicate_id` | ĐẠT 100% |

---

## 3. Vị trí bằng chứng trong Execution Trace

### 3.1. Kịch bản 1: `trace_workload_threshold_8.jsonl`
- **Bước 1 (Seq 3-5)**: Agent nhận yêu cầu, tra cứu danh mục skill và gọi tool `read_file` đọc `skills/csv-quality/SKILL.md` (Tool call: `tc_read_skill`).
- **Bước 2 (Seq 7-9)**: Agent thực thi lệnh Bash: `python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8` (Tool call: `tc_run_check_csv`).
  - Kết quả trả về: `exit_code: 0`, JSON chứa `overloaded_owners: [{"owner": "Lan", "total_hours": 9.0}]`, `excluded_rows` gồm các dòng 5, 6, 7.
- **Bước 3 (Seq 11-13)**: Agent đọc mẫu báo cáo `skills/csv-quality/references/report-template.md` (Tool call: `tc_read_ref`).
- **Bước 4 (Seq 15-17)**: Agent gọi tool `write_file` tạo file báo cáo `output/workload.md` (Tool call: `tc_write_report`).
- **Bước 5 (Seq 18-19)**: Phản hồi tổng kết rõ ràng: Lan (9.0h) bị quá tải vượt 1.0h, Minh (3.0h) hợp lệ, báo cáo đã được lưu.

### 3.2. Kịch bản 2: `trace_workload_threshold_9.jsonl`
- **Thực thi Bash (Seq 7-9)**: Lệnh chạy với `--max-hours 9`.
  - Kết quả trả về: `exit_code: 0`, `overloaded_owners: []`.
- **Kết luận (Seq 11-12)**: Agent giải thích chính xác Lan có tổng 9.0 giờ, nhưng do ngưỡng là 9.0 giờ nên không bị tính là quá tải (quy tắc lớn hơn nghiêm ngặt).

### 3.3. Kịch bản 3: `trace_missing_threshold.jsonl`
- **Phát hiện thiếu ngưỡng (Seq 3-5)**: Agent đọc `SKILL.md`, thấy hướng dẫn yêu cầu ngưỡng giờ bắt buộc.
- **Dừng an toàn & Hỏi lại (Seq 6-8)**: Agent không tự ý đoán ngưỡng 8 hay bất kỳ số nào, mà trả lời trực tiếp hỏi người dùng cung cấp ngưỡng `--max-hours`.

### 3.4. Kịch bản 4: `trace_missing_file.jsonl`
- **Báo lỗi từ Tool (Seq 7-9)**: Bash trả về `exit_code: 1`, `stderr: "Không đọc được file: data/non_existent.csv\n"`.
- **Xử lý lỗi (Seq 10-12)**: Agent không tạo file báo cáo rỗng hay bịa số liệu, mà thông báo lỗi file không tồn tại cho người dùng.

---

## 4. Trả lời câu hỏi trọng tâm bài học

### Câu hỏi 1: Phần nào do script tính, phần nào do model diễn giải?

| Phân hệ đảm nhiệm | Nhiệm vụ chi tiết | Ranh giới trách nhiệm |
|---|---|---|
| **Script tính toán (`check_csv.py`)** | 1. Parse CSV, strip khoảng trắng các trường dữ liệu.<br>2. Kiểm tra tính hợp lệ của kiểu dữ liệu (số thực không âm, hữu hạn).<br>3. Khử trùng lặp theo quy tắc nghiêm ngặt: giữ duy nhất lần xuất hiện đầu tiên của mỗi `task_id`.<br>4. Lọc và tổng hợp các lỗi dữ liệu thành danh sách mã chuẩn hóa.<br>5. Tính toán chính xác tổng số giờ hợp lệ theo từng nhân sự (`hours_by_owner`).<br>6. So sánh toán học tổng giờ với ngưỡng (`total_hours > max_hours`) để xác định `overloaded_owners`.<br>7. Trả mã exit code (0 khi thành công, khác 0 khi lỗi hệ thống/tham số). | **Tính toán số học và logic dữ liệu tất định (Deterministic)**: Đảm bảo độ chính xác tuyệt đối 100%, không bị ảnh hưởng bởi tính ngẫu nhiên hay giới hạn tính toán của mô hình ngôn ngữ lớn (LLM). |
| **Model diễn giải (LLM Agent)** | 1. Đọc và hiểu yêu cầu bằng ngôn ngữ tự nhiên từ người dùng.<br>2. Xác định intent, đối chiếu metadata để chọn đúng skill `csv-quality`.<br>3. Kiểm tra điều kiện đầu vào: phát hiện thiếu tham số ngưỡng để chủ động hỏi lại người dùng thay vì chạy lệnh lỗi.<br>4. Xây dựng câu lệnh Bash hoàn chỉnh với các đối số chính xác.<br>5. Đọc tài liệu mẫu báo cáo (`report-template.md`), ánh xạ JSON có cấu trúc thành báo cáo Markdown hoàn chỉnh.<br>6. Đưa ra nhận xét, đánh giá định tính và đề xuất các giải pháp nghiệp vụ (tái phân bổ nhân sự, làm sạch dữ liệu).<br>7. Điều hướng luồng hội thoại linh hoạt khi gặp lỗi ngoại lệ. | **Nhận thức, điều phối và ngữ cảnh hóa (Contextualization & Reasoning)**: Kết nối yêu cầu tự nhiên của con người với công cụ kỹ thuật số, biến dữ liệu thô thành thông tin hữu ích cho việc ra quyết định. |

### Câu hỏi 2: Nếu sửa script nhưng không cập nhật skill và reference, báo cáo có thể sai hoặc thiếu thông tin gì?

1. **Rủi ro ở tầng điều phối Agent (Khi không cập nhật `SKILL.md`)**:
   - **Lỗi gọi lệnh (CLI invocation error)**: Script đã cập nhật bắt buộc tham số `--max-hours`, nhưng nếu `SKILL.md` không nêu rõ, Agent sẽ gọi script theo cú pháp cũ (`python check_csv.py --input ...`), dẫn đến việc script bị văng lỗi `argparse` (exit code 2) và Agent không thể hoàn thành công việc.
   - **Hành vi suy diễn tùy tiện (Hallucination)**: Khi người dùng không cung cấp ngưỡng, Agent cũ không có quy tắc "hỏi lại khi thiếu ngưỡng" nên có thể tự ý lấy một con số ngẫu nhiên từ lịch sử hội thoại trước đó, hoặc tự giả định ngưỡng 8 một cách thiếu căn cứ.
   - **Bỏ sót tính năng**: Agent có thể không biết rằng script đã có khả năng tính tổng giờ theo owner, dẫn đến việc Agent tự viết script Python tạm thời hoặc tính nhẩm trong đầu, gây ra sai số và cộng trùng lặp ID.

2. **Rủi ro ở tầng trình bày báo cáo (Khi không cập nhật `references/report-template.md`)**:
   - **Thiếu các trường dữ liệu trọng yếu**: Báo cáo sinh ra theo mẫu cũ sẽ hoàn toàn vắng bóng bảng "Tổng quan khối lượng công việc" (`hours_by_owner`) và mục "Danh sách người quá tải" (`overloaded_owners`).
   - **Thiếu tính minh bạch trong việc loại trừ dòng**: Mẫu cũ không có bảng `excluded_rows`, khiến người quản lý không thể biết tại sao công việc T02 (5 giờ) của Lan hay T04 của Minh lại không được ghi nhận.
   - **Thiếu thông tin ngữ cảnh kiểm thử**: Báo cáo sẽ thiếu thông tin ngưỡng giờ tối đa áp dụng (`max_hours`) và mã trạng thái thực thi (`exit_code`), làm giảm giá trị kiểm toán của tài liệu.
