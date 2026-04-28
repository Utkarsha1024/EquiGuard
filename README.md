<div align="center">

```
███████╗ ██████╗ ██╗   ██╗██╗ ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗
██╔════╝██╔═══██╗██║   ██║██║██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗
█████╗  ██║   ██║██║   ██║██║██║  ███╗██║   ██║███████║██████╔╝██║  ██║
██╔══╝  ██║▄▄ ██║██║   ██║██║██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
███████╗╚██████╔╝╚██████╔╝██║╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝
```

### **AI Bias Firewall — EEOC Compliance Audit Engine**

*Intercept bias before it reaches production. Not after a lawsuit.*

[![Live App](https://img.shields.io/badge/🚀_Live_App-equiguard.streamlit.app-6366f1?style=for-the-badge)](https://equiguard.streamlit.app/)
[![CI](https://github.com/Utkarsha1024/EquiGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/Utkarsha1024/EquiGuard/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-FF4B4B?logo=streamlit&logoColor=white)
![EEOC](https://img.shields.io/badge/compliance-EEOC%204%2F5ths-6366f1)
![aif360](https://img.shields.io/badge/fairness-IBM%20aif360-0f62fe)
![Gemini](https://img.shields.io/badge/AI-Gemini%20Flash-8E75B2?logo=google&logoColor=white)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-22c55e)

**[🚀 Try the Live App](https://equiguard.streamlit.app/) · [📖 API Docs](http://localhost:8000/docs) · [🐛 Report a Bug](https://github.com/Utkarsha1024/EquiGuard/issues)**

</div>

---

## ⚡ Why EquiGuard Exists

Every day, companies deploy AI models that quietly discriminate. A hiring model never checks gender — but penalises employment gaps that disproportionately affect women. A loan approval model never checks race — but uses zip code as a proxy. The model gets deployed. Thousands of real decisions are made. Nobody notices. Until the lawsuit.

Most bias detection tools are **retrospective** — they analyse models after deployment, after real people have been harmed. EquiGuard is different. It is a **firewall** — it sits between your model and production and blocks non-compliant models before a single decision reaches a real person.

---

## 🛡️ Audit Pipeline

```
① Upload CSV
      ↓
② Gemini Pre-flight ─── AI scans column stats for sensitive columns & proxies
      ↓                  Falls back to keyword heuristics (zip, age, race...)
③ Proxy Hunter ──────── FeatureAgglomeration + Pearson correlation
      ↓                  Flags features where |r| ≥ 0.15 vs protected column
④ Model Training ─────── sklearn Pipeline: Imputer → Scaler → LogisticRegression
      ↓                   80/20 train/test split, random_state=42
⑤ EEOC Compliance Audit ─ IBM aif360 BinaryLabelDataset + ClassificationMetric
      ↓                    • Disparate Impact Ratio  (threshold ≥ 0.80)
      ↓                    • Equal Opportunity Difference
      ↓                    • Average Odds Difference
⑥ SHAP Explainability ──── LinearExplainer → top 5 features by mean |SHAP|
      ↓
⑦ Pass / Fail Decision
      │
      ├── FAIL ──→  Slack webhook alert · Auto-mitigation: drop proxies → retrain → re-audit
      │             Log to SQLite
      │
      └── PASS ──→  Log to SQLite
                    Executive PDF Report · EEOC Compliance Certificate · Regulatory ZIP
```

---

## ✨ Features

### 🔍 Bias Detection & Auditing

| Feature | Detail |
|---------|--------|
| **Gemini Pre-flight Scan** | Analyses column stats before training — flags sensitive columns and proxies. Falls back to keyword heuristics when no API key is set. |
| **Proxy Variable Detection** | `FeatureAgglomeration` clusters numeric features. Pearson correlation between each cluster centroid and the protected attribute — features with `\|r\| ≥ 0.15` are flagged. |
| **EEOC 4/5ths Compliance** | IBM aif360 `BinaryLabelDataset` + `ClassificationMetric`. Computes Disparate Impact Ratio, Equal Opportunity Difference, and Average Odds Difference. Falls back to manual pandas calculation if aif360 fails. |
| **SHAP Explainability** | `shap.LinearExplainer` on the pipeline's transformed test data. Returns top 5 features by mean `\|SHAP\|`. |
| **Intersectional Audit** | Auto-detects all protected columns. Runs EEOC audit for each individually, then computes a full Pearson correlation heatmap. |
| **Multi-Model Pareto** | Trains Logistic Regression, Random Forest, Gradient Boosting, and Decision Tree simultaneously. Plots accuracy vs. fairness ratio. |
| **What-If Simulator** | Drops each numeric feature one-by-one, retrains, re-audits. Returns projected fairness ratio and accuracy delta per feature. |

### 🤖 Google AI Integrations

All AI features have a **full model fallback chain** — if the primary model returns 429, 404, or 503, the next is tried automatically.

**Fallback chain:** `gemini-3.0-flash → gemini-2.5-flash → gemini-3.1-flash-lite → gemini-2.5-flash-lite`

| Feature | Endpoint | What it does | Fallback |
|---------|----------|-------------|---------|
| **Pre-flight Scan** | `POST /audit/preflight` | Flags sensitive columns and proxies before training | Keyword heuristics |
| **Column Suggester** | `frontend/utils.py` | Auto-suggests `target_col` and `protected_col` with reasons | First column as default |
| **Risk Narrative** | `POST /audit/narrative` | 3-paragraph CCO-ready legal risk assessment | Plain-text template |
| **Remediation Agent** | `POST /audit/remediate` | 3 production-ready Python mitigation strategies | Parameterised code template |
| **Visual Bias Scanner** | `POST /audit/vision` | Scans images for faces and demographic signals | `{"risk_level": "UNKNOWN"}` |
| **Intersectional AI Summary** | Frontend `intersectional.py` | Narrates the correlation heatmap with recommendations | Button disabled with `.env` hint |

### 📊 Compliance Outputs

| Output | Endpoint | Contents |
|--------|----------|---------|
| **Executive PDF Report** | `POST /audit/export` | EEOC status, proxy scan, selection rate chart, SHAP waterfall, feature impact table |
| **EEOC Compliance Certificate** | `POST /audit/certificate` | UUID-stamped PDF with fairness ratio, group rates, SHAP primary driver, criteria checklist. Issued only if `compliance_pass: true`. |
| **Regulatory ZIP Package** | `POST /audit/package` | Executive Report + Certificate + `methodology.txt` + `audit_log.json`. Compliant models only. |

### 🚨 Webhook Alerting

When `compliance_pass: false`, the compliance endpoint fires `fire_audit_alert()` as a FastAPI `BackgroundTask` — non-blocking, never delays the API response, and catches all exceptions silently.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Streamlit Frontend · port 8501                │
│  🏠 Dashboard  ⚙️ Audit Engine  📊 Bias Leaderboard                  │
│  ⧡ Model Compare  ⬢ Intersectional  ◎ Vision Scanner                │
└────────────────────────────┬────────────────────────────────────────┘
                             │  HTTP · X-API-Key header
┌────────────────────────────▼────────────────────────────────────────┐
│                        FastAPI Backend · port 8000                  │
│  Routers: health · audit (17 endpoints) · google_ai (3 endpoints)   │
│  Auth: APIKeyHeader dependency · Alerting: BackgroundTask on FAIL   │
└────────┬──────────────────┬──────────────────┬──────────────────────┘
         │                  │                  │
┌────────▼──────┐  ┌────────▼──────┐  ┌────────▼────────────────────┐
│  audit_engine │  │  SQLite DB    │  │  Google AI · Gemini         │
│               │  │  audit_history│  │  Fallback chain (4 models)  │
│ model_runner  │  │  + file_name  │  └─────────────────────────────┘
│ compliance    │  └───────────────┘
│ proxy_hunter  │
│ mitigation    │
│ simulator     │
│ intersectional│
│ report_gen    │
│ certificate   │
└───────────────┘
```

---

## 📁 Project Structure

```
EquiGuard/
├── audit_engine/
│   ├── certificate.py        EEOC compliance certificate (fpdf2)
│   ├── compliance.py         aif360 metrics + SHAP explainability
│   ├── intersectional.py     Per-attribute EEOC audit + Pearson heatmap
│   ├── mitigation.py         Drops flagged columns, retrains
│   ├── model_registry.py     LR, RF, GB, DT — Pareto comparison
│   ├── model_runner.py       sklearn Pipeline: Imputer → Scaler → Classifier
│   ├── proxy_hunter.py       FeatureAgglomeration + Pearson |r| ≥ 0.15
│   ├── report_gen.py         4-section executive PDF
│   └── simulator.py          Per-feature what-if analysis
├── backend/
│   ├── main.py               FastAPI app factory
│   ├── alerting.py           fire_audit_alert() — Slack-compatible webhook
│   ├── config.py             get_settings() — load_dotenv on each call
│   ├── dependencies.py       require_api_key — HTTP 403 on failure
│   └── routers/
│       ├── audit.py          17 endpoints
│       ├── google_ai.py      Gemini fallback chain: narrative, vision, remediation
│       └── health.py         GET / and GET /health (no auth)
├── frontend/
│   ├── app.py                Session state, CSS injection, sidebar routing
│   ├── utils.py              api_get / api_post helpers + column suggester
│   ├── components.py         Fairness gauge, SHAP waterfall, bias drift chart
│   └── views/
│       ├── hero.py           Animated canvas hero page
│       ├── dashboard.py      4 KPI cards + live /health probe
│       ├── audit_engine.py   Full audit workflow UI
│       ├── bias_leaderboard.py  Drift chart + audit history table
│       ├── comparison.py     Pareto scatter chart
│       ├── intersectional.py Heatmap + Gemini summary
│       └── vision_scanner.py Image upload → Gemini multimodal scan
├── database/
│   └── db.py                 init_db, log_audit_run, get_audit_history
├── data/
│   └── golden_demo_dataset.csv   COMPAS-derived demo dataset
├── tests/
│   └── test_equiguard.py     pytest suite
├── scripts/
│   └── generate_golden_data.py   Fetches COMPAS, remaps columns
├── .github/workflows/ci.yml  pytest on push to main
├── .env.example              All vars with inline documentation
├── Dockerfile                python:3.11-slim + uv resolver + non-root user
└── docker-compose.yml        backend + frontend; db_data volume; health check
```

---

## 🚀 Quickstart — Local Setup

**Prerequisites:** Python 3.11, Git

```bash
# 1 — Clone
git clone https://github.com/Utkarsha1024/EquiGuard.git
cd EquiGuard

# 2 — Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3 — Install dependencies
pip install -r requirements.txt

# 4 — Configure environment
cp .env.example .env
# Set EQUIGUARD_API_KEY in .env
# Generate a secure key: python -c "import secrets; print(secrets.token_hex(32))"

# 5 — Generate demo dataset
python scripts/generate_golden_data.py

# 6 — Start services (two terminals)
uvicorn backend.main:app --reload --port 8000   # Terminal 1
streamlit run frontend/app.py                   # Terminal 2
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8501 |
| Swagger API Docs | http://localhost:8000/docs |

---

## 🐳 Run with Docker

```bash
cp .env.example .env
# Set EQUIGUARD_API_KEY in .env

docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8501 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

```bash
docker-compose down       # stop
docker-compose down -v    # stop + wipe audit database
```

---

## 📡 API Reference

All endpoints except `GET /` and `GET /health` require:
```
X-API-Key: your-EQUIGUARD_API_KEY-value
```

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Status check |
| `GET` | `/health` | Docker liveness probe |

### Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/audit/preflight` | Gemini pre-flight column scan |
| `POST` | `/audit/model` | Train model, return accuracy + predictions |
| `POST` | `/audit/compliance` | Full EEOC audit; logs to SQLite; fires webhook on FAIL |
| `POST` | `/audit/preprocess` | Proxy variable scan |
| `POST` | `/audit/mitigate` | Drop proxies, retrain, re-audit |
| `POST` | `/audit/simulate` | Per-feature what-if simulator |
| `POST` | `/audit/intersectional` | Multi-attribute audit + correlation heatmap |
| `POST` | `/audit/compare` | 4-model Pareto comparison |
| `POST` | `/audit/export` | Executive PDF report |
| `GET` | `/audit/history` | Full audit log from SQLite |
| `POST` | `/audit/certificate` | EEOC compliance certificate (PASS only) |
| `POST` | `/audit/package` | Regulatory ZIP package (PASS only) |

### Google AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/audit/narrative` | Gemini legal risk narrative |
| `POST` | `/audit/vision` | Gemini multimodal image scan |
| `POST` | `/audit/remediate` | Gemini-generated mitigation strategies |

### Example — Full compliance audit

```bash
curl -X POST http://localhost:8000/audit/compliance \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "data_path": "data/golden_demo_dataset.csv",
    "file_name": "golden_demo_dataset.csv",
    "target_col": "loan_approved",
    "protected_col": "race"
  }'
```

```json
{
  "compliance_pass": true,
  "fairness_ratio": 0.8412,
  "top_biased_feature": "priors_count",
  "group_a_rate": 0.72,
  "group_b_rate": 0.61,
  "shap_summary": {
    "priors_count": 0.183,
    "age": 0.094,
    "juv_fel_count": 0.071,
    "c_charge_degree": 0.043
  },
  "equal_opportunity_diff": -0.031,
  "avg_odds_diff": -0.028
}
```

---

## ⚙️ Environment Variables

Copy `.env.example` → `.env`.

### Required

| Variable | Description |
|----------|-------------|
| `EQUIGUARD_API_KEY` | Strong random secret. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `development` | `development` or `production` |
| `HOST` | `127.0.0.1` | uvicorn bind address |
| `PORT` | `8000` | Backend port |
| `API_BASE_URL` | `http://127.0.0.1:8000` | Docker overrides to `http://backend:8000` |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///equiguard.db` | Connection string |
| `DATABASE_PATH` | — | Full path override (Docker: `/app/db_data/equiguard.db`) |

### Google AI — all optional, all degrade gracefully

| Variable | Powers | Get it at |
|----------|--------|-----------|
| `GEMINI_API_KEY` | All 6 AI features | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP service account JSON path | GCP Console → IAM → Service Accounts |
| `GCP_PROJECT_ID` | Vertex AI integration | GCP Console |
| `GCP_LOCATION` | GCP region | Default: `us-central1` |

### Alerting

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBHOOK_ENABLED` | `false` | Set `true` to enable Slack alerts on FAIL |
| `WEBHOOK_URL` | — | Slack Incoming Webhook or any POST endpoint |

---

## 🤖 Google AI Setup

### Gemini API Key

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → **Create API Key**
2. Add to `.env`:
```env
GEMINI_API_KEY=AIza...your-key
```

### GCP Service Account (optional — Vertex AI only)

```
IAM & Admin → Service Accounts → Create
Name: equiguard-sa  ·  Role: Vertex AI User
```
Download key → save as `gcp-credentials.json` in project root, then set in `.env`:
```env
GOOGLE_APPLICATION_CREDENTIALS=./gcp-credentials.json
GCP_PROJECT_ID=your-project-id
```

> ⚠️ Never commit `gcp-credentials.json`. It's already in `.gitignore`.

### Degradation Table

| Missing | What happens |
|---------|-------------|
| No `GEMINI_API_KEY` | Pre-flight → keyword heuristics · Narrative → template · Remediation → parameterised template · Vision → `UNKNOWN` |
| No GCP credentials | Vertex AI falls back to Gemini client |

---

## 🔔 Webhook Alerting

```env
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../xxx
```

`/audit/compliance` fires `fire_audit_alert()` as a **BackgroundTask** when `compliance_pass: false`. Non-blocking — the API response is returned immediately. Compatible with Slack, Teams, Discord (Slack-compat), and any POST JSON endpoint.

---

## 🧪 Running Tests

```bash
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=audit_engine --cov=backend --cov-report=term-missing
```

---

## 🧰 Tech Stack

| Layer | Library | Purpose |
|-------|---------|---------|
| **Backend** | FastAPI 0.68+ | Async REST API |
| **Frontend** | Streamlit 1.0+ | Dashboard UI |
| **ML** | scikit-learn | Imputer → Scaler → Classifier pipeline |
| **Fairness** | IBM aif360 | Disparate impact, EOD, AOD |
| **Explainability** | SHAP 0.49+ | LinearExplainer |
| **Visualisation** | Plotly | Bias drift, SHAP waterfall, Pareto |
| **PDF** | fpdf2 + Matplotlib | Reports + certificates |
| **Database** | SQLite | Audit log |
| **AI** | google-genai 1.73.1 | Gemini text + multimodal vision |
| **Containers** | Docker + Compose | One-command deployment |
| **CI** | GitHub Actions | pytest on push to `main` |

---

## 🤝 Contributing

1. Fork and branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make atomic commits and add/update tests in `tests/test_equiguard.py`
3. Run `pytest tests/ -v`
4. Open a pull request

**Good first issues:**
- Add test coverage for `simulator.py`, `intersectional.py`, `audit_preflight`
- Add k-fold cross-validation to `model_runner.py`

---

## 📄 License

[MIT License](LICENSE) — Copyright © 2025 Utkarsha

---

<div align="center">

**[🚀 Try the Live App](https://equiguard.streamlit.app/)**

*EquiGuard — because the time to find bias is before deployment, not during a deposition.*

[![GitHub stars](https://img.shields.io/github/stars/Utkarsha1024/EquiGuard?style=social)](https://github.com/Utkarsha1024/EquiGuard)
[![GitHub forks](https://img.shields.io/github/forks/Utkarsha1024/EquiGuard?style=social)](https://github.com/Utkarsha1024/EquiGuard/fork)
[![GitHub issues](https://img.shields.io/github/issues/Utkarsha1024/EquiGuard?style=social)](https://github.com/Utkarsha1024/EquiGuard/issues)

</div>
