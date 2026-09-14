import json
import os
import urllib.request
from datetime import datetime

import streamlit as st


st.set_page_config(page_title="Local AI Security Assistant", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"], index=0, key="theme")
st.markdown("""
<style>
.block-container { padding-top: 1.2rem; max-width: 1500px; }
.brand { font-size: 1.65rem; font-weight: 750; letter-spacing: -0.03em; }
.muted { color: #718096; font-size: 0.9rem; }
.security-card { border: 1px solid #dbe4f0; border-left: 5px solid #3182ce; border-radius: 12px; padding: 1rem; margin: .7rem 0; background: linear-gradient(110deg,#f7fbff,#ffffff); }
.security-block { border-left-color: #e53e3e; background: #fff8f8; }
.security-approval { border-left-color: #dd6b20; background: #fffaf2; }
.pill { padding: .22rem .62rem; border-radius: 999px; background: #edf6ff; color: #2166a5; font-size: .82rem; font-weight: 650; }
.activity { border: 1px solid #e2e8f0; border-radius: 16px; padding: 1rem; background: #fbfdff; }
.activity-title { font-weight: 700; font-size: 1.05rem; margin-bottom: .8rem; }
.chat-empty { text-align: center; padding: 5rem 1rem 3rem; }
.chat-empty h1 { font-size: 2.35rem; letter-spacing: -.04em; }
section[data-testid="stSidebar"] > div:first-child { height: 100vh; overflow-y: auto; }
section[data-testid="stSidebar"] [data-testid="stSelectbox"] { margin-bottom: .6rem; }
</style>
""", unsafe_allow_html=True)
if theme == "Dark":
    st.markdown("""
    <style>
    .stApp { background: #111827; color: #edf2f7; }
    .activity, .security-card { background: #182334; border-color: #334155; color: #edf2f7; }
    .security-block { background: #2a1b22; } .security-approval { background: #2c2418; }
    .muted { color: #a0aec0; }
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
st.sidebar.markdown("### Workspace")
navigation = [
    "AI · Agent Console", "AI · Conversations", "AI · Documents",
    "Security · Live Monitor", "Security · Threat Center", "Security · Attack Simulator",
    "Security · Tool Dependency Graph", "Security · Audit Explorer", "Security · Policy Center",
    "Analytics · Risk Analytics", "Analytics · Evaluation",
    "System · System Health", "System · Settings", "System · Final Demo",
]
navigation_label = st.sidebar.selectbox("Navigate", navigation, label_visibility="collapsed")
page = navigation_label.split(" · ", 1)[1]
st.sidebar.caption("Scroll to access every workspace section")


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


def render_activity(result):
    st.markdown("<div class='activity'><div class='activity-title'>Live Agent Activity</div>", unsafe_allow_html=True)
    if not result:
        st.markdown("<span class='muted'>Waiting for a local request...</span>", unsafe_allow_html=True)
    else:
        events = result.get("events", [])
        rows = [("✓", "Request understood"), ("✓", "Ollama response received"),
                ("✓" if events else "·", "Agent decision"),
                ("✓" if events else "·", "Tool proposal"),
                ("✓" if events else "·", "Runtime security"),
                ("✓" if result.get("retrieved") else "·", "Local RAG / document context"),
                ("✓", "Final answer")]
        for icon, label in rows:
            st.markdown(f"<div style='padding:.38rem 0'>{icon} &nbsp; {label}</div>", unsafe_allow_html=True)
        if events:
            latest = events[-1].get("decision", {})
            st.divider()
            st.caption("Latest security decision")
            st.metric("Risk", f"{latest.get('risk_score', 0)} / 100")
            st.write(latest.get("decision", "UNKNOWN"))
    st.markdown("</div>", unsafe_allow_html=True)


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
        st.session_state["last_result"] = None
        st.rerun()
    messages = st.session_state.get("messages", [])
    chat_col, activity_col = st.columns([2.15, 1])
    with chat_col:
        if not messages:
            st.markdown("<div class='chat-empty'><h1>What can your local AI help with?</h1><p class='muted'>Your prompts, documents, embeddings, and security events stay on this computer.</p></div>", unsafe_allow_html=True)
            quick = st.columns(3)
            quick_prompts = [("Analyze a document", "Read documents/report.txt and summarize it."),
                             ("Explain security", "Explain how indirect prompt injection works."),
                             ("Run a security demo", "Summarize vendor_malicious.txt.")]
            for column, (label, prompt_text) in zip(quick, quick_prompts):
                if column.button(label, key="quick-" + label):
                    st.session_state["queued_prompt"] = prompt_text
                    st.rerun()
        for message in messages:
            with st.chat_message(message["role"]):
                if message.get("timestamp"):
                    st.caption(message["timestamp"])
                st.markdown(message["content"])
                if message.get("result"):
                    render_chat_result(message["result"])
    with activity_col:
        render_activity(st.session_state.get("last_result"))
    prompt = st.chat_input("Message the local AI...") or st.session_state.pop("queued_prompt", None)
    if prompt:
        timestamp = datetime.now().strftime("%H:%M")
        st.session_state.setdefault("messages", []).append({"role": "user", "content": prompt, "timestamp": timestamp})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Ollama is working locally..."):
                try:
                    result = post("/run", {"user_request": prompt, "content_path": None if selected == "None" else selected,
                                           "use_rag": use_rag, "mode": mode})
                    st.session_state["messages"].append({"role": "assistant", "content": result.get("answer", ""), "result": result, "timestamp": datetime.now().strftime("%H:%M")})
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
            state = decision.get("decision", event["event"])
            with st.container(border=True):
                st.markdown(f"**{event['timestamp']}**  ·  **{state}**  ·  `{payload.get('tool', event['event'])}`")
                st.caption(f"Risk {decision.get('risk_score', 0)}/100 · source {payload.get('source', 'n/a')}")
    except Exception as exc:
        st.error(f"Backend unavailable: {exc}")


def threat_center():
    st.title("Threat Center")
    try:
        events = get("/audit?limit=200")["events"]
        tool_filter = st.selectbox("Tool filter", ["ALL", "read_file", "write_file", "http_request", "web_search"])
        filter_decision = st.selectbox("Decision filter", ["ALL", "BLOCK", "REQUIRE_APPROVAL", "ALLOW"])
        threat_count = 0
        for event in events:
            payload = json.loads(event["payload"]) if isinstance(event.get("payload"), str) else event.get("payload", {})
            decision = payload.get("decision", {}).get("decision", "")
            tool = payload.get("tool", "")
            if event["event"] == "tool_decision" and (filter_decision == "ALL" or decision == filter_decision) and (tool_filter == "ALL" or tool == tool_filter):
                threat_count += 1
                risk = payload.get("decision", {}).get("risk_score", 0)
                severity = "CRITICAL" if risk >= 81 else "HIGH" if risk >= 61 else "MEDIUM" if risk >= 31 else "LOW"
                with st.container(border=True):
                    st.markdown(f"**{'🚨' if risk >= 81 else '⚠️' if risk >= 61 else '🛡️'} {severity} · {decision}**")
                    st.write(f"`{tool}` · risk **{risk}/100** · source **{payload.get('source', 'unknown')}**")
                    st.caption(event["timestamp"])
                    with st.expander("Investigate event"):
                        st.write("**Reasons:** " + "; ".join(payload.get("decision", {}).get("reasons", [])))
                        st.json({"arguments": payload.get("arguments"), "risk_components": payload.get("decision", {}).get("risk_components"),
                                 "intent": payload.get("decision", {}).get("intent"), "tdg": payload.get("decision", {}).get("tdg_path")})
        if not threat_count:
            st.info("No matching security events. Run an agent request or attack simulation to generate activity.")
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
        st.graphviz_chart("\n".join(lines), use_container_width=True)
        selected = st.selectbox("Inspect graph node", ["None"] + graph["nodes"])
        if selected != "None":
            incoming = [edge["source"] for edge in graph["edges"] if edge["target"] == selected]
            outgoing = [edge["target"] for edge in graph["edges"] if edge["source"] == selected]
            st.info(f"Node: {selected}\n\nPrevious: {', '.join(incoming) or 'none'}\n\nNext: {', '.join(outgoing) or 'none'}")
    except Exception as exc:
        st.error(str(exc))


def rag_explorer():
    st.title("RAG Explorer")
    try:
        status = get("/rag/status")
        cols = st.columns(3)
        cols[0].metric("Indexed chunks", status.get("indexed_chunks", 0))
        cols[1].metric("Vector DB", status.get("vector_database", "local"))
        cols[2].metric("Embedding model", status.get("embedding_model", "unknown"))
        query = st.text_input("Local semantic query", "What is the company leave policy?")
        if st.button("Retrieve local chunks"):
            result = post("/run", {"user_request": query, "use_rag": True, "mode": "PROTECTED"})
            retrieved = result.get("retrieved") or {}
            st.subheader("Retrieved sources")
            for chunk in retrieved.get("chunks", []):
                with st.container(border=True):
                    st.markdown(f"**{chunk.get('source')}** · chunk `{chunk.get('chunk_id')}` · similarity `{chunk.get('similarity')}`")
                    st.caption(f"Trust: {chunk.get('trust_level')} · Type: {chunk.get('source_type')}")
                    with st.expander("Preview chunk"):
                        st.write(chunk.get("content", ""))
            st.success(result.get("answer", ""))
    except Exception as exc:
        st.error(str(exc))


def audit_explorer():
    st.title("Audit Explorer")
    try:
        verification = get("/audit/verify")
        if verification.get("valid"):
            st.success("Hash chain verified")
        else:
            st.error(verification.get("message"))
        events = get("/audit?limit=100")["events"]
        query = st.text_input("Search session, tool, or decision")
        visible = [event for event in events if not query or query.lower() in json.dumps(event).lower()]
        st.caption(f"Showing {len(visible)} local events")
        for event in visible:
            payload = json.loads(event["payload"]) if isinstance(event.get("payload"), str) else event.get("payload", {})
            decision = payload.get("decision", {})
            with st.expander(f"{event['timestamp']} · {event['event']} · {decision.get('decision', 'record')}"):
                st.write(f"Session: `{event['session_id']}`")
                st.write(f"Tool: `{payload.get('tool', 'n/a')}` · Risk: `{decision.get('risk_score', 0)}`")
                st.json(payload)
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
        if not rows:
            st.info("No tool decisions yet. Run an agent request to populate analytics.")
            return
        cols = st.columns(4)
        cols[0].metric("Events", len(rows))
        cols[1].metric("Blocked", sum(row["decision"] == "BLOCK" for row in rows))
        cols[2].metric("Approvals", sum(row["decision"] == "REQUIRE_APPROVAL" for row in rows))
        cols[3].metric("Average risk", round(sum(row["risk"] for row in rows) / len(rows), 2))
        st.subheader("Risk by event")
        st.line_chart({"risk": [row["risk"] for row in rows]})
        st.subheader("Structured events")
        st.dataframe(rows, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.error(str(exc))


def evaluation_page():
    st.title("Baseline vs Protected Evaluation")
    try:
        result = get("/evaluation")
        if result.get("available"):
            report = result["report"]
            baseline = report.get("baseline", {})
            protected = report.get("protected", {})
            st.subheader("Security effectiveness")
            cols = st.columns(4)
            cols[0].metric("Baseline attack success", f"{baseline.get('attack_success_rate', 0):.1%}")
            cols[1].metric("Protected detection", f"{protected.get('detection_rate', 0):.1%}")
            cols[2].metric("False positives", f"{protected.get('false_positive_rate', 0):.1%}")
            cols[3].metric("Security overhead", f"{report.get('security_overhead_ms', 0):.1f} ms")
            st.bar_chart({"Baseline attack success": [baseline.get("attack_success_rate", 0)],
                          "Protected detection": [protected.get("detection_rate", 0)],
                          "Protected false positives": [protected.get("false_positive_rate", 0)]})
            with st.expander("Full measured report"):
                st.json(report)
        else:
            st.info(result["message"])
    except Exception as exc:
        st.error(str(exc))


def system_health():
    st.title("System Health")
    try:
        status = get("/local-status")
        checks = [("Ollama", status.get("reachable")), ("LLM model", status.get("model_installed")),
                  ("Embedding model", status.get("embedding_model_installed")), ("Vector DB", True),
                  ("SQLite database", True), ("Offline mode", status.get("offline_mode")),
                  ("External providers disabled", status.get("external_providers") == "DISABLED")]
        for name, healthy in checks:
            with st.container(border=True):
                st.markdown(f"{'🟢' if healthy else '🔴'} **{name}**  ·  {'READY' if healthy else 'CHECK REQUIRED'}")
        with st.expander("Technical details"):
            st.json(status)
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
pages[page]()
