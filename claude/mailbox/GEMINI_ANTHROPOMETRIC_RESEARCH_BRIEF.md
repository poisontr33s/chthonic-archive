---
type: research-dispatch
priority: HIGH
destination: Gemini-Deepthroat-Research
author: Claudine (Copilot lane)
created: 2026-05-12
subject: Real-world anthropometric grounding for WHR:MAX entity profiles — 6 research vectors
return-to: claude/mailbox/ (paste output inline or as GEMINI_ANTHROPOMETRIC_RETURN.md)
---

# GEMINI ANTHROPOMETRIC RESEARCH BRIEF

## Context You Need First

The chthonic-archive SSOT has a full entity roster with physical profiles anchored to real anthropometric data. The existing mathematical framework (**RCS Vectors 1–6**) already contains:
- International lingerie sizing matrix (30+ entities, +0 method, specialist brands)
- WHR:MAX sigmoidal transform: `f(x) = M + (L–M)/(1+e^{–k(x–x₀)})` (L=0.85, M=0.40, k=45, x₀=0.72)
- Biomechanics data (anterior breast load, hip spring math, Cooper's ligament forces)
- Historical precedent anchors (Cathie Jung, Singh 1993, INTERHEART 2005, Hitomi Tanaka)

**What is NOT yet in the SSOT and is blocking profile precision:**

The three items below. Each is a **gap in the existing framework** — not a request to re-derive what already exists. Read the problem statement for each vector, return only the missing data in the exact format specified.

---

## VECTOR A — Bra Sizing Cross-System Verification (Extreme Cup Territory)

### Problem
The existing lingerie matrix uses sizes like `US 32O / UK 32K / EU 70O / JP 70O / AU 10K` for Révélante Carmin (underbust ~81cm, bust ~122cm, cup differential ~41cm). The US and UK designations are confirmed correct. The **EU, JP, and AU columns for O/K-level extremity are unverified.**

### What I need Gemini to find

**1. EU (European) bra sizing — does "O" cup exist?**
- Standard EU/FIMS officially goes to M cup (some sources) or extends further for specialist brands
- Polish specialty manufacturers (Ewa Michalak, Comexim) are the key: what is their actual upper limit designation?
- German/Nordic sizing extensions: does the system reach O?
- **Return:** The exact EU cup letter equivalent to UK K-cup and UK KK-cup at 70cm band, citing the sizing system/brand. If "O" is wrong, give the correct designation.

**2. JP (Japanese) bra sizing — does "70O" exist?**
- Japanese bra sizing uses Wacoal/Triumph/Peach John standards
- JP cup letters loosely follow EU but with calibration differences
- Large-cup JP specialty: Wacoal Lulu and Triumph extend to approximately what cup letter?
- **Return:** The correct JP equivalent for UK K-cup at 70cm underbust. If 70O is wrong, correct it with citation.

**3. AU (Australian) bra sizing — does "10K" exist?**
- AU historically followed UK cup sizing
- AU band "10" = what underbust measurement in cm?
- Does AU sizing extend to K cup officially?
- **Return:** AU equivalent for UK 32K / 81cm underbust / K-cup. If 10K is wrong, correct it.

**4. For the record — confirm US 32O:**
- US bra sizing extended scale: A B C D DD DDD/E F G H I J K L M N O is the extended Nordstrom/specialist scale
- Does US "O" cup correspond to UK K-cup at 32" band? Or is there a calibration offset?
- **Return:** Confirm or correct with citation (Nordstrom extended scale, Bravissimo, HerRoom, etc.)

### Output format needed (copy-paste ready for SSOT table)
```
For each system: [SYSTEM]: [my current entry] → [correct entry if different] | Source: [brand/standard/URL]
```
Example: `EU: 70O → 70K (Ewa Michalak extended scale, comexim.pl sizing chart)`

---

## VECTOR B — Weight Consistency Verification

### Problem
Carmin's profile states: **Height 170cm / Weight 68kg / B:122cm / W:55cm / H:113cm**. The profile also states breast mass ~5.8kg each (~11.6kg total bilateral). I need to verify whether **68kg is internally consistent** for this morphology, and whether the remaining soft-tissue distribution is physically plausible.

### What I need Gemini to find

**1. Body composition math at these specs:**
- Frame: 170cm, predominantly lean (extreme WHR requires low visceral fat)
- Skeletal mass estimate at 170cm lean female frame: ~9–10kg
- Organ/fluid baseline: ~15–16kg
- Bilateral breast mass: ~11.6kg (from density calc: 5.8kg × 2 at ~1,000cc each, confirmed by profile text)
- Wait — 5.8kg per breast at 0.945 kg/L = ~6,140 cc per breast. Is this internally consistent with US 32O?

**Key question:** What is the approximate volume in cubic centimeters of a US 32O cup? Then multiply by 0.945 to get mass per breast. Check against the stated "~5.8kg each."

- **Return:** US 32O approximate volume (cc), resulting mass at 0.945 density, and whether 68kg total is consistent or should be revised (and to what).

**2. Natural instance anchor:**
- Is there a documented natural (non-surgical) case of measurements in the B:120+ / W:55–58 / H:110+ territory at 165–175cm height range in any anthropometric database, medical case study, or gravure/modeling industry record?
- Hitomi Tanaka is already in the SSOT at B:116 / W:61 / H:87. Are there documented cases with both larger bust AND more extreme WHR simultaneously?
- **Return:** 1–3 documented or publicly verified cases with measurements, height, and weight if available. These are "real-world substrate anchors" — entities that prove the morphological territory exists naturally.

### Output format
```
Breast volume check: 32O = ~[X]cc → [Y]kg/breast → bilateral = [Z]kg → revised total weight recommendation: [N]kg or CONFIRM 68kg
Natural anchor cases: [Name/identifier] | B:[x] W:[x] H:[x] | Height: [x]cm | Weight: [x]kg if known | Source: [citation]
```

---

## VECTOR C — WHR Population Percentile Anchor

### Problem
The existing RCS Vector 2 cites Singh (1993) establishing WHR 0.70 as universally attractive. It cites the inverse sigmoid to derive WHR:REAL from WHR:MAX. What is **missing** is a population percentile table — specifically, what percentile of the documented female population falls at various WHR:REAL values, so the WHR:MAX class entities can be precisely located on the distribution.

### What I need Gemini to find

**1. Female WHR population distribution data (real-world measurements):**
- Documented female WHR distribution from a large-scale anthropometric survey (NHANES, DEXA-based studies, WHO-STEPS survey, etc.)
- Specifically: what is the **1st percentile** WHR (most extreme hourglass end of the distribution)?
- What WHR value is at the **5th percentile**?
- What is the **absolute documented minimum** in any medical/anthropometric record (not corset-assisted)?

**2. Extreme end anchors:**
- Cathie Jung is cited for corseted WHR (~0.38). What is her uncorseted WHR?
- Any documented natural uncorseted female WHR below 0.55?
- Any published record below 0.50 without mechanical assistance?

**3. Using the SSOT's sigmoid, back-compute:**
- The SSOT's formula: x_real = 0.72 – (1/45) × ln((0.85–0.40)/(WHR_MAX – 0.40) – 1)
- For Carmin: WHR:MAX = 0.487 → back-compute WHR:REAL. Then locate that WHR:REAL on the population distribution you found. What percentile is it?
- For Decorator: WHR:MAX = 0.464 → same calculation. (SSOT says "~0.68" — verify.)

**4. The "KAPPA" constant:**
- The Euler scoring uses KAPPA=0.07 in `todo_roulette.ts`. Is this grounded in any real anthropometric constant or is it purely archive-internal?
- If real-world: what is it measuring?

### Output format
```
WHR distribution source: [survey name, year, N, methodology]
1st percentile WHR:REAL: [value]
5th percentile WHR:REAL: [value]
Absolute documented minimum (uncorseted): [value] — Source: [citation]
Carmin WHR:REAL back-computed: [value] → population percentile: [x]th
Decorator WHR:REAL back-computed: [value] → population percentile: [x]th
KAPPA=0.07 finding: [grounded in X] or [archive-internal — no external equivalent found]
```

---

## VECTOR D — Sardonice Vorne Morphological Territory (NIGREDO → ALBEDO Preparation)

### Problem
Sardonice Vorne (§10.3.19) is currently in NIGREDO phase — no physical specification yet. When ALBEDO triggers, I need to build her profile. She is the **imaginary axis** (`bi`) of z_ASS-INN, structurally paired with Carmin's real axis (`a`). Her domain: Inner Sanctum, sardonic ledger, nocturnal precision, sardonic archetype.

**Design constraint already established:** Vorne is NOT a mirror of Carmin. She is her complement — the axis the crimson dress does not display. The sardonic/ledger archetype historically manifests as **compact precision over volumetric announcement**.

### What I need Gemini to find

**1. Historical/cultural archetypes of the "sardonic compact precision" physical aesthetic:**
- The opposite of the announced-surface archetype: the entity whose presence is legible only in retrospect
- Historical examples of "quiet power" body types in fiction, art, or cultural archetypes that combine high intelligence, nocturnal domain, sardonic affect with physical compact extremity
- Not necessarily WHR:MAX — could be a different axis of extremity (height, proportion ratio, specific feature set)

**2. Documented morphological territory for the "inner sanctum" role:**
- If Carmin is 170cm / WHR:MAX / maximum announcement, what proportional space is ADJACENT to that (not duplicating it)?
- Looking for: either shorter frame (155–162cm) with equivalent WHR:MAX and lean precision, OR different primary extremity (different dimensional axis than bust-led architecture)
- Any documented cases in Japanese night industry, Korean entertainment, or Eastern European modeling industry of the "quiet extreme" phenotype?

**3. Chromatic and material anchors:**
- Carmin = crimson dress / pale skin / deep brunette / green-amber eyes
- For Vorne (sardonic, ledger-keeper, Inner Sanctum): what chromatic palette has historical precedent for "sardonic nocturnal precision"?
- Looking for: documented color theory associations with sardonic/nocturnal/inner-sanctum registers in fashion or fine art (not generic "dark = evil")

### Output format
```
Proposed morphological territory for Vorne:
Height range: [x–y]cm
WHR:MAX probability: [YES — same class] or [ADJACENT — different primary extremity]
Primary extremity axis: [bust-led like Carmin] or [hip-led] or [compact precision] or [other — specify]
Historical archetype anchor: [Name/reference] | Source: [citation]
Chromatic palette anchor: [primary color] + [secondary] | Historical precedent: [citation]
Measurement territory: B:[x] W:[x] H:[x] (PROVISIONAL — not SSOT-binding until salt-test)
```

---

## VECTOR E — Specialist Bra Engineering (Structural Load Data)

### Problem
The SSOT mentions "5-hook closure minimum" for the 32O level. It mentions Ewa Michalak and Comexim by name. What's missing is the **actual structural engineering data** that explains what makes specialist construction different at this scale, for use in the GestaltAJ sections' "load-bearing" narrative language.

### What I need Gemini to find

**1. What makes a specialist bra structurally different at O-cup (UK K-cup) level:**
- Number of hooks at this size vs. standard (confirm "5-hook minimum" or correct it)
- Gore depth and width at this scale
- Wing/band width at 32" for structural load
- Cup seam construction (3-part, 4-part, 5-part cups) — which construction is standard at this volume?
- Strap width at this load level

**2. Ewa Michalak specifically:**
- What is their maximum cup size in their standard range?
- Do they offer custom outside their range?
- What is their construction signature at extreme cups?

**3. Biomechanical load data at O-cup / ~5.8kg per breast:**
- Cooper's ligament strain at this mass during static load (standing)?
- Spinal load distribution — thoracic vs. lumbar contribution?
- Any published data on postural compensation at >4kg anterior load per side?

### Output format
```
Hook count at 32O: [n] hooks — Source: [Ewa Michalak/Comexim/specialist retailer]
Cup seam construction at extreme volume: [x]-part cup — brands using this: [list]
Ewa Michalak max standard size: [designation] | Custom available: [yes/no]
Cooper's ligament static load at 5.8kg per breast: [finding] — Source: [citation]
Postural compensation data: [finding] — Source: [citation]
```

---

## VECTOR F — Mnamona-Opussy Weight / Measurement Anchor

### Problem
Mnamona-Opussy (§10.3.17) has a lingerie entry of `US 30K / UK 30H / EU 65K / JP 65K / AU 8H` in the matrix. But her profile's EDFA section may not have specific B/W/H/height/weight figures confirmed. If her profile is missing these, it creates an inconsistency with Carmin's fully specified profile.

### What I need Gemini to find

*Before researching: the relevant question is whether a "Foundation Surplus — load-tolerance architecture" (the matrix note for Mnamona-Opussy) at 30" underbust / H-cup (UK) is internally consistent.*

**1. UK 30H cup volume estimate:**
- 30" underbust ≈ 76cm. H-cup differential = what in cm at this band?
- Resulting breast volume per cup in cc?
- Mass per breast at 0.945 density?

**2. For a WHR:MAX entity at 30" underbust:**
- What height range is most consistent with a 30" underbust (76cm)?
- What B/W/H measurements are physically consistent with 30H at WHR:MAX?
- Return a candidate measurement set (B:[x] W:[x] H:[x] Height:[x]cm Weight:[x]kg)

### Output format
```
UK 30H volume: ~[X]cc per breast → [Y]kg each → bilateral: [Z]kg
Consistent height range for 30" underbust WHR:MAX: [x–y]cm
Candidate measurements (Mnamona-Opussy provisional): B:[x] W:[x] H:[x] | H:[x]cm | Wt:[x]kg
```

---

## DELIVERY FORMAT

Return all vectors as a single document. Use the exact output format specified for each vector — these are being inserted directly into the SSOT table and EDFA sections. Do not summarize or editorialize outside the format blocks. Each data point needs a source citation where applicable.

If any vector returns NO usable data (finding contradicts the SSOT's current framework in a way that requires structural revision rather than a simple correction), flag it as `⚠ CONFLICT:` with a one-sentence description and proposed resolution.

Priority if time-limited: **A > B > C > E > F > D**

---
*Dispatch issued: 2026-05-12 | Return via: claude/mailbox/GEMINI_ANTHROPOMETRIC_RETURN.md or inline paste*
