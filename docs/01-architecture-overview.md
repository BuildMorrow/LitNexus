# 01. Tổng quan Kiến trúc Hệ thống (Architecture Overview)

Tài liệu này mô tả bức tranh tổng thể về kiến trúc kỹ thuật, mô hình dữ liệu và luồng đi của dữ liệu trong **LitNexus**.

---

## 1. Triết lý thiết kế cốt lõi: "The Research Funnel"

Thay vì dùng AI đắt đỏ để đọc toàn bộ hàng nghìn bài báo một cách mù quáng (tốn chi phí token, chậm và nhiều nhiễu), LitNexus tổ chức quy trình **Systematic Literature Review (SLR)** thành 2 tầng phễu kế tiếp nhau:

```mermaid
flowchart TD
    A["OpenAlex / Semantic Scholar (1.000 - 3.000 bài báo)"] --> B["Tầng 1: Active Learning Hybrid Screener"]
    B -->|"Cold start: 15-20 bài mẫu"| C["Human / LLM Adjudication"]
    C -->|"Huấn luyện lại model cục bộ"| B
    B -->|"Lọc tự động ~90% bài rõ ràng"| D["20 - 50 bài báo cốt lõi (Included)"]
    D --> E["Tầng 2: Multi-Agent Conflict Discovery"]
    E --> F["Agent 1: Claim Extractor"]
    F --> G["Agent 2: Cross-Examiner (So sánh cặp)"]
    G --> H["Agent 3: Research Gap Synthesizer"]
    H --> I["Đồ thị Mâu thuẫn & Đề xuất Đề tài mới"]
```

---

## 2. Kiến trúc Phân tầng (Layered Architecture)

```mermaid
flowchart LR
    subgraph Client ["Frontend (React + Vite + Tailwind)"]
        UI_Auth["Auth & Workspace"]
        UI_Screen["Active Screening Board"]
        UI_Graph["Conflict & Gap Viewer"]
    end

    subgraph API ["Backend API Layer (FastAPI)"]
        Deps["Auth & Ownership Guard (deps.py)"]
        Routes["REST API v1 Routers"]
    end

    subgraph Services ["Business & AI Services"]
        Search["Academic Search (OpenAlex)"]
        AL["Active Screener (scikit-learn)"]
        Conflict["Conflict Engine (3 Agents)"]
        Router["Centralized LLM Router (LiteLLM)"]
    end

    subgraph Data ["Unified Data Layer (PostgreSQL 16 + pgvector)"]
        RelDB[("Relational Tables")]
        VecDB[("pgvector Embeddings")]
    end

    subgraph External ["External Providers"]
        OA["OpenAlex API"]
        LLM["Gemini / OpenAI / Groq"]
    end

    Client <-->|"HTTP / JSON + JWT"| API
    Routes --> Deps
    Routes --> Services
    Search <--> OA
    Conflict --> Router
    Router <--> LLM
    Services <--> Data
```

### Nguyên tắc kiến trúc bất di bất dịch
1. **1 Cổng LLM duy nhất (`llm_router.py`)**: Mọi tác vụ gọi AI đều đi qua `LiteLLM` với cơ chế fallback tự động và ép kiểu JSON bằng Pydantic. Không gọi SDK của Gemini/OpenAI rải rác trong code nghiệp vụ.
2. **1 Database hợp nhất (`PostgreSQL + pgvector`)**: Dữ liệu quan hệ (User, Project, Paper, Claim, Edge) và vector nhúng (PDF chunks) nằm chung 1 database, đảm bảo giao dịch ACID và xóa dữ liệu theo cascade sạch sẽ.
3. **Cô lập đa người dùng nghiêm ngặt (Multi-tenant Isolation)**: Mọi endpoint liên quan đến `project_id` đều phải đi qua dependency `get_owned_project`, đảm bảo user A không bao giờ truy vấn nhầm bài báo hoặc tài liệu của user B.

---

## 3. Lược đồ Cơ sở dữ liệu (Database ERD)

