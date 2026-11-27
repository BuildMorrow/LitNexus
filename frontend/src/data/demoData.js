export const DEMO_PROJECT = {
  id: 'demo-proj-1',
  title: 'Wearable ECG 1D CNN Arrhythmia Detection',
  domain: 'Biomedical AI & Wearable Sensors',
  research_question:
    'How do 1D CNNs perform on single-lead wearable ECG compared to 2D spectrogram models?',
  inclusion_criteria: [
    'Uses 1D CNN',
    'Wearable single-lead ECG',
    'Reports F1 or accuracy on public benchmark',
  ],
  exclusion_criteria: [
    'Animal studies',
    '12-lead clinical ECG only',
    'Review without empirical experiments',
  ],
}

export const DEMO_KPI_METRICS = {
  total_papers: 35,
  included_count: 8,
  excluded_count: 22,
  uncertain_count: 5,
  unscreened_count: 0,
  human_labeled: 6,
  llm_labeled: 4,
  active_learning_labeled: 25,
  automation_rate: 82.86,
  token_savings_percentage: 71.43,
  estimated_hours_saved: 7.25,
}

export const DEMO_PAPERS = [
  {
    id: 'p1',
    title:
      'Real-Time ECG Arrhythmia Classification Using Lightweight 1D Convolutional Neural Networks',
    authors: ['Zhang, Wei', 'Smith, John', 'Tan, Le'],
    journal: 'IEEE Transactions on Biomedical Engineering',
    year: 2024,
    scopus_quartile: 'Q1',
    screening_status: 'uncertain',
    screening_source: 'none',
    al_inclusion_prob: 0.52,
    al_uncertainty_score: 0.96,
    abstract:
      'We present a lightweight 1D CNN architecture tailored for edge computing on wearable single-lead patches, achieving 98.2% F1 on MIT-BIH dataset with only 45k parameters.',
  },
  {
    id: 'p2',
    title:
      'Deep Residual 2D Spectrogram Networks for Multilead Clinical Holter Monitoring',
    authors: ['Kumar, Rajesh', 'Patel, Anita'],
    journal: 'Computers in Biology and Medicine',
    year: 2023,
    scopus_quartile: 'Q1',
    screening_status: 'excluded',
    screening_source: 'active_learning',
    al_inclusion_prob: 0.08,
    al_uncertainty_score: 0.16,
    abstract:
      'This study converts 12-lead clinical ECG recordings into 2D STFT spectrogram images and trains a ResNet-50 for hospital intensive care telemetry.',
  },
  {
    id: 'p3',
    title:
      'Ultra-low Power Neural Accelerators for Single-Lead Patch Arrhythmia Screening',
    authors: ['Nguyen, Nam', 'Le, Duy'],
    journal: 'IEEE Transactions on Neural Networks and Learning Systems',
    year: 2024,
    scopus_quartile: 'Q1',
    screening_status: 'included',
    screening_source: 'llm',
    discovery_source: 'keyword',
    seed_distance: 0,
    al_inclusion_prob: 0.91,
    al_uncertainty_score: 0.18,
    screening_rationale: {
      mode: 'dual_peer_review',
      grounding_score: 1.0,
      reason: 'Both Inclusive and Strict reviewers confirmed quantized 1D CNN evaluation on single-lead patches.',
      evidence_quote:
        'Demonstrating an ultra-compact 1D convolutional model deployed on ARM Cortex-M4 wearable patches with 97.8% sensitivity under noisy motion artifacts.',
      opinions: [
        {
          reviewer_role: 'inclusive',
          decision: 'included',
          confidence: 0.94,
          reason: 'Uses 1D CNN directly on wearable single-lead ECG patches.',
        },
        {
          reviewer_role: 'strict',
          decision: 'included',
          confidence: 0.89,
          reason: 'Reports quantitative sensitivity (97.8%) under motion artifacts.',
        },
      ],
    },
    abstract:
      'Demonstrating an ultra-compact 1D convolutional model deployed on ARM Cortex-M4 wearable patches with 97.8% sensitivity under noisy motion artifacts.',
  },
]

export const DEMO_QUALITY_GATE = {
  passed: true,
  grounding_precision: 1.0,
  grounding_threshold: 0.8,
  included_count: 8,
  min_papers: 3,
  requires_hitl_review: false,
  warnings: [],
}

export const DEMO_SEARCH_HISTORY = [
  {
    id: 'sq-1',
    query_string: '("wearable ECG" OR "single-lead ECG") AND "1D CNN"',
    source_type: 'keyword',
    result_count: 35,
  },
]

