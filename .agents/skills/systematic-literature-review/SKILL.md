---
name: systematic-literature-review
description: >-
  Guides the agent through executing PRISMA-compliant Systematic Literature Reviews (SLR)
  using Active Learning screening, OpenAlex academic search, PICO formulation,
  and uncertainty sampling in LitNexus.
license: MIT
metadata:
  version: "1.0.0"
  framework: "LitNexus Research Funnel"
---

# Systematic Literature Review (SLR) Skill

This skill equips AI agents with the standardized methodology and step-by-step procedures required to run a high-rigor, reproducible **Systematic Literature Review** following the **PRISMA 2020** statement and the LitNexus active-learning funnel.

---

## 1. When to Use This Skill

Activate this skill when:
- Designing or initializing an academic Systematic Literature Review project.
- Formulating research questions using the **PICO** (Population, Intervention, Comparison, Outcome) or **CICero** framework.
- Formulating academic search queries for scholarly databases (OpenAlex, Semantic Scholar, Crossref).
- Executing active learning screening loops and adjudicating borderline papers ($0.15 < p < 0.85$).
- Generating PRISMA Flow Diagram metrics and tracking exclusion rationales.

---

## 2. Core Workflow Protocol

### Step 1: Research Question & PICO Formulation
Before querying any academic database, establish clear boundaries:
- **P (Population / Domain)**: e.g., "Patients with cardiac arrhythmia monitored via single-lead wearable sensors."
- **I (Intervention / Technology)**: e.g., "1D Convolutional Neural Networks and lightweight temporal models."
- **C (Comparison / Baseline)**: e.g., "Traditional machine learning (SVM, Random Forest) or heavy 2D-spectrogram ResNets."
- **O (Outcome / Metrics)**: e.g., "F1-score $\ge 0.90$, inference latency $< 50\text{ms}$, model parameter size $< 2\text{MB}$."

### Step 2: OpenAlex Query Construction
Construct targeted scholarly queries leveraging OpenAlex filters:
- Filter by abstract availability: `filter=has_abstract:true`.
- Specify polite pool headers (`User-Agent: LitNexus/1.0 (mailto:your-email@domain.com)`).
- Reconstruct inverted index abstract payloads into linear academic abstracts.
- Enforce deduplication against existing project papers via DOI and OpenAlex ID.

### Step 3: Active Learning Cold-Start Bootstrap
1. Screen an initial seed set of 6–20 papers:
   - Provide balanced ground truth: at least 3 distinct `included` and 3 distinct `excluded` samples.
   - Ground decisions strictly against the project's inclusion/exclusion criteria.
2. Trigger the local ML training cycle via `ActiveLearningScreener`:
   - Compute sublinear TF-IDF (unigram + bigram, 5,000 features).
   - Fit `LogisticRegression(class_weight="balanced")`.
   - Calculate normalized margin uncertainty $U(p) = 1 - 2|p - 0.5|$.

### Step 4: Gated Adjudication Loop
- High confidence included ($p \ge 0.85$): Automatically tag as `included` (`screening_source = active_learning`).
- High confidence excluded ($p \le 0.15$): Automatically tag as `excluded` (`screening_source = active_learning`).
- Borderline papers ($0.15 < p < 0.85$): Prioritize highest $U(p)$ papers at the top of the queue for human or LLM batch adjudication.
- **Stopping Rule**: When 30 consecutive uncertain papers are evaluated without finding a new included paper, or when the candidate pool contains no remaining papers with $p \ge 0.50$, conclude the screening stage.

### Step 5: PRISMA 2020 Accounting
Maintain exact audit counters:
- $N_{\text{identified}}$: Total works returned by OpenAlex queries.
- $N_{\text{deduplicated}}$: Duplicates filtered by DOI or internal ID.
- $N_{\text{screened}}$: Total unique papers evaluated.
- $N_{\text{excluded}}$: Total excluded, grouped by explicit rationale.
- $N_{\text{included}}$: Final core set passed forward to Stage 2 Conflict Discovery.
