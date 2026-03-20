# Skill Tensor Plan

- Seed: `trainstop-default-seed`
- Seed Value: `12077687225398345945`
- Chain Length: `4`

## Steps
### Step 1
- Executor: `gemini`
- Operator: `link-path-guard`
- Target: `.claude/skills::mailbox-handoff`
- Flavor: `claude`
- Safety: `cross_lane_mutation`
- Artifact Class: `log`
- Command: `uv run scripts/skill_path_guard.py .claude\skills\mailbox-handoff\SKILL.md`

### Step 2
- Executor: `codex`
- Operator: `skill-polisher`
- Target: `.claude/skills::codekiller-remediation-gate`
- Flavor: `claude`
- Safety: `cross_lane_mutation`
- Artifact Class: `verification_report`
- Command: `uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude\skills\codekiller-remediation-gate --mode verify --target-flavor claude --no-require-assets`

### Step 3
- Executor: `codex`
- Operator: `skill-audit`
- Target: `.codex/skills::dumpster-upcycler`
- Flavor: `gemini`
- Safety: `read_only`
- Artifact Class: `machine_report`
- Command: `uv run scripts/skill_audit.py --flavor gemini --root .codex/skills --skill dumpster-upcycler`

### Step 4
- Executor: `codex`
- Operator: `skill-polisher`
- Target: `.claude/skills::imagegen`
- Flavor: `claude`
- Safety: `cross_lane_mutation`
- Artifact Class: `verification_report`
- Command: `uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude\skills\imagegen --mode verify --target-flavor claude --no-require-assets`

