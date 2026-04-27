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
![Gemini](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-8E75B2?logo=google&logoColor=white)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-22c55e)

<br/>

<!-- ══════════════════════════════════════════════════════════ -->
<!--              HERO IMAGE — drop your screenshot here       -->
<!-- ══════════════════════════════════════════════════════════ -->

> ### 📸 Dashboard Preview
> ```
> Replace with your actual screenshot:
> ![EquiGuard Dashboard](docs/assets/hero-dashboard.png)
> ```
>
> ### 🎬 60-Second Demo
> ```
> [![Watch the demo](docs/assets/video-thumbnail.png)](https://youtu.be/YOUR_VIDEO_ID)
> ```

<br/>

</div>

---

## 📋 Table of Contents

<details>
<summary><b>Click to expand full contents</b></summary>

| # | Section |
|---|---------|
| 1 | [Why EquiGuard Exists](#-why-equiguard-exists) |
| 2 | [What It Does](#-what-it-does) |
| 3 | [Feature Breakdown](#-feature-breakdown) |
| 4 | [Architecture](#-architecture) |
| 5 | [Project Structure](#-project-structure) |
| 6 | [Quickstart — Local](#-quickstart--local-in-5-minutes) |
| 7 | [Run with Docker](#-run-with-docker) |
| 8 | [Step-by-Step Audit Walkthrough](#-step-by-step-audit-walkthrough) |
| 9 | [UI Pages Guide](#-ui-pages-guide) |
| 10 | [API Reference](#-api-reference) |
| 11 | [Environment Variables](#-environment-variables) |
| 12 | [Google AI Setup](#-google-ai-setup) |
| 13 | [Webhook Alerting](#-webhook-alerting) |
| 14 | [Running Tests](#-running-tests) |
| 15 | [Tech Stack](#-tech-stack) |
| 16 | [Known Issues & Fixes](#-known-issues--fixes) |
| 17 | [Contributing](#-contributing) |

</details>

---

## ⚡ Why EquiGuard Exists

Every day, companies deploy AI models that quietly discriminate.

A loan approval model trained on historical data learns from decades of redlining. It never explicitly looks at race — but it uses **zip code** as a proxy. A hiring model never checks gender — but it penalises **employment gaps**. The model gets deployed. Thousands of real decisions are made. Nobody notices.

Until the lawsuit.

> *The average employment discrimination class-action settlement in the US is **$2.7 million**. The average cost of finding bias before deployment is near zero.*

**Most bias detection tools are retrospective** — they analyse models after deployment, after real people have been harmed, after regulators are involved. EquiGuard is different. It's a **firewall** — it sits between your model and production and blocks non-compliant models before a single decision reaches a real person.

---

## 🛡️ What It Does

EquiGuard runs a complete bias audit pipeline — from raw CSV to compliance certificate — in a single button click:

```
① Upload CSV
      ↓
② Gemini Pre-flight Scan ──── AI flags sensitive columns before any training
      ↓
③ Proxy Hunter ──────────────  FeatureAgglomeration + Pearson correlation
                                detects hidden proxies (zip_code, school, name…)
      ↓
④ Model Training ────────────  sklearn Pipeline: Imputer → Scaler → Classifier
      ↓
⑤ EEOC Compliance Audit ─────  IBM aif360: Disparate Impact Ratio,
                                Equal Opportunity Difference,
                                Average Odds Difference
      ↓
⑥ SHAP Explainability ───────  LinearExplainer → top 5 bias drivers
      ↓
⑦ Pass / Fail Decision
      │
      ├── FAIL ──→  Fire Slack webhook alert
      │             Autonomous mitigation: drop proxies → retrain → re-audit
      │
      └── PASS ──→  Log to SQLite
                    Executive PDF Report
                    EEOC Compliance Certificate
                    Regulatory ZIP Package
```

---

## ✨ Feature Breakdown

### 🔍 Bias Detection & Auditing

| Feature | How it works |
|---------|-------------|
| **Gemini Pre-flight Scan** | Before any training, Gemini 2.0 Flash-Lite analyses your column statistics and flags sensitive columns, proxy candidates, and overall risk level |
| **Proxy Variable Detection** | `FeatureAgglomeration` clusters features hierarchically, then Pearson correlation identifies clusters correlated with protected attributes (`\|r\| ≥ 0.15`) |
| **EEOC 4/5ths Rule Audit** | IBM aif360 `BinaryLabelDataset` + `ClassificationMetric` computes disparate impact ratio. Threshold: **≥ 0.80** per 29 CFR § 1607 |
| **Extended aif360 Metrics** | Equal Opportunity Difference and Average Odds Difference returned when available |
| **SHAP Explainability** | `shap.LinearExplainer` on the sklearn pipeline. Returns mean `\|SHAP\|` per feature — waterfall chart shows exactly which features drive bias |
| **Intersectional Audit** | Audits **every detected demographic attribute** simultaneously. A model can PASS for race while FAILing for gender — this catches it |
| **Multi-Model Pareto** | Trains Logistic Regression, Random Forest, Gradient Boosting, and Decision Tree simultaneously. Plots accuracy vs. fairness to find the optimal model |
| **What-If Simulator** | Drops each feature one-by-one, retrains, and projects the resulting fairness ratio — shows which single removal gives the biggest compliance gain |

<br/>

<!-- ══════════════════════════════════════════════════════════ -->
<!--           AUDIT RESULTS SCREENSHOT — drop here           -->
<!-- ══════════════════════════════════════════════════════════ -->

> ### 📸 Audit Engine
> ```
> ![Audit Engine](docs/assets/audit-engine.png)
> ```

<br/>

### 🤖 Google AI Integrations

All six AI features degrade gracefully — the app **never crashes** when credentials are missing.

| Feature | Model | What it does | Fallback |
|---------|-------|-------------|---------|
| **Gemini Pre-flight** | `gemini-2.0-flash-lite` | Analyses column stats → flags risks before training | Keyword heuristics (age, zip, race, gender…) |
| **Gemini Column Suggester** | `gemini-2.0-flash-lite` | Reads CSV schema → auto-suggests target and protected columns | First column as default |
| **Gemini Risk Narrative** | `gemini-2.0-flash` | Writes 3-paragraph CCO-ready legal risk assessment | Plain-text template |
| **Gemini Remediation Agent** | `gemini-2.0-flash` | 3 production-ready Python mitigation strategies with full code (3 retry attempts on 429) | Parameterised code template |
| **Visual Bias Scanner** | `gemini-2.0-flash` multimodal | Scans uploaded images for faces and demographic signals | `UNKNOWN` risk level |
| **Intersectional AI Summary** | `gemini-2.0-flash-lite` | Narrates the correlation heatmap — identifies proxies and recommends mitigations (3 retries with exponential back-off) | Button disabled with `.env` prompt |

<br/>

<!-- ══════════════════════════════════════════════════════════ -->
<!--          GEMINI NARRATIVE SCREENSHOT — drop here         -->
<!-- ══════════════════════════════════════════════════════════ -->

> ### 📸 Gemini Risk Narrative
> ```
> ![Gemini Narrative](docs/assets/gemini-narrative.png)
> ```

<br/>

### 📊 Reporting & Compliance Outputs

| Output | Format | Contents |
|--------|--------|---------|
| **Executive PDF Report** | `.pdf` | EEOC status, proxy scan results, selection rate bar chart, SHAP waterfall chart, feature impact table |
| **EEOC Compliance Certificate** | `.pdf` | UUID-stamped, print-ready. Fairness ratio, group rates, SHAP primary driver, criteria checklist, full metadata |
| **Regulatory ZIP Package** | `.zip` | Executive report + certificate + methodology.txt + audit_log.json |

<br/>

<!-- ══════════════════════════════════════════════════════════ -->
<!--        CERTIFICATE + REPORT SCREENSHOTS — drop here      -->
<!-- ══════════════════════════════════════════════════════════ -->

> ### 📸 Compliance Certificate
> ```
> ![Certificate](docs/assets/certificate.png)
> ```

<br/>

### 🚨 Real-Time Webhook Alerting

When a compliance audit **fails**, EquiGuard immediately fires a Slack-compatible POST to your configured webhook URL. The alert includes fairness ratio, top bias driver, group selection rates, and timestamp. **Alerting never crashes an audit** — exceptions are silently swallowed and return `False`.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Streamlit Frontend                             │
│                  Dark enterprise dashboard · port 8501               │
│                                                                      │
│  🏠 Dashboard  ⚙️ Audit Engine  📊 Bias Leaderboard                 │
│  ⧡ Model Compare  ⬢ Intersectional  ◎ Vision Scanner               │
│  Hero page on first load (animated, dismissable)                    │
│                                                                      │
│  MagicBento: spotlight hover · card tilt · GSAP particle effects    │
│  GradualBlur: CSS backdrop-filter injected via st.markdown JS        │
└────────────────────────────┬─────────────────────────────────────────┘
                             │  HTTP · X-API-Key header
┌────────────────────────────▼─────────────────────────────────────────┐
│                        FastAPI Backend                               │
│                   REST API · port 8000 · /docs                       │
│                                                                      │
│  Routers: health · audit (16 endpoints) · google_ai (3 endpoints)   │
│  Auth: APIKeyHeader dependency injected per route                    │
│  Alerting: Slack-compatible webhook fires on FAIL                    │
└────────┬──────────────────┬─────────────────┬────────────────────────┘
         │                  │                 │
┌────────▼──────┐  ┌────────▼──────┐  ┌───────▼────────────────────┐
│  audit_engine │  │  database/    │  │    Google AI (Gemini)       │
│               │  │               │  │                             │
│ model_runner  │  │  SQLite via   │  │  gemini-2.0-flash-lite      │
│ compliance    │  │  db.py        │  │  → pre-flight, column       │
│ proxy_hunter  │  │               │  │    suggest, ix summary      │
│ mitigation    │  │  audit_history│  │                             │
│ simulator     │  │  table with   │  │  gemini-2.0-flash           │
│ intersectional│  │  file_name    │  │  → narrative, remediation   │
│ model_registry│  │  per run      │  │  → vision (multimodal)      │
│ report_gen    │  └───────────────┘  └─────────────────────────────┘
│ certificate   │
└───────────────┘
```

---

## 📁 Project Structure

```
EquiGuard/
│
├── 🔧 audit_engine/                   Core ML + fairness engine
│   ├── __init__.py
│   ├── certificate.py                 EEOC compliance certificate (fpdf2)
│   ├── compliance.py                  aif360 disparate impact + SHAP explainer
│   ├── intersectional.py              Multi-attribute intersectional audit
│   ├── mitigation.py                  Proxy removal + model retraining
│   ├── model_registry.py              4-model Pareto (LR, RF, GB, DT)
│   ├── model_runner.py                sklearn pipeline: Imputer→Scaler→LogReg
│   ├── proxy_hunter.py                FeatureAgglomeration + Pearson proxy scan
│   ├── report_gen.py                  Executive PDF (fpdf2 + matplotlib)
│   └── simulator.py                   Per-feature what-if mitigation simulator
│
├── 🌐 backend/                        FastAPI REST API
│   ├── __init__.py
│   ├── main.py                        App factory + router registration
│   ├── alerting.py                    Slack-compatible webhook on FAIL
│   ├── config.py                      lru_cache settings from .env
│   ├── dependencies.py                X-API-Key auth middleware
│   └── routers/
│       ├── audit.py                   All /audit/* endpoints (16 total)
│       ├── google_ai.py               Gemini narrative, vision, remediation
│       └── health.py                  GET / and GET /health
│
├── 🎨 frontend/                       Streamlit dashboard
│   ├── app.py                         Main entry: session state, global CSS,
│   │                                  GradualBlur, MagicBento tracker, routing
│   ├── utils.py                       API client + Gemini column suggester
│   ├── components.py                  Plotly gauge, SHAP waterfall, bias drift,
│   │                                  Uiverse download button component
│   └── views/
│       ├── hero.py                    Animated hero page (st.iframe)
│       ├── dashboard.py               KPI cards + live backend status probe
│       ├── audit_engine.py            Full audit UI: upload → pre-flight →
│       │                              proxy scan → compliance → SHAP →
│       │                              narrative → mitigation → export
│       ├── bias_leaderboard.py        Temporal drift chart + audit history table
│       ├── comparison.py              Multi-model Pareto scatter chart
│       ├── intersectional.py          Heatmap + per-attribute badges + AI summary
│       └── vision_scanner.py          Image upload + Gemini demographic scanner
│
├── 🗄️ database/
│   └── db.py                          SQLite audit log: init_db, log_audit_run,
│                                      get_audit_history (file_name col per run)
│
├── 📊 data/
│   └── golden_demo_dataset.csv        Synthetic demo (COMPAS → loan approval)
│
├── 🧪 tests/
│   └── test_equiguard.py              pytest suite (18+ tests)
│
├── 📜 scripts/
│   └── generate_golden_data.py        Fetches COMPAS + transforms → demo CSV
│
├── ⚙️ .github/
│   └── workflows/ci.yml               GitHub Actions: pytest on push to main
│
├── .env.example                       All env vars documented with examples
├── Dockerfile                         python:3.11-slim, uv resolver,
│                                      non-root user equiguard, exposes 8000+8501
├── docker-compose.yml                 backend + frontend + db_data volume
└── requirements.txt                   Pinned Google Cloud transitive deps
```

---

## 🚀 Quickstart — Local (in 5 minutes)

### Prerequisites

- Python **3.11**
- Git

### 1 — Clone

```bash
git clone https://github.com/Utkarsha1024/EquiGuard.git
cd EquiGuard
```

### 2 — Virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> ⏱️ First install takes 3–5 minutes — the ML stack (scikit-learn, SHAP, aif360, Google Cloud) is substantial.

### 4 — Configure environment

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```env
EQUIGUARD_API_KEY=your-strong-secret-here
```

Generate a cryptographically secure key instantly:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5 — Generate the demo dataset

```bash
python scripts/generate_golden_data.py
```

This fetches the public COMPAS dataset, transforms it into a loan approval scenario, and saves `data/golden_demo_dataset.csv`.

### 6 — Start both services

**Terminal 1 — FastAPI backend:**

```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Streamlit frontend:**

```bash
streamlit run frontend/app.py
```

### 7 — Open

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8501 |
| Swagger API docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

<br/>

<!-- ══════════════════════════════════════════════════════════ -->
<!--          QUICKSTART GIF — record and drop here           -->
<!-- ══════════════════════════════════════════════════════════ -->

> ### 🎬 Quickstart Demo
> ```
> ![Quickstart](docs/assets/quickstart.gif)
> ```

---

## 🐳 Run with Docker

One command spins the full stack. No Python setup required.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running

### Steps

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and set EQUIGUARD_API_KEY

# 2. Build and start
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Streamlit Frontend | http://localhost:8501 |
| FastAPI Backend | http://localhost:8000 |
| Swagger API Docs | http://localhost:8000/docs |

```bash
# Stop
docker-compose down

# Stop and wipe the audit database
docker-compose down -v
```

### What Docker does under the hood

- Builds a single `python:3.11-slim` image shared by both services
- Uses **`uv`** (Rust-based pip resolver) — handles deep Google Cloud dependency graphs without `pip`'s resolution-too-deep error
- Runs as a non-root user `equiguard` for security
- Stores SQLite in a named `db_data` volume — **audit history survives container restarts**
- The frontend's `API_BASE_URL` is automatically set to `http://backend:8000` via Docker's internal network
- The backend health check (`GET /health`) gates frontend startup — frontend waits until backend is ready

---

## 🔬 Step-by-Step Audit Walkthrough

Here is exactly what happens when you run a full audit.

### Step 1 — The Hero Page

On first load you see the animated hero with a live audit stream animation (canvas particle network, pulsing shield, real-time log lines). Click **"Enter EquiGuard"** to proceed.

### Step 2 — Upload Your Dataset

Navigate to **Audit Engine** in the sidebar. Two options:

**Option A — Demo dataset:** Click *"Use Demo Dataset"* to load `golden_demo_dataset.csv`. Pre-configured with `target_col=loan_approved`, `protected_col=race`.

**Option B — Your own CSV:** Drag and drop any binary classification CSV. EquiGuard handles string or numeric labels in any target column.

> After upload, **Gemini auto-suggests** which column is the target and which is the protected attribute, with a one-sentence explanation for each. You can override either with the dropdowns.

### Step 3 — Pre-flight Dataset Check

Click **"⚡ Pre-flight Dataset Check"**.

Gemini 2.0 Flash-Lite samples up to 500 rows, analyses column statistics (dtype, n_unique, top values), and returns:

```json
{
  "overall_risk": "HIGH",
  "high_risk_columns": ["race"],
  "proxy_candidates": ["priors_count", "juv_fel_count"],
  "summary": "Dataset contains a direct demographic identifier...",
  "engine": "gemini-2.0-flash-lite",
  "columns_checked": 6,
  "rows_sampled": 500
}
```

The UI renders an overall risk badge and lists flagged columns as coloured pills.

### Step 4 — Proxy Variable Scan

Click **"Scan for Proxy Variables"**.

`proxy_hunter.py`:
1. Scales numeric features with `StandardScaler`
2. Clusters with `FeatureAgglomeration` (hierarchical, up to 5 clusters)
3. Computes Pearson correlation between each cluster centroid and the protected attribute
4. Flags every feature in clusters where `|r| ≥ 0.15`

Example output:
```
⚠ Flagged: priors_count   |r| = 0.47  MODERATE proxy for race
⚠ Flagged: juv_fel_count  |r| = 0.31  MODERATE proxy for race
✓ Clean:   age             |r| = 0.09
✓ Clean:   c_charge_degree |r| = 0.06
```

### Step 5 — Run the EEOC Compliance Audit

Click **"Run EEOC Audit"**.

`compliance.py`:
1. Trains a `LogisticRegression` pipeline (Imputer → Scaler → Classifier), 80/20 split
2. IBM aif360 metrics:
   - **Disparate Impact Ratio** = unprivileged_rate / privileged_rate (PASS if ≥ 0.80)
   - **Equal Opportunity Difference** (TPR gap between groups)
   - **Average Odds Difference** (mean FPR + TPR gap)
3. `shap.LinearExplainer` → top 5 features by mean `|SHAP|`

The result card shows the fairness gauge, SHAP waterfall chart, group selection rates, and the aif360 metric set.

### Step 6 — Read the AI Risk Narrative

Click **"✨ Generate Gemini Risk Narrative"**.

Gemini 2.0 Flash writes a 3-paragraph legal assessment:
- **Paragraph 1:** What the audit found (exact numbers cited)
- **Paragraph 2:** What it means legally under 29 CFR § 1607
- **Paragraph 3:** Recommended immediate actions

Falls back to a plain-text template if `GEMINI_API_KEY` is not set.

### Step 7 — Mitigate (if FAIL)

Click **"Run Mitigation"**. `mitigation.py` drops all flagged proxy columns and retrains. Shows:
- New fairness ratio vs. baseline
- Accuracy delta (the fairness-accuracy trade-off)
- Whether the retrained model passes EEOC

Then click **"✨ Generate Remediation Strategies"** for Gemini to write 3 production-ready Python code strategies with exponential back-off on rate limits.

### Step 8 — Download Compliance Package

If your model passes:

| Download | Contents |
|----------|---------|
| **Executive Report** | PDF: EEOC status, proxy results, charts, SHAP table |
| **Compliance Certificate** | UUID-stamped PDF, ready for regulators |
| **Regulatory Package** | ZIP: report + certificate + methodology.txt + audit_log.json |

---

## 🖥️ UI Pages Guide

### 🏠 Dashboard

- **4 KPI cards**: Fairness Ratio · EEOC Status · Top Bias Driver · Compliance Passed
- **Live backend status**: probes `GET /health` on load — green dot if online, red if offline
- **System status panel**: API · EEOC Engine · SHAP Explainer · Alerting

<br/>

> ```
> ![Dashboard](docs/assets/dashboard.png)
> ```

<br/>

### ⚙️ Audit Engine

The main workspace. Full workflow from upload to export. See the [walkthrough](#-step-by-step-audit-walkthrough).

Key UI elements:
- Dataset selector (upload or demo) with Gemini column auto-suggestion
- Pre-flight risk badge + flagged column pills
- Proxy scan results with correlation values
- EEOC result with fairness gauge + SHAP waterfall chart
- Gemini narrative text card
- Mitigation diff: before vs. after fairness ratio
- Gemini remediation code (3 strategies, markdown rendered)
- Uiverse animated download buttons for PDF/certificate/ZIP

### 📊 Bias Leaderboard

- **Temporal Bias Drift**: Plotly area+line chart of fairness ratio over time. PASS = green dot, FAIL = red X. EEOC threshold dotted line at 0.80. Latest audits show most recent file name.
- **Audit History Table**: Every run reverse-chronological with timestamp, ratio, PASS/FAIL badge.
- **Mitigation Impact**: Side-by-side before/after comparison of the last two runs.

<br/>

> ```
> ![Leaderboard](docs/assets/bias-leaderboard.png)
> ```

<br/>

### ⧡ Model Comparison

Trains 4 classifier families simultaneously and plots a **Pareto scatter chart** (accuracy vs. fairness ratio). The gold star ★ marks the recommended model — highest fairness among passing models, or highest accuracy if all fail.

| Model | Key hyperparameters |
|-------|-------------------|
| Logistic Regression | `max_iter=1000` |
| Random Forest | `n_estimators=100` |
| Gradient Boosting | default sklearn params |
| Decision Tree | `max_depth=5` |

<br/>

> ```
> ![Model Comparison](docs/assets/model-comparison.png)
> ```

<br/>

### ⬢ Intersectional Audit

Detects all candidate protected columns (categorical or low-cardinality integer, 2–10 unique values) and:
1. Runs an EEOC audit for each detected attribute individually
2. Renders a **compliance badge** per attribute (PASS/FAIL/N/A + ratio)
3. Renders a **Pearson correlation heatmap** (numeric features × protected attributes)
   - `|r| > 0.15` = potential proxy (proxy hunter threshold, shown as amber)
   - `|r| > 0.50` = high risk (shown as red)
4. AI summary via Gemini (3 retries, exponential back-off on 503/429)

<br/>

> ```
> ![Intersectional Audit](docs/assets/intersectional.png)
> ```

<br/>

### ◎ Vision Scanner

Upload any image (JPG, PNG, WEBP). EquiGuard sends it to Gemini 2.0 Flash multimodal with a structured prompt. Returns:

| Field | Values |
|-------|--------|
| `risk_level` | `CRITICAL` / `LOW` / `UNKNOWN` |
| `risk_score` | 95 if CRITICAL, 10 if LOW |
| `faces_detected` | 1 if CRITICAL, 0 if LOW |
| `compliance_warning` | GDPR Article 9 / EEOC risk statement |
| `recommendation` | Actionable next step |

**Use case:** Resume scanners, KYC systems, and hiring tools that process photos. Catches demographic data leakage before an image enters a scoring pipeline.

---

## 📡 API Reference

All endpoints except `GET /` and `GET /health` require:

```
X-API-Key: your-key-from-.env
```

### Health

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/` | — | Status check — returns env and uptime message |
| `GET` | `/health` | — | Liveness probe for Docker health checks |

### Core Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/audit/preflight` | Gemini pre-flight scan of dataset columns |
| `POST` | `/audit/model` | Train model, return accuracy + predictions |
| `POST` | `/audit/compliance` | Full EEOC audit — ratio, pass/fail, SHAP, aif360 metrics |
| `POST` | `/audit/preprocess` | Proxy variable scan |
| `POST` | `/audit/mitigate` | Drop proxies, retrain, re-audit |
| `POST` | `/audit/simulate` | Per-feature what-if mitigation simulator |
| `POST` | `/audit/intersectional` | Multi-attribute intersectional audit + correlations |
| `POST` | `/audit/compare` | 4-model Pareto comparison |

### Reports & Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/audit/export` | Download executive PDF report |
| `GET` | `/audit/history` | Full audit log from SQLite (includes `file_name` per run) |
| `POST` | `/audit/certificate` | EEOC compliance certificate PDF |
| `POST` | `/audit/package` | Regulatory ZIP: report + cert + methodology + JSON |

### Google AI

| Method | Endpoint | Model | Description |
|--------|----------|-------|-------------|
| `POST` | `/audit/narrative` | `gemini-2.0-flash` | 3-paragraph legal risk narrative |
| `POST` | `/audit/vision` | `gemini-2.0-flash` | Image demographic leakage scan |
| `POST` | `/audit/remediate` | `gemini-2.0-flash` | 3 bias mitigation code strategies |

### Example — Full compliance audit

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

### Example — Pre-flight scan

```bash
curl -X POST http://localhost:8000/audit/preflight \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"data_path": "data/golden_demo_dataset.csv"}'
```

**Response:**

```json
{
  "overall_risk": "HIGH",
  "high_risk_columns": ["race"],
  "proxy_candidates": ["priors_count", "juv_fel_count"],
  "summary": "The dataset contains a direct demographic identifier (race)...",
  "engine": "gemini-2.0-flash-lite",
  "columns_checked": 6,
  "rows_sampled": 500
}
```

> 📖 Full interactive docs at `http://localhost:8000/docs`

---

## ⚙️ Environment Variables

Copy `.env.example` → `.env` and fill in your values. Every variable is explained in `.env.example` with comments.

### Required

| Variable | Description |
|----------|-------------|
| `EQUIGUARD_API_KEY` | Strong random secret — protects all audit endpoints. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `development` | `development` or `production` |
| `HOST` | `127.0.0.1` | Bind address for uvicorn |
| `PORT` | `8000` | Backend port |
| `API_BASE_URL` | `http://127.0.0.1:8000` | Where Streamlit reaches the backend. Docker sets this to `http://backend:8000` automatically |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///equiguard.db` | Connection string |
| `DATA_DIR` | project root | Directory for `equiguard.db` |
| `DATABASE_PATH` | — | Full path override (takes precedence). Docker uses `/app/db_data/equiguard.db` |

### Google AI — all optional, all degrade gracefully

| Variable | Powers | Where to get it |
|----------|--------|----------------|
| `GEMINI_API_KEY` | Pre-flight · Column suggester · Narrative · Remediation · Vision · Intersectional summary | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON | GCP Console → IAM → Service Accounts → Keys |
| `GCP_PROJECT_ID` | GCP project identifier | GCP Console dashboard |
| `GCP_LOCATION` | GCP region | Default: `us-central1` |

### Alerting

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBHOOK_ENABLED` | `false` | Set `true` to enable alerts on FAIL |
| `WEBHOOK_URL` | — | Slack Incoming Webhook URL or any HTTP endpoint |

---

## 🤖 Google AI Setup

### Gemini API Key — 2 minutes

Everything powered by Gemini only needs this one key.

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Create API Key**
3. Add to `.env`:

```env
GEMINI_API_KEY=AIza...your-key
```

This unlocks all six AI features: pre-flight, column suggester, risk narrative, remediation code, visual scanner, and intersectional summary.

---

### GCP Service Account — 5 minutes (optional)

Only needed for Vertex AI integration. Gemini directly handles all current AI tasks.

**Step 1** — Create or select a GCP project at [console.cloud.google.com](https://console.cloud.google.com)

**Step 2** — Enable APIs:
```
APIs & Services → Enable APIs → Vertex AI API
```

**Step 3** — Create a service account:
```
IAM & Admin → Service Accounts → Create Service Account
Name: equiguard-sa
Role: Vertex AI User
```

**Step 4** — Download the key:
```
Service Account → Keys tab → Add Key → JSON
Save as: gcp-credentials.json  (project root)
```

> ⚠️ **Never commit this file.** Add `gcp-credentials.json` to `.gitignore`.

**Step 5** — Configure `.env`:
```env
GOOGLE_APPLICATION_CREDENTIALS=./gcp-credentials.json
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
```

---

### Degradation table

| Missing | Behaviour |
|---------|-----------|
| No `GEMINI_API_KEY` | Pre-flight → keyword heuristics · Column suggester → first columns · Narrative → template · Remediation → template code · Vision → `UNKNOWN` |
| No `GOOGLE_APPLICATION_CREDENTIALS` | No current impact — Vision uses Gemini multimodal, not Cloud Vision API |
| No `GCP_PROJECT_ID` | Vertex AI endpoints use Gemini fallback |

---

## 🔔 Webhook Alerting

```env
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../xxx
```

When any audit returns `compliance_pass: false`, `alerting.py` fires a POST **before** returning the API response:

```json
{
  "text": "⚠️ EquiGuard EEOC Alert: Model FAILED Compliance Audit\nFairness Ratio: 0.6821 (threshold: 0.80)",
  "attachments": [{
    "color": "danger",
    "fields": [
      { "title": "Fairness Ratio",         "value": "0.6821 (threshold: 0.80)", "short": true },
      { "title": "Top Bias Driver",         "value": "priors_count",            "short": true },
      { "title": "Privileged Group Rate",   "value": "72.1%",                   "short": true },
      { "title": "Unprivileged Group Rate", "value": "49.2%",                   "short": true },
      { "title": "Timestamp",              "value": "2025-04-27T14:32:01",      "short": false }
    ]
  }]
}
```

**Compatible with:** Slack · Microsoft Teams (with Slack adapter) · Discord (Slack-compat mode) · PagerDuty · any endpoint accepting POST JSON.

**Safety guarantee:** `alerting.py` wraps everything in `try/except Exception` and returns `False` silently. A broken webhook **never** crashes an audit.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

### Test coverage

```
tests/test_equiguard.py

  ✓ Bias score is a float in [0.0, 1.0]
  ✓ Disparate impact ratio calculation correctness
  ✓ EEOC threshold: ratio 0.81 → PASS
  ✓ EEOC threshold: ratio 0.79 → FAIL
  ✓ EEOC boundary: exactly 0.80 → PASS
  ✓ Single demographic group edge case → ratio = 1.0
  ✓ Mitigation reduces bias score vs. baseline
  ✓ Proxy hunter detects engineered correlated feature
  ✓ Model pipeline returns correct type (sklearn Pipeline)
  ✓ Audit log round-trip via SQLite (write + read)
  ✓ file_name column persisted in audit_history
  ✓ POST /audit/model → 200 + accuracy key
  ✓ POST /audit/compliance → 200 + fairness_ratio key
  ✓ GET /audit/history → 200 + history list
  ✓ POST /audit/preprocess → 200 + flagged_columns key
  ✓ POST /audit/mitigate → 200 + compliance_pass key
  ✓ No API key → 403
  ✓ Wrong API key → 403
```

### With coverage report

```bash
pytest tests/ -v --cov=audit_engine --cov=backend --cov-report=term-missing
```

---

## 🧰 Tech Stack

| Layer | Library | Version | Purpose |
|-------|---------|---------|---------|
| **Backend** | FastAPI | 0.68+ | Async REST API with auto-generated OpenAPI docs |
| **Frontend** | Streamlit | 1.0+ | Dark enterprise dashboard |
| **UI Effects** | GSAP | 3.12.2 | MagicBento: spotlight, card tilt, particle effects |
| **ML** | scikit-learn | latest | Imputer → Scaler → Classifier pipeline |
| **Fairness** | IBM aif360 | latest | Disparate impact, EOD, AOD via `ClassificationMetric` |
| **Explainability** | SHAP | 0.49+ | `LinearExplainer` + generic `Explainer` fallback |
| **Visualisation** | Plotly | latest | Bias drift, SHAP waterfall, Pareto scatter |
| **PDF** | fpdf2 | latest | Executive reports + compliance certificates |
| **Charts in PDF** | Matplotlib | latest | Bar charts saved as temp PNGs, embedded in PDF |
| **Database** | SQLite (built-in) | — | Audit log with `file_name` column per run |
| **AI — Text** | google-genai | 1.73.1 | Gemini 2.0 Flash / Flash-Lite |
| **AI — Multimodal** | google-genai | 1.73.1 | Gemini vision for image demographic scanning |
| **Auth** | python-dotenv | latest | `.env` config, `lru_cache` settings loader |
| **Containers** | Docker + compose | latest | One-command reproducible deployment |
| **Resolver** | uv | latest | Rust-based pip resolver (handles deep Google Cloud deps) |
| **CI** | GitHub Actions | latest | pytest on every push to `main` |

---

## 🐛 Known Issues & Fixes

### 1. `st.components.v1.html` deprecation warning

**Warning in logs:**
```
Please replace st.components.v1.html with st.iframe.
st.components.v1.html will be removed after 2026-06-01.
```

**Affected files and exact fixes:**

**`frontend/app.py`** — Two usages:

*`render_gradual_blur()` function (line ~133):*
```python
# Before
_components.html("<script>" + js + "</script>", height=0)

# After — script runs in the parent document directly, no iframe needed
st.markdown("<script>" + js + "</script>", unsafe_allow_html=True)
# Also change every  window.parent.document  →  document  in the JS string
```

*MagicBento tracker (line ~1366):*
```python
# Before
import streamlit.components.v1 as components
components.html("""<script>...(uses parentDoc = window.parent.document)...</script>""", height=0)

# After
st.markdown("""<script>...(replace parentDoc with doc = document)...</script>""", unsafe_allow_html=True)
```

**`frontend/views/hero.py`** (line 803):
```python
# Before
components.html(HERO_HTML, height=10000, scrolling=False)

# After — st.iframe does NOT support scrolling= argument
st.iframe(HERO_HTML, height=10000)
# scrolling=False effect is already achieved by overflow:hidden on the <body> in HERO_HTML
```

**`frontend/views/audit_engine.py`** (lines ~100, ~221):
```python
# Before
components.html("""<script>...(uses window.parent.document)...</script>""", height=0)

# After
st.markdown("""<script>...(replace window.parent.document with document)...</script>""", unsafe_allow_html=True)
```

**`frontend/components.py`** — `render_uiverse_download` (last few lines):
```python
# Before
st.components.v1.html(js, height=0)

# After
st.markdown(js, unsafe_allow_html=True)
# Also change window.parent.document → document in the js string
```

**The universal rule:** Scripts injected via `st.markdown(unsafe_allow_html=True)` run in the **current page document**, not inside an iframe. Replace every `window.parent.document` with `document`.

---

### 2. Duplicate routing at the bottom of `app.py`

Lines 1487–1489 repeat the Vision Scanner and Intersectional routing. Remove the duplicate block:

```python
# DELETE these duplicate lines:
elif st.session_state.active_page == "Vision Scanner":
    render_vision_scanner()
elif st.session_state.active_page == "Intersectional":
    render_intersectional()
```

---

### 3. Duplicate `return fig` in `components.py`

`render_bias_drift` ends with two consecutive `return fig` statements. The second one is unreachable — delete it.

---

## 📸 Media Placeholders

Create `docs/assets/` and drop your files. Replace the placeholder blocks throughout this README.

```
docs/assets/
  hero-dashboard.png        Full dashboard screenshot
  audit-engine.png          Audit Engine with results shown
  gemini-narrative.png      Gemini legal risk narrative panel
  certificate.png           EEOC compliance certificate PDF
  executive-report.png      Executive PDF report preview
  bias-leaderboard.png      Temporal drift chart + history table
  model-comparison.png      Multi-model Pareto scatter chart
  intersectional.png        Intersectional heatmap + badges
  vision-scanner.png        Visual bias scanner with results
  dashboard.png             KPI cards + status panel
  quickstart.gif            60-second screen recording
  video-thumbnail.png       YouTube demo video thumbnail
```

To add a screenshot inline:
```markdown
![Dashboard](docs/assets/dashboard.png)
```

To embed a YouTube demo:
```markdown
[![Watch the demo](docs/assets/video-thumbnail.png)](https://youtu.be/YOUR_VIDEO_ID)
```

---

## 🤝 Contributing

Contributions are welcome.

1. Fork and create a branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make clear, atomic commits

3. Add or update tests in `tests/test_equiguard.py`

4. Run the full suite:
   ```bash
   pytest tests/ -v
   ```

5. Open a pull request — describe what changed and why

> For significant changes, open an issue first to discuss the approach.

### Good first issues

- Fix `st.components.v1.html` deprecation in all affected files (see [Known Issues](#-known-issues--fixes))
- Remove duplicate routing blocks at the bottom of `app.py`
- Remove duplicate `return fig` in `components.py`
- Add k-fold cross-validation to `model_runner.py`
- Add test coverage for `simulator.py` and `intersectional.py`
- Add test for `audit_preflight` endpoint with mocked Gemini response

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

<br/>

**Built with purpose. Bias in AI is a legal risk — not just an ethical one.**

<br/>

*EquiGuard — because the time to find bias is before deployment, not during a deposition.*

<br/>

⭐ **If EquiGuard helped you ship a fairer model, star the repo** ⭐

<br/>

[![GitHub stars](https://img.shields.io/github/stars/Utkarsha1024/EquiGuard?style=social)](https://github.com/Utkarsha1024/EquiGuard)
[![GitHub forks](https://img.shields.io/github/forks/Utkarsha1024/EquiGuard?style=social)](https://github.com/Utkarsha1024/EquiGuard/fork)
[![GitHub issues](https://img.shields.io/github/issues/Utkarsha1024/EquiGuard?style=social)](https://github.com/Utkarsha1024/EquiGuard/issues)

<br/>

</div>