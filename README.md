# LitNexus

**Active-Learning Systematic Review & Cross-Paper Conflict Discovery Engine**

LitNexus giúp các nhà nghiên cứu thực hiện **Systematic Literature Review (SLR)** theo chuẩn PRISMA với 2 năng lực cốt lõi:
1. **Active Learning Hybrid Screening (Phễu lọc tốc độ cao)**: Thu thập hàng nghìn bài báo từ OpenAlex/Semantic Scholar, dùng Machine Learning cục bộ kết hợp với LLM chọn lọc thông minh (*uncertainty sampling*) để giảm 90% chi phí token và thời gian đọc thủ công.
2. **Cross-Paper Multi-Agent Conflict Discovery (Tranh biện & Phát hiện Mâu thuẫn)**: So sánh đối chiếu đa chiều giữa các bài báo cốt lõi để tìm ra **điểm đồng thuận (Consensus)**, **mâu thuẫn thực nghiệm (Empirical Contradictions)**, và đề xuất **Khoảng trống nghiên cứu (Research Gaps)** có bằng chứng trích dẫn rõ ràng.

---

## Tài liệu chi tiết (Documentation)

Trước khi bắt tay vào phát triển tính năng mới, bạn có thể đọc bộ tài liệu kiến trúc tại thư mục `docs/`:
- [01. Tổng quan Kiến trúc & Lược đồ Database (ERD)](docs/01-architecture-overview.md)
- [02. Chi tiết Tính năng, Thuật toán & Cấu trúc Module](docs/02-features-and-modules.md)
- [03. Danh sách API & Lộ trình Triển khai (Roadmap)](docs/03-api-and-roadmap.md)

---

## Kiến trúc công nghệ (Tech Stack)

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 (Async), Alembic
- **Database & Vector Store**: PostgreSQL 16 + `pgvector` (chạy trên Docker)
- **AI & ML**:
  - **LiteLLM Router**: Cổng gọi LLM tập trung với schema validation & automatic provider fallback (Gemini / OpenAI / Groq).
  - **Active Learning Engine**: `scikit-learn` (TF-IDF + LogisticRegression Uncertainty Sampling).
  - **Multi-Agent Pipeline**: Claim Extraction $\to$ Cross-Examiner $\to$ Gap Synthesizer.
- **Academic APIs**: OpenAlex API (miễn phí), Semantic Scholar API, SJR SCImago Quartile lookup.
- **Frontend**: React (Vite), Tailwind CSS, Lucide Icons.

---

## Cài đặt & Khởi chạy Local

### 1. Chuẩn bị biến môi trường & Database
```bash
cp .env.example .env
# Mở .env và điền GEMINI_API_KEY hoặc OPENAI_API_KEY

docker compose up -d db
```

### 2. Khởi chạy Backend
```bash
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Mac/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API docs sẽ có tại: `http://localhost:8000/docs`

### 3. Khởi chạy Frontend
```bash
cd frontend
npm install
npm run dev
```
Truy cập ứng dụng tại: `http://localhost:5173`
