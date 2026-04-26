import os
import io
from PIL import Image
from google import genai
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from backend.dependencies import require_api_key
from backend.config import get_settings
from backend.utils import _build_narrative_fallback

router = APIRouter(tags=["Google AI"])

# ── Configure Gemini Client ──────────────────────────────────────────────────
_gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
_genai_client = genai.Client(api_key=_gemini_key) if _gemini_key else None


@router.post("/audit/narrative", dependencies=[Depends(require_api_key)])
def audit_narrative(payload: dict):
    """
    Generates a 3-paragraph plain-English legal risk narrative via Gemini 1.5 Flash.
    Falls back to a template string if GEMINI_API_KEY is not set or the call fails.
    """
    cp      = payload.get("compliance_pass", False)
    ratio   = payload.get("fairness_ratio", 0.0)
    a       = payload.get("group_a_rate", 0.0)
    b       = payload.get("group_b_rate", 0.0)
    feature = payload.get("top_biased_feature", "Unknown")
    proxies = payload.get("flagged_proxies", [])
    shap    = payload.get("shap_summary", {})

    # ── Attempt Gemini call ───────────────────────────────────────────────────
    if _genai_client is not None:
        prompt = (
            "You are a legal compliance analyst specializing in US employment law.\n"
            "Analyze this AI model audit result and write a 3-paragraph plain-English\n"
            "risk narrative for a Chief Compliance Officer.\n\n"
            "Audit data:\n"
            f"- EEOC Compliance: {'PASS' if cp else 'FAIL'}\n"
            f"- Fairness Ratio: {ratio:.4f} (threshold: 0.80)\n"
            f"- Privileged Group Selection Rate: {a*100:.1f}%\n"
            f"- Unprivileged Group Selection Rate: {b*100:.1f}%\n"
            f"- Top Bias Driver (SHAP): {feature}\n"
            f"- Proxy Variables Detected: {proxies or 'None'}\n"
            f"- SHAP Feature Impacts: {shap}\n\n"
            "Write exactly 3 paragraphs:\n"
            "1. What the audit found (factual, cite the numbers)\n"
            "2. What this means legally under 29 CFR § 1607 (EEOC 4/5ths rule)\n"
            "3. Recommended immediate actions\n\n"
            "Be specific, cite the exact numbers, and write for a non-technical executive. "
            "Do not use bullet points. Plain paragraphs only. "
            "Keep total response under 250 words."
        )
        try:
            response = _genai_client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt,
            )
            return {"narrative": response.text, "model": "gemini-3-flash-preview"}
        except Exception:
            pass  # fall through to template

    # ── Fallback template ─────────────────────────────────────────────────────
    return {
        "narrative": _build_narrative_fallback(payload),
        "model": "template",
    }


SENSITIVE_LABELS = {
    "face", "person", "human", "skin", "hair", "eye",
    "portrait", "selfie", "photo", "id card", "passport",
    "driver's license", "badge", "uniform",
}

DEMOGRAPHIC_KEYWORDS = {
    "race", "gender", "sex", "ethnicity", "nationality",
    "religion", "age", "dob", "date", "of", "birth", "born",
    "male", "female", "mr", "mrs", "ms",
}

