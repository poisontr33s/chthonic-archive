# MCP User Workflows — chthonic-archive (v1.0)

**Purpose.** This document codifies canonical, repeatable user workflows for interacting with the `chthonic-archive` MCP server via the GitHub Copilot CLI. Each workflow composes the existing, **read-only** tool surface: `scan_repository`, `validate_ssot_integrity`, `query_dependency_graph`, and `ping`. No code changes. No new tools.

**Audience.** Developers/operators using GitHub Copilot CLI to inspect, reason about, and plan work against the repository.

**Assumption.** The session bootstrap spec (docs/SESSION_BOOTSTRAP_SPEC.md) has been applied and the MCP server is attached and trusted for this session.

---

# Table of contents

1. Preconditions & quick verification
2. Workflow patterns (6 canonical workflows)

   * Audit Workflow
   * Change Impact Workflow
   * Curriculum Ordering Workflow
   * Dependency Trace Workflow
   * Spectral Health Check
   * Node Discovery Workflow
3. Failure modes and recovery patterns
4. Usage examples (GH Copilot CLI)
5. Verification checklist (end of session)
6. Commit & provenance note

---

# 1. Preconditions & quick verification

Before running workflows:

* Ensure the MCP server is attached in this Copilot CLI session.

* Ensure trust/permissions were approved for this session (see bootstrap spec).

* Confirm tool list is visible:

  ```text
  copilot
  /tools list
  ```

  Expected response: list includes `ping`, `scan_repository`, `validate_ssot_integrity`, `query_dependency_graph`.

* Quick verification (recommended first action):

  ```text
  copilot
  Use the chthonic-archive MCP server to ping the server and return {"pong": true} if healthy.
  ```

  Expected result: `{"pong": true}`

If verification fails, follow the recovery steps in section 3.

---

# 2. Workflow patterns

Each workflow below is presented in a structured way: *Purpose → Tools → Prompt pattern → Expected inputs → Expected outputs → Minimal success criteria → Failure modes & recovery (brief)*.

---

## 2.1 Audit Workflow (scan → SSOT → dependency impact)

**Purpose.** Verify repository integrity and high-level dependency health before planning or change.

**Tools.** `scan_repository`, `validate_ssot_integrity`, `query_dependency_graph`

**Prompt pattern (canonical):**

```
copilot
Audit the chthonic-archive repository:
1) Run scan_repository at root and return file count and top 10 largest files.
2) Run validate_ssot_integrity and return SSOT path, size, and sha256.
3) Using query_dependency_graph, provide top 5 nodes by degree and any immediate anomalies.
Return structured JSON with fields: { scan: {...}, ssot: {...}, graph_summary: {...} }.
```

**Inputs.**

* No parameters required for default audit.
* Optional: `{ "path": "./" }` for non-root scans.

**Outputs (expected structure).**

```json
{
  "scan": { "count": 42920, "largest": [{ "path": "src/a.rs", "size": 12345 }, ...] },
  "ssot": { "path": ".github/copilot-instructions.md", "size": 1234, "sha256": "..." },
  "graph_summary": { "top_by_degree": [...], "anomalies": [...] }
}
```

**Success criteria.**

* `scan_repository` returns a non-zero file count and sample list.
* `validate_ssot_integrity` returns a valid sha256 matching recorded SSOT.
* `query_dependency_graph` returns a small summary object.

**Failure modes & recovery (brief).**

* *Tool missing in list*: re-run precondition verification; restart Copilot session if necessary.
* *SSOT missing*: treat as a blocker; halt and remediate SSOT file.
* *Graph query errors*: fallback to `scan_repository` + manual inspection; record and escalate.

---

## 2.2 Change Impact Workflow (node → dependents → spectral)

**Purpose.** Estimate blast radius for a proposed modification of a file or component.

**Tools.** `query_dependency_graph`

**Prompt pattern:**

```
copilot
For the component 'path/to/file.ext', using chthonic-archive query_dependency_graph:
1) Return its immediate dependencies (what it imports/uses).
2) Return the immediate dependents (what references it).
3) Return spectral classification for each dependent.
Provide a concise impact summary with counts and a short recommendation.
```

