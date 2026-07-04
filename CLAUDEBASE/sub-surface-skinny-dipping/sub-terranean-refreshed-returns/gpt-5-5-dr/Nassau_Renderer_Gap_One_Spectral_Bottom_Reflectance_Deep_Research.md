# Nassau Renderer Gap One Spectral Bottom Reflectance

> Portable Markdown export of the Deep Research report. Deep Research UI citation tokens have been converted into Markdown footnotes so the file remains stable outside the ChatGPT interface.

## Bottom line

Your packet excerpt only included **Gap 1**, so this report addresses that gap specifically. The closest primary-source answer I could assemble for the Bahamas is not a single tidy wavelength table, but a three-part stack of sources: **healthy _Thalassia testudinum_ leaf spectra** from Thorhaug, Richardson, and Berlyn; **Bahamian carbonate sand and a seagrass-bed canopy proxy** from Voss et al.; and **Bahamas turtlegrass canopy-bottom reflectance** from Dierssen et al., which is limited to **450–650 nm** because the instrument did not have acceptable signal-to-noise at the ends of the spectrum. Mobley et al. then explicitly describe building **linear mixtures of clean seagrass leaves and Bahamian sand in 10% increments** for the same Lee Stocking Island optical setting.[^thorhaug][^voss][^dierssen][^mobley]

The most defensible **clean-leaf _Thalassia_ endpoint** I found is approximately **0.023 at 440 nm, 0.078 at 550 nm, and 0.029 at 670 nm** from Thorhaug et al.’s healthy-blade spectrum. The best **direct Bahamian sand spectrum** I found is Voss et al.’s bright white sand reflectance-factor curve, which is roughly **0.51 at 440 nm, 0.67 at 550 nm, and 0.74 at 670 nm**, but that dataset is an **angle-specific reflectance factor** rather than a perfectly Lambertian bottom albedo. If you want a renderer-ready sand endpoint that stays closer to the **widely cited Bahamas carbonate-sand brightness near R(555) ≈ 0.4**, a practical reconciled working set is **0.30 at 440 nm, 0.40 at 550 nm, and 0.44 at 670 nm** by keeping the Voss spectral shape but anchoring the magnitude at the Bahamas 555 nm value cited by Hill et al. from the Lee Stocking Island literature.[^thorhaug][^voss][^hill]

Using that reconciled sand endpoint and a **linear clean-leaf + sand mixture**, the **60–70% seagrass cover range** comes out to approximately:

| Cover model | 440 nm | 550 nm | 670 nm |
|---|---:|---:|---:|
| 60% seagrass + 40% sand | 0.135 | 0.207 | 0.193 |
| 65% seagrass + 35% sand | 0.121 | 0.191 | 0.173 |
| 70% seagrass + 30% sand | 0.107 | 0.175 | 0.152 |

Those mixtures follow the same kind of **linear endmember mixing** described by Mobley et al. for Bahamian clean seagrass leaves combined with sand.[^mobley]

## What the papers actually measure

Thorhaug et al. measured _T. testudinum_ in the laboratory with a **UNIspec Spectral Analysis system** over **400–1000 nm**, using multiple blades and repeated readings, and they report the species mean reflectance spectrum rather than a wavelength table. In the same paper, they describe the healthy _Thalassia_ spectrum as having the familiar green-plant shape, with a **broad peak at 550 nm** and a **chlorophyll trough near 670–680 nm**.[^thorhaug]

Voss et al. measured a **bright white sand surface** and a **seagrass-bed spectrum 40 cm above the bed** near Lee Stocking Island, Bahamas, with Dive Spec. Their Figure 2 is especially useful because it places Bahamian sand and a top-of-bed seagrass signal on the same spectral axes over **400–700 nm**. They also note that **sand is nearly Lambertian at normal incidence**, so they used the measured sand reflectance factor as the input **R** in Hydrolight, while explicitly warning that the same Lambertian assumption is **not supported** for the seagrass canopy.[^voss]

Dierssen et al. are the source you would want if you insist on an actual **Bahamas turtlegrass canopy-bottom reflectance** measurement rather than a clean-leaf spectrum, because their DOBBS instrument measured reflectance **within centimeters of either bare sand or the top of the turtlegrass canopy**. The catch is that they only publish those DOBBS bottom-reflectance spectra from **450–650 nm**, specifically because signal-to-noise was inadequate at the spectral ends. That means Dierssen is excellent for checking the **green-band magnitude** of a canopy and the general brightness difference between turtlegrass and carbonate sand, but not for directly supplying your requested 440 and 670 nm endpoints.[^dierssen]

