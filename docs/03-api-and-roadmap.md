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
| `POST` | `/projects/assist/scope-optimizer` | Agent 1 (Research Setup): Phân tích & tối ưu phạm vi đề tài | ✅ Sẵn sàng |
| `POST` | `/projects/assist/criteria-generator` | Agent 2 (Research Setup): Sinh tiêu chí Inclusion / Exclusion chuẩn SLR | ✅ Sẵn sàng |
| `POST` | `/projects/assist/pico-query` | Agent 3 (Research Setup): Phân rã PICO & tạo truy vấn Boolean học thuật | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/papers` | Lấy danh sách bài báo (ưu tiên bài `uncertain` lên đầu) | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/search` | Tìm kiếm bài báo trên OpenAlex, đối chiếu SJR (`Q1`–`Q4`) & lưu DB | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/search/snowball` | Mở rộng tập bài báo 2 chiều (Backward & Forward Citation Snowballing) | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/search/history` | Lịch sử các truy vấn tìm kiếm & snowballing của project | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/papers/{paper_id}/ingest-pdf` | Tải tự động Open Access PDF, bóc tách chunk & vector hóa vào `pgvector` | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/papers/{paper_id}/upload-pdf` | Tải trực tiếp file PDF cục bộ, bóc tách chunk & lưu vector vào `pgvector` | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/papers/{paper_id}/pdf-highlight` | Tô sáng nguyên văn trên PDF (PyMuPDF Bounding Box + PNG Base64 Highlight) | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/screening/quality-gate` | Kiểm tra cổng chất lượng Grounding Gate ($\ge 80\%$) & số bài báo tối thiểu | ✅ Sẵn sàng |
| `PATCH` | `/projects/{project_id}/screening/papers/{paper_id}/label` | Gắn nhãn thủ công (`included` / `excluded`) | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/screening/papers/{paper_id}/hitl-override` | Người dùng quyết định cuối cùng (Human-in-the-Loop Override) | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/screening/run-active-learning` | Chạy vòng lặp ML (`TF-IDF + LogisticRegression`) & phân loại tự động | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/screening/auto-label-uncertain` | Dùng LLM chấm điểm tự động các bài `uncertain` | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/screening/dual-peer-screen` | Sàng lọc song song 2 Agent + Grounding Verifier & Quality Gate 80% | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/workspace/messages` | Lấy lịch sử hội thoại Hybrid RAG của project | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/workspace/chat` | Truy vấn Hybrid RRF RAG (`pgvector` + Lexical + Guardrail + Citations) | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/conflicts` | Xem các cạnh mâu thuẫn (`ConflictEdge`) & `ResearchGap` đã lưu | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/conflicts/analyze` | Chạy pipeline 3 Agent (Full-Text Claim Extraction + Verbatim Gate) | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/conflicts/comparative-matrix` | Bảng tổng hợp bằng chứng (Evidence Synthesis Matrix) | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/conflicts/kpi-metrics` | Chỉ số hiệu năng SLR (% tiết kiệm token, số giờ tiết kiệm, tỷ lệ tự động) | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/conflicts/graph` | Lấy dữ liệu đồ thị mâu thuẫn (`nodes`, `edges`, `research_gaps`) cho React Flow | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/conflicts/export-draft` | Xuất bản thảo Markdown, LaTeX (`.tex`), Quarto (`.qmd`), BibTeX & PRISMA 2020 SVG | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/conflicts/export-xlsx` | Xuất sổ tính Excel `.xlsx` 3 sheet (*Papers*, *Claims & Conflicts*, *Gaps*) | ✅ Sẵn sàng |
| `GET` | `/projects/{project_id}/conflicts/usage-observability` | Thống kê lượng token sử dụng, chi phí ước tính & token tiết kiệm nhờ Active Learning | ✅ Sẵn sàng |
| `GET/POST` | `/projects/{project_id}/analysis/datasets` | Quản lý & phân tích hồ sơ bộ dữ liệu định lượng (CSV) | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/analysis/datasets/upload-file` | Tải file `.csv` để tự động kiểm định schema & missingness | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/analysis/datasets/{dataset_id}/advise` | Cố vấn phương pháp thống kê / ML, cảnh báo rủi ro dữ liệu & sinh mã Python | ✅ Sẵn sàng |
| `POST` | `/projects/{project_id}/analysis/datasets/{dataset_id}/execute` | Thực thi mã Python EDA trong AST-Guarded Code Sandbox an toàn | ✅ Sẵn sàng |

*(Sau khi chạy backend, bạn có thể test toàn bộ các endpoint này trực quan qua Swagger UI tại `http://localhost:8000/docs`)*

