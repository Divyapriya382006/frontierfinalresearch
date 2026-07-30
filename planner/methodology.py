"""
Small helpers for building/validating a Methodology object, and a
DRY_RUN-safe default used when no LLM call is available.
"""
from shared.schemas.experiment_schema import Methodology


def default_methodology(topic: str) -> Methodology:
    topic_lower = (topic or "").lower()
    if any(term in topic_lower for term in ["language", "multilingual", "translation", "cross-lingual", "low-resource"]):
        return Methodology(
            overview=f"A multilingual and parameter-efficient evaluation study on: {topic}.",
            steps=[
                "Collect and preprocess the selected multilingual datasets",
                "Reproduce a strong baseline on the target language tasks",
                "Implement a parameter-efficient adaptation strategy such as LoRA or adapter tuning",
                "Run controlled experiments across high-resource and low-resource settings",
                "Analyze transfer performance, error cases, and compute cost",
            ],
            baseline_models=["Full fine-tuning baseline", "LoRA-tuned baseline", "Zero-shot prompting baseline"],
            proposed_approach="A resource-efficient adaptation method tailored to low-resource transfer and multilingual robustness.",
        )

    if any(term in topic_lower for term in ["classification", "detection", "segmentation", "recognition"]):
        return Methodology(
            overview=f"A benchmark-driven comparison study for: {topic}.",
            steps=[
                "Curate and preprocess the selected task datasets",
                "Reproduce a competitive baseline architecture",
                "Implement the proposed modeling change or training recipe",
                "Run controlled experiments with identical hyperparameters and compute budgets",
                "Analyze accuracy, calibration, and failure modes",
            ],
            baseline_models=["Standard supervised baseline", "Prompt-based baseline"],
            proposed_approach="A task-specific modeling or optimization strategy designed to improve robustness and generalization.",
        )

    return Methodology(
        overview=f"A baseline-vs-proposed comparison study on: {topic}.",
        steps=[
            "Collect and preprocess the selected datasets",
            "Reproduce established baseline methods",
            "Implement the proposed approach",
            "Run controlled experiments comparing baselines to the proposed approach",
            "Analyze results and error cases",
        ],
        baseline_models=["Fine-tuned baseline model", "Zero-shot/few-shot prompting baseline"],
        proposed_approach="A parameter-efficient adaptation method tailored to the identified research gap.",
    )
