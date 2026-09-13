# How It Works

1. I type a request.
2. Ollama runs the local LLM on my computer.
3. The model decides whether it needs a tool.
4. If no tool is needed, it answers locally.
5. If a tool is needed, it proposes a structured action.
6. The security gateway receives that action.
7. The system checks my original intention.
8. It checks where the instruction came from.
9. It checks capabilities, paths, destinations, and sensitive data.
10. It calculates explainable risk components.
11. It checks deterministic YAML policies.
12. It checks the tool dependency graph.
13. It decides `ALLOW`, `BLOCK`, or `REQUIRE_APPROVAL`.
14. Only an allowed action reaches a local tool.
15. The result goes back to Ollama.
16. Ollama gives the final answer.
17. Security events are recorded in SQLite and chained with SHA-256.

## What Ollama Does

```text
Ollama
    -> loads qwen2.5:3b locally
    -> the model runs on this computer
    -> the application sends requests to localhost:11434
    -> the model generates a response locally
    -> the response returns to the local application
```

No cloud LLM is used. Internet is needed only to install Ollama, download models, and install packages once.
