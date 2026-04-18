# EquiGuard: AI Bias Firewall

![CI](https://github.com/Utkarsha1024/EquiGuard/actions/workflows/ci.yml/badge.svg)
![Static Badge](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-0.89+-red.svg)

## The Problem
Companies deploy AI models that contain hidden demographic biases, exposing them to lawsuits. 

## The Solution
EquiGuard is an enterprise AI Bias Firewall. It intercepts automated decisions, mathematically audits them against US EEOC compliance laws, identifies the exact neural pathways causing the bias, and autonomously retrains the model to safely pass compliance.

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
