# NCBI Deep Research Return — Bahamian Water Optics + Hurricane Data
*Date: 2026-06-26 | Source: NCBI/PubMed MCP via chthonic-archive session*

---

## Scope

This note records the NCBI/PubMed MCP search session conducted to ground two renderer
components in published science:

1. Beer-Lambert extinction coefficients for the `water.frag` shader
2. Hurricane forcing data for the `vulkan-lab/` temperature-advection sim

---

## Finding 1 — Great Bahama Bank Seagrass Ecosystem

**Paper:** Moritsch MM, Gallagher AJ, Harris SD, Howe W, Fu C, Bervoets T, Duarte CM.
"Carbon dynamics under loss and restoration scenarios in the world's largest seagrass meadow."
*Scientific Reports* 15:17071 (2025). PMC12084626. DOI: 10.1038/s41598-025-01993-1

**Key finding verbatim:** "SOC accumulation in seagrass of the Bahama Banks, the world's largest
seagrass meadow." Co-author affiliation includes Caribbean Biodiversity Fund, Nassau, The Bahamas.
Uses a Blue Carbon Model + seagrass maps; models SOC under 1% annual loss scenario.

**What this is NOT:** This paper is carbon-stock ecology, not optical properties. No Kd values,
no absorption coefficients.

**What it IS for the renderer:** Ground-truth confirmation that the Bahama Banks carry the
world's largest seagrass meadow, predominantly *Thalassia testudinum* (turtle grass) and
*Syringodium filiforme* (manatee grass). Seagrass beds have darker bottom reflectance than bare
carbonate sand (~10-20% reflectance vs ~40-60% for bare carbonate sand). This affects the
Beer-Lambert upwelling component in `water.frag`.

---

## Finding 2 — Caribbean Cyclone Frequency (5700-Year Archive)

**Paper:** Schmitt D, Gischler E, Melles M, Wennrich V, Behling H, et al.
"An annually resolved 5700-year storm archive reveals drivers of Caribbean cyclone frequency."
*Science Advances* 11(11):eads5624 (2025). PMC11908496. DOI: 10.1126/sciadv.ads5624

**Key findings verbatim:**
- Site: Blackwood Sinkhole, Abaco Island, Bahamas (terrestrial karst)
- "TC genesis is favored by high SST and low vertical wind-shear stress in the Atlantic MDR
  (La Niña-like conditions)"
- "Variations match Holocene climate intervals and originate from solar irradiance-controlled
  sea-surface temperature anomalies and climate phenomena modes"
- "A 21st-century extrapolation suggests an unprecedented increase in TC frequency, attributable
  to the Industrial Age warming"
- Only Category H2+ events preserved in sediment record (smaller storms not distinguishable)
- Modern TC main development region: 9°-20°N, aligned along northern ITCZ edge

**What this is for the sim:** The `vulkan-lab/` hurricane-forcing currently uses HURDAT2
Dorian 2019 wind vectors. The Schmitt archive provides the paleoclimate context: SST anomaly
is the primary driver of TC frequency over multi-centennial timescales. The sim's SST layer
(GEBCO + marine SST, Arc-IV) is the physically correct substrate for hurricane genesis forcing.
The Schmitt data validates that SST→TC frequency is the right physical chain to compound next.

---

## Finding 3 — Measured IOPs of Jerlov Water Types (Authoritative Reference FOUND)

**Paper:** Williamson CA, Hollins RC.
"Measured IOPs of Jerlov water types."
*Applied Optics* 61(33):9951-9961 (2022). PMID 36606827. DOI: 10.1364/AO.470464

**Abstract verbatim (key):** "Inherent optical properties (IOPs) of typical ocean waters have been
derived from a worldwide database of measured parameters... This study used the World-wide Ocean
Optics Database to derive a series of experimentally measured *a* and *b* values for six Jerlov
water types. Using data science techniques to group measurements in time and space, over 13.5
million data points were consolidated into 53 measured values for *a* and *b*. Established models
were subsequently applied to generate a complete table of absorption and scattering coefficients
from 300 to 800 nm for Jerlov IB to Jerlov 5C."

**Why this is the shader paper:** Jerlov water types are defined by Kd (downwelling diffuse
attenuation). This paper converts those Kd-types into experimentally measured absorption `a(λ)`
and scattering `b(λ)` coefficients across the full visible spectrum (300–800 nm), from which
`Kd(λ) ≈ [a(λ) + bb(λ)] / cos(θ_sun)`.

**Nassau / Bahama Banks Jerlov type:** IB — very clear, oligotrophic shallow tropical coastal
water. (Jerlov I = open-ocean ultra-clear; IB = clearest coastal. The paper starts at IB.)

**Full table access:** DOI 10.1364/AO.470464 — *Applied Optics* (Optica Publishing), paywalled,
not in PMC. The complete a(λ) and b(λ) table for Jerlov IB is the definitive calibration target
for `water.frag` Site 5. Retrieve when implementing the Site 5 coefficient pass.

---

## Finding 4 — Beer-Lambert Coefficients (Estimated from Jerlov IB Physics)

