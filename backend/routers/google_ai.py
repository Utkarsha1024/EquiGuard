import os
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from backend.dependencies import require_api_key
from backend.config import get_settings
from backend.utils import _build_narrative_fallback

router = APIRouter(tags=["Google AI"])

# ── Google AI imports (optional — degrade gracefully if not installed) ──────────
try:
    from google import genai as _genai_sdk
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel as VertexModel
    _VERTEX_AVAILABLE = True
except ImportError:
    _VERTEX_AVAILABLE = False

try:
    from google.cloud import vision as _vision
    _VISION_AVAILABLE = True
except ImportError:
    _VISION_AVAILABLE = False

# ── Configure Gemini Client ──────────────────────────────────────────────────
_gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
_genai_client = None
if _gemini_key and _GENAI_AVAILABLE:
    _genai_client = _genai_sdk.Client(api_key=_gemini_key)


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
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return {"narrative": response.text, "model": "gemini-2.5-flash"}
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
    Scans an uploaded image for demographic data leakage using Cloud Vision AI.
    Auth: manually checks X-API-Key header (file upload incompatible with Depends).
    Degrades gracefully when Vision AI credentials are not configured.
    """
    settings = get_settings()
    api_key  = request.headers.get("X-API-Key", "")
    if not api_key or api_key != settings["api_key"]:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key. Pass your key in the X-API-Key header.",
        )

    if not _VISION_AVAILABLE:
        return {
            "error": "Vision AI not configured — install google-cloud-vision and set GOOGLE_APPLICATION_CREDENTIALS",
            "risk_level": "UNKNOWN",
        }

    try:
        vision_client = _vision.ImageAnnotatorClient()
    except Exception as e:
        return {
            "error": f"Vision AI credentials not configured: {e}",
            "risk_level": "UNKNOWN",
        }

    content = await file.read()
    image   = _vision.Image(content=content)

    faces_detected  = 0
    flagged_labels  = []
    flagged_text    = []

    try:
        face_resp      = vision_client.face_detection(image=image)
        faces_detected = len(face_resp.face_annotations)
    except Exception as e:
        if "403" in str(e) or "disabled" in str(e).lower() or "permission" in str(e).lower():
            return {
                "error": f"Vision AI API Error: {e}",
                "risk_level": "UNKNOWN",
            }
        pass

    try:
        label_resp = vision_client.label_detection(image=image, max_results=20)
        flagged_labels = [
            lbl.description.lower()
            for lbl in label_resp.label_annotations
            if lbl.description.lower() in SENSITIVE_LABELS and lbl.score > 0.7
        ]
    except Exception:
        pass

    try:
        text_resp = vision_client.text_detection(image=image)
        if text_resp.text_annotations:
            detected_text = text_resp.text_annotations[0].description
            flagged_text = [
                word for word in detected_text.lower().split()
                if word in DEMOGRAPHIC_KEYWORDS
            ]
    except Exception:
        pass

    risk_points = 0
    if faces_detected > 0:
        risk_points += 40
    risk_points += min(len(flagged_labels) * 10, 30)
    risk_points += min(len(flagged_text) * 5, 30)
    risk_score  = min(risk_points, 100)

    if risk_score >= 70:
        risk_level = "CRITICAL"
    elif risk_score >= 40:
        risk_level = "HIGH"
    elif risk_score >= 20:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    compliance_warning = (
        "This image contains detectable protected attributes (faces, demographic labels, "
        "or demographic text). Using images of this type as inputs to automated hiring, "
        "scoring, or decision-making systems may violate GDPR Article 9 and EEOC guidelines."
        if risk_level in ("HIGH", "CRITICAL") else
        "No significant protected attributes detected. Standard data minimisation practices apply."
    )

    recommendation = (
        "Do not feed images of this type into hiring or scoring models. "
        "Remove or anonymise faces and any demographic identifiers before ingestion."
        if risk_level in ("HIGH", "CRITICAL") else
        "Low demographic signal detected. Continue monitoring for edge cases."
    )

    return {
        "risk_level":          risk_level,
        "risk_score":          risk_score,
        "faces_detected":      faces_detected,
        "flagged_labels":      flagged_labels,
        "flagged_text":        flagged_text,
        "compliance_warning":  compliance_warning,
        "recommendation":      recommendation,
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
    Generates three production-ready Python mitigation strategies via Vertex AI Gemini.
    Falls back to a parameterised template when Vertex AI is not configured.
    """
    top_feature     = payload.get("top_biased_feature", "unknown_feature")
    flagged_columns = payload.get("flagged_columns", [])
    fairness_ratio  = payload.get("fairness_ratio", 0.0)
    data_path       = payload.get("data_path", "data/golden_demo_dataset.csv")
    target_col      = payload.get("target_col", "loan_approved")
    protected_col   = payload.get("protected_col", "race")

    settings = get_settings()
    project  = settings["gcp_project_id"]
    location = settings["gcp_location"]

    if project and _VERTEX_AVAILABLE:
        try:
            vertexai.init(project=project, location=location)
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
            vertex_model = VertexModel("gemini-1.5-flash-001")
            response     = vertex_model.generate_content(prompt)
            return {
                "mitigation_code":  response.text,
                "model":            "vertex-ai/gemini-1.5-flash-001",
                "zero_retention":   True,
                "note":             "Generated via Vertex AI — enterprise zero-data-retention environment",
            }
        except Exception:
            pass  # fall through to template

    code = _REMEDIATE_FALLBACK_TEMPLATE.format(
        data_path=data_path,
        flagged_columns=flagged_columns,
        target_col=target_col,
        protected_col=protected_col,
        fairness_ratio=fairness_ratio,
    )
    return {
        "mitigation_code":  code,
        "model":            "template",
        "zero_retention":   False,
        "note":             "Vertex AI not configured — showing parameterised template code",
    }
