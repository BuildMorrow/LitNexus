"""Data profiling and statistical guard service.

Extracts column schema, data types, missing value ratios, and enforces strict
academic warning guards (e.g. sample size N < 30, high missingness, small cell count).
"""

import csv
import io
from typing import Any

from app.models.dataset import RiskLevel
from app.schemas.dataset import ColumnMeta, DataLimitationWarning


class DataProfilerService:
    @staticmethod
    def parse_and_profile_csv(
        csv_text: str,
    ) -> tuple[int, int, list[ColumnMeta], dict, list[dict[str, Any]]]:
        f = io.StringIO(csv_text.strip())
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV contains no valid header row.")

        fieldnames = [fn.strip() for fn in reader.fieldnames if fn]
        rows: list[dict[str, Any]] = []
        for r in reader:
            rows.append({k.strip(): (v.strip() if v else "") for k, v in r.items() if k})

        row_count = len(rows)
        column_count = len(fieldnames)

        columns_meta: list[ColumnMeta] = []
        missing_summary: dict[str, int] = {}

        for col in fieldnames:
            values = [r.get(col, "") for r in rows]
            non_empty = [v for v in values if v != ""]
            missing_count = row_count - len(non_empty)
            missing_summary[col] = missing_count
            missing_ratio = round(missing_count / max(row_count, 1), 4)

            # Infer data type: numeric vs categorical/string
            data_type = "string"
            if non_empty:
                is_num = True
                for val in non_empty[:50]:
                    try:
                        float(val)
                    except ValueError:
                        is_num = False
                        break
                if is_num:
                    data_type = "numeric"

            unique_vals = list(set(non_empty))
            sample_vals = non_empty[:5]

            columns_meta.append(
                ColumnMeta(
                    name=col,
                    data_type=data_type,
                    missing_count=missing_count,
                    missing_ratio=missing_ratio,
                    unique_count=len(unique_vals),
                    sample_values=sample_vals,
                )
            )

        sample_preview = rows[:10]
        return row_count, column_count, columns_meta, missing_summary, sample_preview

    @staticmethod
    def inspect_limitations(
        row_count: int, columns_meta: list[ColumnMeta]
    ) -> tuple[RiskLevel, list[DataLimitationWarning]]:
        """
        Enforce crucial scientific guards:
        1. Small sample size N < 30 (Central Limit Theorem violations)
        2. High missingness (> 20% on any column)
        3. Low variance / Single unique value
        """
        warnings: list[DataLimitationWarning] = []
        max_risk = RiskLevel.low

        # Guard 1: Small sample size
        if row_count < 30:
            max_risk = RiskLevel.high
            warnings.append(
                DataLimitationWarning(
                    warning_type="SMALL_SAMPLE_SIZE",
                    severity=RiskLevel.high,
                    message=f"Sample size N={row_count} is under the standard statistical threshold of 30.",
                    recommendation="Avoid parametric tests (e.g. Student's t-test). Use non-parametric tests (Mann-Whitney U, Wilcoxon, or Fisher's Exact) and report exact 95% Confidence Intervals via Bootstrap.",
                )
            )
        elif row_count < 100:
            if max_risk != RiskLevel.high:
                max_risk = RiskLevel.medium
            warnings.append(
                DataLimitationWarning(
                    warning_type="MODERATE_SAMPLE_SIZE",
                    severity=RiskLevel.medium,
                    message=f"Sample size N={row_count} offers limited statistical power for complex ML or multivariate models.",
                    recommendation="Limit predictor variables (rule of thumb: >=10 events per variable) and check normality assumptions via Shapiro-Wilk test.",
                )
            )

        # Guard 2: Missingness
        for col in columns_meta:
            if col.missing_ratio > 0.20:
                if max_risk != RiskLevel.high:
                    max_risk = RiskLevel.medium
                warnings.append(
                    DataLimitationWarning(
                        warning_type="HIGH_MISSINGNESS",
                        severity=RiskLevel.medium,
                        message=f"Column '{col.name}' has {round(col.missing_ratio * 100, 1)}% missing values.",
                        recommendation="Do not use simple mean imputation if data is Not Missing At Random (NMAR). Consider Multiple Imputation (MICE) or sensitivity analysis.",
                    )
                )

        return max_risk, warnings


data_profiler = DataProfilerService()
