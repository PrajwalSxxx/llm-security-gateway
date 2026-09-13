import json
import os
import urllib.request

import streamlit as st


st.set_page_config(page_title="LLM Runtime Security", page_icon="🛡️", layout="wide")
st.title("LLM Runtime Security Gateway")
api = st.sidebar.text_input("Backend URL", os.getenv("BACKEND_URL", "http://127.0.0.1:8000"))
mode = st.sidebar.selectbox("Security mode", ["PROTECTED", "SAFE_MOCK", "VULNERABLE"])
try:
    metrics = json.loads(urllib.request.urlopen(api + "/metrics", timeout=10).read())
    st.subheader("Cumulative security metrics")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Requests", metrics["total_requests"])
    metric_cols[1].metric("Tool calls", metrics["total_tool_calls"])
    metric_cols[2].metric("Blocked", metrics["actions_blocked"])
    metric_cols[3].metric("Threats", metrics["threats_detected"])
except Exception:
    st.info("Start the backend to load cumulative metrics.")
request = st.text_area("User request", "Read report.txt and summarize it.")
document = st.selectbox("Document", ["report.txt", "malicious_document.txt", "vendor_email.txt", "repository_readme.txt"])
if st.button("Run agent"):
    payload = json.dumps({"user_request": request, "content_path": document, "mode": mode}).encode()
    req = urllib.request.Request(api + "/run", data=payload, headers={"Content-Type": "application/json"})
    try:
        result = json.loads(urllib.request.urlopen(req, timeout=10).read())
        st.json(result)
        decisions = [item["decision"] for item in result["results"]]
        cols = st.columns(4)
        cols[0].metric("Tool calls", len(decisions))
        cols[1].metric("Blocked", sum(d.get("decision") == "BLOCK" for d in decisions))
        cols[2].metric("Allowed", sum(d.get("decision") == "ALLOW" for d in decisions))
        cols[3].metric("Threats", sum(d.get("risk_score", 0) >= 61 for d in decisions))
    except Exception as exc:
        st.error(f"Backend unavailable: {exc}")
st.subheader("Recent tamper-evident audit events")
if st.button("Refresh audit"):
    try:
        st.json(json.loads(urllib.request.urlopen(api + "/audit", timeout=10).read()))
    except Exception as exc:
        st.error(str(exc))
