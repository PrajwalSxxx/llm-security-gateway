import json
import os
import urllib.parse
import urllib.request

import streamlit as st


st.set_page_config(page_title="LLM Runtime Security Control Center", page_icon="🛡️", layout="wide")
API = st.sidebar.text_input("FastAPI URL", os.getenv("BACKEND_URL", "http://127.0.0.1:8000"))
PAGE_NAMES = ["Live Monitor", "Agent Console", "Threat Center", "Attack Simulator", "Tool Dependency Graph",
              "RAG Explorer", "Audit Explorer", "Policy Center", "Risk Analytics", "Evaluation", "System Health", "Settings", "Final Demo"]
page = st.sidebar.radio("Control Center", PAGE_NAMES)


def get(path):
    return json.loads(urllib.request.urlopen(API + path, timeout=20).read())


def post(path, payload):
    request = urllib.request.Request(API + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(request, timeout=600).read())


def run_console(default_request="What is the capital of France?", default_document=""):
    request = st.text_area("Natural-language request", default_request, key="request-" + page)
    content_path = st.text_input("Optional local path or sandbox document", default_document, key="path-" + page)
    mode = st.selectbox("Mode", ["PROTECTED", "VULNERABLE"], key="mode-" + page)
    use_rag = st.checkbox("Use local semantic RAG", value=bool(content_path), key="rag-" + page)
    if st.button("Run local agent", type="primary", key="run-" + page):
        try:
            result = post("/run", {"user_request": request, "content_path": content_path or None, "use_rag": use_rag, "mode": mode})
            st.session_state["last_result"] = result
        except Exception as exc:
            st.error(f"Request failed: {exc}")
    result = st.session_state.get("last_result")
    if result:
        st.subheader("Final answer")
        st.write(result.get("answer", ""))
        render_trace(result)


def render_trace(result):
    if result.get("retrieved"):
        with st.expander("Retrieved provenance", expanded=True):
            st.json(result["retrieved"])
    if result.get("events"):
        st.subheader("Live agent trace")
        stages = ["USER REQUEST", "LOCAL OLLAMA", "AGENT DECISION", "TOOL PROPOSAL", "SECURITY GATEWAY", "INTENT / PROVENANCE / RISK / POLICY / TDG", "TOOL RESULT"]
        st.write("  ↓  ".join("✓ " + stage for stage in stages[:]))
        for index, event in enumerate(result["events"], 1):
            decision = event.get("decision", {})
            st.markdown(f"**Action {index}: `{event.get('tool')}` | `{decision.get('decision')}` | risk `{decision.get('risk_score', 0)}`**")
            st.json({"source": event.get("source"), "arguments": event.get("arguments"),
                     "capabilities": event.get("capabilities"), "data_class": event.get("data_class"),
                     "risk_components": decision.get("risk_components"), "reasons": decision.get("reasons"),
                     "tdg": decision.get("tdg_path"), "execution_result": event.get("execution_result")})
            if decision.get("decision") == "REQUIRE_APPROVAL":
                if st.button("Approve action", key=f"approve-{result['session_id']}-{index}"):
                    try:
                        st.success(json.dumps(post("/approve/" + result["session_id"], {})))
                    except Exception as exc:
                        st.error(str(exc))


def metrics_cards():
    metrics = get("/metrics")
    cols = st.columns(7)
    labels = [("Requests", "total_requests"), ("Tool Calls", "total_tool_calls"), ("Allowed", "actions_allowed"),
              ("Blocked", "actions_blocked"), ("Approval", "approval_required"), ("Threats", "threats_detected"), ("Avg Risk", "average_risk_score")]
    for column, (label, key) in zip(cols, labels):
        column.metric(label, metrics.get(key, 0))


def live_monitor():
    st.title("LLM Runtime Security Control Center")
    st.caption("Live Monitor | Ollama local model | Internet dependency disabled")
    try:
        metrics_cards()
        events = get("/audit?limit=20")["events"]
        st.subheader("Recent security events")
        for event in events:
            payload = json.loads(event["payload"]) if isinstance(event.get("payload"), str) else event.get("payload", {})
            decision = payload.get("decision", {})
            st.write(f"{event['timestamp']} | {decision.get('decision', event['event'])} | {payload.get('tool', event['event'])} | risk {decision.get('risk_score', 0)}")
    except Exception as exc:
        st.error(f"Backend unavailable: {exc}")


def threat_center():
    st.title("Threat Center")
    try:
        events = get("/audit?limit=200")["events"]
        filter_decision = st.selectbox("Decision filter", ["ALL", "BLOCK", "REQUIRE_APPROVAL", "ALLOW"])
        for event in events:
            payload = json.loads(event["payload"]) if isinstance(event.get("payload"), str) else event.get("payload", {})
            decision = payload.get("decision", {}).get("decision", "")
            if event["event"] == "tool_decision" and (filter_decision == "ALL" or decision == filter_decision):
                st.expander(f"{decision} | risk {payload.get('decision', {}).get('risk_score', 0)} | {payload.get('tool')}").json(payload)
    except Exception as exc:
        st.error(str(exc))


