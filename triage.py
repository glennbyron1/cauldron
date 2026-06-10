#!/usr/bin/env python3
"""triage.py - send recent Wazuh alerts to a local Ollama model for triage.

Reads Wazuh's alerts.json (one JSON object per line), filters by alert level,
asks the local LLM for a short structured analysis of each, and writes a
markdown report. All inference is on-prem via the lab Ollama endpoint.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime

import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://10.10.20.30:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

PROMPT = """You are a SOC analyst assistant. Analyze this Wazuh alert and reply in EXACTLY this format:

SUMMARY: <one sentence, plain English, what happened>
LIKELY SEVERITY: <low|medium|high> - <one-sentence why>
NEXT CHECKS: <2-3 short concrete things a human should verify>
FALSE POSITIVE LIKELIHOOD: <low|medium|high> - <one-sentence why>

Be concise. Do not invent details not present in the alert.

ALERT JSON:
{alert}
"""


def load_alerts(path: str, limit: int, min_level: int) -> list[dict]:
    alerts: list[dict] = []
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                a = json.loads(line)
            except json.JSONDecodeError:
                continue
            level = int(a.get("rule", {}).get("level", 0))
            if level >= min_level:
                alerts.append(a)
    return alerts[-limit:]  # newest at the end of the file


def slim(alert: dict) -> dict:
    """Trim the alert to the fields that matter so the prompt stays small."""
    rule = alert.get("rule", {})
    return {
        "timestamp": alert.get("timestamp"),
        "agent": alert.get("agent", {}).get("name"),
        "rule_id": rule.get("id"),
        "level": rule.get("level"),
        "description": rule.get("description"),
        "groups": rule.get("groups"),
        "full_log": (alert.get("full_log") or "")[:800],
        "src_ip": alert.get("data", {}).get("srcip"),
        "user": alert.get("data", {}).get("dstuser"),
    }


def ask_ollama(alert: dict) -> str:
    body = {
        "model": MODEL,
        "prompt": PROMPT.format(alert=json.dumps(slim(alert), indent=2)),
        "stream": False,
        "options": {"temperature": 0.2},  # low temp: analysis, not creativity
    }
    r = requests.post(f"{OLLAMA_URL}/api/generate", json=body, timeout=120)
    r.raise_for_status()
    return r.json().get("response", "").strip()


def main() -> None:
    p = argparse.ArgumentParser(description="AI triage for Wazuh alerts (local Ollama)")
    p.add_argument("--alerts", default="/var/ossec/logs/alerts/alerts.json")
    p.add_argument("--limit", type=int, default=10, help="max alerts to triage")
    p.add_argument("--min-level", type=int, default=7, help="min Wazuh level")
    p.add_argument("--out", default="triage-report.md")
    args = p.parse_args()

    try:
        alerts = load_alerts(args.alerts, args.limit, args.min_level)
    except FileNotFoundError:
        sys.exit(f"Alerts file not found: {args.alerts}")

    if not alerts:
        print("No alerts at/above the level threshold. Nothing to triage.")
        return

    lines = [f"# AI Triage Report - {datetime.now():%Y-%m-%d %H:%M}",
             f"_Model: {MODEL} @ {OLLAMA_URL} - {len(alerts)} alert(s), "
             f"level >= {args.min_level}._",
             "",
             "> AI-assisted analysis. **Verify before acting** - the model "
             "explains and suggests; it does not decide.",
             ""]

    for i, alert in enumerate(reversed(alerts), 1):  # newest first
        s = slim(alert)
        print(f"[{i}/{len(alerts)}] {s['rule_id']} {s['description']!r} ...")
        try:
            analysis = ask_ollama(alert)
        except requests.RequestException as e:
            analysis = f"(Ollama unreachable: {e})"
        lines += [f"## {i}. [{s['timestamp']}] {s['description']}",
                  f"- **Agent:** {s['agent']}  -  **Rule:** {s['rule_id']}  "
                  f"-  **Wazuh level:** {s['level']}",
                  "", analysis, "", "---", ""]

    with open(args.out, "w") as fh:
        fh.write("\n".join(lines))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
