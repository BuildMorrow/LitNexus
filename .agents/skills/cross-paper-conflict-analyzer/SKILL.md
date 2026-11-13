---
name: cross-paper-conflict-analyzer
description: >-
  Guides the agent through cross-paper claim extraction, pairwise dialectical cross-examination,
  empirical conflict detection, and research gap synthesis in LitNexus.
license: MIT
metadata:
  version: "1.0.0"
  framework: "LitNexus 3-Agent Conflict Engine"
---

# Cross-Paper Conflict & Gap Analyzer Skill

This skill guides AI agents through the multi-agent dialectical protocol used in **LitNexus Stage 2** to uncover empirical contradictions, hidden assumption mismatches, and novel research gaps across a curated corpus of scientific papers.

---

## 1. When to Use This Skill

Activate this skill when:
- Analyzing a curated cohort of included papers ($\ge 2$ papers) from an SLR.
- Deconstructing paper abstracts or full texts into structured, verifiable scientific claims (`PaperClaim`).
- Moderating pairwise dialectical debates between competing research groups.
- Diagnosing the root causes of contradictory findings across empirical studies.
- Synthesizing unresolved scholarly disputes into high-novelty Research Gaps.

---

## 2. Multi-Agent Dialectical Protocol

### Agent 1: Structured Claim Extraction
For each included paper, extract 1–3 concrete empirical claims conforming to `ExtractedClaimSchema`:
1. **`claim_text`**: The primary scientific finding or proposition. Avoid vague generalizations; insist on specific causal or performance assertions.
2. **`methodology`**: The exact algorithmic architecture, experimental framework, or statistical model utilized.
3. **`dataset`**: The specific benchmark, cohort, or simulated environment evaluated.
4. **`metric_summary`**: Concrete quantitative measurements (e.g., Accuracy, F1-score, Latency, Memory Footprint, ROC-AUC).
5. **`assumptions`**: Unstated or stated prerequisites (e.g., "stationary noise", "balanced classes", "homogeneous sensor hardware").
6. **`evidence_quote`**: An exact, verbatim quotation from the text supporting the extracted claim.

### Agent 2: Pairwise Dialectic Cross-Examination
For each pair of claims $(C_A, C_B)$ evaluated across different papers:
1. **Adopt Dual Perspectives**:
   - *Advocate for Paper A*: Defends the validity and generalizability of Claim A under its experimental design.
   - *Challenger representing Paper B*: Challenges Claim A using findings or empirical evidence from Paper B.
2. **Classify the Relationship**:
   - `contradicts`: Direct contradiction under comparable benchmarks or conditions.
   - `assumption_mismatch`: Findings diverge because Paper A and Paper B operated under divergent hidden assumptions or data distributions.
   - `refines`: Paper B tightens the operating envelope, clarifies failure modes, or improves upon Paper A.
   - `supports`: Independent verification through different experimental setups.
3. **Formulate Root Cause Hypothesis**:
   - Pinpoint the exact divergence mechanism: data drift, signal preprocessing filter bandwidth, batch size, loss function discrepancy, or sensor hardware sensitivity.

### Agent 3: Research Gap Synthesis
1. Gather all discovered `contradicts` and `assumption_mismatch` conflict edges.
2. Align conflicts against the project's root `research_question`.
3. Synthesize the top 3 actionable Research Gaps:
   - **Title**: Concise, publishable title for the proposed investigation.
   - **Description**: Summary of the scientific tension and why existing literature fails to resolve it.
   - **Suggested Direction**: Concrete experimental protocol, novel architecture, or benchmark design capable of adjudicating the dispute.
   - **Novelty Score ($S \in [0.0, 1.0]$)**: Calibrated based on unresolved literature divergence and prospective publication impact.
