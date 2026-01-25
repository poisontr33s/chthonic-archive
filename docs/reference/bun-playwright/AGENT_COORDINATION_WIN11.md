# Agent Coordination Protocol: Win11 Bun-Playwright

> **Mediator**: User | **Agents**: Claude Opus 4.5 + GPT-5.2 Codex
> **Objective**: Solve Playwright browser launch on enterprise Windows 11

---

## Task Delegation

### 🔵 Claude Opus 4.5 (This Session)
**Role**: Architecture, documentation, code generation

| Task | Status | Output |
|------|--------|--------|
| Create win11-diagnostic.ts script | 🔲 Ready | File in bun-playwright-poc/ |
| Generate pipe-mode launcher variant | 🔲 Ready | bun-launcher-pipe.ts |
| Analyze diagnostic results | 🔲 Waiting | Update trajectory doc |
| Draft IT allowlist request | 🔲 If needed | IT_ALLOWLIST_REQUEST.md |

### 🟢 GPT-5.2 Codex (Other Session)
**Role**: Execution, runtime testing, terminal operations

| Task | Status | Output |
|------|--------|--------|
| Run win11-diagnostic.ts | 🔲 Ready | Paste output back |
| Test pipe-mode launcher | 🔲 Ready | Report success/failure |
| Capture firewall/WDAC status | 🔲 Ready | Paste diagnostic output |
| Kill hung processes if needed | 🔲 Standby | taskkill commands |

---

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Claude generates diagnostic script                 │
│          → User copies to Codex session                     │
│          → Codex runs script, captures output               │
│          → User pastes output back to Claude                │
├─────────────────────────────────────────────────────────────┤
│  STEP 2: Claude analyzes results, generates fix             │
│          → User copies fix to Codex session                 │
│          → Codex applies and tests fix                      │
│          → User reports result to Claude                    │
├─────────────────────────────────────────────────────────────┤
│  STEP 3: Iterate until browser launches OR                  │
│          → Confirm WSL2 fallback required                   │
│          → Generate IT documentation                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Message Templates

### User → Codex
```
Claude generated this file. Please:
1. Save it to bun-playwright-poc/win11-diagnostic.ts
2. Run: bun run bun-playwright-poc/win11-diagnostic.ts
3. Paste full output back to me
```

### User → Claude
```
Codex ran the diagnostic. Output:
[paste output here]

What's next?
```

---

## Shared State (Update After Each Step)

| Checkpoint | Result | Agent |
|------------|--------|-------|
| TCP to 127.0.0.1:19222 | ❓ | Codex will test |
| HTTP to /json/version | ❓ | Codex will test |
| WebSocket upgrade | ❓ | Codex will test |
| Pipe mode works | ❓ | Codex will test |
| WSL2 works | ❓ | Codex will test |

---

## Current Handoff

**Claude → Codex**: I'll now generate win11-diagnostic.ts as a runnable file. 

User: Tell Codex to run it and report results.
