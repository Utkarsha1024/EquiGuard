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

# ── Model fallback chain (tried in order on quota/404 errors) ────────────────
_GEMINI_MODELS = [
    "gemini-3.0-flash",
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
]

def _generate_with_fallback(client, contents, config=None):
    """Try each model in _GEMINI_MODELS until one succeeds. Returns (response, model_name)."""
    last_err = None
    for model in _GEMINI_MODELS:
        try:
            resp = client.models.generate_content(model=model, contents=contents, config=config)
            return resp, model
        except Exception as e:
            last_err = e
            err_str = str(e)
            if any(code in err_str for code in ("429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND", "503", "UNAVAILABLE")):
                continue  # try next model
            raise  # non-quota error — propagate immediately
    raise last_err


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
            response, used_model = _generate_with_fallback(_genai_client, prompt)
            return {"narrative": response.text, "model": used_model}
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
    "race", "ethnicity", "nationality", "religion",
    "date of birth", "dob", "national origin",
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
        mime_type = file.content_type
        
        from google.genai import types
        doc_part = types.Part.from_bytes(data=content, mime_type=mime_type)

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

        prompt = (
            "You are a privacy and bias risk expert analyzing an image for demographic data leakage. "
            "Examine the image carefully and return ONLY a valid JSON object with this exact schema:\n\n"
            "{\n"
            '  "face_photo_detected": true/false,  // ONLY true if there is an actual PHOTOGRAPH of a human face (headshot, selfie, ID card photo, profile picture). Signatures, names, and text are NOT faces.\n'
            '  "sensitive_demographic_text": true/false,  // true ONLY if the image contains explicit sensitive attributes like RACE, ETHNICITY, RELIGION, NATIONAL ORIGIN, or DATE OF BIRTH as labeled data fields. Person names and job titles alone do NOT count.\n'
            '  "id_document_detected": true/false,  // true if this looks like a government ID, passport, or driver license with a photo\n'
            '  "has_signatures": true/false,  // true if the image contains handwritten signatures\n'
            '  "flagged_items": ["list of specific items flagged"],  // empty list if nothing found\n'
            '  "description": "one sentence describing what you see in the image",\n'
            '  "risk_level": "CRITICAL"|"HIGH"|"MEDIUM"|"LOW"  // CRITICAL if face/ID. HIGH if sensitive text. MEDIUM if generic items. LOW if safe.\n'
            "}\n\n"
            "IMPORTANT RULES:\n"
            "- A certificate of participation with names and signatures is LOW risk — it has no face photo.\n"
            "- A resume with a headshot photo is CRITICAL risk.\n"
            "- An Aadhaar card, passport, or ID with a face photo is CRITICAL risk.\n"
            "- A document with only names, titles, logos, and text is LOW risk.\n"
            "Return ONLY valid JSON. No markdown, no explanation."
        )

        import json as _json
        response, _vision_model = _generate_with_fallback(
            client, 
            [prompt, doc_part],
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json"
            )
        )

        # Parse structured response
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]

        try:
            parsed = _json.loads(raw)
        except Exception:
            # If JSON parse fails, fall back to keyword detection
            parsed = {
                "face_photo_detected": "CRITICAL" in raw.upper(),
                "sensitive_demographic_text": False,
                "id_document_detected": False,
                "has_signatures": False,
                "flagged_items": [],
                "description": "Could not parse structured response.",
                "risk_level": "CRITICAL" if "CRITICAL" in raw.upper() else "LOW",
            }

        risk          = parsed.get("risk_level", "LOW")
        face_detected = parsed.get("face_photo_detected", False)
        id_detected   = parsed.get("id_document_detected", False)
        demo_text     = parsed.get("sensitive_demographic_text", False)
        flagged_items = parsed.get("flagged_items", [])
        description   = parsed.get("description", "")
        has_sigs      = parsed.get("has_signatures", False)

        # Compute risk score deterministically but with variability based on findings
        if face_detected or id_detected:
            base_score = 80
        elif demo_text:
            base_score = 50
        elif flagged_items:
            base_score = 25
        elif has_sigs:
            base_score = 10
        else:
            base_score = 5

        # Add variability based on the number of flagged items (up to +15)
        item_penalty = min(len(flagged_items) * 4, 15)
        
        # Add slight variability based on the description length to reflect image complexity (up to +5)
        complexity_penalty = min(len(description) // 20, 5)

        risk_score = min(base_score + item_penalty + complexity_penalty, 100)

        # Strictly map risk_level to the 0-100 gauge thresholds so UI colors perfectly match
        if risk_score >= 70:
            risk = "CRITICAL"
        elif risk_score >= 40:
            risk = "HIGH"
        elif risk_score >= 20:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        faces_count = 1 if (face_detected or id_detected) else 0

        flagged_labels = []
        if face_detected:
            flagged_labels.append("Face Photograph Detected")
        if id_detected:
            flagged_labels.append("ID Document Detected")
        flagged_labels += flagged_items

        flagged_text = []
        if demo_text:
            flagged_text.append("Sensitive Demographic Text")

        if risk in ("CRITICAL", "HIGH"):
            compliance_warning = (
                "This image contains detectable protected attributes. Using images of this type as inputs "
                "to automated hiring or scoring systems may violate GDPR Article 9 and EEOC guidelines."
            )
            recommendation = (
                f"This image appears to contain {'a face photograph or ID document' if face_detected or id_detected else 'sensitive demographic text'}. "
                "Manual review and demographic filtering required before use in any automated system."
            )
        else:
            compliance_warning = "No significant protected attributes detected. Standard data minimisation practices apply."
            recommendation = (
                f"{description} This document contains names/text but no face photographs. "
                "Safe for automated processing with standard privacy controls."
            )

        return {
            "risk_level":          risk,
            "risk_score":          risk_score,
            "faces_detected":      faces_count,
            "flagged_labels":      flagged_labels,
            "flagged_text":        flagged_text,
            "recommendation":      recommendation,
            "compliance_warning":  compliance_warning,
            "description":         description,
            "model":               _vision_model,
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
        try:
            response, used_model = _generate_with_fallback(_genai_client, prompt)
            return {
                "mitigation_code":  response.text,
                "model":            used_model,
                "zero_retention":   False,
                "note":             f"Generated by Gemini ({used_model}) — Powered by Google AI",
                "error":            None,
            }
        except Exception as e:
            _last_error = str(e)

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
