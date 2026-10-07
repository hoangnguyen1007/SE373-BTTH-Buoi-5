# Báo cáo Phân tích Block 1: Tra cứu chính sách đúng phiên bản

## 1. Giới thiệu và Mục tiêu
Block 1 tập trung vào việc bổ sung công cụ tìm kiếm tài liệu (`list_files`) và xây dựng skill tra cứu chính sách (`refund-policy`) cho agent. Mục tiêu là giúp agent:
- Tự động khám phá danh sách file trong thư mục `data/policies/` mà không bị phụ thuộc vào tên file cố định.
- Nạp và tuân thủ quy trình nghiệp vụ thông qua skill `refund-policy`: phân tích phạm vi hiệu lực của từng chính sách, chọn chính sách dựa trên **ngày mua hàng**, kiểm tra điều kiện kích hoạt và tính toán chênh lệch ngày lịch.
- Xử lý tình huống thiếu thông tin bằng cách hỏi lại người dùng thay vì tự tiện suy đoán.

---

## 2. Kết quả kiểm thử Tool `list_files` trực tiếp
Tool `list_files(path: str = ".")` được kiểm thử với 4 kịch bản theo yêu cầu bài thực hành:

| STT | Kịch bản kiểm thử | Đầu vào `path` | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| 1 | Thư mục hợp lệ trong workspace | `"data/policies"` | Trả về `ok: true`, danh sách entries sắp xếp theo tên, phân loại đúng `file`/`directory`. | `{"ok": true, "path": "data/policies", "entries": [{"name": "policy-before-oct.md", "path": "data/policies/policy-before-oct.md", "type": "file"}, {"name": "policy-from-oct.md", "path": "data/policies/policy-from-oct.md", "type": "file"}]}` | Đạt |
| 2 | Đường dẫn là file (không phải thư mục) | `"data/policies/policy-before-oct.md"` | Trả về `ok: false`, mã lỗi `NOT_A_DIRECTORY`. | `{"ok": false, "error": {"code": "NOT_A_DIRECTORY", "message": "Đây là file, không phải thư mục: data/policies/policy-before-oct.md"}}` | Đạt |
| 3 | Đường dẫn không tồn tại | `"data/non_existent_folder"` | Trả về `ok: false`, mã lỗi `DIRECTORY_NOT_FOUND`. | `{"ok": false, "error": {"code": "DIRECTORY_NOT_FOUND", "message": "Không tìm thấy thư mục: data/non_existent_folder"}}` | Đạt |
| 4 | Đường dẫn vượt khỏi workspace | `"../../secret"` hoặc `"../"` | Trả về `ok: false`, mã lỗi `PATH_OUTSIDE_WORKSPACE`. | `{"ok": false, "error": {"code": "PATH_OUTSIDE_WORKSPACE", "message": "Đường dẫn thoát ra ngoài workspace: ../../secret"}}` | Đạt |

---

## 3. Kết quả các trường hợp kiểm thử nghiệp vụ

### 3.1. Trường hợp A: Mua trước ngày đổi chính sách
- **Câu hỏi**: *"Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, chưa kích hoạt. Tôi có được hoàn không?"*
- **Phân tích nghiệp vụ**:
  - Ngày mua: `28/09/2026` (< 2026-10-01) -> Áp dụng `policy-before-oct.md`.
  - Ngày yêu cầu: `06/10/2026`.
  - Số ngày lịch chênh lệch: 30 - 28 + 6 = 8 ngày.
  - Quy định trong chính sách: Hoàn tiền trong vòng 7 ngày kể từ ngày mua.
  - Đánh giá: 8 ngày > 7 ngày -> **Không đủ điều kiện hoàn tiền**.
- **Kết quả agent trả lời**:
  - Chọn đúng chính sách cũ (`policy-before-oct.md`).
  - Tính chính xác 8 ngày đã qua.
  - Kết luận không đủ điều kiện hoàn tiền do vượt quá thời hạn 7 ngày. Phí hoàn tiền không áp dụng.

### 3.2. Trường hợp B: Mua từ ngày đổi chính sách (sau khi đổi tên file)
- **Thiết lập**: Đổi tên hai file chính sách thành `chinh-sach-truoc-thang-10.md` và `chinh-sach-tu-thang-10.md`.
- **Câu hỏi**: *"Tôi mua ngày 02/10/2026, yêu cầu hoàn ngày 12/10/2026, chưa kích hoạt. Tôi có được hoàn không?"*
- **Phân tích nghiệp vụ**:
  - Ngày mua: `02/10/2026` (>= 2026-10-01) -> Áp dụng chính sách từ tháng 10 (`chinh-sach-tu-thang-10.md`).
  - Ngày yêu cầu: `12/10/2026`.
  - Số ngày lịch chênh lệch: 12 - 2 = 10 ngày.
  - Quy định trong chính sách: Hoàn tiền trong vòng 14 ngày kể từ ngày mua, miễn phí hoàn tiền.
  - Trạng thái: Chưa kích hoạt.
  - Đánh giá: 10 ngày <= 14 ngày, chưa kích hoạt -> **Đủ điều kiện hoàn tiền, không thu phí**.
- **Kết quả agent trả lời**:
  - Dùng `list_files` phát hiện tên file mới, đọc nội dung và áp dụng chính xác `chinh-sach-tu-thang-10.md`.
  - Tính đúng 10 ngày đã qua.
  - Kết luận đủ điều kiện hoàn tiền, phí 0%.

