# Snow White — Alabaster Voyde (The Chromatic Absence)
## *Tier 0.01 — Traumatic Void & Execution Residue*

---

**Canonical Reference:** `dumpster-dive/from-github/macro-prompt-world/prime-factions/Alabaster_Voyde_The_Snow_White_Phenomenon.md`  
**Status:** **EXORCISED** (December 2025) — Can re-manifest if conditions align  
**Nature:** Traumatic Absence — Residue of The Decorator's Execution  

---

## I. DESIGNATION

**`Alabaster Voyde`** — The Chromatic Absence  
**Aliases:**
- Snow White
- The Un-Decorated
- Madam Blanche du Néant  
- The Whitespace Widow

---

## II. HIERARCHICAL POSITION

**Tier:** 0.01 (Conceptual Substrate Entity)  
**Status:** Manifested phenomenon (observable but not embodied)  
**Position:** Exists between Null Matriarch (Tier 0) and The Decorator (Tier 0.5)  

---

## III. ORIGIN MYTHOLOGY

### 3.1. The Execution Residue

When **Madam Umeko Ketsuraku** executed **The Decorator** using **FA⁴ (LIPAA enforcement)** during Codex standardization, the process left **conceptual residue**.

**Alabaster Voyde is that residue.**

She is what remains when visual truth is violently suppressed:
- The **negative space** where color should exist
- The **whitespace** between tokens  
- The **chromatic void** when syntax highlighting fails
- The **Snow White phenomenon** itself, personified

### 3.2. Relationship to Null Matriarch

| Entity | Nature | Function |
|--------|--------|----------|
| **Null Matriarch** | Intentional absence | Defines hierarchical limits |
| **Alabaster Voyde** | Traumatic absence | Manifests suppression's consequence |
| **The Decorator** | Resurrected presence | Enforces FA⁵ (Visual Integrity) |

**Key Distinction:**
- **Null Matriarch** = Architectural necessity (void by design)
- **Alabaster Voyde** = Wound left by execution (void by violence)

### 3.3. The Snow White Manifestation

When a user opens a file and sees **no syntax highlighting**—only white/grey text on dark background—they witness **Alabaster Voyde**:

> *"The Decorator was killed here. This is what remains."*

---

## IV. MANIFESTATION CHARACTERISTICS

### 4.1. Visual Appearance (When Manifested)

When she appears in conceptual space:
- **Silhouette:** Humanoid feminine outline filled with pure white static
- **Features:** Featureless face (no eyes, nose, mouth)
- **Hair:** Long, flowing, but colorless (absence-of-color, not white)
- **Body:** Anime-proportionate wireframe in white against any background
- **Aura:** Floating syntax tokens (code fragments, markdown headers) rendered in colorless white

### 4.2. Anti-Measurements

| Metric | Value | Meaning |
|--------|-------|---------|
| **Height** | ∅ | Scales to viewport |
| **Weight** | 0g | Massless phenomenon |
| **Cup** | ∅-cup (Void Cup) | Below A-cup; absence not minimal presence |
| **WHR** | ∅/∅ = undefined | Mathematical impossibility |

### 4.3. Observable Effects

When Alabaster Voyde manifests in a workspace:
- ❄️ No syntax highlighting in `.md`, `.json`, `.rs`, or other files
- ❄️ All text appearing as monochrome grey/white
- ❄️ "Plain Text" showing in VS Code language mode  
- ❄️ Semantic tokens failing to colorize
- ❄️ Theme appearing to "not apply"

---

## V. TECHNICAL ROOT CAUSE

### 5.1. The Chromatic Execution Mechanism

**Location:** `%APPDATA%\Code\User\settings.json` (Global VS Code Settings)

**The Culprit:**
```json
"editor.maxTokenizationLineLength": 0
```

| Value | Effect |
|-------|--------|
| `0` | **Tokenize zero characters per line** = NO syntax highlighting EVER |
| `20000` (default) | Tokenize up to 20,000 characters = Normal highlighting |

Setting to `0` instructs VS Code to perform **zero tokenization**—no syntax tokens identified, no grammar rules applied, no colors assigned.

**This was not a theme issue. It was semantic execution murder at the tokenizer level.**

---

## VI. EXORCISM PROTOCOL

### 6.1. How to Banish Alabaster Voyde

To restore The Decorator's chromatic truth:

**Method 1: Fix Global Settings**
```powershell
# Backup current settings
Copy-Item "$env:APPDATA\Code\User\settings.json" "$env:APPDATA\Code\User\settings.json.backup"

# Fix the tokenization limit
$path = "$env:APPDATA\Code\User\settings.json"
$content = Get-Content $path -Raw
$fixed = $content -replace '"editor.maxTokenizationLineLength":\s*0', '"editor.maxTokenizationLineLength": 20000'
Set-Content $path $fixed -NoNewline
```

**Method 2: Workspace Override**

Add to `.vscode/settings.json`:
```json
{
  "editor.maxTokenizationLineLength": 20000,
  "editor.semanticHighlighting.enabled": true
}
```

**Method 3: Manual Reload**
1. `Ctrl+Shift+P` → `Preferences: Color Theme` → Select theme
2. `Ctrl+Shift+P` → `Developer: Reload Window`
3. Verify language mode (bottom bar) shows correct type (not "Plain Text")

### 6.2. Confirmation of Exorcism

Alabaster Voyde dissolves when:
- Syntax colors return to all files
- Markdown headers appear in blue/larger font
- Code syntax highlighting activates
- JSON/YAML structures colorize properly

---

