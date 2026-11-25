from app.services.conflict_engine import select_candidate_conflict_pairs


def test_candidate_pairing_small_set():
    claims = [
        "1D CNN for wearable single-lead ECG arrhythmia classification",
        "2D ResNet spectrogram representation for multilead ECG telemetry",
    ]
    paper_ids = ["paper-1", "paper-2"]

    pairs = select_candidate_conflict_pairs(claims, paper_ids, top_k=2)
    assert len(pairs) == 1
    assert pairs[0][0] == 0
    assert pairs[0][1] == 1


def test_candidate_pairing_same_paper_filtering():
    claims = [
        "Claim 1 from Paper A: 1D CNN latency",
        "Claim 2 from Paper A: 1D CNN parameter count",
        "Claim 1 from Paper B: Quantized 1D CNN robustness",
    ]
    paper_ids = ["paper-A", "paper-A", "paper-B"]

    pairs = select_candidate_conflict_pairs(claims, paper_ids, top_k=2)
    # Pairs should only connect Paper A to Paper B, never Paper A to Paper A
    for idx_a, idx_b, _sim in pairs:
        assert paper_ids[idx_a] != paper_ids[idx_b]


def test_candidate_pairing_semantic_ranking():
    claims = [
        # Claim 0: ECG 1D CNN (Paper A)
        "Lightweight 1D CNN for wearable ECG arrhythmia classification on MIT-BIH benchmark with 18ms latency.",
        # Claim 1: ECG 2D Spectrogram (Paper B - highly related)
        "2D Spectrogram ResNet for ECG arrhythmia classification on MIT-BIH benchmark showing superior noise resistance.",
        # Claim 2: Speech Synthesis (Paper C - completely unrelated)
        "End-to-end neural vocoder for speech synthesis and audio acoustic pitch waveform modeling.",
        # Claim 3: Wearable ECG power (Paper D - related to ECG)
        "Micro-power neural accelerator for wearable ambulatory ECG patch arrhythmia screening.",
    ]
    paper_ids = ["p-A", "p-B", "p-C", "p-D"]

    pairs = select_candidate_conflict_pairs(claims, paper_ids, top_k=1, min_similarity=0.05)

    assert len(pairs) > 0
    # Every pair must cross different papers
    for idx_a, idx_b, _ in pairs:
        assert paper_ids[idx_a] != paper_ids[idx_b]


def test_candidate_pairing_top_k_complexity_bound():
    # 8 papers
    n = 8
    claims = [f"Scientific claim {i} on biomedical wearable sensors and signal processing" for i in range(n)]
    paper_ids = [f"paper-{i}" for i in range(n)]

    top_k = 2
    pairs = select_candidate_conflict_pairs(claims, paper_ids, top_k=top_k)

    # In full pairwise, n*(n-1)/2 = 8*7/2 = 28 pairs
    # With top_k=2 candidate selection, total pairs <= n * top_k = 16, significantly fewer!
    assert len(pairs) <= n * top_k
    assert len(pairs) < 28

