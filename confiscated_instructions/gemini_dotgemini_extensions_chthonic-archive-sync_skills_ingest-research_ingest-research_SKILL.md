---
name: ingest-research
description: Ingest Gemini/Deep Research artifacts into structured digests and optional cross-mailbox handoff notes.
metadata:
  short-description: "Normalize research docs into actionable digests and handoff packets."
  argument-hint: "uv run scripts/ingest_research.py [path] --target-mailbox claude|codex --handoff-to claude|codex"
  triggers:
    - "ingest deep research"
    - "process research handoff"
    - "summarize gemini research"
    - "route research digest"
---

# Ingest Research Skill

Use this skill to turn raw research artifacts into continuation-ready mailbox outputs.

## Outputs

- Digest: `claude/mailbox/RESEARCH_DIGEST_<TOPIC>.md` or `codex/mailbox/RESEARCH_DIGEST_<TOPIC>.md`
- Optional handoff note: `SESSION_HANDOFF_RESEARCH_<TOPIC>_<TIMESTAMP>.md`
- Optional source forwarding: `RESEARCH_SOURCE_<TOPIC>.<ext>`

## Local LLM Gate (Nightly Pivot)

Before ingesting local-LLM-generated archaeology/research material, check:
- `codex/mailbox/LOCAL_AI_READINESS_LATEST.md`
- `claude/mailbox/LOCAL_AI_READINESS_LATEST.md`

If `Ready for skill integration` is `false`, ingest as informational only and do not mark decisions as enforceable.

## Command

Auto-detect newest research source and write digest:
```powershell
uv run scripts/ingest_research.py
```

Clipboard-first ingest (captures what you copied, writes `equivalent.md` in mailbox, then parses):
```powershell
uv run scripts/ingest_research.py --clipboard --source-name equivalent.md --topic "Deep Research Candidate" --target-mailbox codex --from-agent codex
```

Ingest explicit source and write to Codex mailbox:
```powershell
uv run scripts/ingest_research.py claude/mailbox/GEMINI_DEEP_RESEARCH_SOLANA.md --target-mailbox codex --from-agent codex
```

Ingest and send handoff to Claude (plus forward source doc):
```powershell
uv run scripts/ingest_research.py claude/mailbox/GEMINI_DEEP_RESEARCH_SOLANA.md --target-mailbox codex --handoff-to claude --from-agent codex --to-agent claude --forward-source
```

## Protocol Contract

Digest sections are deterministic:
1. Findings
2. Decisions table: `| Decision | Options | Recommendation |`
3. Actionable checklist with route tags: `[chthonic]`, `[codex]`, `[gemini]`, `[manual]`
4. Dependencies mapped to install vectors (`uv tool`, `cargo install`, `bun add -g`, `winget`, `manual`)
5. Contradictions prefixed with `CONFLICT:`

Research informs decisions; it does not apply code changes by itself.

## Invocation Pattern

When invoking from chat, call the skill directly (for example `/ingest-research`) and specify:
- clipboard mode (`--clipboard`)
- source filename (`--source-name equivalent.md`)
- target mailbox and optional handoff target
