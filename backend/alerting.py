"""
backend/alerting.py
Fires a Slack-compatible webhook alert when an EEOC audit fails.
Never raises — alerting must never crash the audit flow.
"""
import requests
from datetime import datetime


def fire_audit_alert(audit_result: dict, settings: dict) -> bool:
    """
    POSTs a Slack-compatible webhook payload if WEBHOOK_ENABLED=true
    and WEBHOOK_URL is configured.
    Returns True on success, False silently on any failure.
    """
    if not settings.get("webhook_enabled") or not settings.get("webhook_url"):
        return False

    ratio      = audit_result.get("fairness_ratio", 0.0)
    top_feat   = audit_result.get("top_biased_feature", "Unknown")
    group_a    = audit_result.get("group_a_rate", 0.0)
    group_b    = audit_result.get("group_b_rate", 0.0)
    timestamp  = datetime.now().isoformat()

    payload = {
        "text": (
            f"⚠️ *EquiGuard EEOC Alert: Model FAILED Compliance Audit*\n"
            f"Fairness Ratio: `{ratio:.4f}` (threshold: `0.80`)"
        ),
        "attachments": [
            {
                "color": "danger",
                "fields": [
                    {
                        "title": "Fairness Ratio",
                        "value": f"{ratio:.4f} (threshold: 0.80)",
                        "short": True,
                    },
                    {
                        "title": "Top Bias Driver",
                        "value": top_feat,
                        "short": True,
                    },
                    {
                        "title": "Privileged Group Rate",
                        "value": f"{group_a * 100:.1f}%",
                        "short": True,
                    },
                    {
                        "title": "Unprivileged Group Rate",
                        "value": f"{group_b * 100:.1f}%",
                        "short": True,
                    },
                    {
                        "title": "Timestamp",
                        "value": timestamp,
                        "short": False,
                    },
                ],
            }
        ],
    }

    try:
        resp = requests.post(
            settings["webhook_url"],
            json=payload,
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False
