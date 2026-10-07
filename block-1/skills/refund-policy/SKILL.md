---
name: refund-policy
description: Tra cứu và áp dụng chính sách hoàn tiền cho khách hàng dựa trên ngày mua hàng. Dùng khi khách hàng hỏi về điều kiện, thời hạn, phí hoàn tiền hoặc chính sách đổi trả theo ngày mua.
---

# Refund policy

Hướng dẫn tra cứu và áp dụng chính sách hoàn tiền theo ngày mua của khách hàng.

## Các bước thực hiện

1. **Tìm tài liệu chính sách**:
   - Dùng tool `list_files` với đường dẫn `data/policies` để liệt kê các file chính sách hiện có trong thư mục `data/policies/`.
   - Không đoán trước hoặc ghi cố định tên file vì tên file có thể thay đổi giữa các phiên bản.

2. **Đọc tài liệu và chọn chính sách**:
   - Dùng tool `read_file` đọc nội dung từng file tìm được trong `data/policies/`.
   - Đọc kỹ phạm vi hiệu lực của từng tài liệu.
   - Chọn chính sách áp dụng dựa trên **ngày mua hàng** (`purchase date`) của khách hàng, không căn cứ vào ngày yêu cầu hoàn hay ngày hiện tại.

3. **Kiểm tra thông tin bắt buộc**:
   Xác định đủ 3 thông tin từ câu hỏi của khách hàng:
   - Ngày mua hàng (`purchase date`)
   - Ngày yêu cầu hoàn tiền (`refund request date`)
   - Trạng thái kích hoạt sản phẩm (`activation status`)

   *Lưu ý quan trọng*: Nếu thiếu bất kỳ thông tin nào trong 3 thông tin trên (ví dụ chưa rõ sản phẩm đã kích hoạt hay chưa), **phải hỏi lại người dùng** để làm rõ trước khi kết luận. Tuyệt đối không tự suy đoán (không tự giả định là "chưa kích hoạt").

4. **Tính toán và đối chiếu điều kiện**:
   - Tính số ngày đã qua: là chênh lệch số ngày lịch giữa ngày yêu cầu hoàn và ngày mua (`request_date - purchase_date`).
   - Bằng đúng giới hạn quy định vẫn được tính là đủ điều kiện về thời gian.
   - Sử dụng ngày yêu cầu nêu trong câu hỏi, không dùng ngày hiện tại của máy tính.
   - Đối chiếu điều kiện kích hoạt: nếu sản phẩm đã kích hoạt thì không được hoàn tiền.

5. **Trình bày câu trả lời**:
   - Đọc template tại `skills/refund-policy/references/answer-template.md` (hoặc `references/answer-template.md`).
   - Trình bày câu trả lời gồm các phần: chính sách áp dụng, số ngày đã qua, kết luận đủ/không đủ điều kiện, phí hoàn tiền nếu đủ điều kiện (hoặc không áp dụng) và đường dẫn tài liệu làm căn cứ.
