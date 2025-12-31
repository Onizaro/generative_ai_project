# Short Technical Report

## Key design decisions
- Multi-stage deliberation pipeline separated into three explicit stages (Initial Opinions, Review & Critique, Final Synthesis) to improve transparency and traceability of model outputs.
- Lightweight HTTP coordination using Flask endpoints (`/api/council/stage1`, `/api/council/stage2`, `/api/council/stage3`) so the frontend can poll and render partial results incrementally with minimal infrastructure changes.
- Simple in-memory cache (`deliberation_cache`) keyed by user query to persist intermediate stage outputs between requests. This keeps the implementation minimal and easy to reason about; suitable for prototypes but should be replaced by persistent/shared storage for multi-worker deployments.
- Basic telemetry and health monitoring per model (`model_metrics`, `model_status`) to track latencies, request counts, token approximations and availability checks.

## Chosen LLM models
- `Agent_Llama3` — model identifier `llama3` (local Ollama endpoint) used as one council member.
- `Agent_Mistral` — model identifier `mistral` used as another council member.
- `Agent_Qwen2.5:7b` — model identifier `qwen2.5:7b` used as a third council member.
- `Chairman_Phi3` — chairman model identifier `phi3` used to synthesize the final answer.

Note: models are called through a local Ollama-compatible HTTP API (`/api/generate`). Models and endpoints are configured in `app.py`.

## Improvements made over the original repository (karpathy/llm-council)
This project builds on the ideas from the `karpathy/llm-council` reference implementation (https://github.com/karpathy/llm-council). Key improvements and differences include:

- Incremental UI updates: the original repo offers a deliberation flow; here the server API is split into three explicit stage endpoints (`/api/council/stage1`, `/api/council/stage2`, `/api/council/stage3`) so the frontend can render Stage 1 results immediately and show progress for later stages.
- Metrics and monitoring: added per-model telemetry (`model_metrics`) and a background heartbeat (`heartbeat_monitor`) to monitor availability, latency, request counts, token estimates and errors — useful for debugging and capacity planning.
- Local-First: Removed all cloud-based API dependencies (OpenRouter/OpenAI).
- Architecture: Implemented a distributed-ready REST architecture.
- Strict Separation: Explicit separation of the Chairman role from the Council.
- Transparency: Allows inspection of intermediate model outputs.

