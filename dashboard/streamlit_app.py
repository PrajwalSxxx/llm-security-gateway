import json
import os
import urllib.request

import streamlit as st


st.set_page_config(page_title="Offline LLM Runtime Security", page_icon="🛡️", layout="wide")
st.title("Offline LLM Runtime Security Gateway")
api = st.sidebar.text_input("FastAPI URL", os.getenv("BACKEND_URL", "http://127.0.0.1:8000"))
mode = st.sidebar.selectbox("Execution mode", ["PROTECTED", "VULNERABLE"])
use_rag = st.sidebar.checkbox("Use local semantic RAG", value=False)


def get(path):
    return json.loads(urllib.request.urlopen(api + path, timeout=10).read())


try:
    status = get("/local-status")
    st.sidebar.success("LOCAL / OFFLINE READY")
    st.sidebar.write(f"LLM Provider: {status['provider']}")
    st.sidebar.write(f"Model: {status['models'][-1] if status['models'] else 'unknown'}")
    st.sidebar.write(f"Connection: LOCAL ({status['endpoint']})")
    st.sidebar.write("Internet Dependency: DISABLED")
    st.sidebar.write(f"Offline Mode: {'ON' if status['offline_mode'] else 'OFF'}")
except Exception as exc:
    st.sidebar.error(f"Ollama/backend unavailable: {exc}")

try:
    metrics = get("/metrics")
    st.subheader("Cumulative Metrics")
    columns = st.columns(6)
    columns[0].metric("Requests", metrics["total_requests"])
    columns[1].metric("Tool Calls", metrics["total_tool_calls"])
    columns[2].metric("Allowed", metrics["actions_allowed"])
    columns[3].metric("Blocked", metrics["actions_blocked"])
    columns[4].metric("Threats", metrics["threats_detected"])
    columns[5].metric("Average Risk", metrics["average_risk_score"])
except Exception:
    st.info("Start the backend to load metrics.")

request = st.text_area("User request", "What is the capital of France?")
content_path = None if document == "None" else document

if st.button("Run local agent", type="primary"):
    payload = json.dumps({"user_request": request, "content_path": content_path, "use_rag": use_rag, "mode": mode}).encode()
    req = urllib.request.Request(api + "/run", data=payload, headers={"Content-Type": "application/json"})
    try:
        result = json.loads(urllib.request.urlopen(req, timeout=600).read())
        st.subheader("Agent response")
        st.write(result.get("answer", ""))
        st.subheader("Execution trace")
        for event in result.get("events", []):
            decision = event.get("decision", {})
            st.json({"source": event.get("source"), "tool": event.get("tool"), "capabilities": event.get("capabilities"),
                     "data_class": event.get("data_class"), "risk": decision.get("risk_score"),
                     "risk_components": decision.get("risk_components"), "policies": decision.get("reasons"),
                     "tdg": decision.get("tdg_path"), "decision": decision.get("decision"),
                     "execution_result": event.get("execution_result")})
            if decision.get("decision") == "REQUIRE_APPROVAL":
                if st.button("Approve action", key="approve-" + result["session_id"]):
                    approved = get("/approve/" + result["session_id"])
                    st.success(json.dumps(approved))
        if result.get("retrieved"):
            st.subheader("Retrieved provenance")
            st.json(result["retrieved"])
    except Exception as exc:
        st.error(f"Request failed: {exc}")

if st.button("Verify tamper-evident audit chain"):
    st.json(get("/audit/verify"))