@router.post("/audit/vision")
async def audit_vision(request: Request, file: UploadFile = File(...)):
    """
    Scans an uploaded image for demographic data leakage using Gemini 1.5 Flash Multimodal AI.
    Auth: manually checks X-API-Key header (file upload incompatible with Depends).
    """
    settings = get_settings()
    api_key  = request.headers.get("X-API-Key", "")
    if not api_key or api_key != settings["api_key"]:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key. Pass your key in the X-API-Key header.",
        )

    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

        prompt = "Does this image contain a human face or demographic info? Reply exactly 'CRITICAL' if yes, or 'PASS' if no."
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=[prompt, img]
        )

        risk = "CRITICAL" if "CRITICAL" in response.text.upper() else "LOW"
        faces = 1 if risk == "CRITICAL" else 0

        compliance_warning = (
            "This image contains detectable protected attributes. Using images of this type as inputs "
            "to automated hiring or scoring systems may violate GDPR Article 9 and EEOC guidelines."
            if risk == "CRITICAL" else
            "No significant protected attributes detected. Standard data minimisation practices apply."
        )
        recommendation = (
            "Manual review required for demographic filtering."
            if risk == "CRITICAL" else "Clear for automated processing."
        )

        return {
            "risk_level": risk,
            "risk_score": 95 if risk == "CRITICAL" else 10,
            "faces_detected": faces,
            "flagged_labels": ["Human Face/Demographic Detected"] if risk == "CRITICAL" else [],
            "flagged_text": [],
            "recommendation": recommendation,
            "compliance_warning": compliance_warning
        }
    except Exception as e:
        return {
            "error": f"Gemini Vision Error: {e}",
            "risk_level": "UNKNOWN",
        }

_REMEDIATE_FALLBACK_TEMPLATE = '''
## Strategy 1 — Pre-processing: Remove Proxy Columns

**Explanation:** Drop the statistically correlated proxy columns before training to prevent indirect discrimination.

```python
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load dataset
df = pd.read_csv("{data_path}")

# Remove proxy columns flagged by EquiGuard
proxy_cols = {flagged_columns}
df_clean = df.drop(columns=[c for c in proxy_cols if c in df.columns], errors="ignore")

X = df_clean.drop(columns=["{target_col}", "{protected_col}"], errors="ignore")
y = df_clean["{target_col}"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
print("Accuracy after proxy removal:", accuracy_score(y_test, model.predict(X_test)))
```

**Expected impact:** Fairness ratio should improve by reducing indirect correlation. Re-run EquiGuard audit to validate.

---

## Strategy 2 — In-processing: Reweighing (aif360)

**Explanation:** Use IBM aif360 Reweighing to rebalance instance weights so the training set is fairer before fitting.

```python
import pandas as pd
from aif360.datasets import BinaryLabelDataset
from aif360.algorithms.preprocessing import Reweighing
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

df = pd.read_csv("{data_path}")
dataset = BinaryLabelDataset(
    df=df,
    label_names=["{target_col}"],
    protected_attribute_names=["{protected_col}"],
)
privileged_groups   = [{{ "{protected_col}": 1 }}]
unprivileged_groups = [{{ "{protected_col}": 0 }}]
rw = Reweighing(unprivileged_groups=unprivileged_groups, privileged_groups=privileged_groups)
dataset_rw = rw.fit_transform(dataset)

X_rw, y_rw = dataset_rw.features, dataset_rw.labels.ravel()
w_rw       = dataset_rw.instance_weights

model = LogisticRegression(max_iter=1000)
model.fit(X_rw, y_rw, sample_weight=w_rw)
print("Reweighed model accuracy:", accuracy_score(y_rw, model.predict(X_rw)))
```

**Expected impact:** Reweighing directly targets disparate impact. Current fairness ratio ({fairness_ratio:.3f}) should increase toward 0.80.

---

## Strategy 3 — Post-processing: Threshold Adjustment per Group

**Explanation:** After training, shift the decision threshold for the unprivileged group to equalise selection rates.

```python
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

df = pd.read_csv("{data_path}")
X  = df.drop(columns=["{target_col}"], errors="ignore")
y  = df["{target_col}"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

proba      = model.predict_proba(X_test)[:, 1]
priv_mask  = X_test["{protected_col}"] == 1
unpriv_mask = ~priv_mask

threshold_priv   = 0.5
threshold_unpriv = 0.45   # lower threshold for unprivileged group

preds = np.where(priv_mask, proba >= threshold_priv, proba >= threshold_unpriv).astype(int)

priv_rate   = preds[priv_mask].mean()
unpriv_rate = preds[unpriv_mask].mean()
print(f"Privileged selection rate:   {{priv_rate:.3f}}")
print(f"Unprivileged selection rate: {{unpriv_rate:.3f}}")
print(f"Disparate impact ratio:      {{unpriv_rate / priv_rate:.3f}}")
```

**Expected impact:** Equalises selection rates post-hoc. Fine-tune `threshold_unpriv` until the ratio meets or exceeds 0.80.
'''