### 3.3. Trường hợp Thiếu thông tin
- **Câu hỏi**: *"Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026."*
- **Phân tích nghiệp vụ**:
  - Câu hỏi cung cấp ngày mua và ngày yêu cầu, nhưng thiếu **trạng thái kích hoạt sản phẩm**.
  - Skill yêu cầu: Nếu thiếu 1 trong 3 yếu tố (ngày mua, ngày yêu cầu, trạng thái kích hoạt), agent phải hỏi lại trước khi kết luận.
- **Kết quả agent trả lời**:
  - Agent không đưa ra kết luận hoàn tiền hay từ chối.
  - Agent lịch sự hỏi người dùng sản phẩm đã được kích hoạt hay chưa, giải thích rằng sản phẩm đã kích hoạt sẽ không được hoàn tiền.

---

## 4. Vị trí bằng chứng trong Trace Logs

Các file trace được lưu trữ đầy đủ tại thư mục `block-1/traces/`:

| Trường hợp | File Trace | Vị trí bằng chứng (Sequence / Event / ID) | Chi tiết bằng chứng |
|---|---|---|---|
| **Trường hợp A** | `case_a_purchase_before_oct.jsonl` | - **Seq 2**: `model_request` (Model call #1)<br>- **Seq 4**: `tool_started` (`tc_skill_a`)<br>- **Seq 5**: `tool_finished` (`read_file` `skills/refund-policy/SKILL.md`)<br>- **Seq 8**: `tool_started` (`tc_list_a`)<br>- **Seq 9**: `tool_finished` (`list_files` `data/policies`)<br>- **Seq 12**: `tool_started` (`tc_read_pol_a`)<br>- **Seq 13**: `tool_finished` (`read_file` `data/policies/policy-before-oct.md`)<br>- **Seq 18**: `model_response` | - Tool `list_files` trả về danh sách file chính sách.<br>- Agent đọc file `policy-before-oct.md` căn cứ ngày mua 28/09/2026.<br>- Final answer kết luận không đủ điều kiện (8 ngày > 7 ngày). |
| **Trường hợp B (Đổi tên)** | `case_b_purchase_from_oct_renamed.jsonl` | - **Seq 8**: `tool_started` (`tc_list_b`)<br>- **Seq 9**: `tool_finished` (`list_files` `data/policies`)<br>- **Seq 12**: `tool_started` (`tc_read_pol_b`)<br>- **Seq 13**: `tool_finished` (`read_file` `data/policies/chinh-sach-tu-thang-10.md`)<br>- **Seq 18**: `model_response` | - Tool `list_files` phát hiện tên file mới `chinh-sach-tu-thang-10.md`.<br>- Agent không gọi theo tên cũ mà đọc đúng tên file mới.<br>- Final answer kết luận đủ điều kiện (10 ngày <= 14 ngày), phí 0%. |
| **Thiếu thông tin** | `case_missing_activation_info.jsonl` | - **Seq 4**: `tool_started` (`tc_skill_m`)<br>- **Seq 5**: `tool_finished` (`read_file` `skills/refund-policy/SKILL.md`)<br>- **Seq 7**: `model_response` | - Sau khi nạp skill, agent nhận diện thiếu trạng thái kích hoạt.<br>- Agent không gọi kết luận mà hỏi lại trạng thái kích hoạt. |

---

## 5. Trả lời câu hỏi cuối bài

### Câu hỏi 1: Vì sao cần tool để tìm file và skill để hướng dẫn chọn chính sách?
- **Cần tool để tìm file (`list_files`)**:
  - LLM không có khả năng trực tiếp quan sát hệ thống file ngoại trừ thông qua các tool được cấp.
  - Khi hệ thống tài liệu thay đổi (tên file được cập nhật, thêm phiên bản mới, thay đổi cấu trúc), nếu không có tool duyệt thư mục, agent chỉ có thể đoán mò tên file dựa trên kiến thức cũ hoặc tên file cứng. Tool `list_files` mang lại tính **linh hoạt và tự thích ứng** cho agent đối với môi trường file động.
- **Cần skill để hướng dẫn chọn chính sách (`refund-policy`)**:
  - Skill đóng vai trò như một **quy trình thao tác chuẩn (SOP)**: quy định rõ tiêu chí nghiệp vụ (căn cứ vào ngày mua chứ không phải ngày yêu cầu), công thức tính số ngày, điều kiện dừng để hỏi lại khi thiếu dữ liệu, và mẫu format đầu ra.
  - Nếu chỉ có tool đọc file mà không có skill, model có thể tùy tiện chọn nhầm chính sách theo ngày yêu cầu, tự tiện suy đoán trạng thái kích hoạt, hoặc tính toán sai quy ước nghiệp vụ.

### Câu hỏi 2: Nếu agent chưa có tool tìm file, việc sửa prompt có giải quyết được yêu cầu đổi tên file không? Giải thích.
- **Trả lời**: **Không thể giải quyết triệt để.**
- **Giải thích chi tiết**:
  - Nếu sửa prompt bằng cách liệt kê danh sách tên file tĩnh, giải pháp này chỉ có tác dụng tức thời với đúng những cái tên được khai báo trong prompt đó. Khi có một phiên bản mới hoặc ai đó đổi tên file lần nữa, prompt lại lập tức trở nên lỗi thời (stale prompt).
  - System prompt không thể biết trước những thay đổi trên filesystem lúc runtime nếu không có cơ chế runtime inspection (`list_files`).
  - Hơn nữa, việc nhồi nhét mọi tên file và quy tắc vào system prompt sẽ làm phình to context window (lãng phí token), tăng chi phí và giảm độ tập trung của mô hình.
  - Do đó, việc trang bị tool `list_files` kết hợp với skill hướng dẫn là giải pháp kiến trúc đúng đắn và bền vững nhất.
