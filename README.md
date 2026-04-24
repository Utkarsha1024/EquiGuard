<div align="center">

<br/>

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

<br/>

[![CI](https://github.com/Utkarsha1024/EquiGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/Utkarsha1024/EquiGuard/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-FF4B4B?logo=streamlit&logoColor=white)
![EEOC](https://img.shields.io/badge/compliance-EEOC%204%2F5ths-6366f1)
![aif360](https://img.shields.io/badge/fairness-IBM%20aif360-0f62fe)
![License](https://img.shields.io/badge/license-MIT-22c55e)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-8E75B2?logo=google&logoColor=white)

<br/>

<!-- ═══════════════════════════════════════════════ -->
<!-- HERO SCREENSHOT — replace with your actual screenshot -->
<!-- ═══════════════════════════════════════════════ -->

> **📸 Screenshot / Demo Video**
>
> *Drop your hero dashboard screenshot here*
> ```
> ![EquiGuard Dashboard](docs/assets/hero-dashboard.png)
> ```
> *Or embed a demo video:*
> ```
> [![Watch the demo](docs/assets/video-thumbnail.png)](https://youtu.be/YOUR_VIDEO_ID)
> ```

<br/>

</div>

---

## 📖 Table of Contents

| # | Section |
|---|---------|
| 1 | [The Problem — Why This Exists](#-the-problem) |
| 2 | [The Solution — What EquiGuard Does](#-the-solution) |
| 3 | [Key Features](#-key-features) |
| 4 | [Architecture](#-architecture) |
| 5 | [Quickstart — Up in 5 Minutes](#-quickstart) |
| 6 | [Running with Docker](#-running-with-docker) |
| 7 | [Project Structure](#-project-structure) |
| 8 | [Full Audit Walkthrough](#-full-audit-walkthrough) |
| 9 | [API Reference](#-api-reference) |
| 10 | [Environment Variables](#-environment-variables) |
| 11 | [Google AI Setup](#-google-ai-setup) |
| 12 | [Webhook Alerting](#-webhook-alerting) |
| 13 | [Running Tests](#-running-tests) |
| 14 | [Tech Stack](#-tech-stack) |
| 15 | [Contributing](#-contributing) |
| 16 | [License](#-license) |

---

## ⚡ The Problem

Every day, companies deploy AI models that quietly discriminate.

A loan approval model trained on historical data learns from decades of redlining, systemic inequality, and biased human decisions. It never explicitly looks at race — but it uses **zip code** as a proxy. It never checks gender — but it penalises **employment gaps** that disproportionately affect women. The model gets deployed. Thousands of decisions are made. And the company has no idea.

Until the lawsuit.

> *"The average employment discrimination class-action settlement in the US is $2.7M. The average cost of finding bias pre-deployment is near zero."*

**Most teams only discover bias after the damage is done.** Existing bias detection tools are retrospective — they analyse models after deployment, after real people have been harmed, after regulators are involved.

---

## 🛡️ The Solution

**EquiGuard is an AI Bias Firewall.**

It sits between your model and production. Before a single decision reaches a real person, EquiGuard:

1. **Scans** your dataset for hidden proxy variables (features that correlate with protected attributes like race or gender)
2. **Audits** your model against the US EEOC 4/5ths rule using IBM aif360
3. **Explains** every bias driver using SHAP feature attribution
4. **Mitigates** — drops proxies, retrains the model, re-audits automatically
5. **Certifies** — issues a UUID-stamped EEOC compliance certificate
6. **Alerts** — fires a Slack webhook the moment a FAIL is detected

No manual intervention. No waiting for a legal team. A compliant model, or a blocked one.

<!-- ═══════════════════════════════════════════════ -->
<!-- AUDIT FLOW DEMO GIF — replace with yours -->
<!-- ═══════════════════════════════════════════════ -->

> **🎬 See it in action**
> ```
> ![Audit Flow](docs/assets/audit-flow-demo.gif)
> ```

---

## ✨ Key Features

<br/>

### 🔍 Bias Detection

| Feature | What it does |
|---------|-------------|
| **EEOC 4/5ths Rule Audit** | Computes the disparate impact ratio using IBM aif360. If the unprivileged group's selection rate is less than 80% of the privileged group's rate, the model fails. |
| **Proxy Variable Detection** | Uses `FeatureAgglomeration` (hierarchical clustering) + Pearson correlation to find features acting as stand-ins for protected attributes — things like zip code, name, or school acting as proxies for race. |
| **Intersectional Audit** | Audits every detected demographic attribute simultaneously. A model can pass for race while failing for gender. This catches it. |
| **SHAP Explainability** | Every audit result comes with a SHAP waterfall chart showing exactly which features pushed decisions — and by how much. |

<br/>

### 🤖 Google AI Integration

| Feature | Powered By | What it does |
|---------|-----------|-------------|
| **Gemini Legal Risk Narrative** | Gemini 2.5 Flash | Generates a 3-paragraph CCO-ready legal risk assessment from audit numbers |
| **AI Column Suggester** | Gemini 2.5 Flash | Analyses your uploaded CSV and auto-suggests which column is the target and which is the protected attribute |
| **Visual Bias Scanner** | Cloud Vision AI | Scans images (photos, ID cards, resumes) for faces, demographic labels, and demographic text — stops image-based bias before it enters the pipeline |
| **Vertex AI Remediation Agent** | Vertex AI Gemini | Generates 3 production-ready Python mitigation strategies (pre-processing, in-processing, post-processing) with full runnable code |
| **AI Intersectional Summary** | Gemini 2.5 Flash | Narrates the correlation heatmap in plain English — identifies high-risk proxies and recommends specific mitigations |

<br/>

### 🔧 Autonomous Mitigation

```
AUDIT → FAIL detected
      → Proxy variables identified
      → Flagged features dropped
      → Model retrained on clean data
      → Re-audited
      → PASS → Certificate issued
```

One button. No data scientist required.

<br/>

### 📊 Reporting & Compliance

| Output | Description |
|--------|-------------|
| **Executive PDF Report** | 4-section report: compliance status, proxy scan results, bias analysis charts, SHAP feature table |
| **EEOC Compliance Certificate** | UUID-stamped, print-ready PDF. Formatted for submission to regulators, legal teams, or enterprise auditors |
| **Regulatory ZIP Package** | Everything in one download: executive report + certificate + methodology doc + audit JSON log |
| **Bias Drift Leaderboard** | Plotly time-series chart of fairness ratio across all audit runs. Catches model decay before it matters |
| **Multi-Model Pareto Chart** | Trains 4 classifier families simultaneously and plots accuracy vs. fairness — pick the optimal model |

<br/>

### 🚨 Real-Time Alerting

When a compliance audit fails, EquiGuard immediately fires a Slack-compatible webhook with the full audit context — fairness ratio, top bias driver, group selection rates, timestamp. Configurable via `.env`. Never crashes the audit flow.

<!-- ═══════════════════════════════════════════════ -->
<!-- FEATURES SCREENSHOT GRID — replace with yours -->
<!-- ═══════════════════════════════════════════════ -->

> **📸 Feature Screenshots**
> ```
> | Dashboard | SHAP Chart | Certificate |
> |-----------|-----------|-------------|
> | ![Dashboard](docs/assets/dashboard.png) | ![SHAP](docs/assets/shap.png) | ![Cert](docs/assets/cert.png) |
> ```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Streamlit Frontend                           │
│                   Dark enterprise dashboard · port 8501             │
│                                                                     │
│   🏠 Dashboard  ·  ⚙️ Audit Engine  ·  📊 Bias Leaderboard        │
│   ⧡ Model Compare  ·  ⬢ Intersectional  ·  ◎ Vision Scanner       │
└────────────────────────────┬────────────────────────────────────────┘
                             │  HTTP  (X-API-Key auth)
┌────────────────────────────▼────────────────────────────────────────┐
│                         FastAPI Backend                             │
│                    REST API · port 8000 · /docs                     │
│                                                                     │
│  /audit/model       /audit/compliance    /audit/preprocess          │
│  /audit/mitigate    /audit/simulate      /audit/intersectional      │
│  /audit/compare     /audit/export        /audit/certificate         │
│  /audit/package     /audit/narrative     /audit/vision              │
│  /audit/remediate                                                   │
└────────┬──────────────────┬──────────────────┬───────────────────────┘
         │                  │                  │
┌────────▼──────┐  ┌────────▼──────┐  ┌────────▼────────────────────┐
│  audit_engine │  │   database/   │  │     Google AI Services      │
│               │  │               │  │                             │
│ model_runner  │  │  SQLite DB    │  │  Gemini 2.5 Flash           │
│ compliance    │  │  audit log    │  │  Cloud Vision AI            │
│ proxy_hunter  │  │  history      │  │  Vertex AI Gemini           │
│ mitigation    │  │               │  │                             │
│ simulator     │  └───────────────┘  └─────────────────────────────┘
│ intersectional│
│ model_registry│
│ report_gen    │
│ certificate   │
└───────────────┘
```

### The Audit Pipeline

```
CSV Upload
    │
    ▼
① Pre-flight Scan ──────────────── Gemini analyses column stats
    │                               Flags sensitive columns
    ▼
② Proxy Hunter ─────────────────── FeatureAgglomeration clustering
    │                               Pearson correlation vs. protected attr
    │                               Flags: zip_code, school, name...
    ▼
③ Model Training ───────────────── sklearn Pipeline
    │                               Imputer → Scaler → LogisticRegression
    ▼
④ EEOC Compliance Check ─────────── IBM aif360 BinaryLabelDataset
    │                               Disparate Impact Ratio
    │                               Equal Opportunity Difference
    │                               Average Odds Difference
    ▼
⑤ SHAP Explainability ──────────── LinearExplainer on pipeline
    │                               Mean |SHAP| per feature → top 5
    ▼
⑥ Pass / Fail Decision
    │
    ├─── FAIL ──► Fire Slack webhook alert
    │             Log to SQLite
    │             Mitigation: drop proxies → retrain → re-audit
    │
    └─── PASS ──► Log to SQLite
                  Executive PDF report
                  EEOC Compliance Certificate
                  Regulatory ZIP package
```

---

## 🚀 Quickstart

### Prerequisites

- Python **3.11**
- Git
- A terminal

### Step 1 — Clone the repo

```bash
git clone https://github.com/Utkarsha1024/EquiGuard.git
cd EquiGuard
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> ⏱️ This takes 2–4 minutes the first time — the ML stack (scikit-learn, SHAP, aif360) is heavy.

### Step 4 — Configure environment

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```env
EQUIGUARD_API_KEY=any-strong-secret-string-you-choose
```

Generate a cryptographically strong key instantly:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5 — Generate the demo dataset

```bash
python scripts/generate_golden_data.py
```

This downloads the public COMPAS dataset, transforms it into a loan approval format, and saves it to `data/golden_demo_dataset.csv`.

### Step 6 — Start both services

Open **two terminals**:

```bash
# Terminal 1 — FastAPI backend
uvicorn backend.main:app --reload --port 8000
```

```bash
# Terminal 2 — Streamlit frontend
streamlit run frontend/app.py
```

### Step 7 — Open the dashboard

```
http://localhost:8501
```

The Swagger API docs are at:
```
http://localhost:8000/docs
```

<!-- ═══════════════════════════════════════════════ -->
<!-- QUICKSTART GIF — replace with yours -->
<!-- ═══════════════════════════════════════════════ -->

> **🎬 Quickstart demo**
> ```
> ![Quickstart](docs/assets/quickstart.gif)
> ```

---

## 🐳 Running with Docker

The cleanest way — one command spins the full stack.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Step 1 — Configure `.env`

```bash
cp .env.example .env
# Set EQUIGUARD_API_KEY in .env
```

### Step 2 — Build and run

```bash
docker-compose up --build
```

That's it. Docker handles everything:

| Service | URL |
|---------|-----|
| Streamlit Frontend | http://localhost:8501 |
| FastAPI Backend | http://localhost:8000 |
| Swagger API Docs | http://localhost:8000/docs |

### Stop the stack

```bash
docker-compose down
```

### Persistent data

The SQLite audit database is stored in a Docker volume (`db_data`) — your audit history survives container restarts.

```bash
# View volumes
docker volume ls

# Remove everything including data
docker-compose down -v
```

---

## 📁 Project Structure

```
EquiGuard/
│
├── 🔧 audit_engine/                  # Core ML + compliance engine
│   ├── certificate.py                # EEOC compliance certificate (fpdf2)
│   ├── compliance.py                 # aif360 disparate impact + SHAP
│   ├── intersectional.py             # Multi-attribute intersectional audit
│   ├── mitigation.py                 # Proxy removal + model retraining
│   ├── model_registry.py             # 4-model Pareto comparison registry
│   ├── model_runner.py               # sklearn pipeline training + inference
│   ├── proxy_hunter.py               # FeatureAgglomeration proxy detection
│   ├── report_gen.py                 # Executive summary PDF (fpdf2)
│   └── simulator.py                  # What-if mitigation simulator
│
├── 🌐 backend/                       # FastAPI REST API
│   ├── main.py                       # App factory + router registration
│   ├── alerting.py                   # Slack webhook alert system
│   ├── config.py                     # lru_cache settings from .env
│   ├── dependencies.py               # API key auth middleware
│   └── routers/
│       ├── audit.py                  # All /audit/* endpoints
│       ├── google_ai.py              # Gemini + Vision AI endpoints
│       └── health.py                 # Health check endpoints
│
├── 🎨 frontend/                      # Streamlit dashboard
│   ├── app.py                        # Main app + navigation
│   ├── utils.py                      # API client + Gemini column suggester
│   ├── components.py                 # Plotly gauge, SHAP, drift charts
│   └── views/
│       ├── hero.py                   # Landing hero page
│       ├── dashboard.py              # KPI dashboard
│       ├── audit_engine.py           # Main audit UI
│       ├── bias_leaderboard.py       # Temporal drift leaderboard
│       ├── comparison.py             # Multi-model Pareto chart
│       ├── intersectional.py         # Intersectional heatmap + AI summary
│       └── vision_scanner.py         # Image demographic scanner
│
├── 🗄️ database/
│   └── db.py                         # SQLite audit log (write + read)
│
├── 📊 data/
│   └── golden_demo_dataset.csv       # Synthetic demo dataset
│
├── 🧪 tests/
│   └── test_equiguard.py             # pytest test suite
│
├── 📜 scripts/
│   └── generate_golden_data.py       # Demo dataset generator
│
├── ⚙️ .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions CI pipeline
│
├── .env.example                      # Environment variable template
├── Dockerfile                        # Multi-service Docker image
├── docker-compose.yml                # Full stack orchestration
└── requirements.txt                  # Pinned Python dependencies
```

---

## 🔬 Full Audit Walkthrough

Here's exactly what happens when you run a full audit through the UI.

### 1. Upload Your Dataset

Go to **Audit Engine** in the sidebar. Upload any CSV with:
- A binary outcome column (hired/not hired, loan approved/denied, etc.)
- At least one protected attribute column (race, gender, age group, etc.)

**Gemini auto-suggests** which columns to use based on your data — you just confirm.

### 2. Run the Pre-Processing Scan

Click **"Scan for Proxy Variables"**.

EquiGuard runs `FeatureAgglomeration` to cluster your features, then computes Pearson correlation between each cluster and the protected attribute. Any cluster with `|r| ≥ 0.15` is flagged.

Example output:
```
⚠ Flagged: zip_code  |r| = 0.61  — HIGH correlation with race
⚠ Flagged: school    |r| = 0.34  — MODERATE correlation with race
✓ Clean:   income    |r| = 0.08
✓ Clean:   age       |r| = 0.11
```

### 3. Run the Compliance Audit

Click **"Run EEOC Audit"**.

The engine:
1. Trains a `LogisticRegression` pipeline (Imputer → Scaler → Classifier)
2. Splits 80/20 train/test
3. Computes EEOC metrics via aif360:
   - **Disparate Impact Ratio** = unprivileged selection rate / privileged selection rate
   - **Equal Opportunity Difference**
   - **Average Odds Difference**
4. Runs SHAP LinearExplainer for feature attribution
5. Returns pass/fail + top 5 bias drivers

**PASS** = ratio ≥ 0.80 (EEOC 4/5ths rule, 29 CFR § 1607)

### 4. Read the Gemini Risk Narrative

Click **"Generate Legal Narrative"**.

Gemini 2.5 Flash writes a 3-paragraph CCO-ready legal risk assessment:
- Paragraph 1: What the audit found (exact numbers)
- Paragraph 2: What it means under 29 CFR § 1607
- Paragraph 3: Recommended immediate actions

### 5. Mitigate (if FAIL)

If your audit fails, click **"Run Mitigation"**.

EquiGuard:
1. Drops all flagged proxy variables
2. Retrains the model on the clean feature set
3. Re-audits automatically
4. Reports the new fairness ratio and accuracy delta

### 6. Download Your Compliance Package

If the model passes:
- 📄 **Executive PDF Report** — 4-section audit summary with charts
- 🏆 **EEOC Compliance Certificate** — UUID-stamped, print-ready
- 📦 **Regulatory ZIP** — report + certificate + methodology + JSON log

<!-- ═══════════════════════════════════════════════ -->
<!-- WALKTHROUGH SCREENSHOTS — replace with yours -->
<!-- ═══════════════════════════════════════════════ -->

> **📸 Walkthrough screenshots**
> ```
> Step 2 — Proxy scan results
> ![Proxy Scan](docs/assets/proxy-scan.png)
>
> Step 3 — EEOC audit result + SHAP chart
> ![EEOC Audit](docs/assets/eeoc-audit.png)
>
> Step 6 — Compliance certificate
> ![Certificate](docs/assets/certificate.png)
> ```

---

## 📡 API Reference

All endpoints except `/` and `/health` require the `X-API-Key` header.

```bash
X-API-Key: your-secret-key-from-.env
```

### Core Audit Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check — returns env and status |
| `GET` | `/health` | Liveness probe for Docker/load balancers |
| `POST` | `/audit/model` | Train model, return accuracy + predictions |
| `POST` | `/audit/compliance` | Full EEOC audit — fairness ratio, pass/fail, SHAP |
| `POST` | `/audit/preprocess` | Scan dataset for proxy variables |
| `POST` | `/audit/mitigate` | Drop proxies, retrain, re-audit |
| `POST` | `/audit/simulate` | What-if simulator — project ratio per feature drop |
| `POST` | `/audit/intersectional` | Multi-attribute intersectional audit |
| `POST` | `/audit/compare` | Train 4 models, return Pareto comparison |

### Reporting & Export Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/audit/export` | Download executive summary PDF |
| `GET` | `/audit/history` | Full audit log from SQLite |
| `POST` | `/audit/certificate` | Generate EEOC compliance certificate PDF |
| `POST` | `/audit/package` | Download full regulatory ZIP |

### Google AI Endpoints

| Method | Endpoint | Powered By | Description |
|--------|----------|-----------|-------------|
| `POST` | `/audit/narrative` | Gemini 2.5 Flash | Generate 3-paragraph legal risk narrative |
| `POST` | `/audit/vision` | Cloud Vision AI | Scan image for demographic data leakage |
| `POST` | `/audit/remediate` | Vertex AI | Generate 3 bias mitigation code strategies |

### Example: Full compliance audit

```bash
curl -X POST http://localhost:8000/audit/compliance \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "data_path": "data/golden_demo_dataset.csv",
    "target_col": "loan_approved",
    "protected_col": "race"
  }'
```

**Response:**

```json
{
  "compliance_pass": true,
  "fairness_ratio": 0.8412,
  "top_biased_feature": "zip_code",
  "group_a_rate": 0.72,
  "group_b_rate": 0.61,
  "shap_summary": {
    "zip_code": 0.183,
    "income": 0.094,
    "priors_count": 0.071,
    "age": 0.043,
    "c_charge_degree": 0.021
  },
  "equal_opportunity_diff": -0.031,
  "avg_odds_diff": -0.028
}
```

### Example: Proxy variable scan

```bash
curl -X POST http://localhost:8000/audit/preprocess \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "data_path": "data/golden_demo_dataset.csv",
    "target_col": "loan_approved",
    "protected_col": "race"
  }'
```

**Response:**

```json
{
  "proxies_detected": true,
  "flagged_columns": ["zip_code", "school_district"]
}
```

> 📖 **Interactive API docs** (Swagger UI) at `http://localhost:8000/docs`

---

## ⚙️ Environment Variables

Copy `.env.example` → `.env` and fill in your values.

### Required

| Variable | Description |
|----------|-------------|
| `EQUIGUARD_API_KEY` | Strong secret key — protects every audit endpoint. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `development` | `development` or `production` |
| `HOST` | `127.0.0.1` | Bind address for uvicorn |
| `PORT` | `8000` | Port for FastAPI backend |
| `API_BASE_URL` | `http://127.0.0.1:8000` | Where Streamlit reaches the backend. In Docker this is set to `http://backend:8000` automatically |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///equiguard.db` | SQLite path (local dev) |
| `DATA_DIR` | project root | Directory for `equiguard.db` |
| `DATABASE_PATH` | — | Full path override (takes precedence) |

### Google AI (optional — all degrade gracefully)

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Powers narrative generation + AI column suggester + intersectional summary. Get from [aistudio.google.com](https://aistudio.google.com/apikey) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON key. Powers Cloud Vision AI |
| `GCP_PROJECT_ID` | Your GCP project ID. Powers Vertex AI remediation |
| `GCP_LOCATION` | GCP region (default: `us-central1`) |

### Alerting (optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBHOOK_ENABLED` | `false` | Set `true` to enable Slack alerts on FAIL |
| `WEBHOOK_URL` | — | Slack Incoming Webhook URL or any HTTP endpoint |

---

## 🤖 Google AI Setup

All three Google AI features degrade gracefully when not configured — the app never crashes.

### Feature 1: Gemini Risk Narrative + AI Column Suggester

**Time to set up: 2 minutes**

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Create API Key**
3. Add to `.env`:
   ```env
   GEMINI_API_KEY=AIza...your-key-here
   ```

That's it. Gemini 2.5 Flash powers both the legal risk narrative and the CSV column auto-detection.

---

### Feature 2: Cloud Vision AI (Image Demographic Scanner)

**Time to set up: 5 minutes**

#### Step 1 — Create or select a GCP project

Go to [console.cloud.google.com](https://console.cloud.google.com)

#### Step 2 — Enable the Vision API

```
APIs & Services → Enable APIs → search "Cloud Vision API" → Enable
```

#### Step 3 — Create a service account

```
IAM & Admin → Service Accounts → Create Service Account
Name: equiguard-sa
Role: Cloud Vision API User
```

#### Step 4 — Download the key

```
Service Account → Keys tab → Add Key → JSON
Save as: gcp-credentials.json  (in project root)
```

> ⚠️ **Never commit this file.** Add it to `.gitignore`.

#### Step 5 — Configure `.env`

```env
GOOGLE_APPLICATION_CREDENTIALS=./gcp-credentials.json
```

---

### Feature 3: Vertex AI Remediation Agent

Same service account as Vision AI, just add the additional role:

```
IAM & Admin → Service Accounts → your equiguard-sa account
Add role: Vertex AI User
```

Then configure `.env`:

```env
GOOGLE_APPLICATION_CREDENTIALS=./gcp-credentials.json
GCP_PROJECT_ID=your-project-id-here
GCP_LOCATION=us-central1
```

Enable the API:
```
APIs & Services → Enable APIs → search "Vertex AI API" → Enable
```

---

### Degradation behaviour

| Missing credential | What happens |
|-------------------|-------------|
| No `GEMINI_API_KEY` | Narrative returns a plain-text template. Column suggester returns first columns as fallback. |
| No `GOOGLE_APPLICATION_CREDENTIALS` | Vision scanner returns `{"risk_level": "UNKNOWN"}` with a clear error message |
| No `GCP_PROJECT_ID` | Remediation returns parameterised Python template code (still useful) |

---

## 🔔 Webhook Alerting

When a compliance audit **fails**, EquiGuard fires an outbound POST to your webhook URL before the API response returns.

### Setup

```env
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../xxx
```

### Payload format (Slack-compatible)

```json
{
  "text": "⚠️ EquiGuard EEOC Alert: Model FAILED Compliance Audit\nFairness Ratio: 0.6821 (threshold: 0.80)",
  "attachments": [{
    "color": "danger",
    "fields": [
      { "title": "Fairness Ratio", "value": "0.6821 (threshold: 0.80)", "short": true },
      { "title": "Top Bias Driver", "value": "zip_code", "short": true },
      { "title": "Privileged Group Rate", "value": "74.2%", "short": true },
      { "title": "Unprivileged Group Rate", "value": "50.6%", "short": true },
      { "title": "Timestamp", "value": "2025-04-24T14:32:01", "short": false }
    ]
  }]
}
```

Works with **Slack**, **Microsoft Teams** (with adapter), **Discord** (with Slack-compat mode), **PagerDuty**, or any endpoint that accepts a POST with JSON.

Alerting **never crashes the audit** — if the webhook fails, the audit response is still returned normally.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

### What's covered

```
tests/test_equiguard.py

  ✓ Bias score is a float in [0, 1]
  ✓ Disparate impact ratio calculation correctness
  ✓ EEOC threshold: ratio 0.81 → PASS
  ✓ EEOC threshold: ratio 0.79 → FAIL
  ✓ EEOC boundary: exactly 0.80 → PASS
  ✓ Single demographic group (no comparison) → ratio = 1.0
  ✓ Mitigation reduces bias score vs. baseline
  ✓ Proxy hunter detects engineered correlated feature
  ✓ Model pipeline returns correct type (sklearn Pipeline)
  ✓ Audit log round-trip via SQLite
  ✓ POST /audit/model → 200 + accuracy key
  ✓ POST /audit/compliance → 200 + fairness_ratio key
  ✓ GET /audit/history → 200 + history list
  ✓ POST /audit/preprocess → 200 + flagged_columns key
  ✓ POST /audit/mitigate → 200 + compliance_pass key
  ✓ No API key → 403
  ✓ Wrong API key → 403
```

### Run with coverage report

```bash
pytest tests/ -v --cov=audit_engine --cov=backend --cov-report=term-missing
```

---

## 🧰 Tech Stack

| Layer | Library | Version | Purpose |
|-------|---------|---------|---------|
| **Backend** | FastAPI | 0.68+ | Async REST API with auto-generated OpenAPI docs |
| **Frontend** | Streamlit | 1.0+ | Dark enterprise dashboard UI |
| **ML** | scikit-learn | latest | Training pipelines: Imputer → Scaler → Classifier |
| **Fairness** | IBM aif360 | latest | EEOC metrics: disparate impact, equal opportunity |
| **Explainability** | SHAP | 0.49+ | Linear + Tree explainers, mean |SHAP| attribution |
| **Visualisation** | Plotly | latest | Bias drift, SHAP waterfall, Pareto scatter |
| **PDF** | fpdf2 | latest | Executive reports + compliance certificates |
| **Database** | SQLite | built-in | Audit log persistence |
| **AI — Text** | google-genai | 1.73.1 | Gemini 2.5 Flash (narrative, column suggester) |
| **AI — Vision** | google-cloud-vision | 3.13.0 | Demographic data leakage detection |
| **AI — Code** | google-cloud-aiplatform | 1.148.1 | Vertex AI remediation agent |
| **Auth** | python-dotenv | latest | `.env` config + API key middleware |
| **Containers** | Docker + compose | latest | One-command reproducible deployment |
| **CI** | GitHub Actions | latest | pytest on every push to `main` |

---

## 🤝 Contributing

Contributions are welcome. Here's the workflow:

1. **Fork** the repository and create a branch from `main`

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with clear, atomic commits

3. **Add or update tests** in `tests/test_equiguard.py` to cover your changes

4. **Run the test suite** and make sure everything passes

   ```bash
   pytest tests/ -v
   ```

5. **Open a pull request** with:
   - A concise description of what changed and why
   - Screenshots if it's a UI change
   - Reference to any related issues

> For significant changes (new endpoints, new ML methods, architectural changes) — please open an issue first to discuss the approach before writing code.

### Good first issues

- Add k-fold cross-validation to `model_runner.py` (replace single `train_test_split`)
- Add test coverage for `simulator.py` and `intersectional.py`
- Add a `POST /audit/preflight` endpoint powered by Gemini for pre-flight dataset analysis
- Improve the EEOC certificate to include the Equal Opportunity Difference metric

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

```
MIT License — Copyright (c) 2025 Utkarsha

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 📸 Media Placeholders

*Replace these with your actual screenshots and videos.*

```
docs/
└── assets/
    ├── hero-dashboard.png         # Main dashboard screenshot
    ├── audit-flow-demo.gif        # Animated audit walkthrough
    ├── proxy-scan.png             # Proxy variable scan results
    ├── eeoc-audit.png             # EEOC audit result + SHAP chart
    ├── shap-waterfall.png         # SHAP feature waterfall chart
    ├── certificate.png            # EEOC compliance certificate
    ├── leaderboard.png            # Bias drift leaderboard
    ├── vision-scanner.png         # Visual bias scanner
    ├── pareto-chart.png           # Multi-model Pareto comparison
    ├── video-thumbnail.png        # YouTube video thumbnail
    └── quickstart.gif             # 60-second quickstart demo
```

To add a screenshot:
```markdown
![Dashboard](docs/assets/hero-dashboard.png)
```

To embed a YouTube demo:
```markdown
[![Watch the demo](docs/assets/video-thumbnail.png)](https://youtu.be/YOUR_VIDEO_ID)
```

---

<div align="center">

<br/>

**Built with purpose. Bias is a legal risk — not just an ethical one.**

<br/>

*EquiGuard — because the time to find bias is before deployment, not during a deposition.*

<br/>

⭐ **Star this repo if EquiGuard helped you ship fairer models** ⭐

<br/>

[![GitHub stars](https://img.shields.io/github/stars/Utkarsha1024/EquiGuard?style=social)](https://github.com/Utkarsha1024/EquiGuard)
[![GitHub forks](https://img.shields.io/github/forks/Utkarsha1024/EquiGuard?style=social)](https://github.com/Utkarsha1024/EquiGuard/fork)

</div>