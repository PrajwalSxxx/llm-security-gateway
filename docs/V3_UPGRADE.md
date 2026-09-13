# V3 Upgrade

This upgrade preserves the V2 Ollama/security implementation and adds the missing user-facing workflows.

## Added

- Natural-language Windows and Unix path extraction.
- Preflight authorization before an explicitly requested local file is read.
- Configured allowed roots: project, sandbox, user Documents, and Desktop.
- Traversal and disallowed-root blocking.
- Local extraction for TXT, Markdown, PDF, DOCX, CSV, and JSON.
- Semantic RAG support for the additional local file types.
- Multi-page Streamlit control center.
- Live monitor, agent console, threat center, attack simulator, TDG graph, RAG explorer, audit explorer, policy center, risk analytics, evaluation, system health, settings, and final demo pages.
- Dashboard endpoints for TDG, policies, RAG status, and evaluation results.
- Beginner usage and five-demo guides.
- Regression test for natural path extraction and path traversal blocking.

## Security Boundary

Explicit file requests are preflighted by the gateway before document extraction. Once an allowed file is read, the model can receive its extracted text, but any subsequent tool proposal still passes through the gateway.

The dashboard exposes structured security metadata only. It does not display hidden model chain-of-thought.
