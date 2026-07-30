"""
Small helpers for building/validating an EvaluationPlan object, and a
DRY_RUN-safe default used when no LLM call is available.
"""
from shared.schemas.experiment_schema import EvaluationPlan, EvaluationMetric


def default_evaluation_plan(topic: str = "") -> EvaluationPlan:
    topic_lower = (topic or "").lower()
    if any(term in topic_lower for term in ["language", "multilingual", "translation", "cross-lingual", "low-resource"]):
        metrics = [
            EvaluationMetric(name="BLEU", description="Translation quality on held-out multilingual test data."),
            EvaluationMetric(name="COMET", description="Semantic adequacy and fluency for translation outputs."),
            EvaluationMetric(name="ChrF", description="Character-level overlap for morphologically rich languages."),
            EvaluationMetric(name="Compute Cost", description="Training time / GPU-hours relative to the baseline."),
        ]
        evaluation_protocol = "Evaluate on multilingual validation and test splits, then report transfer performance for low-resource languages."
    elif any(term in topic_lower for term in ["classification", "detection", "segmentation", "recognition"]):
        metrics = [
            EvaluationMetric(name="Accuracy", description="Overall task accuracy on the held-out test set."),
            EvaluationMetric(name="F1 Score", description="Harmonic mean of precision and recall for imbalanced classes."),
            EvaluationMetric(name="Recall", description="Sensitivity to rare or difficult cases."),
        ]
        evaluation_protocol = "Use a stratified train/validation/test split and compare robustness across difficult subgroups."
    else:
        metrics = [
            EvaluationMetric(name="Accuracy", description="Overall task accuracy on the held-out test set."),
            EvaluationMetric(name="F1 Score", description="Harmonic mean of precision and recall, for imbalanced tasks."),
            EvaluationMetric(name="Compute Cost", description="Training time / GPU-hours relative to baseline."),
        ]
        evaluation_protocol = "80/10/10 train/val/test split with 3-run averaging to control for variance."

    return EvaluationPlan(metrics=metrics, evaluation_protocol=evaluation_protocol)
