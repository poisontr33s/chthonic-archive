# 🔬 THE AUTOPSY PROTOCOL: DEBT DECOMPOSITION

## 1. STRATEGIC CONTEXT
- **Objective**: Systematic extraction and refactoring of "Hostile Debt" identified by the `overnight_daemon.ts`.
- **Trigger**: Presence of files in `dumpster-dive/intake/overnight-siphon/`.
- **Mindset**: Triage Surgeon. Do not "fix" bugs; decompose "rot" into manageable structures.

## 2. TEMPORAL ROUTINES (Norwegian Timezone / CET)
- **04:00 - 05:00**: Daemon completes its run. Siphon is populated.
- **08:00 - 09:00**: Morning Triage. The AI analyzes the `report.json` and selects the "Primary Corpse."
- **Ongoing**: Refactor proposals are generated and validated against the `calculateDebtScore` formula.

## 3. PROCEDURAL STEPS (The "Autopsy")

### Step A: Reason Retrieval
- Locate the entry for the target file in the latest `report.json`.
- Identify the specific **Smells** triggered:
    - `🚨 Critical Complexity` / `⚠️ High Complexity`
    - `Documentation Debt` (Density < 0.20)
    - `Anti-pattern: Deeply nested logic` (Nesting > 5)
    - `Governance: Fragile error handling` (Rust `unwrap`)

### Step B: Structural Audit
- Read the siphoned file from `dumpster-dive/intake/overnight-siphon/`.
- Map the code sections corresponding to the debt "Smells."
- Identify the "Brain" (The dense, low-documentation core logic).

### Step C: The Decomposition Plan
Generate a plan that follows these priorities:
1. **Decouple the Brain**: Extract the 500+ line functions into smaller, deterministic modules.
2. **Support the Connective Tissue**: Add docstrings to bring Documentation Density above 30% (Zeroing the multiplier).
3. **Safety compliance**: Replace dangerous patterns (`unwrap`, `any`, `eval`) with robust equivalents (`Result`, interfaces, sandboxed logic).

### Step D: Validation
- Simulate the `calculateDebtScore` for the proposed change.
- The refactor is only successful if the **Debt Score** is reduced by >40% without breaking functional parity.

## 4. OUTPUT FORMAT
- **Diagnosis**: 1-sentence summary of why the file was "dying."
- **Anatomy**: List of functions/modules being extracted.
- **Resulting Score**: Predicted new Debt Score.
- **The Scalpel**: Unified diff or tool calls to implement the changes.
