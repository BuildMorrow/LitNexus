# 07. Khảo sát Hệ sinh thái Công cụ & Agent Skills Học thuật trên GitHub (Ecosystem Survey)

Tài liệu này tổng hợp kết quả khảo sát các kho mã nguồn mở, công cụ nghiên cứu học thuật, và hệ thống **Agent Skills** hàng đầu hiện nay trên GitHub liên quan đến **Systematic Literature Review (SLR)**, **Active Learning**, và **Multi-Agent Scientific Discovery**.

---

## 1. Tổng quan Khảo sát & Xu hướng Công nghệ

Trong giai đoạn 2024–2026, nghiên cứu học thuật có sự dịch chuyển mạnh mẽ từ việc "sử dụng mô hình ngôn ngữ lớn để tóm tắt văn bản thông thường" sang:
1. **Agent Skills Standard**: Chuẩn hóa năng lực tác vụ của AI agent dưới dạng các gói `SKILL.md` có thể cắm ghép vào các IDE và Agent framework (như Cursor, Claude Code, Codex, Antigravity).
2. **Active Learning Screening**: Ứng dụng Machine Learning học tương tác để giải quyết bài toán sàng lọc hàng nghìn bài báo với chi phí token tối thiểu.
3. **Evidence Grounding & Citation Rigor**: Chuyển từ tổng hợp văn bản sang bóc tách luận điểm có bằng chứng (`claims + evidence quotes + page pinning`) và phân tích mâu thuẫn chéo giữa các bài báo (*cross-paper dialectic*).

---

## 2. Các Dự án Mã nguồn Mở Tiêu biểu trên GitHub

### 2.1. ASReview LAB (`asreview/asreview`)
- **Tổ chức**: Utrecht University (Hà Lan)
- **Điểm nổi bật**:
  - Dự án tiên phong ứng dụng **Active Learning** vào Systematic Review và phân tích tổng hợp (meta-analysis).
  - Sử dụng cơ chế *Oracle Mode* (Human-in-the-loop): Sau mỗi bài báo người dùng gắn nhãn, mô hình ML cục bộ (Naive Bayes, Logistic Regression, hoặc Neural Networks) tự động tính toán lại xác suất liên quan và tái sắp xếp toàn bộ kho bài chưa đọc.
  - Cung cấp chế độ *Simulation Mode* để đánh giá tỷ lệ phần trăm bài đọc tiết kiệm được trên các bộ dữ liệu đánh giá chuẩn (benchmark datasets).
- **Điểm hạn chế so với LitNexus**:
  - ASReview tập trung thuần túy vào sàng lọc thống kê, không có tầng 2 để bóc tách luận điểm chuyên sâu, không có cơ chế đối chiếu mâu thuẫn hay gợi ý Research Gaps.

---

### 2.2. PaperQA / PaperQA2 (`Future-House/paper-qa`)
- **Tổ chức**: FutureHouse Inc.
- **Điểm nổi bật**:
  - Gói RAG chuyên biệt dành riêng cho các bài báo khoa học và tệp PDF kỹ thuật.
  - Phiên bản PaperQA2 bổ sung cơ chế Agentic: tự động lặp lại truy vấn (*iterative query refinement*), kiểm tra tính hợp lệ của trích dẫn, phát hiện bài báo bị rút (*retraction checking*), và gắn chỉ mục trang chính xác tuyệt đối.
  - Sử dụng chiến lược phân tách đoạn văn bản thông minh (token-aware chunking).
- **Điểm hạn chế so với LitNexus**:
  - PaperQA2 hoạt động theo cơ chế hỏi-đáp câu hỏi cụ thể (Question Answering) trên một tập PDF có sẵn, không xây dựng quy trình phễu lọc hàng ngàn bài từ đầu theo chuẩn PRISMA và không tự động dựng đồ thị mâu thuẫn liên bài báo.

---

### 2.3. Stanford STORM (`stanford-oval/storm`)
- **Tổ chức**: Stanford Open Virtual Assistant Lab (OVAL)
- **Điểm nổi bật**:
  - STORM (*Synthesis of Topic Outlines through Repeated Multiperspective Questioning*) mô phỏng cuộc phỏng vấn đa góc nhìn giữa nhiều chuyên gia giả lập để viết bài tổng quan kiến thức hoàn chỉnh với đầy đủ trích dẫn kiểu Wikipedia.
  - Phân tích chủ đề từ nhiều quan điểm học thuật trái chiều.
