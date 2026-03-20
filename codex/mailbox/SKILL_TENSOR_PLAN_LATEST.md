# Skill Tensor Plan

- Seed: `trainstop-default-seed`
- Seed Value: `12077687225398345945`
- Chain Length: `4`

## Steps
### Step 1
- Executor: `claude`
- Operator: `link-path-guard`
- Target: `.codex/skills::conceptualize`
- Flavor: `claude`
- Action Scope: `skill`
- Action Key: `['link-path-guard', 'skill', '.codex/skills', 'conceptualize']`
- Safety: `cross_lane_mutation`
- Artifact Class: `log`
- Command: `uv run scripts/skill_path_guard.py .codex\skills\conceptualize\SKILL.md`

### Step 2
- Executor: `codex`
- Operator: `skill-audit`
- Target: `.gemini/extensions/chthonic-archive-sync/skills::openai-docs`
- Flavor: `gemini`
- Action Scope: `skill`
- Action Key: `['skill-audit', 'skill', 'gemini', '.gemini/extensions/chthonic-archive-sync/skills', 'openai-docs']`
- Safety: `read_only`
- Artifact Class: `machine_report`
- Command: `uv run scripts/skill_audit.py --flavor gemini --root .gemini/extensions/chthonic-archive-sync/skills --skill openai-docs`

### Step 3
- Executor: `gemini`
- Operator: `link-path-guard`
- Target: `.claude/skills::api-manager`
- Flavor: `codex`
- Action Scope: `skill`
- Action Key: `['link-path-guard', 'skill', '.claude/skills', 'api-manager']`
- Safety: `cross_lane_mutation`
- Artifact Class: `log`
- Command: `uv run scripts/skill_path_guard.py .claude\skills\api-manager\SKILL.md`

### Step 4
- Executor: `claude`
- Operator: `skill-polisher`
- Target: `.claude/skills::openai-docs`
- Flavor: `claude`
- Action Scope: `skill`
- Action Key: `['skill-polisher', 'skill', 'verify', 'claude', '.claude/skills', 'openai-docs']`
- Safety: `local_mutation`
- Artifact Class: `verification_report`
- Command: `uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude\skills\openai-docs --mode verify --target-flavor claude --no-require-assets`

