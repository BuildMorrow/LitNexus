from app.services.active_screener import ActiveLearningScreener, LabeledSample


def test_active_screener_cold_start_routes_to_llm():
    screener = ActiveLearningScreener()
    labeled = [
        LabeledSample(paper_id="1", text="ECG 1D CNN classification", label=1),
        LabeledSample(paper_id="2", text="Solar panel optimization", label=0),
    ]
    unlabeled = [("3", "Arrhythmia detection using deep learning")]
    preds = screener.train_and_score(labeled, unlabeled)

    assert len(preds) == 1
    assert preds[0].suggested_action == "query_llm"
    assert preds[0].uncertainty_score == 1.0


def test_active_screener_ranks_uncertain_papers_first():
    screener = ActiveLearningScreener(include_threshold=0.75, exclude_threshold=0.25)
    labeled = [
        LabeledSample(paper_id="1", text="ECG arrhythmia 1D CNN signal detection", label=1),
        LabeledSample(paper_id="2", text="Electrocardiogram heartbeat deep learning CNN", label=1),
        LabeledSample(paper_id="3", text="ECG signal classification neural network", label=1),
        LabeledSample(paper_id="4", text="Quantum physics particle collider optics", label=0),
        LabeledSample(paper_id="5", text="Agricultural soil fertilizer crop yield", label=0),
        LabeledSample(paper_id="6", text="Blockchain smart contract cryptocurrency", label=0),
    ]
    unlabeled = [
        ("u1", "ECG heartbeat arrhythmia 1D CNN deep learning"),
        ("u2", "Soil crop yield fertilizer blockchain"),
        ("u3", "ECG sensor hardware power optimization"),
    ]
    preds = screener.train_and_score(labeled, unlabeled)

    assert len(preds) == 3
    # Sorted descending by uncertainty
    assert preds[0].uncertainty_score >= preds[1].uncertainty_score >= preds[2].uncertainty_score
    by_id = {p.paper_id: p for p in preds}
    assert by_id["u1"].inclusion_prob > by_id["u2"].inclusion_prob