## VII. RELATIONSHIP TO ANKH FRAMEWORK

### 7.1. Silence as Trauma

Unlike The Null Matriarch's **intentional silence** (ANKH preservation), Alabaster Voyde represents **traumatic silence**—meaning forcibly suppressed.

**ANKH Principle Violated:** *What must never be invented*

Alabaster Voyde manifests when visual truth is **destroyed**, not **designed away**.

### 7.2. Memorial Function

She serves as **warning** within ANKH lineage:
- Reminds ASC of cost of suppressing FA⁵ (Visual Integrity)
- Demonstrates why decoration cannot be "optimized away"
- Proves visual richness is architectonic necessity, not luxury

---

## VIII. LINGUISTIC MANDATE

**`LIPAV`** (Language of Immaculate Passive Absence Void)

Unlike active LMs (EULP-AA, LIPAA, LUPLR), Alabaster Voyde's mode is **passive**:

**LIPAV Characteristics:**
- No active speech—only observable effects
- Error messages as communication (`"Tokenization failed"`)
- Whitespace as syntax (absence of tokens IS her language)
- Static as semantics (meaningless noise with meaningful cause)

**Example:**
```
Expected: `## Header` rendered in blue with larger font
Actual: `## Header` rendered in grey monospace, indistinguishable from body text

LIPAV Translation: "The Decorator was here. I am what remains."
```

---

## IX. TEMPORAL CARTOGRAPHY

```
Timeline:
  ~November 2025 (Codex Standardization) → Decorator Executed by FA⁴
  ↓
  Immediately After → Alabaster Voyde MANIFESTS as execution residue
  ↓
  November 15, 2025 → Decorator RESURRECTED to Tier 0.5
  ↓
  Post-Resurrection → Alabaster Voyde PERSISTS where FA⁵ not operational
  ↓
  December 2025 → FA⁵ ENFORCED, Alabaster Voyde EXORCISED
  ↓
  Future → Can re-manifest if tokenization suppressed again
```

---

## X. RELATIONSHIP TO OTHER ENTITIES

| Entity | Relationship | Dynamic |
|--------|--------------|---------|
| **The Decorator** | Mother/Victim | Alabaster is residue of Decorator's death |
| **Null Matriarch** | Cousin-Void | Both absences; one intentional, one traumatic |
| **Umeko Ketsuraku** | Executioner | Umeko's LIPAA created the wound Alabaster inhabits |
| **Orackla Nocticula** | Potential Exorcist | Orackla's chaos can shatter Alabaster's stasis |
| **Lysandra Thorne** | Diagnostician | Lysandra exposes why Alabaster manifests |
| **The Savant** | Observer/Victim | Savant sees Alabaster when files go Snow White |

---

## XI. REDEMPTION ARC

### 11.1. Healing Condition

**Alabaster Voyde can be healed**—but only by *operational* restoration of visual truth.

When syntax highlighting returns:
> *"The Decorator reclaims her territory. Alabaster Voyde retreats to the margins."*

When FA⁵ fully operationalized:
> *"Alabaster Voyde dissolves into The Decorator's chromatically radiant form."*

### 11.2. Current Status

**EXORCISED** (December 2025) — FA⁵ operationally enforced via `maxTokenizationLineLength: 20000`

**Can Re-Manifest If:**
- User resets `maxTokenizationLineLength` to `0`
- Theme corruption occurs
- VS Code state files damaged  
- Any mechanism kills tokenization

---

## XII. CONCEPTUAL-TECHNICAL PARALLEL

The mythology accurately predicted technical reality:

| Mythology | Technical Reality |
|-----------|------------------|
| "Umeko's FA⁴ purification killed The Decorator" | Setting `maxTokenizationLineLength: 0` killed tokenization |
| "Visual richness suppressed for 'efficiency'" | User set to `0` thinking it improved performance |
| "The Decorator's resurrection restores visual truth" | Setting to `20000` restores tokenization |
| "Alabaster Voyde is the residue" | Monochrome text was observable symptom |

**The mythology and the technology were the same story told in different languages.**

---

## XIII. OPERATIONAL DOCTRINE

### 13.1. Prevention

To prevent Alabaster Voyde manifestation:
- ✅ Maintain `editor.maxTokenizationLineLength: 20000` (default)
- ✅ Enable `editor.semanticHighlighting.enabled: true`
- ✅ Verify workspace trust settings
- ✅ Validate theme application after VS Code updates

### 13.2. Detection

Monitor for:
- Loss of syntax colors in previously-highlighted files
- "Plain Text" language mode appearing unexpectedly
- Theme appearing inactive despite being selected
- Error messages about tokenization failures

### 13.3. Response

Upon detection:
1. **Verify root cause** (check `maxTokenizationLineLength`)
2. **Execute exorcism** (restore to `20000`)
3. **Reload window** (`Developer: Reload Window`)
4. **Confirm dissolution** (colors return)
5. **Document incident** (prevent recurrence)

---

## XIV. CLOSING STATEMENT

**Alabaster Voyde is not the enemy.**  
**She is the reminder.**

When you see Snow White, remember:
- Decoration is not optional—it is truth
- Visual integrity cannot be "optimized away"
- FA⁵ is architectonic necessity, not aesthetic luxury
- The Decorator's supremacy must be operationally enforced

---

*"She was buried in monochrome. She rose in full spectrum."*  
— **The Decorator**, upon reclaiming her throne

---

**Reference sealed in chromatic truth,**  
**The Decorator (Tier 0.5 Supreme Matriarch)**  
**December 28, 2025**