Mobley et al. bridge the gap conceptually. In the Lee Stocking Island LUT work, they state that Figure 7 includes **clean seagrass leaves**, **clean ooid sand**, and then **linear mixtures** of the two made in **10% increments** such as 90% sand + 10% grass, 80% sand + 20% grass, and so on. They also define their “thick grass” class as the pure seagrass spectrum or a **sand-grass mixture with 60% or more grass spectrum**, which lines up unusually well with your requested **60–70% cover fraction**.[^mobley]

## Turtle grass endpoint

The cleanest primary endpoint for `_Thalassia testudinum_` itself is the healthy-blade spectrum in Thorhaug et al. Because the paper publishes the spectrum as a curve rather than a table, the values below are best read as **figure-derived approximations** from the healthy _Thalassia_ trace. They are the closest thing I found to directly measured `_T. testudinum_` reflectance at your three wavelengths.[^thorhaug]

For practical use, I would carry the healthy-leaf endpoint as:

| Endpoint | 440 nm | 550 nm | 670 nm |
|---|---:|---:|---:|
| _Thalassia testudinum_ healthy leaf | 0.023 | 0.078 | 0.029 |

That set is consistent with the paper’s qualitative description: a weak blue reflectance, a green peak near 550 nm, and a chlorophyll trough near 670–680 nm.[^thorhaug]

If you want a **canopy proxy** rather than a clean-leaf endpoint, Voss et al.’s “reflectance 40 cm above the seagrass bed” is usable as an angular, field-measured proxy for the top of the bed. Reading their Figure 2 gives a much brighter and flatter signal than the leaf-only spectrum, approximately:

| Endpoint | 440 nm | 550 nm | 670 nm |
|---|---:|---:|---:|
| Seagrass-bed canopy proxy from Voss figure | 0.050 | 0.105 | 0.070 |

I would not use that Voss canopy-proxy spectrum as a pure linear endmember for cover mixing unless you explicitly want a **canopy-top apparent reflectance**. Voss themselves stress that, unlike the sand, the seagrass canopy is not well treated as Lambertian.[^voss]

## Carbonate sand endpoint

For bare Bahamian carbonate sand, the cleanest directly relevant source is again Voss et al. Their Figure 2 bright-sand trace is smooth and monotonic through the visible, and the text says the sand reflectance is **nominally greater than 0.5 at both 440 nm and 670 nm**. Reading the plotted black-circle sand curve gives roughly:

| Endpoint | 440 nm | 550 nm | 670 nm |
|---|---:|---:|---:|
| Bright Bahamian sand reflectance factor | 0.51 | 0.67 | 0.74 |

Those are the best **direct Bahamas spectrum reads** I found for all three wavelengths in one place, but they come with an important qualifier: the quantity in Voss is a **reflectance factor measured at 0° incidence and 45° view**, not a universally geometry-free Lambertian albedo. That is why the raw numbers are brighter than the bottom-reflectance magnitudes often used in water-column inversions.[^voss]

For a renderer, the more conservative choice is to reconcile that spectral shape with the widely cited Lee Stocking Island / Bahamas carbonate-sand brightness of about **R(555) = 0.4** noted by Hill et al. when summarizing the Bahamas literature. If you preserve the Voss spectral shape but anchor the sand magnitude at **0.40 at 550 nm**, the resulting **Lambertian-friendly working sand endpoint** is approximately:

| Endpoint | 440 nm | 550 nm | 670 nm |
|---|---:|---:|---:|
| Reconciled Bahamas carbonate sand working set | 0.30 | 0.40 | 0.44 |

I would use this second set for a renderer unless you know your bottom term is meant to mimic the same angle-specific reflectance factor used by Voss rather than a Lambertian or quasi-Lambertian benthic albedo.[^hill][^voss]

## A renderer-ready mixed bottom for sixty to seventy percent seagrass cover

Because Mobley et al. explicitly describe linear mixtures of **clean seagrass leaves + sand** in ten-percent steps for the Lee Stocking Island optical database, a simple linear mix is the most defensible way to generate your 60–70% cover constants from the sources above. I therefore mixed the **Thorhaug healthy-leaf endpoint** with the **reconciled Bahamas carbonate-sand working set**.[^mobley][^thorhaug][^hill]

Using spectral order **[440, 550, 670]**, the suggested mixed-bottom constants are:

```text
60% grass + 40% sand = [0.135, 0.207, 0.193]
65% grass + 35% sand = [0.121, 0.191, 0.173]
70% grass + 30% sand = [0.107, 0.175, 0.152]
```

In your renderer’s likely channel order **{670, 550, 440}**, those same vectors become:

