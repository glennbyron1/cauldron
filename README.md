# Cauldron — Wazuh Alerts → Local LLM Triage

Pulls recent Wazuh alerts and sends them to the lab's self-hosted Ollama endpoint (the GPU node) for plain-English triage: what happened, how severe it likely is, and what to check next. All inference stays on-prem — no alert data leaves the network.

This demonstrates *building with* AI, not just hosting it: a practical SOC-assist tool wired to self-hosted infrastructure, which is exactly the on-prem/air-gap-friendly AI pattern relevant to defense environments.

## Architecture

```
Wazuh manager (10.10.20.25)
   alerts.json ──► triage.py ──► Ollama API (10.10.20.30:11434)
                                     └─► llama3.1:8b on the 2060 Super
                      └─► triage-report.md  (alert + AI analysis, newest first)
```

Simplest data path: run this ON the Wazuh box and read
`/var/ossec/logs/alerts/alerts.json` directly (tail of recent alerts).
Roadmap: switch to the Wazuh API for remote pulls.

## Usage

```bash
pip install --break-system-packages requests
python3 triage.py --alerts /var/ossec/logs/alerts/alerts.json --limit 10
cat triage-report.md
```

Env/flags:
- `OLLAMA_URL` (default `http://10.10.20.30:11434`)
- `OLLAMA_MODEL` (default `llama3.1:8b`)
- `--min-level 7` — only triage Wazuh alerts at level ≥ 7 (skip noise)

## Honest framing (important for interviews)

- The LLM **assists** triage; it does not replace judgment. Models can be wrong or overconfident — every output says "verify before acting."
- An 8B model is good at summarizing/explaining and suggesting next checks; it is NOT a detection engine. Detection is Wazuh's job; explanation is the model's.
- Sending security logs to a *local* model is the point — the same workflow with a cloud API would leak alert contents off-network.

## Roadmap

- [ ] Wazuh API instead of local file read
- [ ] "STIG finding explainer" mode: paste a finding ID, get plain-English remediation
- [ ] Severity disagreement flag: when the model's assessment differs from Wazuh's level, highlight for human review

## GUI

```bash
pip install streamlit pandas requests --break-system-packages
streamlit run gui.py
```
Opens a local dashboard on :8501. Works against the included test data.
