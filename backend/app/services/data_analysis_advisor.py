"""Data analysis & statistical advisory service.

Generates recommended statistical/ML methods, robust executable Python code,
and academic interpretations with explicit limitations and assumptions.
"""

from pydantic import BaseModel, Field

from app.models.dataset import RiskLevel
from app.schemas.dataset import (
    AnalysisMethodProposal,
    ColumnMeta,
    DataLimitationWarning,
)
from app.services.llm_router import llm_router


class _LLMAnalysisAdvicePayload(BaseModel):
    recommended_methods: list[AnalysisMethodProposal] = Field(default_factory=list)
    suggested_python_code: str = Field(description="Executable, clean Python script using pandas, scipy.stats, or scikit-learn")
    interpretation_guide: str = Field(description="Scholarly guidance on how to interpret p-values, effect sizes, and reporting format (APA/IEEE)")
    additional_limitations: list[str] = Field(default_factory=list)


class DataAnalysisAdvisor:
    @staticmethod
    async def advise_methods(
        research_question: str,
        analysis_goal: str,
        row_count: int,
        columns_meta: list[ColumnMeta],
        rule_warnings: list[DataLimitationWarning],
        risk_level: RiskLevel,
    ) -> tuple[list[AnalysisMethodProposal], str, str, list[DataLimitationWarning]]:
        cols_summary = "\n".join(
            f"- {c.name} ({c.data_type}): {c.missing_count} missing, {c.unique_count} unique values. Samples: {c.sample_values}"
            for c in columns_meta
        )

        existing_warnings_str = "\n".join(
            f"[{w.severity.value.upper()}] {w.warning_type}: {w.message} -> {w.recommendation}"
            for w in rule_warnings
        )

        prompt = f"""
You are a senior biostatistician and quantitative methodology expert.
Analyze the user's research question, analysis goal, and empirical dataset profile.

[Project Research Question]: {research_question}
[Specific Analysis Goal]: {analysis_goal}
[Dataset Profile]:
Total observations (N): {row_count}
Columns schema:
{cols_summary}

[Statistical Limitation Warnings Detected]:
{existing_warnings_str or 'None'}

INSTRUCTIONS:
1. Recommend 2 to 3 candidate statistical or ML methods appropriate for N={row_count} and the specific variable types.
2. If N < 30, strictly prioritize Non-Parametric tests (e.g. Mann-Whitney U, Kruskal-Wallis, Fisher Exact, Bootstrap).
3. Provide clean, production-ready Python code using pandas, scipy.stats, statsmodels, or scikit-learn. Include code to test assumptions (e.g. normality tests, homoscedasticity) and compute effect size (Cohen's d or Cliff's delta).
4. Provide an academic interpretation guide explaining how the researcher should report results in an IEEE/Nature journal paper.
"""

        system_prompt = (
            "You are a rigorous academic statistician. You provide verifiable, conservative, "
            "and methodologically sound statistical advice. Never recommend underpowered tests."
        )

        try:
            llm_result = await llm_router.generate_structured(
                prompt=prompt,
                schema=_LLMAnalysisAdvicePayload,
                system_prompt=system_prompt,
                temperature=0.2,
            )

            # Combine rule warnings with any extra warnings from LLM
            combined_warnings = list(rule_warnings)
            for extra in llm_result.additional_limitations:
                combined_warnings.append(
                    DataLimitationWarning(
                        warning_type="METHODOLOGICAL_CAUTION",
                        severity=RiskLevel.medium,
                        message=extra,
                        recommendation="Verify reporting standard against STROBE or PRISMA guidelines.",
                    )
                )

            return (
                llm_result.recommended_methods,
                llm_result.suggested_python_code,
                llm_result.interpretation_guide,
                combined_warnings,
            )
        except Exception:
            # Fallback deterministic statistical advice if LLM is unavailable
            fallback_methods = [
                AnalysisMethodProposal(
                    method_name="Mann-Whitney U Test" if row_count < 50 else "Two-Sample Independent T-Test",
                    category="Hypothesis Testing",
                    rational=f"Appropriate for comparing two distributions with sample size N={row_count}.",
                    assumptions=["Independent observations", "Ordinal or continuous scale"],
                    is_recommended=True,
                ),
                AnalysisMethodProposal(
                    method_name="Bootstrap 95% Confidence Intervals",
                    category="Resampling",
                    rational="Provides robust non-parametric estimation of effect size without assuming normality.",
                    assumptions=["Representative random sample"],
                    is_recommended=True,
                ),
            ]
            fallback_code = f"""import pandas as pd
import numpy as np
from scipy import stats

# 1. Load dataset
# df = pd.read_csv('your_data.csv')
print("Observations: {row_count}")

# 2. Check normality (Shapiro-Wilk)
# stat, p_val = stats.shapiro(data_sample)
# print(f"Shapiro-Wilk p-value: {{p_val:.4f}}")

# 3. Non-parametric comparison
# u_stat, u_pval = stats.mannwhitneyu(group_a, group_b)
# print(f"Mann-Whitney U p-value: {{u_pval:.4f}}")
"""
            fallback_guide = (
                f"For sample size N={row_count}, report median and interquartile range (IQR) "
                "alongside exact p-values. If p < 0.05, discuss practical significance and effect size."
            )
            return fallback_methods, fallback_code, fallback_guide, rule_warnings


data_analysis_advisor = DataAnalysisAdvisor()
