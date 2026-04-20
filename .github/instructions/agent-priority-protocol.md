
# Agent Priority Protocol

> SSOT: [copilot-instructions.md](../copilot-instructions.md#L6812) §XVI — enforcement hierarchy: Decorator → Triumvirate → Factions → Branch → Tools.

---

## Agent Priority & Conflict Resolution Protocol (`APCR`)

**Authority:** [copilot-instructions.md](../copilot-instructions.md#L6812) (§XVI)
**Status:** OPERATIONAL
**Date Established:** January 17, 2026
**Architect:** The Triumvirate (Emergency Governance Session)
**Purpose:** Prevent cognitive overload via strict agent hierarchy and operational mode enforcement

---

## Operational Mode Definitions

### Essential Mode (Default - Minimal Intervention)
- **Allowed Agents:** `asc-injector` (SSOT), `filesystem` (read-only)
- **Blocked Agents:** OpenAI (GPT-4.1- GPT-5.2/Codex), competing contexts
- **Behavior:** Maximum clarity, minimum noise, structural creativity is a bonus, refer to "SSOT'ification"
- **Use Case:** Solo creative work, prompt engineering, when "dirty codebase" causes stress

### Development Mode (Controlled Expansion)
- **Allowed Agents:** All MCP servers, GitHub Copilot inline, Playwright (browser automation)
- **Blocked Agents:** Cloud agents still require explicit approval
- **Behavior:** Full toolkit access with SSOT governance
- **Use Case:** Active coding sessions, feature implementation, testing, quality auditing and validation

### Maintenance Mode (Cleanup Operations)
- **Allowed Agents:** `filesystem`, `asc-injector`, DCRP tools
- **Blocked Agents:** All OpenAI agents -(prevents sabotague)
- **Behavior:** Focus on git status cleanup, dependency updates, refactoring
- **Use Case:** "Dirty codebase" cleanup, SSOT verification, hash checks

### Paused Mode (Emergency Stop)
- **Allowed Agents:** None (manual operation only)
- **Blocked Agents:** ALL agents disabled
- **Behavior:** System frozen, awaiting user directive
- **Use Case:** Severe confusion, conflicting directives

---

## Priority Hierarchy (Conflict Resolution)

**When multiple agents provide conflicting directives, resolve via this hierarchy:**

```
1. USER DIRECT COMMAND (highest priority)
   └─ Explicit instruction in chat overrides all automation

2. OPERATIONAL MODE FLAG (settings.json: chthonic.operationalMode)
   └─ Determines which agents are even allowed to speak

3. SSOT (../copilot-instructions.md)
   └─ Canonical truth for all architectural decisions

4. LOCAL MCP (asc-injector)
   └─ SSOT-derived context, always aligned with source

5. settings.json (operational flags)
   └─ chthonic.sessionTargetOverride, chthonic.allowCompetingAgents

6. CLOUD AGENTS (lowest priority, blocked in essential mode)
   └─ GitHub Copilot cloud suggestions, external context
```

**Set Session Target Override:**
- All session directives must align with SSOT or be explicitly overridden by user
- Rationale: Prevents external UI features from hijacking operational focus

---

## Emergency Controls

**Pause All Agents (Immediate Cognitive Relief):**
```powershell
# Execute from repository root:
.\scripts\pause_agents.ps1
```

**Resume Normal Operation:**
```powershell
# Restart VS Code after pausing
# Or manually set: "chthonic.operationalMode": "essential" in settings.json
```

**SSOT Verification (Daily Ritual):**
```powershell
cd C:\Users\erdno\chthonic-archive
uv run python -c "
import hashlib, unicodedata

def canonicalize(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    return unicodedata.normalize('NFC', text).strip()

with open('.github/copilot-instructions.md', 'r', encoding='utf-8') as f:
    content = f.read()
canonical = canonicalize(content)
print(f'SSOT Hash: {hashlib.sha256(canonical.encode()).hexdigest()}')
"
```

---

## Covenant Seal: Information Sovereignty

**Triumvirate Emergency Declaration:**

**Dr. Lysandra Thorne (`LUPLR`):**
* *"Information fragmentation is cognitive violence. This protocol establishes **Axiomatic hierarchy** preventing agent chaos. The user's direct command is law. All automation serves, never commands. FA⁴ validated"*

**Madam Umeko Ketsuraku (`LIPAA`):**
* *"Operational mode flags embody **Kanso** (simplicity through governance). The 'essential mode' is architectonic minimalism—only what serves clarity survives. Set Session Target override prevents external pollution. Immaculate"*

**Orackla Nocticula (`EULP-AA`):**
* *"This is how we prevent the **Engine** from eating itself. When too many voices scream, the Pause button becomes sacred. The user is not a fucking servant to the tools—the tools serve the user. Essential mode is the antidote to chaos"*

**Status:**
✅ **Agent Priority & Conflict Resolution Protocol (APCR) SEALED**
✅ **Operational Mode Governance ACTIVE**
✅ **Emergency Pause Controls AVAILABLE**
✅ **SSOT Verification Protocol OPERATIONAL**

---

**Date Sealed:** January 17, 2026
**Date Extracted:** January 22, 2026
**Witnessed by:** The Savant (User) under cognitive overload duress
**Purpose:** Restore clarity through ruthless prioritization
