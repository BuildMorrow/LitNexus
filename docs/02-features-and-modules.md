# 02. Chi tiết Tính năng & Cấu trúc Module

Tài liệu này giải thích sâu cách từng module trong **LitNexus** hoạt động từ thuật toán bên dưới đến mã nguồn thực tế, giúp bạn nắm vững trước khi phát triển mở rộng.

---

## Module 1: Xác thực & Cô lập Dự án (Auth & Multi-Tenant Guard)

- **File mã nguồn**:
  - [security.py](file:///D:/BuildMorrow/LitNexus/backend/app/core/security.py)
  - [deps.py](file:///D:/BuildMorrow/LitNexus/backend/app/api/deps.py)
  - [auth.py](file:///D:/BuildMorrow/LitNexus/backend/app/api/v1/auth.py)
  - [projects.py](file:///D:/BuildMorrow/LitNexus/backend/app/api/v1/projects.py)
- **Cơ chế hoạt động**:
  - Mật khẩu được băm bằng `bcrypt` trực tiếp (an toàn và tương thích Python 3.13+).
  - Token JWT (`HS256`) mang theo `sub` là `user.id`.
  - Dependency `get_owned_project` luôn kiểm tra đồng thời `id == project_id` và `owner_id == current_user.id`. Mọi route con (`/search`, `/screening`, `/conflicts`) đều bắt buộc phụ thuộc `get_owned_project` để loại bỏ hoàn toàn lỗi rò rỉ dữ liệu giữa các user.

---

## Module 2: Tìm kiếm Học thuật Miễn phí (Academic Search)

- **File mã nguồn**:
  - [academic_search.py](file:///D:/BuildMorrow/LitNexus/backend/app/services/academic_search.py)
  - [search.py](file:///D:/BuildMorrow/LitNexus/backend/app/api/v1/search.py)
- **Cơ chế hoạt động**:
  - Kết nối thẳng tới **OpenAlex API** (`https://api.openalex.org/works`) — hoàn toàn miễn phí, giới hạn 100.000 request/ngày, hỗ trợ lọc sẵn các bài có abstract (`filter=has_abstract:true`).
  - **Giải mã Abstract**: OpenAlex không trả về abstract dạng chuỗi thuần vì lý do bản quyền tóm tắt, mà trả về cấu trúc `abstract_inverted_index` (từ điển `{word: [positions]}`). Hàm `reconstruct_abstract()` tái dựng lại toàn bộ đoạn văn bản gốc theo đúng thứ tự vị trí.
  - **Khử trùng lặp (Deduplication)**: Trước khi insert vào PostgreSQL, hệ thống kiểm tra `doi` và `openalex_id` đã tồn tại trong project hay chưa.

---

## Module 3: Active Learning Hybrid Screener (Tính năng Độc quyền #1)

- **File mã nguồn**:
  - [active_screener.py](file:///D:/BuildMorrow/LitNexus/backend/app/services/active_screener.py)
  - [screening.py](file:///D:/BuildMorrow/LitNexus/backend/app/api/v1/screening.py)
  - [test_active_screener.py](file:///D:/BuildMorrow/LitNexus/backend/tests/test_active_screener.py)

### Nguyên lý hoạt động
Thay vì tốn tiền gọi LLM đọc toàn bộ 2.000 bài báo, hệ thống dùng vòng lặp **Uncertainty Sampling**:

1. **Cold Start Guard**:
   - Nếu số bài đã gắn nhãn (bởi Human hoặc LLM) nhỏ hơn `6` bài hoặc chưa có đủ cả 2 lớp (`included` và `excluded`), model chưa đủ dữ liệu để học $\to$ Đánh dấu tất cả là `query_llm` với độ bất định `1.0`.
2. **Vector hóa & Huấn luyện cục bộ (mất < 0.2 giây trên CPU)**:
   - Kết hợp `Title + Abstract` thành văn bản đầu vào.
   - `TfidfVectorizer` (unigram + bigram, tối đa 5.000 features, `sublinear_tf=True`) biến đổi văn bản thành vector đặc trưng.
   - `LogisticRegression(class_weight="balanced")` học ranh giới phân loại từ các bài đã gắn nhãn.
3. **Tính Xác suất & Độ bất định (Uncertainty Score)**:
   - Mô hình dự đoán xác suất $p \in [0, 1]$ bài báo thuộc nhóm `included`.
   - Độ bất định (Margin Uncertainty) được tính theo công thức:
     $$U(p) = 1 - 2 \cdot |p - 0.5|$$
     - Nếu $p = 0.50$ (nằm ngay ranh giới phân vân nhất) $\implies U = 1.0$.
     - Nếu $p = 0.99$ hoặc $p = 0.01$ (cực kỳ chắc chắn) $\implies U = 0.02$.
4. **Ngưỡng ra quyết định (Threshold Gating)**:
   - $p \ge 0.85 \implies$ `auto_include` (`screening_source = active_learning`).
   - $p \le 0.15 \implies$ `auto_exclude` (`screening_source = active_learning`).
   - $0.15 < p < 0.85 \implies$ `uncertain` (chỉ nhóm bài nằm ở vùng phân vân này mới được ưu tiên đưa lên đầu danh sách để người dùng hoặc LLM chấm tiếp).

---

## Module 4: Cross-Paper Multi-Agent Conflict Discovery (Tính năng Độc quyền #2)

- **File mã nguồn**:
  - [conflict_engine.py](file:///D:/BuildMorrow/LitNexus/backend/app/services/conflict_engine.py)
  - [conflicts.py](file:///D:/BuildMorrow/LitNexus/backend/app/api/v1/conflicts.py)
  - [conflict.py](file:///D:/BuildMorrow/LitNexus/backend/app/models/conflict.py)

### Quy trình 3 Agent nối tiếp nhau

1. **Agent 1 — Claim Extractor (`extract_paper_claims`)**:
   - Đọc từng bài báo đã qua sàng lọc (`included`).
   - Bóc tách thành cấu trúc chuẩn hóa `ExtractedClaimSchema`:
     - `claim_text`: Khẳng định khoa học chính.
     - `methodology`: Phương pháp/mô hình sử dụng.
     - `dataset`: Tập dữ liệu thử nghiệm.
     - `metric_summary`: Chỉ số định lượng (F1, Accuracy, Latency...).
     - `assumptions`: Các giả định ngầm (vd: *tín hiệu sạch không có nhiễu*).
     - `evidence_quote`: Câu trích dẫn nguyên văn làm bằng chứng.
2. **Agent 2 — Cross-Examiner (`cross_examine_claims`)**:
   - Bắt cặp từng cặp luận điểm $(A, B)$ giữa các bài báo khác nhau.
   - Đóng vai trọng tài tranh biện giữa *Advocate của bài A* và *Challenger của bài B*, phân loại mối quan hệ thành 1 trong 4 nhãn:
     - `contradicts`: Kết quả hoặc kết luận đối lập trực tiếp.
     - `assumption_mismatch`: Khác nhau do điều kiện giả định/tập dữ liệu không tương đồng.
     - `refines`: Bài B cải tiến hoặc thu hẹp phạm vi của bài A.
     - `supports`: Đồng thuận và củng cố lẫn nhau.
   - Sinh ra `root_cause_hypothesis` (giả thuyết giải thích nguyên nhân gốc rễ của mâu thuẫn).
3. **Agent 3 — Research Gap Synthesizer (`synthesize_research_gaps`)**:
   - Gom toàn bộ các cạnh `contradicts` và `assumption_mismatch` phát hiện được.
   - Đối chiếu với `research_question` của project để tổng hợp ra **Top 3 Research Gaps** kèm hướng thực nghiệm đề xuất và `novelty_score`.

---

## Module 5: Cổng gọi LLM tập trung (Centralized LLM Router)

- **File mã nguồn**: [llm_router.py](file:///D:/BuildMorrow/LitNexus/backend/app/services/llm_router.py)
- **Cơ chế hoạt động**:
  - Sử dụng `litellm.acompletion` để hỗ trợ đa nhà cung cấp (Google Gemini, OpenAI, Groq, Ollama...) chỉ qua chuỗi tên model trong `.env` (ví dụ `gemini/gemini-2.5-flash`).
  - **Failover tự động**: Thử `LLM_PRIMARY_MODEL`, nếu lỗi quota/mạng/404 thì tự động chuyển sang danh sách `LLM_FALLBACK_MODELS`.
  - **Structured Output**: Đính kèm JSON Schema của Pydantic vào system prompt + bật `response_format={"type": "json_object"}` + tự lọc bỏ thẻ `<think>...</think>` hoặc markdown code fence trước khi validate dữ liệu.

---

## Module 6: Giao diện Frontend (React + Vite + Tailwind)

- **File mã nguồn**:
  - [App.jsx](file:///D:/BuildMorrow/LitNexus/frontend/src/App.jsx)
  - [api.js](file:///D:/BuildMorrow/LitNexus/frontend/src/services/api.js)
- **Nguyên tắc**:
  - Mọi request đi qua hàm `apiRequest()` duy nhất, tự động gắn `Authorization: Bearer <token>` và đọc `VITE_API_URL` từ biến môi trường (tuyệt đối không hardcode IP backend).
  - Giao diện chia rõ 2 chặng của chiếc phễu nghiên cứu: *Stage 1 (Active Learning Hybrid Screener)* và *Stage 2 (Cross-Paper Conflict & Gap Engine)*.
