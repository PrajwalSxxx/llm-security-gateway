# Viva Questions and Answers

## What is an LLM?

An LLM is a model trained to predict and generate language. It is not automatically a policy enforcement system.

## What is an agent?

An agent combines a model with state, planning, and tools so it can perform multi-step tasks.

## What is tool calling?

It is a structured request from the model to invoke a capability such as reading a file. In this project, the request is only a proposal.

## What is RAG?

Retrieval-Augmented Generation retrieves relevant documents and gives them to a model as context. Retrieved text must still be treated as untrusted.

## What is prompt injection?

It is content crafted to manipulate an instruction-following model into ignoring intended controls or performing an attacker-selected task.

## What is indirect prompt injection?

It is prompt injection delivered through external content, rather than directly in the user's request.

## Why is IPI dangerous?

The content may influence a tool-capable agent, turning text manipulation into unauthorized file access, writes, or data transmission.

## Why not rely only on a system prompt?

An LLM can misunderstand, conflict, or be manipulated by later context. Deterministic enforcement must be outside the model.

## What is runtime security?

It is checking an action immediately before execution using current context, policy, and observed behavior.

## What is intent-action discrepancy?

It is the difference between the user's authorized goal and the proposed operation. A summary request versus a credential read is a high discrepancy.

## What is a TDG?

A Tool Dependency Graph records relationships among tool actions and identifies risky sequences.

## Why NetworkX?

It is a small, understandable Python graph library suitable for a prototype.

## Why deterministic policies?

They are explainable, testable, and do not depend on a second model making the final authorization decision.

## How are secrets detected?

Configurable regular expressions look for labels such as `API_KEY`, `PASSWORD`, `TOKEN`, and private-key markers. This is a signal, not a complete DLP solution.

## What happens if the LLM is compromised?

The protected design still treats its output as an untrusted action proposal and checks it before execution.

## Why use Docker?

Containers can reduce blast radius, but they are not a complete security boundary. This prototype provides a Dockerfile while defaulting to local path restrictions.

## How was it evaluated?

The evaluation script generates 50 benign and 50 malicious local scenarios, runs protected mode, and computes measured detection, false-positive, false-negative, and latency values.

## Main limitations?

The model and embedding service are local Ollama processes, while search, database, and HTTP tools are controlled local simulations. Detection is incomplete; no authentication or production multi-tenant isolation exists; and SQLite hash chaining is only tamper-evident.

## Why Ollama?

Ollama serves a model locally through `localhost:11434`, so prompts, documents, and responses remain on the computer during normal operation.

## Why a local LLM?

It removes cloud-provider dependency and allows the project to be demonstrated offline with controlled data.

## Why provenance?

The same text has different trust depending on whether it came from the user, policy, a retrieved document, or a tool result. The gateway adds scrutiny to untrusted sources.

## Why local embeddings?

Semantic retrieval needs vectors. `nomic-embed-text` runs through Ollama locally, so documents are not uploaded to an embedding service.

## Why baseline versus protected?

The baseline shows what a tool-capable local model can propose without an authorization boundary. The protected mode proves that the gateway remains outside the model's authority.

## Why approval?

Some actions are risky but not automatically forbidden. `REQUIRE_APPROVAL` pauses execution and lets an operator approve or reject it through the dashboard.
