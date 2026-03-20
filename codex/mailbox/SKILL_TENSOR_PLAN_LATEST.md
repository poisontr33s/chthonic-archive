# Skill Tensor Plan

- Seed: `trainstop-default-seed`
- Seed Value: `12077687225398345945`
- Chain Length: `4`

## Steps
### Step 1
- Executor: `claude`
- Operator: `skill-polisher`
- Target: `.gemini/extensions/chthonic-archive-sync/skills::gh-mcp-autonomy`
- Flavor: `codex`
- Action Scope: `skill`
- Action Key: `['skill-polisher', 'skill', 'verify', 'codex', '.gemini/extensions/chthonic-archive-sync/skills', 'gh-mcp-autonomy']`
- Safety: `cross_lane_mutation`
- Artifact Class: `verification_report`
- Command: `uv run .claude\skills\skill-polisher\skill-polisher\scripts\polish_skill.py .gemini\extensions\chthonic-archive-sync\skills\gh-mcp-autonomy --mode verify --target-flavor codex --no-require-assets`

### Step 2
- Executor: `gemini`
- Operator: `link-path-guard`
- Target: `.claude/skills::imagegen`
- Flavor: `codex`
- Action Scope: `skill`
- Action Key: `['link-path-guard', 'skill', '.claude/skills', 'imagegen']`
- Safety: `cross_lane_mutation`
- Artifact Class: `log`
- Command: `uv run scripts/skill_path_guard.py .claude\skills\imagegen\SKILL.md`

### Step 3
- Executor: `claude`
- Operator: `mailbox-handoff`
- Target: `.codex/skills::gh-fix-ci`
- Flavor: `codex`
- Action Scope: `skill`
- Action Key: `['mailbox-handoff', 'skill', 'codex', 'codex', '.codex/skills', 'gh-fix-ci']`
- Safety: `read_only`
- Artifact Class: `link_report`
- Command: `uv run .claude\skills\mailbox-handoff\mailbox-handoff\scripts\mailbox_check.py --mode link-canon --link-canon-file .codex\skills\gh-fix-ci\SKILL.md --link-canon-no-fail`

### Step 4
- Executor: `codex`
- Operator: `link-path-guard`
- Target: `.gemini/extensions/chthonic-archive-sync/skills::iron-maiden-runtime`
- Flavor: `claude`
- Action Scope: `skill`
- Action Key: `['link-path-guard', 'skill', '.gemini/extensions/chthonic-archive-sync/skills', 'iron-maiden-runtime']`
- Safety: `cross_lane_mutation`
- Artifact Class: `log`
- Command: `uv run scripts/skill_path_guard.py .gemini\extensions\chthonic-archive-sync\skills\iron-maiden-runtime\SKILL.md`