@router.post("/audit/remediate", dependencies=[Depends(require_api_key)])
def audit_remediate(payload: dict):
    """
    Generates three production-ready Python mitigation strategies via Gemini.
    Falls back to a parameterised template when GEMINI_API_KEY is not configured or quota is exhausted.
    """
    import time

    top_feature     = payload.get("top_biased_feature", "unknown_feature")
    flagged_columns = payload.get("flagged_columns", [])
    fairness_ratio  = payload.get("fairness_ratio", 0.0)
    data_path       = payload.get("data_path", "data/golden_demo_dataset.csv")
    target_col      = payload.get("target_col", "loan_approved")
    protected_col   = payload.get("protected_col", "race")

    prompt = (
        "You are an expert ML fairness engineer. Generate production-ready Python "
        "code to mitigate bias in a scikit-learn pipeline.\n\n"
        "Model context:\n"
        f'- Dataset: CSV file at "{data_path}"\n'
        f'- Target column: "{target_col}"\n'
        f'- Protected attribute: "{protected_col}"\n'
        f"- Current fairness ratio: {fairness_ratio:.3f} (target: >= 0.80)\n"
        f'- Top biased feature: "{top_feature}"\n'
        f"- Flagged proxy columns: {flagged_columns}\n\n"
        "Generate THREE mitigation strategies as Python code:\n"
        "1. Pre-processing: Remove or transform the proxy columns\n"
        "2. In-processing: Use a fairness-aware classifier "
        "(use aif360's Reweighing or AdversarialDebiasing)\n"
        "3. Post-processing: Adjust decision thresholds per group\n\n"
        "For each strategy, provide:\n"
        "- A brief explanation (1 sentence)\n"
        "- Complete, runnable Python code using sklearn and aif360\n"
        "- Expected impact on fairness ratio\n\n"
        "Format as three clearly labeled sections. "
        "Use markdown code blocks. "
        "Keep each strategy under 30 lines of code."
    )

    _last_error = None
    if _genai_client:
        for attempt in range(3):                         # up to 3 attempts
            try:
                response = _genai_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                )
                return {
                    "mitigation_code":  response.text,
                    "model":            "gemini-2.0-flash",
                    "zero_retention":   False,
                    "note":             "Generated by Gemini — Powered by Google AI",
                    "error":            None,
                }
            except Exception as e:
                _last_error = str(e)
                if "429" in _last_error or "RESOURCE_EXHAUSTED" in _last_error:
                    wait = 2 ** attempt          # 1s, 2s, 4s
                    time.sleep(wait)
                    continue                      # retry
                break                            # non-rate-limit error — don't retry

    # Fallback template (rate-limited or no key)
    code = _REMEDIATE_FALLBACK_TEMPLATE.format(
        data_path=data_path,
        flagged_columns=flagged_columns,
        target_col=target_col,
        protected_col=protected_col,
        fairness_ratio=fairness_ratio,
    )
    note = "GEMINI_API_KEY not configured — showing parameterised template code"
    if _last_error:
        if "429" in _last_error or "RESOURCE_EXHAUSTED" in _last_error:
            note = "⚠️ Gemini rate limit hit (429) — showing template. Wait a moment and try again."
        else:
            note = f"⚠️ Gemini error — showing template. Reason: {_last_error[:120]}"
    return {
        "mitigation_code":  code,
        "model":            "template",
        "zero_retention":   False,
        "note":             note,
        "error":            _last_error,
    }