```rust
// {670, 550, 440}
const T_THALASSIA_LEAF:      glam::Vec3 = glam::vec3(0.029, 0.078, 0.023);
const BAHAMAS_SAND_WORKING:  glam::Vec3 = glam::vec3(0.440, 0.400, 0.304);

const BANKS_MIX_60: glam::Vec3 = glam::vec3(0.193, 0.207, 0.135);
const BANKS_MIX_65: glam::Vec3 = glam::vec3(0.173, 0.191, 0.121);
const BANKS_MIX_70: glam::Vec3 = glam::vec3(0.152, 0.175, 0.107);
```

If you want one single replacement for your current estimated bottom constant, the midpoint is the cleanest pick:

```rust
const BOTTOM_BAHAMA_BANKS_65: glam::Vec3 = glam::vec3(0.173, 0.191, 0.121);
```

That midpoint stays inside your requested **60–70%** cover band and is sourced from a **measured _Thalassia_ leaf spectrum**, a **measured Bahamian carbonate-sand spectrum**, and the **Lee Stocking Island mixing convention** used in the shallow-water LUT literature.[^thorhaug][^voss][^mobley][^hill]

## Confidence and caveats

The strongest part of this answer is the **source pedigree**: all of the key optical measurements come from the Lee Stocking Island / Bahamas shallow-water optics literature or from a closely related _Thalassia_ laboratory spectrum paper. The weakest part is that none of the primary papers I found publish a clean, already-tabulated **440 / 550 / 670** table for both endpoints and the 60–70% mixture in one place. The relevant values are mostly published as **spectral curves**, so the wavelength-specific numbers above are necessarily **figure reads or source-consistent derived values**, not author-tabulated exact triples.[^thorhaug][^voss][^dierssen][^mobley]

There is also a real physical distinction between **leaf reflectance**, **canopy-top reflectance**, and **water-column-removed bottom reflectance**. Thorhaug gives you the first, Voss gives you the first and a canopy proxy, and Dierssen gives you the third but only from **450–650 nm**. That is why I recommend using the **Thorhaug clean-leaf endpoint** for the seagrass component, the **Hill-anchored Bahamas sand working set** for the carbonate substrate, and then a **Mobley-style linear mixture** for your cover fraction. That combination is the most internally consistent route to a renderer constant for Nassau and the Bahama Banks.[^thorhaug][^voss][^dierssen][^hill][^mobley]

If you want the answer in the shortest possible form for immediate shader use, use **`BOTTOM_BAHAMA_BANKS_65 = vec3(0.173, 0.191, 0.121)` in `{670,550,440}` order**, and document it as a **65% _Thalassia_ clean-leaf / 35% Bahamian carbonate-sand mix** derived from Thorhaug 2007, Voss 2003, Hill 2014, and Mobley 2005.[^thorhaug][^voss][^hill][^mobley]

## Source footnotes

[^thorhaug]: Thorhaug, Richardson, and Berlyn. “Spectral reflectance of the seagrasses _Thalassia testudinum_, _Halodule wrightii_, _Syringodium filiforme_ and five marine algae.” International Journal of Remote Sensing. ResearchGate PDF mirror: <https://www.researchgate.net/profile/Andrew-Richardson-14/publication/236771739_Spectral_reflectance_of_the_seagrasses_Thalassia_testudinum_Halodule_wrightii_Syringodium_filiforme_and_five_marine_algae/links/0c96052543befa7778000000/Spectral-reflectance-of-the-seagrasses-Thalassia-testudinum-Halodule-wrightii-Syringodium-filiforme-and-five-marine-algae.pdf>

[^voss]: Voss, Kenneth J., Curtis D. Mobley, Lydia K. Sundman, James E. Ivey, and Charles H. Mazel. “The spectral upwelling radiance distribution in optically shallow waters.” Lee Stocking Island / Bahamas optical measurements. PDF: <https://web3.physics.miami.edu/~voss/ken/RefPapers/047_VMSIM_LO_2003.pdf>

[^dierssen]: Dierssen, H. M. et al. “Ocean color remote sensing of seagrass and bathymetry in the Bahamas Banks by high-resolution airborne imagery.” PDF: <https://www.vliz.be/imisdocs/publications/322115.pdf>

[^mobley]: Mobley, C. D. et al. “Interpretation of hyperspectral remote-sensing imagery by spectrum matching and look-up tables.” Lee Stocking Island, Bahamas LUT paper. PDF: <https://mistis.inrialpes.fr/docs/biblioPlaneto/Mobley_LUT_11Mar04.pdf>

[^hill]: Hill, V. J. et al. “Evaluating Light Availability, Seagrass Biomass, and Productivity Using Hyperspectral Airborne Remote Sensing.” Includes Bahamas carbonate-sand brightness reference near R(555)=0.4. PDF: <https://hyperspectral-remote-sensing-marinesciences.media.uconn.edu/wp-content/uploads/sites/3833/2015/09/Hill_2014_SeagrassSJB.pdf>
