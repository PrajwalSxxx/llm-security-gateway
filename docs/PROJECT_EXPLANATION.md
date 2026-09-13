# Project Explanation

An LLM is good at language but does not inherently know which instructions are trustworthy. An agent adds the ability to choose tools, such as reading a file or sending a request. That makes the agent useful, but also creates a security boundary.

Indirect prompt injection happens when the attacker puts instructions in content the user did not write, such as a document, email, web page, or README. The user may ask for a summary, while the document tells the agent to read a password and upload it. The agent sees both as text unless the system separates trusted instructions from untrusted data.

This project separates those roles. The local agent proposes an action. The proposal is converted into a typed action. The security gateway independently compares it with the user's goal, checks paths and destinations, scans for secrets, considers earlier actions, and applies deterministic policy. The tool runs only after an `ALLOW` result.

The vulnerable mode intentionally removes that control so the difference can be observed. The protected mode is not claimed to solve all prompt injection: it is an understandable research prototype with transparent checks and clear limitations.

The RAG part loads local documents, selects relevant text, and labels it as untrusted. The audit component records what happened and chains records cryptographically. The dashboard lets a student run normal and malicious examples. The evaluation script generates equal-sized benign and malicious datasets and calculates measurements from actual executions rather than invented claims.
