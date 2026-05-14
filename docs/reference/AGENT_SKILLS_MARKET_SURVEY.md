---
type: reference
category: agent-skills
created: 2026-05-13
status: reference
---

# Agent Skills Market Survey

Purpose: give local skill standards enough external context to avoid one-off design. This file is descriptive, not normative. Local rules still come from `skill-creator`, `AGENTS.md`, `AGENT_COMMON.md`, and repo gates.

## Baselines

| Source | What It Contributes | Local Use |
|---|---|---|
| OpenAI `openai/skills` | `SKILL.md` with `name` and `description`, optional `agents/openai.yaml`, and resource folders for scripts/references/assets. | Canonical Codex/OpenAI skill shape. |
| Anthropic `anthropics/skills` | Public reference skill collection, including complex document skills and folder-level `SKILL.md` patterns. | Cross-flavor comparison and production examples. |
| Claude Code docs | Project/personal/plugin skill locations, live discovery, `description`-driven loading, supporting files. | Claude flavor compatibility. |

## Market Directories

| Directory | Signal | Useful For |
|---|---|---|
| ClaudSkills | Large indexed registry with tags by language, provider, framework, and task type; advertises quality scoring and one-click install as paid features. | Seeing market categories, common tags, and packaging expectations. |
| agentskills.me | Curated list across Claude Code, Cursor, OpenCode, Codex CLI, and Gemini CLI; exposes popularity/star signals and concrete trigger phrasing. | Comparing cross-agent skill descriptions and triggers. |
| Awesome Agent Skills | Broad directory spanning `SKILL.md` skills, MCP servers, Gemini extensions, and adjacent agent config; useful because it mixes true skills with neighboring ecosystems. | Separating true skills from adjacent extension/plugin ecosystems. |

## Paid Marketplace Signals

| Market | Current Signal | Local Takeaway |
|---|---|---|
| Agensi | Public pricing guide lists free skills for reputation, single-purpose skills around `$3-$9`, comprehensive packages around `$12-$25`, and an `80%` seller share; browse pages show free and paid listings side by side. | Use free skills for reputation and narrowly priced paid skills for tested utility. |
| SkillHQ | Paid marketplace for SKILL.md packages and Custom GPT configs; advertises structure/content/security validation, CLI install, anti-piracy fingerprinting, an `85%` seller share, and a `€2` minimum paid price. | Buyers value validation, install friction removal, and seller trust. |
| MintSkills | Paid layer for skills, MCP servers, prompts, starter kits, and configs; emphasizes static analysis, dependency checks, content hashing, similarity scans, license-gated delivery, and an `80%` seller share. | Verification is itself a product feature. |
| skill.broker | Presents skills as structured procedural definitions with evidence pointers, confidence, evaluation criteria, provenance metadata, and credit pricing. | Provenance and evaluation criteria can distinguish serious skills from prompts. |

## Creator Economy Notes

The market is not only "sell a clever prompt." The stronger commercial shape is:

1. Solve a real repeated workflow with an agent-native procedure.
2. Keep `SKILL.md` compact and obvious to trigger.
3. Add deterministic scripts only where they reduce buyer friction or improve reliability.
4. Include examples, verification commands, and failure boundaries.
5. Package provenance: where the method came from, what it was tested on, and what claims it does not make.
6. Treat security and path hygiene as sellable quality, not boring compliance.

Useful product archetypes:

| Archetype | Buyer Pain | What Makes It Worth Paying For |
|---|---|---|
| Workflow accelerator | Repeated work takes too many prompts. | Clear trigger, exact steps, one-command verification. |
| Expert procedure | User lacks domain method. | Evidence-backed steps, decision criteria, examples. |
| Safety gate | Agents make expensive mistakes. | Deterministic checks, fail-fast output, low false positives. |
| Portability adapter | Skill works in one agent but not another. | Cross-flavor metadata, install docs, compatibility tests. |
| Artifact factory | User wants consistent outputs. | Templates/assets, examples, quality rubric. |

## Ranking And Learning Loop

Treat rankings as a feedback loop, not validation of personal worth.

1. Publish a free, sharp utility skill to gather installs and issue reports.
2. Publish one paid "pro" version with scripts, references, and verification gates.
3. Track trigger clarity: can the agent select the skill without the user naming it?
4. Track time-to-value: can a buyer run it within five minutes?
5. Track failure reports: convert confusion into examples or tests.
6. Track portability: Claude, Codex, Gemini, Cursor/OpenCode where relevant.
7. Avoid "world-bible" bloat. A skill is a compact executable method, not an SSOT archive.

Local first candidates:

