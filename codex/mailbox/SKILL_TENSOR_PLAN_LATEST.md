# Skill Tensor Plan

- Seed: `trainstop-default-seed`
- Seed Value: `12077687225398345945`
- Chain Length: `4`

## Steps
### Step 1
- Executor: `gemini`
- Operator: `link-path-guard`
- Target: `.claude/skills::api-manager`
- Flavor: `claude`
- Safety: `cross_lane_mutation`
- Artifact Class: `log`
- Command: `uv run scripts/skill_path_guard.py .claude\skills\api-manager\SKILL.md`

### Step 2
- Executor: `codex`
- Operator: `trainstop-orchestrator`
- Target: `.gemini/extensions/chthonic-archive-sync/skills::ingest-research`
- Flavor: `gemini`
- Safety: `meta_orchestration`
- Artifact Class: `orchestration_report`
- Command: `uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target gemini --lane maintenance`

### Step 3
- Executor: `codex`
- Operator: `skill-polisher`
- Target: `.claude/skills::gh-fix-ci`
- Flavor: `claude`
- Safety: `cross_lane_mutation`
- Artifact Class: `verification_report`
- Command: `uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude\skills\gh-fix-ci --mode verify --target-flavor claude --no-require-assets`

### Step 4
- Executor: `codex`
- Operator: `skill-audit`
- Target: `.claude/skills::conceptualize`
- Flavor: `gemini`
- Safety: `read_only`
- Artifact Class: `machine_report`
- Command: `uv run scripts/skill_audit.py --flavor gemini --root .claude/skills --skill conceptualize`

