import os
import json
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE    = os.getenv("API_BASE_URL", "http://backend:8000") # Need to support docker network
_API_KEY    = os.getenv("EQUIGUARD_API_KEY", "")
API_HEADERS = {"X-API-Key": _API_KEY} if _API_KEY else {}

def api_get(path: str):
    return requests.get(f"{API_BASE}{path}", headers=API_HEADERS)

def api_post(path: str, json_data: dict):
    return requests.post(f"{API_BASE}{path}", json=json_data, headers=API_HEADERS)

def get_kpi_values():
    res = st.session_state.audit_result
    if res is None:
        return {"ratio": "—", "status": "Pending", "feature": "—", "passed": "—"}
    return {
        "ratio": f"{res.get('fairness_ratio', 0):.2f}",
        "status": "PASS" if res.get("compliance_pass") else "FAIL",
        "feature": res.get("top_biased_feature", "N/A"),
        "passed": "Yes" if res.get("compliance_pass") else "No"
    }


def suggest_columns(df: pd.DataFrame) -> dict:
    """
    Uses Gemini 2.5 Flash to suggest the best target_col and protected_col
    for an EEOC bias audit, given a DataFrame.

    Returns a dict with keys:
      - target_col      (str)
      - protected_col   (str)
      - target_reason   (str)
      - protected_reason (str)

    Falls back to the first column silently on any failure.
    """
    columns = df.columns.tolist()
    fallback = {
        "target_col":       columns[0],
        "protected_col":    columns[0],
        "target_reason":    "",
        "protected_reason": "",
    }
    if not columns:
        return fallback

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        return fallback

    # Build a compact column profile for the prompt
    col_profile = []
    for col in columns:
        dtype    = str(df[col].dtype)
        n_unique = int(df[col].nunique())
        sample   = df[col].dropna().head(5).tolist()
        top_vals = df[col].value_counts().head(5).to_dict()
        col_profile.append({
            "name":     col,
            "dtype":    dtype,
            "n_unique": n_unique,
            "sample":   [str(s) for s in sample],
            "top_values": {str(k): int(v) for k, v in top_vals.items()},
        })

    prompt = (
        "You are an EEOC bias-audit expert. Given the following dataset column profiles, "
        "identify the most likely target column (the outcome to predict, e.g. hired/loan_approved) "
        "and the most likely protected attribute (e.g. race, gender, age group).\n\n"
        "Return ONLY a valid JSON object with exactly these keys:\n"
        "{\n"
        '  "target_col": "<column name>",\n'
        '  "protected_col": "<column name>",\n'
        '  "target_reason": "<one sentence>",\n'
        '  "protected_reason": "<one sentence>"\n'
        "}\n\n"
        "Column profiles:\n" + json.dumps(col_profile, indent=2) + "\n\n"
        "Return ONLY valid JSON. No markdown, no explanation outside the JSON."
    )

    try:
        from google import genai as _genai
        _client = _genai.Client(api_key=gemini_key)
        resp = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw = resp.text.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        data = json.loads(raw)

        # Validate that suggested columns actually exist
        suggested_target    = data.get("target_col", columns[0])
        suggested_protected = data.get("protected_col", columns[0])
        if suggested_target not in columns:
            suggested_target = columns[0]
        if suggested_protected not in columns:
            suggested_protected = columns[0]

        return {
            "target_col":       suggested_target,
            "protected_col":    suggested_protected,
            "target_reason":    data.get("target_reason", ""),
            "protected_reason": data.get("protected_reason", ""),
        }
    except Exception:
        return fallback
