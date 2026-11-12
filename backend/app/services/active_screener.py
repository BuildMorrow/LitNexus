from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


@dataclass
class LabeledSample:
    paper_id: str
    text: str
    label: int  # 1 = included, 0 = excluded


@dataclass
class PredictionResult:
    paper_id: str
    inclusion_prob: float
    uncertainty_score: float
    suggested_action: str  # "auto_include" | "auto_exclude" | "query_llm"


class ActiveLearningScreener:
    """
    Hybrid Active Learning engine combining fast local ML (TF-IDF + LogisticRegression)
    with uncertainty sampling to minimize expensive LLM screening calls.
    """

    def __init__(
        self,
        include_threshold: float = 0.85,
        exclude_threshold: float = 0.15,
    ) -> None:
        self.include_threshold = include_threshold
        self.exclude_threshold = exclude_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self.classifier = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            C=1.0,
        )

    @staticmethod
    def _uncertainty(prob: float) -> float:
        """Normalized margin uncertainty in [0, 1]; 1.0 means maximum uncertainty (prob=0.5)."""
        return float(1.0 - 2.0 * abs(prob - 0.5))

    def train_and_score(
        self,
        labeled: list[LabeledSample],
        unlabeled: list[tuple[str, str]],
    ) -> list[PredictionResult]:
        if not unlabeled:
            return []

        labels = [s.label for s in labeled]
        if len(set(labels)) < 2 or len(labeled) < 6:
            # Cold start: not enough both positive & negative samples yet -> query LLM/human
            return [
                PredictionResult(
                    paper_id=pid,
                    inclusion_prob=0.5,
                    uncertainty_score=1.0,
                    suggested_action="query_llm",
                )
                for pid, _ in unlabeled
            ]

        corpus_labeled = [s.text for s in labeled]
        corpus_unlabeled = [text for _, text in unlabeled]

        # Fit vectorizer on full pool for vocabulary coverage, train classifier on labeled only
        all_texts = corpus_labeled + corpus_unlabeled
        x_all = self.vectorizer.fit_transform(all_texts)
        x_train = x_all[: len(corpus_labeled)]
        x_pool = x_all[len(corpus_labeled) :]

        y_train = np.array(labels)
        self.classifier.fit(x_train, y_train)

        probs = self.classifier.predict_proba(x_pool)[:, 1]
        results: list[PredictionResult] = []

        for (pid, _), prob in zip(unlabeled, probs):
            p = float(prob)
            unc = self._uncertainty(p)
            if p >= self.include_threshold:
                action = "auto_include"
            elif p <= self.exclude_threshold:
                action = "auto_exclude"
            else:
                action = "query_llm"

            results.append(
                PredictionResult(
                    paper_id=pid,
                    inclusion_prob=round(p, 4),
                    uncertainty_score=round(unc, 4),
                    suggested_action=action,
                )
            )

        # Rank most uncertain first so active learning queries focus on the boundary
        results.sort(key=lambda r: r.uncertainty_score, reverse=True)
        return results