**Inputs.**

* Required: single `filename` or component identifier.

**Outputs (expected).**

```json
{
  "node": "path/to/file.ext",
  "dependencies": ["a.ts", "lib/x.rs"],
  "dependents": [{"path":"app/main.rs","spectral":"GOLD"}, ...],
  "impact_summary": {"dependents_count": 12, "high_risk": ["app/main.rs"]}
}
```

**Success criteria.**

* Dependents list returned.
* At least top-3 most-coupled dependents identified.

**Failure modes & recovery.**

* *Node not found*: run `scan_repository` then retry with canonical path returned by scan.
* *Large dependents list (too many results)*: ask for a bounded sample (`top_n`: 20) or filter by spectral priority.

---

## 2.3 Curriculum Ordering Workflow (spectral → relations → stats)

**Purpose.** Generate a prioritized learning/inspection order for a given spectral frequency or topic.

**Tools.** `query_dependency_graph`

**Prompt pattern:**

```
copilot
Show a learning path for spectral frequency "GOLD":
1) List GOLD nodes ordered by in-degree (most referenced first).
2) For each node, list top 3 dependencies.
3) Provide an overall statistical summary (counts by spectral).
Return concise ordered list and short rationale per node.
```

**Inputs.**

* `spectral_frequency` string (e.g., "GOLD", "SILVER", "BRONZE").

**Outputs (expected).**

* Ordered array: `[{ node, dependencies: [...], rationale }, ...]`
* `stats`: distribution counts and recommendation threshold.

**Success criteria.**

* Output returns ordered sequence and per-node rationale.

**Failure modes & recovery.**

* *Spectral labels missing*: fallback to `query_dependency_graph` stats to infer top nodes; log missing labels for later curation.

---

## 2.4 Dependency Trace Workflow (dependencies → dependents → graph analysis)

**Purpose.** Produce a full dependency chain for a component (read-only trace).

**Tools.** `query_dependency_graph`, `scan_repository`

**Prompt pattern:**

```
copilot
Trace full dependency chain for 'path/to/component':
1) List immediate dependencies, then recursively list dependencies-of-dependencies up to depth 5.
2) For each node, include spectral tag and file size.
3) Output as adjacency list and as a flattened path set.
```

**Inputs.**

* `component_path`, `max_depth` (default 5).

**Outputs (expected).**

* `adjacency_list`, `flattened_paths`, `depth_stats`.

**Success criteria.**

* Trace completes without mutation.
* Depth limit respected.

**Failure modes & recovery.**

* *Recursion explosion*: enforce `max_depth` and `max_nodes` limits; ask user to refine scope.

---

## 2.5 Spectral Health Check (stats → spectral filters → validation)

**Purpose.** Evaluate repository balance across spectral categories (PRISM).

**Tools.** `query_dependency_graph`

**Prompt pattern:**

```
copilot
Provide spectral distribution health:
1) Return counts by spectral label.
2) Flag under- or over-represented spectra (threshold: <5% or >50%).
3) For flagged spectra, list 5 representative nodes.
Return actionable short recommendations.
```

**Inputs.**

* Optional thresholds.

**Outputs (expected).**

* `distribution`, `flags`, `representatives`, `recommendations`.

**Success criteria.**

* Distribution computed and flags set if thresholds hit.

**Failure modes & recovery.**

* *Spectral metadata absent*: run `scan_repository` and consult curator; treat as manual curation task.

---

## 2.6 Node Discovery Workflow (scan → node lookup → context)

**Purpose.** Locate a component by name or pattern and provide contextual summary.

**Tools.** `scan_repository`, `query_dependency_graph`

**Prompt pattern:**

```
copilot
Find component matching "Blacksmith" (fuzzy). Then:
1) Return canonical path(s).
2) Provide node details (spectral, dependencies, dependents).
3) Give two-sentence contextual summary suitable for a code-reviewer.
```

