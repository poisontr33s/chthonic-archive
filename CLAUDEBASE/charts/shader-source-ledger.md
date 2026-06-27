# Shader Source Ledger

Every numeric constant in the water rendering pipeline — value, units, physical meaning, citation.
No constant without a source chain. Artistic/engineering constants are marked as such.

---

## `assets/shaders/water.frag`

### Volumetric optics — scientifically grounded

| Constant | Value | Channel | Units | Physical meaning | Source |
|---|---|---|---|---|---|
| `Y_SCALE` | 1.0 | — | m m⁻¹ | render.y = ENU elevation metres directly; no scaling needed | Ellipsoid Fork I Site 2 (2026-06-26): bathymetry mesh now outputs ENU.z → render.y. WGS84 ENU convention. |
| `SIGMA.r` | 0.471 | 670 nm | m⁻¹ | Diffuse attenuation Kd (red) | Williamson & Hollins 2022, PMID 36606827, Table 7, Jerlov IB water type. Nassau/Bahama Banks optical classification. |
| `SIGMA.g` | 0.076 | 550 nm | m⁻¹ | Diffuse attenuation Kd (green) | Same. |
| `SIGMA.b` | 0.050 | 440 nm | m⁻¹ | Diffuse attenuation Kd (blue) | Same. |
| `SAND.r` | 0.150 | 670 nm | — | Bottom albedo, red channel | 70% *Thalassia testudinum* dense canopy (R670=0.02, CoBOP/Voss 2003 Lee Stocking Island) + 30% Bahamas carbonate sand (R670=0.44, Hill 2014; Voss 2003). Linear mix per Mobley 2005 LUT. Cover fraction from Moritsch 2025 (PMC12084626, ~92,000 km²). DR 2026-06-27. |
| `SAND.g` | 0.172 | 550 nm | — | Bottom albedo, green channel | Same. Canopy R550=0.09, sand R550=0.40. |
| `SAND.b` | 0.097 | 440 nm | — | Bottom albedo, blue channel | Same. Canopy R440=0.03, sand R440=0.30. |
| `WATER.r` | 0.006 | 670 nm | — | Asymptotic deep-water in-scatter (R∞, red) | R∞ ∝ b_b/a (Morel & Maritorena 2001 Case 1). Williamson-Hollins 2022 IOPs → simple R∞=0.0083, refined=0.0045; midpoint≈0.006. G/B ratio 0.32, R/B ratio 0.032. DR 2026-06-27. |
| `WATER.g` | 0.060 | 550 nm | — | Asymptotic deep-water in-scatter (R∞, green) | Same. G/B=0.32 means G=0.185×0.32=0.059≈0.060. |
| `WATER.b` | 0.185 | 440 nm | — | Asymptotic deep-water in-scatter (R∞, blue) | Same. Blue anchor from Hollins 2023 particle-split analysis; Jerlov IB is oligotrophic → bb dominated by pure-water backscatter at 440 nm. |

### Optical pipeline — arithmetic identity

| Constant | Value | Physical meaning | Note |
|---|---|---|---|
| `2.0` (Beer-Lambert factor) | 2 | Round-trip path multiplier: down + up | Physically exact for a Lambertian flat seabed. |
| `0.299, 0.587, 0.114` (luminance weights) | ITU-R BT.601 | floor_vis luminance for mix() blend | Standard luma for linear RGB → perceived brightness. |

### Fresnel, shading — engineering/artistic

| Constant | Value | Physical meaning | Rationale |
|---|---|---|---|
| Fresnel F0 (both modes) | 0.02 | Reflectance at normal incidence for water-air interface | Physically exact: F0 = ((n₁-n₂)/(n₁+n₂))² = ((1.0-1.34)/2.34)² ≈ 0.021. Rounded to 0.02. |
| Fresnel scale (seabed) | 0.30 | Schlick scale: reduced to model view-through-water-column blur | Artistic; full Schlick (0.98) over-states specular on the sub-surface seabed view. |
| Fresnel scale (surface) | 0.98 | Schlick scale for ocean surface | Full Schlick; water-air interface at grazing is near-mirror. |
| Surface glint exponent | 200 | Specular shininess — ocean surface | Tight sun glint on calm Bahama Banks water. Artistic. |
| Seabed glint exponent | 80 | Specular shininess — seabed wet-sand sheen | Lower = broader highlight on coral/sand. Artistic. |
| Lambert ambient | 0.30 | Ambient fraction in `0.30 + 0.70 * diffuse` | Prevents total black in shadow. Artistic. |
| Lambert diffuse | 0.70 | Diffuse fraction | `1 − ambient`. |
| Cloud-into-sky blend | 0.7 | Fraction of cloud layer mixed into reflected sky | Artistic blend for cloud Fresnel contribution. |
| Ocean surface alpha | 0.30 | Fragment alpha for ocean mesh | Translucent so seabed turquoise reads through. Artistic. |
| Motion debug gain | 12000 | Scale for motion-vector debug view | Sub-pixel wave motion; gain exposes the signal. Debug only. |

