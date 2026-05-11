---
type: reference
category: infra
created: 2026-05-11
ticket: 21056e32
title: AAI Provider Lanes — Routed Evidence Matrix
---

# AAI Provider Lanes — Routed Evidence Matrix

**Purpose:** Map each provider surface to what class of evidence it proves. No probe is added until its lane is assigned here first.

---

## Lane Registry

| Lane ID | Provider Surface | Auth Model | Evidence Class | Proof Mode | Status |
|---------|----------------|------------|---------------|------------|--------|
| `L1` | Copilot Chat / Claude 4.x (VS Code) | GitHub OAuth | Interactive reasoning, tool-use, agent protocols, session continuity | Manual / canary | ✅ Active |
| `L2` | GitHub Models (REST/SDK) | GitHub PAT (`models:read`) | API-route reachability, model availability, provider budget gates | Automated probe | ✅ Active (budget-gated) |
| `L3` | Azure AI Foundry | Azure CLI / MSI | Cloud-substrate deployment, managed identity, Bicep provisioning | Automated + manual | ⚠️ Probe pending |
| `L4` | HuggingFace Inference API | `HF_TOKEN` | Open-weight model availability, HF Hub reachability, gated-model acceptance | Automated probe | ✅ Active |
| `L5` | Poe (Account 1) | `POE_API_KEY_1` | Commercial-model fallback, third-party routing, rate-limit resilience | Automated probe | ✅ Active |
| `L6` | Poe (Account 2) | `POE_API_KEY_2` | Dual-account redundancy, provider-level failover | Automated probe | ✅ Active |
| `L7` | Local GPU inference (tabbyAPI) | local | On-device latency, EXL2/EXL3 quantization, Python 3.14 stack coherence | Automated gate ladder (G1–G6) | ✅ Gate ladder committed |
| `L8` | OpenAI (direct API) | `OPENAI_API_KEY` | Canonical capability baseline, image gen, Sora video, Realtime | Manual + scripted | ✅ Active |

---

## Evidence Class Definitions

| Class | Meaning | Probe artifact |
|-------|---------|----------------|
| **API-route reachability** | The network path from this repo to the provider's endpoint resolves and authenticates | `manifest/github_models_*.json`, `manifest/poe_*.json` |
| **Interactive reasoning** | A human-in-the-loop session proved the model behaved correctly for complex multi-step tasks | Session log / `claude/mailbox/` handoff |
| **Model availability** | A specific model ID is listed and returns a response at probe time | Provider probe manifests |
| **Budget-gate** | Provider responded but refused inference due to quota/tier — route is valid, gate is external | `manifest/birdcage_*.json` |
| **On-device latency** | Local GPU pipeline proved end-to-end: model loaded, tokens generated, latency measured | `manifest/tabby_model_load_gate.json` |
| **Cloud-substrate deployment** | Infra provisioned, endpoint live, managed identity bound | Bicep output / Foundry deployment log |
| **Gated-model acceptance** | HF gated model accepted `HF_TOKEN` via CLI-first escalation ladder | `manifest/hf_gate_*.json` |

---

## Routing Rules

```
Probe target                 → Assigned lane
─────────────────────────────────────────────
New API-route check          → L2 or L5/L6 (if GitHub Models unavailable)
On-device model behavior     → L7 (tabbyAPI gate ladder)
Open-weight model via HF     → L4
Commercial model fallback    → L5 + L6 (dual-account)
Cloud deployment             → L3 (Foundry/Azure)
Canonical capability proof   → L1 (Copilot Chat) or L8 (OpenAI direct)
Image / video generation     → L8 (OpenAI — imagegen + sora skills)
```

---

## Failure Classification

| Failure pattern | Classification | Action |
|-----------------|---------------|--------|
| `401 / 403` | Auth drift | Rotate key; see `api-manager` skill |
| `429 / quota` | Budget gate | Record as `budget_gated` evidence — route valid |
| `timeout / no route` | Network / infra | Check proxy, DNS; not a model issue |
| `model not found` | Provider deprecation | Update lane's model ID in probe |
| `exit -1073741819` | Win32 ABI mismatch (local GPU) | ZJIT Win32 Prism crash — use Podman lane |

---

## Anti-patterns

- **Do not add a probe before assigning it a lane here.** Probes without lane assignment produce unclassified artifacts.
- **Do not treat budget-gate as proof of failure.** L2 (GitHub Models) is budget-gated in Birdcage — the route is valid.
- **Do not conflate L1 (interactive) with automated evidence.** Manual canary sessions prove agent behavior, not API reachability.
- **Do not add new lanes for provider variants** (e.g. "Poe Account 3") without a corresponding entry in this matrix and a `.json` key in `manifest/`.
