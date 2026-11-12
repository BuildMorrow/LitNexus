# 03. Tham chiếu API & Lộ trình Phát triển (API & Roadmap)

---

## 1. Danh sách API hiện tại (`/api/v1`)

| Method | Endpoint | Mô tả | Trạng thái |
|---|---|---|---|
| `GET` | `/health` | Kiểm tra trạng thái sống của API server | ✅ Sẵn sàng |
| `POST` | `/auth/register` | Đăng ký tài khoản mới, trả về JWT token | ✅ Sẵn sàng |
| `POST` | `/auth/login` | Đăng nhập, trả về JWT token | ✅ Sẵn sàng |
| `GET` | `/projects` | Lấy danh sách project của user đang đăng nhập | ✅ Sẵn sàng |
| `POST` | `/projects` | Tạo project nghiên cứu mới (PICO + Criteria) | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}` | Lấy chi tiết 1 project (có kiểm tra quyền sở hữu) | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/papers` | Lấy danh sách bài báo (ưu tiên bài `uncertain` lên đầu) | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/search` | Tìm kiếm bài báo trên OpenAlex & lưu DB | ✅ Sẵn sàng |
| `PATCH` | `/projects/{project_id}/screening/papers/{paper_id}/label` | Gắn nhãn thủ công (`included` / `excluded`) | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/screening/run-active-learning` | Chạy vòng lặp ML huấn luyện & phân loại tự động | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/conflicts` | Xem các cạnh mâu thuẫn & Research Gaps đã lưu | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/conflicts/analyze` | Chạy pipeline 3 Agent phân tích mâu thuẫn & gợi ý đề tài | ✅ Sẵn sàng |

*(Sau khi chạy backend, bạn có thể test toàn bộ các endpoint này trực quan qua Swagger UI tại `http://localhost:8000/docs`)*

---

## 2. Lộ trình Triển khai Tiếp theo (Development Roadmap)

Để biến khung nền tảng hiện tại thành sản phẩm hoàn chỉnh, bạn nên triển khai lần lượt theo 4 Sprint ngắn:

### Sprint 1: Hoàn thiện Luồng Sàng lọc & LLM Batch Screening
- [ ] Thêm API `POST /projects/{id}/screening/auto-label-uncertain`: Dùng `llm_router` để tự động chấm điểm top 10 bài báo có `al_uncertainty_score` cao nhất (thay vì user phải tự chấm hết bài phân vân).
- [ ] Tích hợp bộ tra cứu **SCImago Journal Rank (SJR)** từ file CSV offline vào bảng tham chiếu để gắn nhãn `Q1`, `Q2`, `Q3`, `Q4` cho mỗi bài báo ngay khi search từ OpenAlex.
- [ ] Xây dựng UI **Auth Modal + Project Setup (PICO Wizard)** và **Active Screening Board** trên React (hiển thị thanh tỷ lệ tiết kiệm token & nút duyệt nhanh 1-click).

### Sprint 2: Trực quan hóa Đồ thị Mâu thuẫn (Conflict Graph UI)
- [ ] Bổ sung API trả về dữ liệu dạng Graph (`nodes` = các bài báo & claims, `edges` = `contradicts` / `supports` / `assumption_mismatch`) kèm tiêu đề bài báo để Frontend dễ vẽ.
- [ ] Tích hợp thư viện vẽ đồ thị (như `react-force-graph` hoặc `@xyflow/react`) để người dùng bấm vào cạnh màu đỏ xem chi tiết cuộc tranh biện giữa 2 bài báo.
- [ ] Tối ưu chi phí Agent 2 (`cross_examine_claims`): Thay vì so sánh mọi cặp $O(N^2)$, dùng embedding của các claim để chỉ bắt cặp những claim có độ tương đồng ngữ nghĩa cao về chủ đề/phương pháp trước khi cho tranh biện.

### Sprint 3: PDF Full-Text Ingestion & Verifiable Citations
- [ ] Viết `pdf_processor.py` dùng **PyMuPDF (`fitz`)** để đọc file PDF bài báo (lưu số trang `page_number` và tiêu đề mục `section_title`).
- [ ] Tạo vector embedding và lưu vào bảng `paper_chunks` (đã thiết kế sẵn cột `Vector(1536)` trong `pgvector`).
- [ ] Nâng cấp Agent 1 (`extract_paper_claims`) đọc từ **toàn văn PDF** thay vì chỉ đọc Abstract, kèm số trang chính xác chứa bằng chứng.

### Sprint 4: Xuất báo cáo chuẩn PRISMA 2020 & Deploy
- [ ] Tự động tính toán số liệu và vẽ sơ đồ **PRISMA Flow Diagram** (SVG) dựa trên số lượng bài ở từng bước (*Identified $\to$ Screened $\to$ Excluded $\to$ Included*).
- [ ] Xuất dữ liệu ra `.bib` (BibTeX), `.xlsx` (Excel), và báo cáo Markdown tổng hợp Research Gaps.
- [ ] Thiết lập Alembic migrations chuẩn cho Production và GitHub Actions CI (chạy `ruff` + `pytest` tự động mỗi lần push).
