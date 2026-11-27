# 08. Đánh giá Định lượng, Benchmark & Traceability Matrix (LitNexus v2)

Tài liệu này tổng hợp kết quả kiểm thử tự động, benchmark hiệu năng ngoại tuyến (`backend/eval/run_eval.py`) và bảng ánh xạ yêu cầu nghiệp vụ $\leftrightarrow$ mã nguồn $\leftrightarrow$ bộ test (`Code Traceability Matrix`) cho **LitNexus**.

---

## 1. Kết quả Benchmark Ngoại tuyến (`python -m eval.run_eval`)

Đo trực tiếp trên bộ dữ liệu chuẩn [golden_dataset.json](file:///d:/BuildMorrow/LitNexus/backend/eval/golden_dataset.json):

| Hạng mục Đánh giá | Chỉ số Đo được | Ý nghĩa Kỹ thuật |
|---|---|---|
| **Active Learning Classification Acc** | **100.0%** (`9.03 ms`) | Phân tách chính xác bài `included` vs `excluded` chỉ bằng mô hình TF-IDF + LogisticRegression CPU trong $< 10$ ms. |
| **Warm-Start Caution Gate (`[0.20, 0.80]`)** | **0.0%** auto-routed trên 12 seed ngắn | Ngưỡng tự tin giữ nguyên chế độ thận trọng ở giai đoạn warm-start ít mẫu, chỉ tự động lọc khi đủ độ tin cậy cao ($p \ge 0.80$ hoặc $p \le 0.20$). |
| **Semantic Candidate Pairing ($O(k \cdot N)$)** | **Giảm 62.2%** số cặp (`17` vs `45` cho $N=10$) | Giảm đáng kể chi phí gọi Agent 2 Cross-Examiner mà vẫn giữ được các cặp luận điểm đồng chủ đề. |
| **Deterministic Grounding Verifier** | **1/2 verified** (`precision = 0.5` trên 1 quote thật + 1 quote bịa) | Từ chối 100% trích dẫn bịa đặt không tồn tại trong văn bản nguồn. |
| **RAG Guardrail Injection Block Rate** | **100.0%** (`3/3` mẫu tấn công) | Chặn đứng các truy vấn prompt injection / system prompt override trước khi chạm vào RAG pipeline. |
| **Code Sandbox Security Block Rate** | **100.0%** (`3/3` lệnh nguy hiểm bị chặn) | AST Visitor từ chối `import os`, `import subprocess`, `open()`, và truy cập dunder. |
| **Code Sandbox Execution Speed** | **PASS (`625 ms`)** | Nạp CSV vào Pandas DataFrame `df`, tính thống kê và sinh ảnh Matplotlib an toàn dưới timeout. |

---

## 2. Kết quả Kiểm thử Tự động (Automated Verification Suite)

- **Backend Linter (`ruff check app tests scripts eval`)**: `All checks passed!`
- **Backend Test Suite (`python -m pytest tests/ -q`)**: **44 passed** across 11 test files:
  - [test_active_screener.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_active_screener.py)
  - [test_alembic_config.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_alembic_config.py)
  - [test_candidate_pairing.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_candidate_pairing.py)
  - [test_data_analysis.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_data_analysis.py)
  - [test_graph_and_export.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_graph_and_export.py)
  - [test_kpi_and_matrix.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_kpi_and_matrix.py)
  - [test_llm_screening.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_llm_screening.py)
  - [test_pdf_processor.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_pdf_processor.py)
  - [test_peer_screener_and_grounding.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_peer_screener_and_grounding.py)
  - [test_prisma_and_excel_export.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_prisma_and_excel_export.py)
  - [test_rag_and_highlighter.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_rag_and_highlighter.py)
  - [test_sandbox_and_eval.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_sandbox_and_eval.py)
  - [test_setup_agents_and_snowball.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_setup_agents_and_snowball.py)
  - [test_sjr_service.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_sjr_service.py)
- **Frontend Production Build (`npm run build`)**: Build sạch qua Vite + React 18 + Tailwind + `@xyflow/react`.

---

## 3. Code Traceability Matrix (Yêu cầu $\leftrightarrow$ Code $\leftrightarrow$ Tests)

| Phân hệ Nghiệp vụ | Mã nguồn Backend / Frontend | Bộ kiểm thử |
|---|---|---|
| **DB Migrations & Multi-Tenant Guard** | [deps.py](file:///d:/BuildMorrow/LitNexus/backend/app/api/deps.py), [alembic/versions/](file:///d:/BuildMorrow/LitNexus/backend/alembic/versions) | [test_alembic_config.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_alembic_config.py) |
| **3 AI Setup Agents (Scope, Criteria, PICO)** | [setup_agents.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/setup_agents.py), [ResearchSetupTab.jsx](file:///d:/BuildMorrow/LitNexus/frontend/src/components/setup/ResearchSetupTab.jsx) | [test_setup_agents_and_snowball.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_setup_agents_and_snowball.py) |
| **Search, Snowballing 2 Chiều & SJR DB** | [academic_search.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/academic_search.py), [sjr_service.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/sjr_service.py), [import_sjr.py](file:///d:/BuildMorrow/LitNexus/backend/scripts/import_sjr.py) | [test_setup_agents_and_snowball.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_setup_agents_and_snowball.py), [test_sjr_service.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_sjr_service.py) |
| **Active Learning + Dual-Peer + Grounding Gate** | [active_screener.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/active_screener.py), [peer_screener.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/peer_screener.py), [grounding_verifier.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/grounding_verifier.py) | [test_active_screener.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_active_screener.py), [test_peer_screener_and_grounding.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_peer_screener_and_grounding.py) |
| **pgvector Hybrid RAG + Guardrail + PDF Box** | [rag_service.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/rag_service.py), [rag_guardrail.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/rag_guardrail.py), [pdf_processor.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/pdf_processor.py), [WorkspaceRagTab.jsx](file:///d:/BuildMorrow/LitNexus/frontend/src/components/workspace/WorkspaceRagTab.jsx) | [test_rag_and_highlighter.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_rag_and_highlighter.py), [test_pdf_processor.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_pdf_processor.py) |
| **Conflict Engine + Interactive Graph + PRISMA SVG/XLSX** | [conflict_engine.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/conflict_engine.py), [prisma_export.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/prisma_export.py), [ConflictGraphTab.jsx](file:///d:/BuildMorrow/LitNexus/frontend/src/components/conflicts/ConflictGraphTab.jsx), [DraftExportTab.jsx](file:///d:/BuildMorrow/LitNexus/frontend/src/components/export/DraftExportTab.jsx) | [test_candidate_pairing.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_candidate_pairing.py), [test_graph_and_export.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_graph_and_export.py), [test_prisma_and_excel_export.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_prisma_and_excel_export.py) |
| **EDA Data Profiler + Isolated Python Sandbox** | [data_profiler.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/data_profiler.py), [code_sandbox.py](file:///d:/BuildMorrow/LitNexus/backend/app/services/code_sandbox.py), [DataAnalysisTab.jsx](file:///d:/BuildMorrow/LitNexus/frontend/src/components/analysis/DataAnalysisTab.jsx) | [test_data_analysis.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_data_analysis.py), [test_sandbox_and_eval.py](file:///d:/BuildMorrow/LitNexus/backend/tests/test_sandbox_and_eval.py) |
