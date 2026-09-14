import json
import os
import urllib.request

import streamlit as st


st.set_page_config(page_title="Local AI Security Assistant", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
.block-container { padding-top: 1.4rem; max-width: 1500px; }
.brand { font-size: 1.65rem; font-weight: 750; letter-spacing: -0.03em; }
.muted { color: #718096; font-size: 0.9rem; }
.security-card { border: 1px solid #dbe4f0; border-left: 5px solid #3182ce; border-radius: 12px; padding: 1rem; margin: .7rem 0; background: linear-gradient(110deg,#f7fbff,#ffffff); }
.security-block { border-left-color: #e53e3e; background: #fff8f8; }
.security-approval { border-left-color: #dd6b20; background: #fffaf2; }
.pill { padding: .22rem .62rem; border-radius: 999px; background: #edf6ff; color: #2166a5; font-size: .82rem; font-weight: 650; }
</style>
""", unsafe_allow_html=True)
API = st.sidebar.text_input("FastAPI URL", os.getenv("BACKEND_URL", "http://127.0.0.1:8000"))


def get(path):
    return json.loads(urllib.request.urlopen(API + path, timeout=20).read())


def post(path, payload):
    request = urllib.request.Request(API + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(request, timeout=600).read())


st.sidebar.markdown("<div class='brand'>Local AI<br>Security Assistant</div><div class='muted'>Ollama + runtime protection</div>", unsafe_allow_html=True)
try:
    sidebar_status = get("/local-status")
    st.sidebar.success(f"Ollama connected · {sidebar_status.get('models', ['local'])[ -1]}")
    st.sidebar.caption(f"LOCAL · OFFLINE MODE {'ON' if sidebar_status.get('offline_mode') else 'OFF'}")
except Exception:
    st.sidebar.error("Ollama/backend offline")
st.sidebar.markdown("### AI")
page = st.sidebar.radio("", ["Agent Console", "Conversations", "Documents"], label_visibility="collapsed")
st.sidebar.markdown("### Security")
security_page = st.sidebar.radio("", ["Live Monitor", "Threat Center", "Attack Simulator", "Tool Dependency Graph", "Audit Explorer", "Policy Center"], label_visibility="collapsed")
st.sidebar.markdown("### Analytics")
analytics_page = st.sidebar.radio("", ["Risk Analytics", "Evaluation"], label_visibility="collapsed")
st.sidebar.markdown("### System")
system_page = st.sidebar.radio("", ["System Health", "Settings", "Final Demo"], label_visibility="collapsed")


def selected_page():
    if page != "Agent Console":
        return page
    if security_page != "Live Monitor" and st.session_state.get("dashboard_override"):
        return st.session_state.pop("dashboard_override")
    return page


def security_card(event):
    decision = event.get("decision", {})
    state = decision.get("decision", "UNKNOWN")
    css = "security-block" if state == "BLOCK" else "security-approval" if state == "REQUIRE_APPROVAL" else ""
    icon = "🚨" if state == "BLOCK" else "⚠️" if state == "REQUIRE_APPROVAL" else "🛡️"
    label = "ACTION BLOCKED" if state == "BLOCK" else "APPROVAL REQUIRED" if state == "REQUIRE_APPROVAL" else "RUNTIME SECURITY"
    st.markdown(f"<div class='security-card {css}'><b>{icon} {label}</b><br>"
                f"Action: <code>{event.get('tool')}</code> · Decision: <b>{state}</b> · Risk: <b>{decision.get('risk_score', 0)} / 100</b><br>"
                f"Source: {event.get('source', 'AGENT_GENERATED')} · Data: {event.get('data_class', 'UNKNOWN')}</div>", unsafe_allow_html=True)
    with st.expander("View security analysis", expanded=False):
        st.write("**Reasons:** " + "; ".join(decision.get("reasons", [])))
        st.json({"capabilities": event.get("capabilities"), "arguments": event.get("arguments"),
                 "risk_components": decision.get("risk_components"), "intent": decision.get("intent"),
                 "tdg": decision.get("tdg_path"), "execution_result": event.get("execution_result")})


def render_chat_result(result):
    if result.get("events"):
        for index, event in enumerate(result["events"], 1):
            security_card(event)
            decision = event.get("decision", {})
            if decision.get("decision") == "REQUIRE_APPROVAL":
                if st.button("Approve action", key=f"approve-chat-{result['session_id']}-{index}"):
                    st.success(json.dumps(post("/approve/" + result["session_id"], {})))
    if result.get("retrieved"):
        with st.expander("Local retrieval and provenance", expanded=False):
            st.json(result["retrieved"])


def run_console():
    st.markdown("<div class='brand'>Local AI Security Assistant</div><div class='muted'>A local Ollama assistant with a runtime authorization boundary.</div>", unsafe_allow_html=True)
    try:
        status = get("/local-status")
        st.markdown(f"<span class='pill'>● Ollama Connected</span> &nbsp; Model: <b>{status.get('models', ['unknown'])[-1]}</b> &nbsp; Mode: <b>Fully Local</b> &nbsp; Internet: <b>Disabled</b>", unsafe_allow_html=True)
    except Exception:
        st.error("Ollama is not running. Start Ollama and try again.")
    controls = st.columns([2, 2, 1])
    with controls[0]:
        mode = st.selectbox("Security mode", ["PROTECTED", "VULNERABLE"], key="chat-mode")
    with controls[1]:
        try:
            documents = [item["path"] for item in get("/documents").get("documents", [])]
        except Exception:
            documents = []
        selected = st.selectbox("Local attachment", ["None"] + documents, key="chat-document")
    with controls[2]:
        use_rag = st.checkbox("Semantic RAG", value=False, key="chat-rag")
    if st.button("New chat", key="new-chat"):
        st.session_state["messages"] = []
        st.rerun()
    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("result"):
                render_chat_result(message["result"])
    prompt = st.chat_input("Message the local AI...")
    if prompt:
        st.session_state.setdefault("messages", []).append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Ollama is working locally..."):
                try:
                    result = post("/run", {"user_request": prompt, "content_path": None if selected == "None" else selected,
                                           "use_rag": use_rag, "mode": mode})
                    st.session_state["messages"].append({"role": "assistant", "content": result.get("answer", ""), "result": result})
                    st.markdown(result.get("answer", ""))
                    render_chat_result(result)
                except Exception as exc:
                    st.error(str(exc))


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


def conversations_page():
    st.title("Conversations")
    messages = st.session_state.get("messages", [])
    if not messages:
        st.info("No local conversation yet. Open Agent Console to start one.")
    else:
        st.write(f"Current local conversation: {len(messages)} messages")
        for message in messages:
            st.write(f"**{message['role'].title()}**: {message['content'][:180]}")


def documents_page():
    st.title("Local Documents")
    st.caption("These are local resources reported by the backend. No document is uploaded to a cloud service.")
    try:
        documents = get("/documents").get("documents", [])
        st.dataframe(documents, use_container_width=True)
    except Exception as exc:
        st.error(str(exc))


pages = {"Agent Console": run_console, "Conversations": conversations_page, "Documents": documents_page,
         "Live Monitor": live_monitor, "Threat Center": threat_center, "Attack Simulator": attack_simulator,
         "Tool Dependency Graph": graph_page, "RAG Explorer": rag_explorer, "Audit Explorer": audit_explorer,
         "Policy Center": policy_center, "Risk Analytics": risk_analytics, "Evaluation": evaluation_page,
         "System Health": system_health, "Settings": settings_page, "Final Demo": final_demo}
active_page = page if page in {"Agent Console", "Conversations", "Documents"} else security_page if security_page != "Live Monitor" else analytics_page if analytics_page != "Risk Analytics" else system_page if system_page != "System Health" else "Live Monitor"
pages[active_page]()