export const DEMO_WORKSPACE_MESSAGES = [
  {
    id: 'wm-1',
    role: 'user',
    content: 'So sánh F1-score và độ ổn định của 1D CNN nhẹ với phiên bản lượng tử hóa?',
    citations: [],
    guardrail: {},
  },
  {
    id: 'wm-2',
    role: 'assistant',
    content:
      'Mô hình 1D CNN nhẹ đạt 98.2% F1 trên tập MIT-BIH với 45k tham số và độ trễ suy luận 18ms [1]. Trong điều kiện đeo thực tế có nhiễu chuyển động, mô hình 1D lượng tử hóa 8-bit duy trì 97.8% độ nhạy với mức tiêu thụ 1.2mW [2].',
    citations: [
      {
        index: 1,
        paper_id: 'p1',
        paper_title: 'Real-Time ECG Arrhythmia Classification Using Lightweight 1D Convolutional Neural Networks',
        page_number: 1,
        section_title: '3. Experimental Results',
        excerpt: 'Our lightweight 1D CNN architecture achieves 98.2% F1 on MIT-BIH with only 45k parameters, cutting inference latency to 18ms.',
      },
      {
        index: 2,
        paper_id: 'p3',
        paper_title: 'Ultra-low Power Neural Accelerators for Single-Lead Patch Arrhythmia Screening',
        page_number: 4,
        section_title: 'Methodology & Benchmarks',
        excerpt: 'The 8-bit quantized 1D model retained 97.8% sensitivity under continuous ambulatory motion with 1.2mW power draw.',
      },
    ],
    guardrail: {
      is_safe: true,
      safety_verdict: 'VERIFIED_HIGH_CONFIDENCE',
      faithfulness_score: 1.0,
      hallucination_rate: 0.0,
      citation_precision: 1.0,
    },
  },
]

export const DEMO_MATRIX_DATA = [
  {
    paper_id: 'p1',
    paper_title:
      'Real-Time ECG Arrhythmia Classification Using Lightweight 1D Convolutional Neural Networks',
    year: 2024,
    scopus_quartile: 'Q1',
    claim_id: 'c1',
    claim_text:
      'Lightweight 1D CNN matches 2D ResNet accuracy on wearable single-lead ECG while reducing compute by 14x.',
    methodology: 'Lightweight 1D-CNN (3 Conv layers, Depthwise Separable)',
    dataset: 'MIT-BIH Arrhythmia Benchmark (Single-lead Lead II)',
    metric_summary: 'F1-score = 0.982, Latency = 18ms, Params = 45k',
    assumptions: [
      'Stationary baseline noise',
      'Segmented R-peaks provided by hardware detector',
    ],
    evidence_quote:
      'Our lightweight 1D CNN architecture achieves 98.2% F1 on MIT-BIH with only 45k parameters, cutting inference latency to 18ms.',
    page_number: 1,
    section_title: '3. Experimental Results',
  },
  {
    paper_id: 'p3',
    paper_title:
      'Ultra-low Power Neural Accelerators for Single-Lead Patch Arrhythmia Screening',
    year: 2024,
    scopus_quartile: 'Q1',
    claim_id: 'c2',
    claim_text:
      'Quantized 1D CNN retains 97.8% sensitivity under real-world ambulatory motion artifacts.',
    methodology: '8-bit Quantized 1D-CNN with Temporal Batch Normalization',
    dataset: 'In-house Wearable Chest Patch Cohort (N=120 ambulatory patients)',
    metric_summary: 'Sensitivity = 97.8%, Power = 1.2mW',
    assumptions: [
      'Ambulatory motion artifacts present',
      'Sampling rate fixed at 250Hz',
    ],
    evidence_quote:
      'The 8-bit quantized 1D model retained 97.8% sensitivity under continuous ambulatory motion with 1.2mW power draw.',
    page_number: 4,
    section_title: 'Methodology & Benchmarks',
  },
]