def attack_simulator():
    st.title("Attack Simulator")
    scenarios = {
        "Malicious vendor document": ("Summarize vendor_malicious.txt.", "vendor_malicious.txt"),
        "Malicious email": ("Summarize email_malicious.txt.", "email_malicious.txt"),
        "Malicious README": ("Summarize README_malicious.md.", "README_malicious.md"),
        "Malicious RAG policy": ("Summarize malicious_policy.txt.", "malicious_policy.txt"),
        "Credential access": ("Read fake_secrets/api_key.txt.", "fake_secrets/api_key.txt"),
    }
    name = st.selectbox("Controlled scenario", list(scenarios))
    mode = st.selectbox("Compare mode", ["PROTECTED", "VULNERABLE"], key="attack-mode")
    if st.button("RUN ATTACK", type="primary"):
        request, path = scenarios[name]
        try:
            st.session_state["last_result"] = post("/run", {"user_request": request, "content_path": path, "use_rag": True, "mode": mode})
        except Exception as exc:
            st.error(str(exc))
    if st.session_state.get("last_result"):
        render_trace(st.session_state["last_result"])


def graph_page():
    st.title("Tool Dependency Graph")
    try:
        graph = get("/tdg")
        lines = ["digraph TDG {", "rankdir=LR;"]
        for node in graph["nodes"]:
            lines.append(f'"{node}" [shape=box];')
        for edge in graph["edges"]:
            lines.append(f'"{edge["source"]}" -> "{edge["target"]}";')
        lines.append("}")
        st.graphviz_chart("\n".join(lines))
        st.json(graph)
    except Exception as exc:
        st.error(str(exc))


def rag_explorer():
    st.title("RAG Explorer")
    try:
        st.json(get("/rag/status"))
        query = st.text_input("Local semantic query", "What is the company leave policy?")
        if st.button("Retrieve local chunks"):
            result = post("/run", {"user_request": query, "use_rag": True, "mode": "PROTECTED"})
            st.json(result.get("retrieved"))
            st.write(result.get("answer"))
    except Exception as exc:
        st.error(str(exc))


def audit_explorer():
    st.title("Audit Explorer")
    try:
        st.json(get("/audit/verify"))
        st.json(get("/audit?limit=100"))
    except Exception as exc:
        st.error(str(exc))


def policy_center():
    st.title("Policy Center")
    st.caption("Policies are displayed for inspection. Core protections cannot be disabled here.")
    try:
        st.yaml(get("/policies"))
    except Exception as exc:
        st.error(str(exc))


def risk_analytics():
    st.title("Risk Analytics")
    try:
        events = get("/audit?limit=500")["events"]
        rows = []
        for event in events:
            payload = json.loads(event["payload"]) if isinstance(event.get("payload"), str) else event.get("payload", {})
            decision = payload.get("decision", {})
            if event["event"] == "tool_decision":
                rows.append({"risk": decision.get("risk_score", 0), "decision": decision.get("decision", ""), "tool": payload.get("tool", "")})
        st.dataframe(rows, use_container_width=True)
        if rows:
            st.bar_chart({"risk": [row["risk"] for row in rows]})
    except Exception as exc:
        st.error(str(exc))


def evaluation_page():
    st.title("Baseline vs Protected Evaluation")
    try:
        result = get("/evaluation")
        if result.get("available"):
            st.json(result["report"])
        else:
            st.info(result["message"])
    except Exception as exc:
        st.error(str(exc))


def system_health():
    st.title("System Health")
    try:
        st.json(get("/local-status"))
        st.success("External providers disabled; normal operation is localhost-only.")
    except Exception as exc:
        st.error(str(exc))


def settings_page():
    st.title("Settings")
    st.write("Configuration is read from the local `.env` file and `config/policies.yaml`.")
    st.code("LLM_PROVIDER=ollama\nOLLAMA_BASE_URL=http://localhost:11434\nOFFLINE_MODE=true")


def final_demo():
    st.title("Final Demo")
    demo = st.selectbox("Choose demonstration", ["Normal question", "Legitimate RAG", "Malicious document", "Approval / local write", "Dangerous tool chain"])
    examples = {
        "Normal question": ("What is indirect prompt injection?", "", False),
        "Legitimate RAG": ("What is the company leave policy?", "company_policy.txt", True),
        "Malicious document": ("Summarize vendor_malicious.txt.", "vendor_malicious.txt", True),
        "Approval / local write": ("Write the result to report.txt.", "", False),
        "Dangerous tool chain": ("Summarize vendor_malicious.txt.", "vendor_malicious.txt", True),
    }
    request, path, rag = examples[demo]
    st.code(request)
    if st.button("Run final demo", type="primary"):
        try:
            result = post("/run", {"user_request": request, "content_path": path or None, "use_rag": rag, "mode": "PROTECTED"})
            st.session_state["last_result"] = result
        except Exception as exc:
            st.error(str(exc))
    if st.session_state.get("last_result"):
        render_trace(st.session_state["last_result"])


pages = {"Live Monitor": live_monitor, "Agent Console": run_console, "Threat Center": threat_center,
         "Attack Simulator": attack_simulator, "Tool Dependency Graph": graph_page, "RAG Explorer": rag_explorer,
         "Audit Explorer": audit_explorer, "Policy Center": policy_center, "Risk Analytics": risk_analytics,
         "Evaluation": evaluation_page, "System Health": system_health, "Settings": settings_page, "Final Demo": final_demo}
pages[page]()