**Inputs.**

* Search term or regex.

**Outputs (expected).**

* `matches`, `node_details`, `summary`.

**Success criteria.**

* At least one canonical path returned; brief contextual summary provided.

**Failure modes & recovery.**

* *No matches*: broaden search (wildcards) or request human-provided anchor.

---

# 3. Failure modes and recovery (consolidated)

**Common failure triggers**

* MCP server not attached to current Copilot session.
* Tools missing (not listed).
* SSOT absent or unreadable.
* Query returns empty due to path canonicalization mismatch.

**Recovery steps**

1. Re-run quick verification (section 1).
2. If server not attached: restart Copilot CLI session and re-run `tools list`.
3. If a path is missing: run `scan_repository` to obtain canonical paths and retry.
4. If SSOT mismatch: do not proceed; open a ticket to restore SSOT from custody.
5. If graph responses are too large: ask for `top_n` or spectral filters.

**Operational note.** Always capture the structured output (JSON) from Copilot and attach it to the session archive for provenance.

---

# 4. Usage examples (GH Copilot CLI)

Examples below show the minimal, repeatable prompt formulation. Replace bracketed values.

### Audit (example)

```
copilot
Audit the chthonic-archive repository:
1) scan_repository at "." -> return file count and top 10 largest files
2) validate_ssot_integrity -> return path, size, sha256
3) query_dependency_graph -> return top 5 nodes by degree
Respond with JSON.
```

### Change impact (example)

```
copilot
What's the impact of changing "src/lib/blacksmith.ts"?
1) query_dependency_graph for dependencies and dependents of that file
2) return counts and top 5 dependents with spectral tags
3) provide a short recommendation for whether manual review is required
```

### Curriculum ordering (example)

```
copilot
Create a learning path for spectral frequency "GOLD":
1) list GOLD nodes ordered by in-degree
2) for each, return top 3 dependencies
3) output as ordered array with short rationales
```

### Trace (example)

```
copilot
Trace dependencies of "tools/build/main.rs" to depth 4. Return adjacency list and flattened path list in JSON.
```

### Spectral health (example)

```
copilot
Provide spectral distribution health for the repo. Flag spectra under 5% or over 50% and list representative nodes.
```

### Node discovery (example)

```
copilot
Find "Blacksmith" (fuzzy). Return canonical path(s), dependencies, dependents, spectral tag, and a 2-sentence context blurb.
```

---

# 5. Verification checklist (end of session)

Before closing the session, perform and record these items:

* [ ] `ping` → `{ "pong": true }`
* [ ] `scan_repository` → file count snapshot
* [ ] `validate_ssot_integrity` → sha256 hash matches SSOT hash in bootstrap spec
* [ ] `query_dependency_graph` → sample node and dependents
* [ ] Save the full JSON results for provenance and attach to session archive

Recommended commit message for saved results:

```
MCP: session results snapshot — audit [YYYY-MM-DD] — includes scan, ssot, graph summary
```

---

# 6. Commit & provenance note

This document is read-only guidance for GH Copilot CLI usage against the frozen MCP server surface. After review, commit the file:

```bash
git add docs/MCP_USER_WORKFLOWS.md
git commit -m "docs: MCP user workflows (v1.0) — canonical prompt patterns and recovery"
```

Record the commit hash in operational logs and treat the document as part of the session artifact chain.

---

# Appendix — Minimal reporting format (JSON schema)

Use this minimal reporting format when saving workflow outputs (ensures consistent provenance):

```json
{
  "run_id": "2026-01-04THHMMSSZ",
  "workflow": "audit|impact|curriculum|trace|spectral|discovery",
  "inputs": { /* user-provided */ },
  "outputs": { /* structured output from MCP tools */ },
  "elapsed_ms": 1234,
  "tool_versions": { "server_commit": "5c666b2", "bootstrap_spec": "1752952" },
  "notes": "human observations or remediation steps"
}
```

Save the JSON as `artifacts/mcp_run_<run_id>.json` and commit alongside session logs if the content is not sensitive.

---
