import os

def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def _build_narrative_fallback(data: dict) -> str:
    """Returns a plain-English templated narrative when Gemini is unavailable."""
    cp      = data.get("compliance_pass", False)
    ratio   = data.get("fairness_ratio", 0.0)
    a       = data.get("group_a_rate", 0.0) * 100
    b       = data.get("group_b_rate", 0.0) * 100
    feature = data.get("top_biased_feature", "Unknown")
    gap     = abs(a - b)
    if cp:
        return (
            f"The audited model achieved a disparate impact ratio of {ratio:.2f}, "
            f"which exceeds the EEOC minimum threshold of 0.80 under the 4/5ths rule. "
            f"The privileged group selection rate of {a:.1f}% and unprivileged group "
            f"rate of {b:.1f}% fall within acceptable bounds under 29 CFR § 1607. "
            f"The primary feature influencing decisions was {feature}. No immediate "
            f"remediation is required, though ongoing monitoring is recommended."
        )
    else:
        return (
            f"The audited model produced a disparate impact ratio of {ratio:.2f}, "
            f"below the EEOC minimum of 0.80. The unprivileged group is selected at "
            f"{b:.1f}% versus {a:.1f}% for the privileged group — a gap of {gap:.1f} "
            f"percentage points. Under 29 CFR § 1607, this constitutes potential adverse "
            f"impact. The feature '{feature}' is the primary driver. Immediate mitigation "
            f"is required before deployment."
        )