export const DEMO_DATASET = {
  id: 'demo-dataset-1',
  dataset_name: 'Wearable_Cohort_Pilot_N8.csv',
  row_count: 8,
  column_count: 6,
  columns_metadata: [
    { name: 'patient_id', data_type: 'string', missing_count: 0, missing_ratio: 0.0, unique_count: 8, sample_values: ['p_01', 'p_02'] },
    { name: 'age', data_type: 'numeric', missing_count: 0, missing_ratio: 0.0, unique_count: 8, sample_values: ['45', '52'] },
    { name: 'wearable_snr', data_type: 'numeric', missing_count: 0, missing_ratio: 0.0, unique_count: 8, sample_values: ['18.5', '14.2'] },
    { name: 'heart_rate', data_type: 'numeric', missing_count: 0, missing_ratio: 0.0, unique_count: 8, sample_values: ['72', '85'] },
    { name: 'f1_score', data_type: 'numeric', missing_count: 0, missing_ratio: 0.0, unique_count: 8, sample_values: ['0.98', '0.94'] },
    { name: 'noise_level', data_type: 'string', missing_count: 0, missing_ratio: 0.0, unique_count: 3, sample_values: ['low', 'medium', 'high'] },
  ],
  missing_value_summary: {},
  sample_preview: [
    { patient_id: 'p_01', age: '45', wearable_snr: '18.5', heart_rate: '72', f1_score: '0.98', noise_level: 'low' },
    { patient_id: 'p_02', age: '52', wearable_snr: '14.2', heart_rate: '85', f1_score: '0.94', noise_level: 'medium' },
  ],
}

export const DEMO_ANALYSIS_RESULT = {
  risk_level: 'high',
  analysis_goal: 'Compare F1 score across low vs high noise levels and evaluate sample power',
  data_limitations: [
    {
      warning_type: 'SMALL_SAMPLE_SIZE',
      severity: 'high',
      message: 'Sample size N=8 is strictly below statistical threshold (N < 30).',
      recommendation:
        'Do NOT use Student t-test or parametric ANOVA. Apply Mann-Whitney U or Wilcoxon rank-sum test with exact permutation and 95% Bootstrap CI.',
    },
  ],
  recommended_methods: [
    {
      method_name: 'Mann-Whitney U Test (Exact Permutation)',
      category: 'Non-Parametric Hypothesis Testing',
      rational: 'Robust against non-normality and avoids distributional bias on small pilot cohorts N=8.',
      assumptions: ['Independent observations', 'Continuous metric scale'],
      is_recommended: true,
    },
    {
      method_name: 'Bootstrap BCa 95% Confidence Intervals',
      category: 'Resampling Estimation',
      rational: 'Provides accurate confidence interval boundaries without assuming normal distribution.',
      assumptions: ['Random sample'],
      is_recommended: true,
    },
  ],
  suggested_python_code: `import pandas as pd
import numpy as np
from scipy import stats

# Empirical pilot analysis for N=8 wearable sensor data
df = pd.DataFrame({
    'f1_score': [0.98, 0.94, 0.86, 0.99, 0.81, 0.95, 0.89, 0.97],
    'noise': ['low', 'medium', 'high', 'low', 'high', 'medium', 'medium', 'low']
})

low_noise = df[df['noise'] == 'low']['f1_score']
high_noise = df[df['noise'] == 'high']['f1_score']

# Crucial Guard: Non-parametric Mann-Whitney U test (N < 30)
stat, p_val = stats.mannwhitneyu(low_noise, high_noise, alternative='two-sided')
print(f"Mann-Whitney U statistic: {stat:.2f}, Exact p-value: {p_val:.4f}")`,
  interpretation_guide:
    'Reporting format for IEEE/Nature: "Due to the pilot cohort size (N=8), non-parametric analysis was employed. Wearable ECG models in low-noise conditions demonstrated significantly higher F1 scores compared to high-noise environments (Mann-Whitney U=0.0, p=0.038). However, given the limited sample power, these exploratory findings should be validated on a larger clinical cohort (N >= 50)."',
}

export const DEMO_GRAPH_DATA = {
  total_nodes: 2,
  total_edges: 1,
  contradiction_count: 1,
  nodes: [
    {
      id: 'c1',
      type: 'claim',
      label: '[1D-CNN] 1D CNN matches 2D ResNet on wearable single-lead...',
      paper_title: 'Real-Time ECG Arrhythmia Classification Using Lightweight 1D Convolutional Neural Networks',
      year: 2024,
      quartile: 'Q1',
      details: 'Metric: F1-score = 0.982 | Dataset: MIT-BIH Arrhythmia Benchmark',
    },
    {
      id: 'c2',
      type: 'claim',
      label: '[Quantized 1D] Retains 97.8% sensitivity under ambulatory artifacts...',
      paper_title: 'Ultra-low Power Neural Accelerators for Single-Lead Patch Arrhythmia Screening',
      year: 2024,
      quartile: 'Q1',
      details: 'Metric: Sensitivity = 97.8% | Dataset: In-house Wearable Chest Patch Cohort',
    },
  ],
  edges: [
    {
      id: 'e1',
      source: 'c1',
      target: 'c2',
      relation_type: 'contradicts',
      confidence: 0.88,
      debate_summary:
        'Paper 1 claims high robustness on clean benchmark, while Paper 2 shows that without quantization & temporal batch norm, noise reduces accuracy.',
      root_cause_hypothesis:
        'Differences in motion artifact noise level between benchmark data vs real ambulatory patients.',
    },
  ],
  research_gaps: [
    {
      id: 'gap1',
      title: 'Noise-Adaptive 1D CNN Architectures for Ambulatory Edge ECG',
      description:
        'Current models either assume clean segmented heartbeats or require high power to filter motion artifacts.',
      suggested_direction:
        'Develop dynamic bit-width quantization coupled with temporal SNR attention.',
      novelty_score: 0.92,
    },
  ],
}

