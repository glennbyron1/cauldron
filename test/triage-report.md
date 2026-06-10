# AI Triage Report - 2026-06-10 00:22
_Model: llama3.1:8b @ http://10.10.20.30:11434 - 2 alert(s), level >= 7._

> AI-assisted analysis. **Verify before acting** - the model explains and suggests; it does not decide.

## 1. [2026-06-09T22:20:11Z] Multiple Windows logon failures
- **Agent:** dc01  -  **Rule:** 60122  -  **Wazuh level:** 8

(Ollama unreachable: HTTPConnectionPool(host='10.10.20.30', port=11434): Max retries exceeded with url: /api/generate (Caused by ConnectTimeoutError(<HTTPConnection(host='10.10.20.30', port=11434) at 0x7fbeab4a1190>, 'Connection to 10.10.20.30 timed out. (connect timeout=120)')))

---

## 2. [2026-06-09T22:14:02Z] sshd: Attempt to login using a non-existent user
- **Agent:** gitlab  -  **Rule:** 5710  -  **Wazuh level:** 10

(Ollama unreachable: HTTPConnectionPool(host='10.10.20.30', port=11434): Max retries exceeded with url: /api/generate (Caused by ConnectTimeoutError(<HTTPConnection(host='10.10.20.30', port=11434) at 0x7fbeab4f6630>, 'Connection to 10.10.20.30 timed out. (connect timeout=120)')))

---
