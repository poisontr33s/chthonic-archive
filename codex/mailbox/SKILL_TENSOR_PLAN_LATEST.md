# Skill Tensor Plan

- Seed: `trainstop-default-seed`
- Seed Value: `12077687225398345945`
- Chain Length: `4`

## Steps
### Step 1
- Executor: `gemini`
- Operator: `link-path-guard`
- Target: `.codex/skills::trainstop-orchestrator`
- Flavor: `gemini`
- Safety: `cross_lane_mutation`
- Artifact Class: `log`
- Command: `uv run scripts/skill_path_guard.py .codex\skills\trainstop-orchestrator\SKILL.md`

### Step 2
- Executor: `codex`
- Operator: `trainstop-orchestrator`
- Target: `.claude/skills::iron-maiden-runtime`
- Flavor: `claude`
- Safety: `meta_orchestration`
- Artifact Class: `orchestration_report`
- Command: `uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target claude --lane maintenance`

### Step 3
- Executor: `codex`
- Operator: `skill-polisher`
- Target: `.claude/skills::gh-fix-ci`
- Flavor: `gemini`
- Safety: `cross_lane_mutation`
- Artifact Class: `verification_report`
- Command: `uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude\skills\gh-fix-ci --mode verify --target-flavor gemini --no-require-assets`

### Step 4
- Executor: `codex`
- Operator: `skill-audit`
- Target: `.claude/skills::corpse-reviver`
- Flavor: `codex`
- Safety: `read_only`
- Artifact Class: `machine_report`
- Command: `uv run scripts/skill_audit.py --flavor codex --root .claude/skills --skill corpse-reviver`

