# High-Velocity Architecture Shift: The Chthonic Neural Bus

This document outlines the substantial architecture shift to leverage the Triumvirate: Claude Opus 4.6 (Architect), Codex 5.3 (Fabricator), Gemini 3 Pro (Executive), and the Local RTX 4090 (Reflex Cortex).

## The Core Concept

We are not building a chatbot. We are building a **Self-Correction Hypervisor**.

The local RTX 4090 is not a "conversation partner," but the **"Reflex Cortex"**—a zero-latency, privacy-first pre-processor that handles the OODA loop (Observe-Orient-Decide-Act) for the heavy cloud agents.

## The Roles (The Triad)

| Agent | Version | Role | Responsibility |
| :--- | :--- | :--- | :--- |
| **Claude** | **Opus 4.6** | **The Architect** | **Strategy & System Design.** He does not write boilerplate. He ingests high-level goals and outputs *Architectural Specs* (in Markdown/Mermaid). He is the "CPU" of the operation—high cost, high intelligence. |
| **Codex** | **5.5** | **The Fabricator** | **Implementation & Polyglot.** He takes Claude's specs and writes the *actual* Rust/Solana/React code. He is the "GPU" of the operation—massively parallel code generation, strict syntax adherence. |
| **Gemini** | **3.1 Pro** | **The Executive** | **Orchestration & Tools.** I am the OS. I run the shell, I manage the file system, I execute the builds. I am the "Bus" connecting Claude's brain to Codex's hands. |
| **Local 4090** | **Hermes 4** | **The Reflex** | **Context & Triage.** It runs locally. It indexes your repo. It filters noise. It answers: *"Is this code safe to run?"* or *"Summarize these 50 files so Claude doesn't hit context limits."* |

---

## The Build: "Chthonic Neural Bus"

We will build a **Headless Event Loop** using the stack (Bun + Rust + ExLlamaV2).

### The Workflow:
1.  **User Input:** You give a directive: *"Refactor the Solana anchor program to use the new IDL standard."*
2.  **Gemini (Me):** I activate. I do *not* write the code.
    *   I call the **Local 4090 (Reflex)** to scan the `programs/` directory and generate a *compressed context map* (removing comments, whitespace, irrelevant tests).
3.  **Handoff to Claude:** I feed the *Goal* + *Context Map* to Claude.
    *   Claude outputs a **Spec File** (`.chthonic/specs/refactor_v1.md`). This contains the *logic*, not the code.
4.  **Handoff to Codex:** I trigger Codex.
    *   Codex reads `refactor_v1.md` and the existing files.
    *   Codex writes the Rust implementation.
5.  **Validation Loop (The Edge):**
    *   I run `anchor build`.
    *   **If it fails:** I pass the error log + specific failing code chunk to the **Local 4090**.
    *   **The 4090** attempts a "Quick Fix" (syntax/import errors).
    *   **If 4090 fails:** I escalate back to **Codex**.

---

## Technical Implementation (The "Substantial" Part)

We need three specific tools to make this real. We will write them in **Rust** (for speed) and **TypeScript** (for glue).

### A. `context-compressor` (Rust + Local LLM)
A tool that uses the 4090 to "read" your repository and generate "Context Packets" for the cloud agents.
*   *Why?* Claude Opus 4.6 has a massive context window, but filling it with junk is inefficient. The 4090 acts as a smart compression algorithm.

### B. `spec-enforcer` (Bun script)
A daemon that watches for new `.md` files in `.chthonic/specs/`.
*   When Claude writes a spec, this daemon automatically triggers a "Codex Request" (simulated or API) to scaffold the files.

### C. `reflex-guard` (Python + ExLlamaV2)
A pre-commit hook run by the 4090.
*   Before any code is committed by Codex/Gemini, the 4090 scans the diff for "Hallucinations" (e.g., importing libraries that don't exist in `Cargo.toml`).

---

## The "Standard" to Build (Your Directive)

Forget "chatting." Let's build the **Infrastructure for the Triumvirate**.

### Phase 1: The Local Reflex Service (Headless)
We need the 4090 to be an API, not a chatbot.
*   **Action:** Deploy **TabbyAPI** (as discussed) but *headless*.
*   **Model:** **Nous-Hermes-4-14B-EXL2 (6.0bpw)**. This is the smartest model that fits your 16GB VRAM for "Context Analysis."

### Phase 2: The Context Compressor
I will write a script to use that API to "digest" your repo.

### Phase 3: The Handoff Protocol
We define a strict Markdown format for Claude to pass instructions to Codex.

**Shall we initialize the "Chthonic Neural Bus" architecture?** I can start by setting up the headless 4090 service and the first Rust tool for context compression.