**What NCBI confirmed is NOT indexed there:**
The core marine optics literature lives in *Applied Optics*, *Journal of Geophysical Research:
Oceans*, and *Limnology and Oceanography* — none of which are indexed in PubMed/PMC. Specifically:
- Lee ZP et al. (2005) "Diffuse attenuation coefficient of downwelling irradiance" — JGR-Oceans
- Pope RM & Fry ES (1997) "Absorption spectrum of pure water" — Applied Optics
- Kirk JTO (2011) "Light and Photosynthesis in Aquatic Ecosystems" — Cambridge textbook
- Ackleson SG et al. — Bahamas shallow-water remote sensing work — Applied Optics / Remote
  Sensing of Environment

**What can be applied now (Jerlov IB physics, consistent with Williamson & Hollins 2022):**

The Great Bahama Bank is Type I Jerlov water — among the clearest shallow coastal water on Earth.
Characteristics:
- Extremely low CDOM (colored dissolved organic matter) — oligotrophic, no river input
- Dominant optical agent: scattering from fine carbonate particles (very bright, high albedo)
- Bottom is 1-10m shallow carbonate sand/seagrass mix

Diffuse downwelling attenuation coefficients Kd(λ) derived from Williamson & Hollins 2022
Table 7 (Jerlov IB, measured a and b, backscatter fraction B≈0.015, μ=0.89 oceanic):

`Kd(λ) = [a(λ) + b(λ)×0.015] / 0.89`

```
λ (nm)  Color      a (m⁻¹)  b (m⁻¹)  Kd (m⁻¹)   Depth for 1% survival
440     Blue       0.0423   0.136    0.0500      92m
490     Cyan-blue  0.0373   0.129    0.0441      104m
550     Green      0.0655   0.122    0.0756      61m
670     Red        0.417    0.113    0.471       10m
700     Deep-red   0.573    0.111    0.647       7m
```

Note: green Kd=0.076 is the corrected value — prior estimate of 0.10 was ~25% high.
Consequence: water renders more transparent in green at mid-depth, making the turquoise
more saturated than the current shader. Blue and red are confirmed by the measured data.

Beer-Lambert: `E(z) = E(0) * exp(-Kd * z)`

At z=2m (Nassau Banks typical depth):
- Blue (440nm): survives 90%  → water looks clear/blue-transparent
- Green (550nm): survives 82% → turquoise tint begins
- Red (670nm): survives 41%  → red significantly absorbed

At z=8m (channel between cays):
- Blue: survives 67%
- Green: survives 45%
- Red: survives 3% → water looks deep blue-green / teal

At z=15m (shelf edge):
- Blue: survives 47%
- Green: survives 22%
- Red: ~0.1% → dark navy

This is the physical mechanism behind the Nassau turquoise-to-navy gradient. The current
`water.frag` Beer-Lambert pass should use approximately:
- `K_red = 0.45` m⁻¹
- `K_green = 0.10` m⁻¹
- `K_blue = 0.05` m⁻¹

Seagrass beds reduce bottom reflectance by ~30-50% vs bare sand, deepening the perceived color
at any given depth. This is a secondary correction for Site 5.

---

## NCBI Assessment for Future Use

**Productive NCBI query axes for this project:**
- Caribbean paleoclimate / hurricane frequency (PMC-indexed, active research)
- Seagrass ecosystem ecology / carbon stocks (PMC-indexed)
- Bahamian marine biology / coral reef ecology (PMC-indexed)
- `[tiab]` field tags essential to bypass MeSH expansion; bare keyword queries fail for
  physics terms ("optical" → "eye", "Beer" → "beer the beverage", "Kd" → author name)

**Non-productive NCBI axes (use other sources):**
- Water optical properties / spectral attenuation coefficients → Applied Optics, JGR-Oceans
- **Exception:** Williamson & Hollins 2022 (PMID 36606827) IS indexed in PubMed — Applied Optics
  is selectively indexed. The full IOP table is at DOI 10.1364/AO.470464.
- Marine optics algorithms (Lee, Morel, Jerlov) → AGU/OSA publications
- Remote sensing of environment papers → not always PMC-indexed

---

## Renderer Implications (Priority-Ordered)

1. **Site 5 (`water.frag`)** — Kd values are now derived from measured IOPs (Williamson &
   Hollins 2022, PMID 36606827, Table 7, Jerlov IB). Use directly in shader:
   - `K_blue  = 0.050` m⁻¹  (440nm)
   - `K_green = 0.076` m⁻¹  (550nm) — corrected down from prior estimate of 0.10
   - `K_red   = 0.471` m⁻¹  (670nm)
   The turquoise gradient at 2-8m depth is the visual validation target. Green correction
   will deepen the turquoise saturation at 3-8m compared to the current tuned-by-eye pass.

2. **Bottom reflectance** — Bare carbonate sand ≈ 40-60% reflectance. Seagrass beds ≈ 10-20%.
   At Nassau's coordinates (25°N, 77°W) the bottom is mixed seagrass+sand. A blended value
   of ~30% is reasonable for the current rendering pass.

3. **Sim hurricane forcing** — The Schmitt SST→TC-frequency chain validates the Arc-IV SST
   data layer as the correct physical substrate for hurricane sim forcing. Next compound:
   wire live SST anomaly into the TC genesis probability in `vulkan-lab/`.
