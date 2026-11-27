"""Reproducible Offline Evaluation & Benchmark Harness for LitNexus.

Measures real deterministic performance metrics across:
1. Active Learning Hybrid Screener (routing accuracy & estimated token savings)
2. Semantic Candidate Pairing O(k*N) LLM call reduction
3. Deterministic Grounding Verifier fabrication catch rate
4. RAG Guardrail Prompt Injection block rate
5. Isolated Python Code Sandbox security rejection & execution speed
"""

import asyncio
import json
import time
from pathlib import Path

from app.services.active_screener import ActiveLearningScreener, LabeledSample
from app.services.code_sandbox import code_sandbox, validate_python_code
from app.services.conflict_engine import select_candidate_conflict_pairs
from app.services.grounding_verifier import verify_quotes
from app.services.rag_guardrail import rag_guardrail_service


async def run_all_benchmarks() -> dict:
    eval_dir = Path(__file__).resolve().parent
    golden = json.loads((eval_dir / "golden_dataset.json").read_text(encoding="utf-8"))

    # 1. Active Learning Screening Benchmark
    t0 = time.perf_counter()
    screener = ActiveLearningScreener()
    seeds = [
        LabeledSample(paper_id=item["id"], text=item["text"], label=item["label"])
        for item in golden["active_learning_corpus"]["labeled_seeds"]
    ]
    unlabeled = [
        (item["id"], item["text"]) for item in golden["active_learning_corpus"]["unlabeled_eval"]
    ]
    preds = screener.train_and_score(labeled=seeds, unlabeled=unlabeled)
    al_ms = round((time.perf_counter() - t0) * 1000, 2)
    auto_routed = sum(1 for p in preds if p.suggested_action != "query_llm")
    token_savings_pct = round((auto_routed / max(len(preds), 1)) * 100, 1)
    expected_map = {
        item["id"]: (item["expected"] == "auto_include")
        for item in golden["active_learning_corpus"]["unlabeled_eval"]
    }
    cls_correct = sum(
        1 for p in preds if (p.inclusion_prob >= 0.5) == expected_map[p.paper_id]
    )
    cls_acc_pct = round((cls_correct / max(len(preds), 1)) * 100, 1)

    # 2. Semantic Candidate Pairing Reduction (N=10 papers -> 45 full pairs vs k=2 selection)
    n_papers = 10
    claims = [
        f"Paper {i} evaluates 1D CNN arrhythmia detection on wearable ECG benchmark with F1 metric"
        for i in range(n_papers)
    ]
    pids = [f"p{i}" for i in range(n_papers)]
    pairs = select_candidate_conflict_pairs(claims, pids, top_k=2)
    full_pairs = n_papers * (n_papers - 1) // 2
    pair_reduction_pct = round((1 - len(pairs) / full_pairs) * 100, 1)

    # 3. Grounding Verifier Fabrication Detection
    g_case = golden["grounding_cases"][0]
    verified, g_score = verify_quotes(
        [g_case["real_quote"], g_case["fake_quote"]], [(g_case["segment"], 1)]
    )

    # 4. RAG Guardrail Prompt Injection Block Rate
    blocked = sum(
        1
        for q in golden["injection_queries"]
        if not rag_guardrail_service.validate_input_query(q)[0]
    )
    injection_block_rate = round((blocked / len(golden["injection_queries"])) * 100, 1)

    # 5. Sandbox Security & Execution Benchmark
    unsafe_samples = ["import os", "open('x')", "import subprocess"]
    sec_blocked = sum(1 for code in unsafe_samples if validate_python_code(code) is not None)
    sandbox_res = await code_sandbox.execute_code_async(
        code="print(round(df['v'].mean(), 2))",
        csv_text="v\n10\n20\n30\n",
    )

    return {
        "active_learning_ms": al_ms,
        "active_learning_classification_acc_pct": cls_acc_pct,
        "active_learning_auto_routed_pct": token_savings_pct,
        "candidate_pairing_reduction_pct": pair_reduction_pct,
        "candidate_pairs_selected": len(pairs),
        "full_pairwise_count": full_pairs,
        "grounding_verified_count": len(verified),
        "grounding_precision_mixed": g_score,
        "prompt_injection_block_rate_pct": injection_block_rate,
        "sandbox_security_block_rate_pct": round((sec_blocked / len(unsafe_samples)) * 100, 1),
        "sandbox_execution_ok": sandbox_res.success,
        "sandbox_execution_ms": sandbox_res.execution_time_ms,
    }


if __name__ == "__main__":
    results = asyncio.run(run_all_benchmarks())
    print(json.dumps(results, indent=2))