- **Điểm hạn chế so với LitNexus**:
  - Mang tính chất tổng hợp bách khoa toàn thư mở rộng (broad encyclopedic overview) hơn là một quy trình Systematic Review tuân thủ tiêu chí khoa học khắt khe (PICO criteria, exclusion reasons, active uncertainty sampling).

---

### 2.4. Scientific Agent Skills (`K-Dense-AI/scientific-agent-skills`)
- **Tổ chức**: K-Dense AI
- **Điểm nổi bật**:
  - Kho lưu trữ bộ kỹ năng mẫu tuân thủ **chuẩn mở Agent Skills (`SKILL.md`)** dành cho các AI coding & research agents.
  - Chứa module `literature-review`: Hướng dẫn Agent cách xây dựng câu hỏi nghiên cứu, tạo chuỗi truy vấn học thuật chuẩn, thiết lập bảng ma trận bằng chứng (*evidence matrix*), và xuất báo cáo khoa học.
  - Cung cấp kỹ năng `scientific-schematics` để tự động vẽ sơ đồ khoa học (như PRISMA flow).

---

## 3. Ma trận So sánh Tính năng (Feature Comparison Matrix)

| Tiêu chí so sánh | ASReview LAB | PaperQA2 | Stanford STORM | K-Dense Skills | **LitNexus (Dự án này)** |
|---|:---:|:---:|:---:|:---:|:---:|
| **Thu thập dữ liệu học thuật mở (OpenAlex)** | ❌ (Cần file CSV/RIS đầu vào) | ❌ (Cần thư mục PDF cục bộ) | ⚠️ (Web Search) | ⚠️ (Tùy agent cấu hình) | **✅ Tích hợp sẵn Polite Pool 100k/ngày** |
| **Active Learning Hybrid Screener** | ✅ (Local ML thuần) | ❌ | ❌ | ❌ | **✅ Local ML + Uncertainty Sampling + LLM fallback** |
| **Bóc tách luận điểm có cấu trúc (Paper Claims)** | ❌ | ⚠️ (Text snippet) | ❌ | ⚠️ (Bảng mẫu) | **✅ Schema chuẩn (Method, Dataset, Metric, Assumptions, Quote)** |
| **Đối chiếu Biện chứng Cặp (Advocate vs Challenger)** | ❌ | ❌ | ⚠️ (Hỏi đáp đa góc nhìn) | ❌ | **✅ 4 nhãn quan hệ + Root Cause Hypothesis** |
| **Đồ thị Mâu thuẫn (Conflict Knowledge Graph)** | ❌ | ❌ | ❌ | ❌ | **✅ PostgreSQL Graph Edges** |
| **Đề xuất Đề tài Mới (Research Gaps + Novelty)** | ❌ | ❌ | ❌ | ❌ | **✅ Tự động tổng hợp Top 3 Gaps** |
| **Chuẩn hóa Agent Skill (`SKILL.md`)** | ❌ | ❌ | ❌ | ✅ | **✅ Cung cấp sẵn trong `.agents/skills/`** |

---

## 4. Định hướng Ứng dụng: Xây dựng Bộ Skill Chuẩn cho LitNexus

Dựa trên khảo sát chuẩn Agent Skills từ GitHub, LitNexus đóng gói 2 kỹ năng cốt lõi đặt trực tiếp trong thư mục `.agents/skills/` của workspace:

1. **`systematic-literature-review`** (`.agents/skills/systematic-literature-review/SKILL.md`):
   - Hướng dẫn AI Agent thực thi đúng chuẩn quy trình Systematic Literature Review: định hình PICO, xây dựng query OpenAlex, áp dụng tiêu chí gán nhãn, điều phối vòng lặp Active Learning, và tính toán số liệu PRISMA 2020.
2. **`cross-paper-conflict-analyzer`** (`.agents/skills/cross-paper-conflict-analyzer/SKILL.md`):
   - Hướng dẫn AI Agent bóc tách luận điểm khoa học có thể kiểm chứng (`PaperClaim`), kích hoạt giao thức tranh biện 2 chiều (Advocate vs Challenger), xác định nguyên nhân gốc rễ (nghi ngờ dữ liệu, giả định ngầm, kỹ thuật chuẩn hóa), và tổng hợp Research Gaps kèm điểm đột phá (`novelty_score`).
