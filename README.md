# EquiGuard: AI Bias Firewall

## Problem Statement

As artificial intelligence systems increasingly automate high-stakes decisions—from loan approvals to hiring and criminal justice—they run the profound risk of amplifying historical biases. An unmonitored model can inadvertently learn proxies for protected attributes, systematically discriminating against specific demographic groups. Not only does this cause severe societal harm, but it also exposes enterprises to significant legal liability, regulatory fines (such as under the EU AI Act), and irreversible brand damage.

## Solution

**EquiGuard** acts as an enterprise-grade AI Bias Firewall. It intercepts, audits, and mitigates automated decisions before deployment using a robust three-layered defense system:

1. **Pre-Processing (Proxy Hunter)**: Utilizes Hierarchical Clustering (`sklearn.cluster.FeatureAgglomeration`) to analyze the dataset prior to training. It mathematically detects combinations of supposedly "safe" variables that correlate heavily with protected attributes (hidden proxies) and flags them for removal.
2. **Post-Processing (Compliance Auditing)**: Evaluates the trained model's predictions against established legal frameworks. It automatically calculates selection rates and strictly enforces the **US EEOC 4/5ths Rule**, guaranteeing demographic parity across all outputs.
3. **Explainability (SHAP Analysis)**: Integrated with SHAP (`LinearExplainer`), the firewall provides deep transparency into the model's decision-making process. By surfacing the top biased features driving unequal outcomes, it transforms black-box algorithms into interpretable, actionable insights.

## Architecture Stack

EquiGuard is built on a modern, highly scalable Python stack:
- **FastAPI**: Asynchronous, high-performance backend routing engine for rapid model inference and compliance checks.
- **Streamlit**: Dynamic frontend UI leveraging custom Material You styling for a premium dashboard experience.
- **Scikit-Learn**: Core machine learning framework for training predictive pipelines and clustering proxies.
- **SHAP**: State-of-the-art explainability library to decode feature importance and detect bias drivers.
- **SQLite**: Lightweight persistence layer to track temporal bias drift and maintain the 'Bias Leaderboard' over time.

## Quickstart / Local Deployment

Follow these commands to deploy the EquiGuard firewall locally:

1. **Activate the Virtual Environment**:
   ```bash
   source equiguard_env/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the Backend API** (in Terminal 1):
   ```bash
   uvicorn backend.main:app --reload
   ```

4. **Launch the Frontend Dashboard** (in Terminal 2):
   ```bash
   streamlit run frontend/app.py
   ```

You can now access the EquiGuard platform via your browser at `http://localhost:8501`.