---

## 2. Lộ trình Triển khai (Development Roadmap — Đã Hoàn Thành Sprints A–F)

Toàn bộ lộ trình 4 Sprint gốc và 6 Sprint nâng cao (Sprint A $\to$ Sprint F) đã được hoàn thiện và kiểm thử tự động:

### Sprint 1 (Sprint B & C): Hoàn thiện Luồng Thiết lập, Sàng lọc & Dual-Agent Peer Screening
- [x] Bộ 3 Agent Thiết lập Nghiên cứu (`Scope Optimizer`, `Criteria Generator`, `PICO & Boolean Query`) và 2-Way OpenAlex Citation Snowballing.
- [x] Tích hợp bộ tra cứu **SCImago Journal Rank (SJR)** từ file CSV offline vào bảng `sjr_journals` để gắn nhãn `Q1`, `Q2`, `Q3`, `Q4` và `h_index`.
- [x] Xây dựng **Dual-Agent Peer Screener** kèm **Deterministic Grounding Verifier**, cổng kiểm soát chất lượng 80% (**Quality Gate**) và **Human-in-the-Loop (HITL) Override**.

### Sprint 2 (Sprint E): Trực quan hóa Đồ thị Mâu thuẫn (Conflict Graph UI)
- [x] API `/projects/{id}/conflicts/graph` trả về dữ liệu dạng Graph (`nodes`, `edges`, `research_gaps`) kèm chi tiết tranh biện.
- [x] Tích hợp `@xyflow/react` trong `ConflictGraphTab.jsx` với bộ lọc loại xung đột và drawer xem chi tiết tranh biện & nguyên nhân gốc rễ.
- [x] Tối ưu bắt cặp ngữ nghĩa trong `conflict_engine.py` để giảm độ phức tạp $O(N^2)$ trước khi gọi Agent 2.

### Sprint 3 (Sprint D): PDF Full-Text Ingestion, Hybrid RAG & Verifiable Citations
- [x] `pdf_processor.py` dùng **PyMuPDF (`fitz`)** đọc toàn văn PDF, chia chunk theo trang/mục và tô sáng nguyên văn bằng chứng (`get_evidence_highlight_data` xuất toạ độ Bounding Box + ảnh PNG Base64).
- [x] Lưu vector embedding vào bảng `paper_chunks` (`pgvector`) và truy vấn bằng **Hybrid RRF (Reciprocal Rank Fusion)** kết hợp Cosine Similarity + Lexical Overlap + **RAG Guardrail**.
- [x] Nâng cấp Agent 1 (`extract_paper_claims`) đọc ưu tiên từ toàn văn `PaperChunk` và kiểm chứng qua **Verbatim Quote Gate**.

### Sprint 4 (Sprint A, E & F): Xuất báo cáo chuẩn PRISMA 2020, Python EDA Sandbox & CI/CD
- [x] Tự động tính toán số liệu và vẽ sơ đồ **PRISMA 2020 Flow Diagram** (`.svg`) và xuất file Excel `.xlsx` 3 sheet chuyên nghiệp (`openpyxl`).
- [x] Tích hợp **AST-Guarded Python EDA Code Sandbox** (`code_sandbox.py`), bảng giám sát chi phí/độ trễ `llm_usage_logs` (`telemetry.py`), và bộ benchmark đánh giá định lượng (`python -m eval.run_eval`).
- [x] Thiết lập Async Alembic migrations (`0001` $\to$ `0004`) và GitHub Actions CI (`ruff` + `pytest` + `eval` + `npm run build`).
