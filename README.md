# EquiGuard — AI Bias Firewall

[![CI](https://github.com/Utkarsha1024/EquiGuard/actions/workflows/ci.yml/badge.svg)
](https://github.com/Utkarsha1024/EquiGuard/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11-blue)
![EEOC](https://img.shields.io/badge/compliance-EEOC%204%2F5ths-indigo)
![Static Badge](https://img.shields.io/badge/License-MIT-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-0.89+-red.svg)
---

## The Problem

Companies deploy AI models that contain hidden demographic bias. A loan approval model trained on historical data may quietly disadvantage applicants by race, gender, or age — not because of an explicit rule, but because of patterns learned from biased outcomes. When that model is used in hiring, lending, or promotion decisions, it exposes the organisation to EEOC violations, class-action lawsuits, and reputational damage.

Most teams only discover the bias after a lawsuit.

## The Solution

**EquiGuard** is an enterprise-grade AI Bias Firewall. It intercepts automated decisions before they reach production, mathematically audits them against US EEOC compliance law, surfaces the exact features driving the disparity using SHAP explainability, and autonomously retrains the model to eliminate bias — without manual intervention.

It provides a full audit trail, temporal drift tracking, executive PDF reports, and downloadable EEOC compliance certificates.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                   │
│         Dark enterprise dashboard  ·  port 8501         │
│   Dashboard · Audit Engine · Bias Leaderboard · Reports │
└────────────────────┬────────────────────────────────────┘
                     │  HTTP  (X-API-Key auth)
┌────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                      │
│              REST API  ·  port 8000                     │
│  /audit/model  /audit/compliance  /audit/mitigate       │
│  /audit/preprocess  /audit/export  /audit/certificate   │
└──────┬──────────────┬───────────────┬───────────────────┘
       │              │               │
┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼───────────────────┐
│ audit_engine│ │  database  │ │     audit_engine/        │
│             │ │            │ │                          │
│ model_runner│ │  SQLite DB │ │  compliance.py  (aif360) │
│ compliance  │ │  audit log │ │  proxy_hunter.py (SHAP)  │
│ mitigation  │ │  history   │ │  mitigation.py           │
│ report_gen  │ └────────────┘ │  report_gen.py  (fpdf2)  │
│ certificate │                │  certificate.py (fpdf2)  │
└─────────────┘                └──────────────────────────┘
```

```
Audit flow
──────────
Upload CSV  →  Pre-processing scan (proxy hunter)
            →  Model training (scikit-learn pipeline)
            →  EEOC compliance check (IBM aif360)
            →  SHAP explanation (feature attribution)
            →  Pass / Fail decision
                   │
             FAIL ─┼─ Mitigation (drop proxies, retrain)
                   │
             PASS ─┼─ Log to SQLite
                         │
                         ├─ Executive PDF report
                         └─ EEOC Compliance Certificate
```

---

## Features

| Feature | Detail |
|---|---|
| **EEOC 4/5ths Rule Audit** | Computes disparate impact ratio using IBM aif360 against any protected attribute |
| **Proxy Variable Detection** | Correlation-based scan identifies features acting as proxies for protected attributes |
| **Autonomous Mitigation** | Drops flagged proxies and retrains the model in a single API call |
| **SHAP Explainability** | Waterfall chart shows exactly which features push each decision — and by how much |
| **Bias Drift Tracking** | Plotly line chart of fairness ratio over time — catches model decay before it matters |
| **Executive PDF Report** | One-click fpdf2-generated summary downloadable from the UI |
| **EEOC Compliance Certificate** | Issued automatically on passing audit — UUID-stamped, ready for regulators |
| **API Key Authentication** | All audit endpoints protected via `X-API-Key` header, config via `.env` |
| **Docker Ready** | Single `docker-compose up` spins both services |
| **CI/CD** | GitHub Actions runs pytest on every push to `main` |

---

## Why EquiGuard?

- **Proactive, not reactive.** Catches bias before deployment, not after a lawsuit. Most bias detection tools are retrospective; EquiGuard is a firewall — it blocks non-compliant models from reaching production.

- **Explainable by design.** Regulatory bodies don't accept black-box answers. Every audit result is backed by SHAP feature attribution and a full aif360 metrics report that can be handed to legal or compliance teams.

- **Closes the loop automatically.** Detecting bias and then telling a data scientist to "go fix it" is not a workflow. EquiGuard retrains the model, re-audits it, and issues a certificate — all from a single button click.

- **Audit-ready paper trail.** Every audit run is logged to SQLite with a timestamp, fairness ratio, and pass/fail status. Downloadable PDF certificates carry a UUID and are formatted for submission to regulators, legal teams, or enterprise auditors.

---

## Quickstart

### Prerequisites

- Python 3.11
- A `.env` file (copy from `.env.example`)

```bash
git clone https://github.com/Utkarsha1024/EquiGuard.git
cd EquiGuard

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set EQUIGUARD_API_KEY to any strong secret string
```

### Run locally (two terminals)

```bash
# Terminal 1 — FastAPI backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Streamlit frontend
streamlit run frontend/app.py
```

Open `http://localhost:8501` in your browser.

### Run with Docker

```bash
docker-compose up --build
```

Backend available at `http://localhost:8000`, frontend at `http://localhost:8501`.

---

## Project Structure

```
EquiGuard/
├── audit_engine/
│   ├── certificate.py       # EEOC compliance certificate (fpdf2)
│   ├── compliance.py        # aif360 disparate impact & EEOC metrics
│   ├── mitigation.py        # Proxy removal + model retraining
│   ├── model_runner.py      # scikit-learn pipeline training & inference
│   ├── proxy_hunter.py      # Correlation-based proxy variable detection
│   └── report_gen.py        # Executive summary PDF (fpdf2)
├── backend/
│   └── main.py              # FastAPI app — all API endpoints + auth
├── database/
│   └── db.py                # SQLite audit log (write + read history)
├── frontend/
│   └── app.py               # Streamlit dashboard — dark enterprise theme
├── scripts/                 # Utility / data generation scripts
├── tests/
│   └── test_audit_engine.py # pytest test suite
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI pipeline
├── .env.example             # Environment variable template
├── Dockerfile
├── docker-compose.yml
├── golden_demo_dataset.csv  # Fully synthetic demo dataset (safe to share)
└── requirements.txt
```

> **Note:** `golden_demo_dataset.csv` is entirely synthetic data generated for demonstration purposes. It contains no real personal information.

---

## API Reference

All endpoints except `/` and `/health` require the `X-API-Key` header.

```
X-API-Key: <your key from .env>
```

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/` | — | Health check, returns env and status |
| `GET` | `/health` | — | Liveness probe for Docker / load balancers |
| `POST` | `/audit/model` | Required | Train model, return accuracy + predictions |
| `POST` | `/audit/compliance` | Required | Full EEOC audit — returns fairness ratio, pass/fail, SHAP |
| `POST` | `/audit/preprocess` | Required | Scan dataset for proxy variables |
| `POST` | `/audit/mitigate` | Required | Drop proxies, retrain, re-audit |
| `POST` | `/audit/export` | Required | Download executive summary PDF |
| `GET` | `/audit/history` | Required | Retrieve full audit log from SQLite |
| `POST` | `/audit/certificate` | Required | Generate EEOC compliance certificate PDF |
| `POST` | `/audit/simulate` | Required | What-if simulator — project fairness ratio per feature drop |
| `POST` | `/audit/intersectional` | Required | Multi-attribute intersectional audit + correlation heatmap |
| `POST` | `/audit/package` | Required | Download full regulatory ZIP (PDF + cert + methodology + JSON) |
| `POST` | `/audit/narrative` | Required | **[AI]** Generate Gemini legal risk narrative (3 paragraphs) |
| `POST` | `/audit/vision` | Required | **[AI]** Scan image for demographic data leakage (Vision AI) |
| `POST` | `/audit/remediate` | Required | **[AI]** Generate 3 bias mitigation strategies (Vertex AI) |


### Example: run a full compliance audit

```bash
curl -X POST http://localhost:8000/audit/compliance \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "data_path": "golden_demo_dataset.csv",
    "target_col": "loan_approved",
    "protected_col": "race"
  }'
```

```json
{
  "compliance_pass": true,
  "fairness_ratio": 0.8412,
  "top_biased_feature": "zip_code",
  "group_a_rate": 0.72,
  "group_b_rate": 0.61,
  "shap_summary": { "zip_code": 0.183, "income": 0.094 }
}
```

Interactive docs available at `http://localhost:8000/docs` (Swagger UI).

---

## Environment Variables

Copy `.env.example` to `.env` and populate before running.

```env
EQUIGUARD_API_KEY=your-secret-key-here   # Required — protects all audit endpoints
DATABASE_URL=sqlite:///equiguard.db      # SQLite path
ENV=development                          # development | production
HOST=127.0.0.1
PORT=8000
API_BASE_URL=http://127.0.0.1:8000       # Used by the Streamlit frontend
```

---

## Running Tests

```bash
pytest tests/ -v
```

Tests cover:

- Bias score returns a float in the range 0–1
- Disparate impact ratio calculation correctness
- EEOC pass/fail threshold logic at the 0.80 boundary
- Mitigation reduces bias score vs the pre-mitigation baseline
- Audit log write and read round-trip via SQLite
- API endpoints via `httpx` (model, compliance, preprocess, mitigate)

---

## Tech Stack

| Layer | Library | Purpose |
|---|---|---|
| Backend | FastAPI | Async REST API |
| Frontend | Streamlit | Dashboard UI |
| ML | scikit-learn | Model training pipelines |
| Fairness | IBM aif360 | EEOC metrics, disparate impact |
| Explainability | SHAP | Feature attribution, waterfall charts |
| Visualisation | Plotly, Altair | Bias drift, SHAP charts |
| PDF | fpdf2 | Reports and compliance certificates |
| Database | SQLite | Audit log persistence |
| Auth | python-dotenv | `.env` config, API key middleware |
| Containers | Docker, docker-compose | Reproducible deployment |
| CI | GitHub Actions | Automated test runs on push |

---

## Contributing

Contributions are welcome. Please follow this workflow:

1. Fork the repository and create a branch from `main`.
2. Make your changes with clear, descriptive commits.
3. Add or update tests in `tests/` to cover your changes.
4. Ensure `pytest tests/` passes locally before submitting.
5. Open a pull request with a concise description of what changed and why.

For significant changes, please open an issue first to discuss the approach.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Google AI Features

Three Google AI integrations are built into EquiGuard and degrade gracefully when credentials are not configured.

| Feature | Endpoint | Powered By | Fallback |
|---|---|---|---|
| **Gemini Legal Risk Narrative** | `POST /audit/narrative` | Gemini 1.5 Flash | Template string |
| **Visual Bias Scanner** | `POST /audit/vision` | Cloud Vision AI | `UNKNOWN` risk level |
| **Vertex AI Remediation Agent** | `POST /audit/remediate` | Vertex AI Gemini | Parameterised code template |

---

## Google AI Setup (5 minutes)

### 1. Create a GCP project

Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project or select an existing one.

### 2. Enable APIs

In your project, enable these two APIs:
- **Cloud Vision API**
- **Vertex AI API**

### 3. Create a service account

1. Go to **IAM & Admin → Service Accounts → Create Service Account**
2. Give it a name (e.g. `equiguard-sa`)
3. Assign these roles:
   - `Vertex AI User`
   - `Cloud Vision API User`
4. Click **Done**

### 4. Download credentials

1. Click the service account you just created
2. Go to the **Keys** tab → **Add Key → Create new key → JSON**
3. Save the downloaded file as `gcp-credentials.json` in the project root
4. Add it to `.gitignore` (already included in the template)

### 5. Get a Gemini API key

Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey) and create a key.

### 6. Configure `.env`

```env
GEMINI_API_KEY=your-gemini-api-key-here
GOOGLE_APPLICATION_CREDENTIALS=./gcp-credentials.json
GCP_PROJECT_ID=your-actual-project-id
GCP_LOCATION=us-central1
```

### 7. Install the Google AI packages

```bash
pip install google-cloud-vision google-cloud-aiplatform google-generativeai
```

Or simply run `pip install -r requirements.txt` — all three are already listed.

### Behaviour without credentials

| Credential missing | Behaviour |
|---|---|
| `GEMINI_API_KEY` not set | Narrative endpoint returns a plain-text template string |
| `GOOGLE_APPLICATION_CREDENTIALS` not set | Vision endpoint returns `{"risk_level": "UNKNOWN", "error": "..."}` |
| `GCP_PROJECT_ID` not set | Remediate endpoint returns parameterised Python template code |

The application never crashes — all AI features degrade gracefully.

---

*EquiGuard — because bias in AI is a legal risk, not just an ethical one.*