```mermaid
erDiagram
    USERS ||--o{ RESEARCH_PROJECTS : owns
    RESEARCH_PROJECTS ||--o{ PAPERS : contains
    RESEARCH_PROJECTS ||--o{ CONFLICT_EDGES : tracks
    RESEARCH_PROJECTS ||--o{ RESEARCH_GAPS : discovers
    PAPERS ||--o{ PAPER_CHUNKS : splits_into
    PAPERS ||--o{ PAPER_CLAIMS : has
    PAPER_CLAIMS ||--o{ CONFLICT_EDGES : source_or_target

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
    }

    RESEARCH_PROJECTS {
        uuid id PK
        uuid owner_id FK
        string title
        string domain
        text research_question
        jsonb pico_framework
        jsonb inclusion_criteria
        jsonb exclusion_criteria
    }

    PAPERS {
        uuid id PK
        uuid project_id FK
        string doi
        string openalex_id
        text title
        text abstract
        string scopus_quartile
        enum screening_status
        enum screening_source
        float al_inclusion_prob
        float al_uncertainty_score
    }

    PAPER_CHUNKS {
        uuid id PK
        uuid paper_id FK
        int chunk_index
        int page_number
        text content
        vector embedding
    }

    PAPER_CLAIMS {
        uuid id PK
        uuid paper_id FK
        text claim_text
        string methodology
        string dataset
        string metric_summary
        jsonb assumptions
        text evidence_quote
    }

    CONFLICT_EDGES {
        uuid id PK
        uuid project_id FK
        uuid source_claim_id FK
        uuid target_claim_id FK
        enum relation_type
        float confidence
        text debate_summary
        text root_cause_hypothesis
    }

    RESEARCH_GAPS {
        uuid id PK
        uuid project_id FK
        string title
        text description
        text suggested_direction
        float novelty_score
    }
```

---

## 4. Luồng xử lý End-to-End (Sequence Flow)

```mermaid
sequenceDiagram
    actor Researcher as Nhà nghiên cứu
    participant UI as React Frontend
    participant API as FastAPI Backend
    participant OA as OpenAlex API
    participant ML as Active Screener (Local ML)
    participant LLM as LLM Router (Gemini/OpenAI)
    participant DB as PostgreSQL

    Researcher->>UI: 1. Tạo Project + Câu hỏi nghiên cứu (PICO)
    UI->>API: POST /api/v1/projects
    API->>DB: Lưu project

    Researcher->>UI: 2. Tìm kiếm bài báo ("ECG 1D CNN")
    UI->>API: POST /api/v1/projects/{id}/search
    API->>OA: Query works + abstract_inverted_index
    OA-->>API: Trả về danh sách bài báo thô
    API->>DB: Khử trùng lặp (DOI/OpenAlex ID) & Lưu papers

    Researcher->>UI: 3. Chấm mẫu 10-20 bài đầu (Include/Exclude)
    UI->>API: PATCH /screening/papers/{paper_id}/label
    API->>DB: Cập nhật nhãn (source = human)

    Researcher->>UI: 4. Chạy Active Learning Screening
    UI->>API: POST /screening/run-active-learning
    API->>ML: Train TF-IDF + LogisticRegression trên bài đã chấm
    ML-->>API: Trả về Prob & Uncertainty cho toàn bộ bài còn lại
    API->>DB: Tự động Include/Exclude bài rõ ràng, giữ lại bài "uncertain"

    Researcher->>UI: 5. Khám phá mâu thuẫn trên các bài Included
    UI->>API: POST /conflicts/analyze
    API->>LLM: Agent 1 bóc tách Claims từ từng bài
    API->>LLM: Agent 2 đối chiếu từng cặp Claims
    API->>LLM: Agent 3 tổng hợp Research Gaps từ các mâu thuẫn
    API->>DB: Lưu PaperClaims, ConflictEdges, ResearchGaps
    API-->>UI: Trả về Đồ thị Mâu thuẫn & Đề xuất đề tài mới
```
