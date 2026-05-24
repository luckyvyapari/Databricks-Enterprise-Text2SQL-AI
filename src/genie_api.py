"""
src/genie_api.py
================
Handles all communication with the Databricks Genie REST API.
Three steps: start conversation → poll for answer → extract result.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../config/.env"))

DATABRICKS_HOST  = os.getenv("DATABRICKS_HOST", "").rstrip("/")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
GENIE_SPACE_ID   = os.getenv("GENIE_SPACE_ID", "")


def _headers():
    return {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type":  "application/json",
    }


def validate_credentials():
    """Returns (is_valid: bool, error_message: str)"""
    missing = [k for k, v in {
        "DATABRICKS_HOST":  DATABRICKS_HOST,
        "DATABRICKS_TOKEN": DATABRICKS_TOKEN,
        "GENIE_SPACE_ID":   GENIE_SPACE_ID,
    }.items() if not v]

    if missing:
        return False, f"Missing in .env file: {', '.join(missing)}"
    return True, ""


def ask_genie(question: str, max_wait: int = 90) -> dict:
    """
    Full flow: send question → poll → return result dict with keys:
        answer   (str)  — human-readable answer from Genie
        sql      (str)  — SQL query Genie wrote (empty string if none)
        error    (str)  — error message if something went wrong (empty if ok)
        status   (str)  — "ok" or "error"
    """
    # ── Step 1: Start conversation ────────────────────────────────────────────
    try:
        start_url = (
            f"{DATABRICKS_HOST}/api/2.0/genie/spaces"
            f"/{GENIE_SPACE_ID}/start-conversation"
        )
        r = requests.post(
            start_url,
            headers=_headers(),
            json={"content": question},
            timeout=30,
        )
    except requests.exceptions.ConnectionError:
        return _err(f"Cannot connect to {DATABRICKS_HOST}. Check DATABRICKS_HOST in .env.")
    except requests.exceptions.Timeout:
        return _err("Connection timed out. Try again.")

    if r.status_code == 401:
        return _err("Token rejected (401). Regenerate your token in Settings → Developer.")
    if r.status_code == 404:
        return _err(f"Genie Space '{GENIE_SPACE_ID}' not found (404). Check GENIE_SPACE_ID in .env.")
    if r.status_code != 200:
        return _err(f"API error {r.status_code}: {r.text[:300]}")

    data = r.json()
    conv_id = data.get("conversation_id") or data.get("id", "")
    msg_id  = (data.get("message_id")
               or data.get("message", {}).get("id", ""))

    if not conv_id or not msg_id:
        return _err(f"Unexpected start-conversation response: {data}")

    # ── Step 2: Poll until answer is ready ────────────────────────────────────
    poll_url = (
        f"{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}"
        f"/conversations/{conv_id}/messages/{msg_id}"
    )
    elapsed = 0
    interval = 2

    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval

        pr = requests.get(poll_url, headers=_headers(), timeout=30)
        if pr.status_code != 200:
            return _err(f"Poll error {pr.status_code}: {pr.text[:300]}")

        msg = pr.json()
        status = msg.get("status", "").upper()

        if status == "COMPLETED":
            answer, sql = _extract(msg)
            return {"status": "ok", "answer": answer, "sql": sql, "error": ""}

        if status == "FAILED":
            err = msg.get("error", {}).get("message", "Genie returned FAILED.")
            return _err(err)

    return _err(
        f"Genie did not respond in {max_wait}s. "
        "Try attaching a dedicated SQL Warehouse in Genie Space → Settings → Compute."
    )


def _extract(msg: dict) -> tuple:
    """Pull answer text and SQL from the message attachments."""
    answer, sql = "", ""
    for att in msg.get("attachments", []):
        if "text" in att:
            block = att["text"]
            answer = block.get("content", "") if isinstance(block, dict) else str(block)
        if "query" in att:
            block = att["query"]
            sql = block.get("query", "") if isinstance(block, dict) else str(block)
    if not answer:
        answer = msg.get("content", "No answer returned.")
    return answer.strip(), sql.strip()


def _err(message: str) -> dict:
    return {"status": "error", "answer": "", "sql": "", "error": message}