---

## `assets/shaders/water.vert`

| Constant | Value | Units | Physical meaning | Source |
|---|---|---|---|---|
| `X_HALF` | 200,000 | m | East half-extent of ocean mesh (ENU-local) | Ellipsoid Fork I Site 3 (2026-06-26). Nassau Banks span ~350 km E-W; 400 km total gives margin. Must match `ocean.rs` X_HALF. |
| `Z_HALF` | 200,000 | m | North half-extent of ocean mesh (ENU-local) | Same. Symmetric around Nassau anchor. |
| `MARGIN` | 1.5/256 | texel fraction | UV inset from cascade texture border | Prevents finite-difference normal spires at the displacement image edge. Empirical: 1 texel insufficient, 1.5 texel eliminates artifacts. |
| Cascade 0 (`binding=0`) label | 5 m patch | — | Tessendorf ripple/chop cascade patch size | Set in `ocean.rs` / `ocean_h0.comp`. 5 m resolves capillary-gravity wave scale for Nassau near-shore. |
| Cascade 1 (`binding=1`) label | 60 m patch | — | Tessendorf swell cascade patch size | Set in `ocean.rs`. 60 m resolves open-ocean swell wavelength dominant in the Bahamas. |
| FD normal scale | `2.0 * texel` | — | Finite-difference denominator | Correct central-difference: Δh / (2Δx). Not artistic. |

---

## `src/render/geodesy.rs`

### WGS84 reference ellipsoid

| Symbol | Value | Units | Source |
|---|---|---|---|
| `WGS84_A` | 6,378,137.0 | m | Semi-major axis (equatorial radius). NIMA TR 8350.2 3rd ed. 2000; ISO 6709:2022; IEC 60050-705. |
| `WGS84_INV_F` | 298.257_223_563 | — | Inverse flattening. Same. |
| `WGS84_F` | 1/298.257_223_563 ≈ 0.003_352_811 | — | Flattening. Derived: 1/WGS84_INV_F. |
| `WGS84_E2` | F×(2−F) ≈ 0.006_694_380 | — | First eccentricity squared. Derived: e² = 2f − f². |
| `WGS84_B` | A×(1−F) ≈ 6,356,752.314 | m | Semi-minor axis (polar radius). Derived: b = a(1−f). |

### Scene datum — Nassau anchor

| Symbol | Value | Units | Physical meaning | Source |
|---|---|---|---|---|
| `NEW_PROVIDENCE_LAT_DEG` | 25.0489 | ° N | Geographic centre of New Providence Island, Bahamas | Geographic centre of the island; ENU origin of the entire scene. |
| `NEW_PROVIDENCE_LON_DEG` | −77.3555 | ° E | Same | Same. |
| `NEW_PROVIDENCE_ALT_M` | 0.0 | m | MSL altitude of scene datum | Sea surface datum; the renderer's zero-elevation plane is the ocean surface. |

---

## `src/render/lens.rs`

| Symbol | Value | Units | Physical meaning | Source |
|---|---|---|---|---|
| `HORIZON_EYE` | (0.0, 0.45, 2.6) | m ENU | Perspective lens eye: 0 m East, 0.45 m Up, 2.6 m North of Nassau anchor | Ellipsoid Fork I Site 4 (2026-06-26). Eye at beach height (45 cm) looking slightly north over the Banks. Tuned vs render-smoke PNG. |
| `LOOK_DISTANCE` | 4.0 | m | Distance to look-at target along heading | Only direction matters for `look_at_rh`; any positive value yields the same view matrix. Artistic. |
| `PERSPECTIVE_FOV_DEG` | 55.0 | ° | Vertical field of view (perspective lens) | Natural wide-angle photography approximation for a coastal horizon view. Artistic. |
| `near` (perspective) | 0.1 | m | Near clip plane | ELLIPSOID-RETROFIT Site 6 tag: correct value pre-metric. Will become 0.1 m after Site 6 scale fix. |
| `far` (perspective) | 1000.0 | m | Far clip plane | ELLIPSOID-RETROFIT Site 6 tag: must become ~1,000,000 m for full-Banks view. Currently limits render to 1 km radius. |
| `Heading::default` az | 180.0 | ° | Default azimuth: due South | Looks toward open ocean (south of Nassau). Artistic. |
| `Heading::default` alt | 11.7 | ° | Default altitude angle | Reproduces original horizon look angle; tuned vs render-smoke. Artistic. |

---

## Scope note

Atmospheric shader constants (`skyview.comp`, `transmittance.comp`, `multiscatter.comp`) follow Bruneton & Neyret 2008 + Hillaire 2020 extended tables — Rayleigh/Mie scale heights, extinction cross-sections, ozone layer parameters. Those are cited inline in the compute shaders and are a separate citation chain from the marine optics above.

Ocean cascade physics (`ocean_h0.comp`, `ocean_evolve.comp`) follow Tessendorf 2001 (SIGGRAPH); wind speed and Phillips spectrum parameters are in `ocean.rs`. The cascade labels in the table above link back to those constants.
