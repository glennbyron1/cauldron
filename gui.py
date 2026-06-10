#!/usr/bin/env python3
"""Cauldron GUI - view AI triage reports + interactive one-off triage.

Run:  streamlit run gui.py
Needs: pip install streamlit requests
Report viewer works offline with the test fixture; the interactive tab needs
an Ollama endpoint (OLLAMA_URL env, default the lab AI node).
"""
import glob
import json
import os

import requests
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://10.10.20.30:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

st.set_page_config(page_title="Cauldron", page_icon="🪄", layout="wide")
st.title("🪄 Cauldron — AI Alert Triage")
st.caption(f"Alerts in, analysis out. Self-hosted inference: {MODEL} @ {OLLAMA_URL}")

tab_reports, tab_live = st.tabs(["📜 Triage reports", "⚗️ Brew one now"])

with tab_reports:
    reports = sorted(
        glob.glob(os.path.join(HERE, "*.md")) +
        glob.glob(os.path.join(HERE, "test", "*.md")),
        key=os.path.getmtime, reverse=True)
    reports = [r for r in reports if "README" not in r]
    if not reports:
        st.info("No triage reports yet — run triage.py first (see TESTING.md).")
    else:
        pick = st.selectbox("Report", reports,
                            format_func=os.path.basename)
        with open(pick) as fh:
            st.markdown(fh.read())

with tab_live:
    st.write("Paste a single Wazuh alert (JSON) and brew an analysis.")
    raw = st.text_area("Alert JSON", height=200,
                       placeholder='{"rule":{"id":"5710","level":10,...}}')
    if st.button("Brew 🫧") and raw.strip():
        try:
            alert = json.loads(raw)
        except json.JSONDecodeError as e:
            st.error(f"Not valid JSON: {e}")
            st.stop()
        prompt = ("You are a SOC analyst assistant. Analyze this Wazuh alert. "
                  "Reply with: SUMMARY, LIKELY SEVERITY, NEXT CHECKS, "
                  "FALSE POSITIVE LIKELIHOOD. Be concise; invent nothing.\n\n"
                  + json.dumps(alert, indent=2))
        with st.spinner("Stirring the cauldron..."):
            try:
                r = requests.post(f"{OLLAMA_URL}/api/generate", timeout=120,
                                  json={"model": MODEL, "prompt": prompt,
                                        "stream": False,
                                        "options": {"temperature": 0.2}})
                r.raise_for_status()
                st.markdown(r.json().get("response", "(empty response)"))
                st.caption("AI-assisted — verify before acting.")
            except requests.RequestException as e:
                st.error(f"Ollama unreachable: {e}")
                st.caption("Start Ollama locally and set OLLAMA_URL=http://localhost:11434 to test without the lab.")