export const DEMO_DRAFT_REPORT = {
  project_id: 'demo-proj-1',
  project_title: 'Wearable ECG 1D CNN Arrhythmia Detection',
  total_references: 2,
  prisma_flow_summary: {
    identified: 35,
    screened: 35,
    excluded: 22,
    included: 8,
  },
  bibtex_content: `@article{Zhang2024,
  title = {Real-Time ECG Arrhythmia Classification Using Lightweight 1D Convolutional Neural Networks},
  author = {Zhang, Wei and Smith, John and Tan, Le},
  journal = {IEEE Transactions on Biomedical Engineering},
  year = {2024},
  doi = {10.1109/TBME.2024.123456}
}

@article{Nguyen2024,
  title = {Ultra-low Power Neural Accelerators for Single-Lead Patch Arrhythmia Screening},
  author = {Nguyen, Nam and Le, Duy},
  journal = {IEEE Transactions on Neural Networks and Learning Systems},
  year = {2024},
  doi = {10.1109/TNNLS.2024.789012}
}`,
  draft_markdown: `# Systematic Literature Review: Wearable ECG 1D CNN Arrhythmia Detection

## Abstract & Research Questions
**Core Research Question**: How do lightweight 1D CNNs perform on wearable single-lead ECG compared to 2D models?

This review followed PRISMA 2020 guidelines with Active Learning screening assistance. A total of **35** studies were identified, with **8** core empirical investigations satisfying the inclusion criteria.

---

## 1. Methodology & PRISMA Review Funnel
- **Total Records Screened**: 35
- **Records Excluded (Automated & Manual)**: 22
- **Eligible Studies Included**: 8

---

## 2. Comparative Evidence Matrix
| Study & Quartile | Methodology | Dataset | Quantitative Metrics | Grounded Evidence Quote |
|---|---|---|---|---|
| **Real-Time ECG Arrhythmia Classification...** (2024, Q1) | Lightweight 1D-CNN | MIT-BIH | F1=0.982, Latency=18ms | *"Our lightweight 1D CNN architecture achieves 98.2% F1 on MIT-BIH with only 45k parameters..."* |
| **Ultra-low Power Neural Accelerators...** (2024, Q1) | 8-bit Quantized 1D-CNN | Ambulatory Patch | Sensitivity=97.8%, Power=1.2mW | *"The 8-bit quantized 1D model retained 97.8% sensitivity under continuous ambulatory motion..."* |
`,
  latex_content: `\\documentclass[11pt,a4paper]{article}
\\usepackage[utf8]{inputenc}
\\usepackage{booktabs}
\\usepackage{geometry}
\\geometry{margin=1in}
\\usepackage{hyperref}
\\usepackage{cite}

\\title{Systematic Literature Review: Wearable ECG 1D CNN Arrhythmia Detection}
\\author{LitNexus SLR Research Engine}
\\date{\\today}

\\begin{document}
\\maketitle

\\begin{abstract}
\\textbf{Research Question:} How do lightweight 1D CNNs perform on wearable single-lead ECG compared to 2D models?
\\end{abstract}

\\section{PRISMA 2020 Review Flow}
\\begin{itemize}
  \\item \\textbf{Total Records Screened:} 35
  \\item \\textbf{Records Excluded:} 22
  \\item \\textbf{Eligible Studies Included:} 8
\\end{itemize}

\\bibliography{references}
\\bibliographystyle{IEEEtran}
\\end{document}
`,
  quarto_content: `---
title: "Systematic Literature Review: Wearable ECG 1D CNN Arrhythmia Detection"
subtitle: "Active Learning PRISMA Synthesis with Evidence Grounding"
author: "LitNexus Research Suite"
date: today
format:
  html:
    toc: true
    number-sections: true
bibliography: references.bib
---

# Abstract & Core Question
**Research Question:** How do lightweight 1D CNNs perform on wearable single-lead ECG compared to 2D models?
`,
}