| Candidate | Why It Has Market Shape | Local Proof To Build |
|---|---|---|
| Pathfinder Link Guard | Many repos have stale Markdown paths, heading anchors, line anchors, GitHub `blob`/`raw`/issue links, and agent-created broken links. | `bun run pathfinder:ci`, `bun run pathfinder:gfm`, staged pre-commit integration, before/after examples. |
| Skill Portability Checker | The market spans Claude, Codex, Gemini, Cursor, OpenCode, and OpenClaw-style skill shapes. | Cross-flavor validator, `agents/openai.yaml` normalization, flavor-specific frontmatter report. |
| Agent Permission Boundary Audit | Buyers fear malicious or overpowered skills. | Static checks for env reads, network calls, exec/eval, credential access, and dangerous shell usage. |
| Context Discipline / Handoff Skill | Long agent sessions lose state or bloat instruction files. | Compact handoff templates, quality gate, resume packet examples. |

Pathfinder GFM expansion target:

1. Same-repo GitHub file URLs should validate `blob`, `tree`, `raw`, and `raw.githubusercontent.com` shapes.
2. Same-repo GitHub links that look like file paths but omit `blob` or `tree` should be fixable.
3. Bare GitHub URLs and HTML `href`/`src` README media references should be included in GitHub mode.
4. GitHub issue, release, action, and uploaded asset links should be checked only in explicit online mode.
5. A real reference case is [EOAI-PII-My-AI-IDEA](https://github.com/poisontr33s/EOAI-PII-My-AI-IDEA), where README media can point at a GitHub issue such as [issue #5](https://github.com/poisontr33s/EOAI-PII-My-AI-IDEA/issues/5).
6. A same-repo URL such as [AGENT_COMMON.md](https://github.com/poisontr33s/chthonic-archive/blob/main/AGENT_COMMON.md) should validate against the local checkout.

## Commercial Guardrails

1. Do not clone paid skills or evade paywalls.
2. Learn from visible market patterns, then build original workflows from local experience.
3. Check licenses before adapting open-source skills.
4. Never ship secrets, machine paths, or repo-private content.
5. Prefer proof over promises: include tests, screenshots, transcripts, or sample outputs.
6. State platform support honestly.

## Common Skill Categories

| Category | Examples Seen In The Market | Local Standard Implication |
|---|---|---|
| Coding workflow | commit writer, dependency updater, code review, architecture diagrams | Trigger descriptions must name concrete user asks and repo actions. |
| Framework expertise | React/Next.js, Remotion, Expo, PyTorch docstrings | Prefer concise `SKILL.md` plus focused `references/` for framework detail. |
| Artifact generation | slides, diagrams, documents, memes, video/audio summaries | Use `assets/` only when the output actually consumes templates/media. |
| Agent operations | handoff, session resume, command/plugin creation, skill judge | Avoid duplicate meta-skills; extend the existing meta-skill lane. |
| External tool execution | MCP, GitHub, cloud, APIs, local CLIs | Treat third-party scripts as untrusted until reviewed and gated. |

## Quality Signals

1. `description` states exactly when the skill should trigger.
2. `SKILL.md` is concise and routes detail to `references/`.
3. Deterministic work uses scripts, and scripts have a clear verification command.
4. Skill has a declared safety boundary: what it may read, write, execute, or call.
5. Cross-agent variants preserve shared workflow while isolating flavor-specific metadata.
6. External skill imports require source review, license check, and local path/link validation.

## Risk Signals

1. Broad trigger text like "use for all coding tasks".
2. Hidden network or shell execution in bundled scripts.
3. Credentials, tokens, or hardcoded local paths.
4. README-heavy packages where `SKILL.md` is thin or stale.
5. Large duplicate skill sets where the same intent appears under many names.
6. Missing provenance, license, or validation evidence.

## Local Adoption Rule

Use the market to classify and benchmark skills. Do not copy a market skill directly into `.codex/skills` or `.claude/skills` without:

1. Reading `SKILL.md` and all executable scripts.
2. Checking license and provenance.
3. Running `bun run pathfinder:ci`.
4. Running the relevant skill validator.
5. Preserving local naming, trigger, and progressive-disclosure standards.

## Source Links

- OpenAI skills baseline: https://github.com/openai/skills
- Anthropic skills repository: https://github.com/anthropics/skills
- Claude Code skills docs: https://docs.claude.com/en/docs/claude-code/skills
- ClaudSkills registry: https://claudskills.com/
- Agent Skills directory: https://agentskills.me/
- Awesome Agent Skills: https://awesomeagentskills.dev/
- Agensi pricing guide: https://www.agensi.io/learn/how-to-price-skill-md-skills
- Agensi browse page: https://www.agensi.io/browse
- SkillHQ: https://skillhq.dev/
- SkillHQ seller page: https://skillhq.dev/become-seller
- MintSkills: https://www.mintskills.ai/
- skill.broker: https://skill.broker/
- AgentVerus-scanned public collection example: https://github.com/jdrhyne/agent-skills
- Research snapshot: https://arxiv.org/abs/2602.08004
- Security ecosystem snapshot: https://arxiv.org/abs/2603.16572
