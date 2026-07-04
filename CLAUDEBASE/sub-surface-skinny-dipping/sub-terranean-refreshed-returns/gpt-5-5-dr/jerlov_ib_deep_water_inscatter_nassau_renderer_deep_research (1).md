# Jerlov IB Deep-Water In-Scatter for the Nassau Renderer

> Portable Markdown export of the Deep Research report. Deep Research UI citation tokens have been converted into Markdown footnotes so the file remains stable outside the ChatGPT interface.

## Executive answer

For the specific quantity you want to calibrate, the most defensible target is **the semi-infinite deep-water return spectrum**, not the raw scattering spectrum. In clear oceanic water, the color that survives once the bottom disappears is controlled primarily by the ratio of **backscattering to absorption**, not by extinction alone. In the classical ocean-color treatment, the deep-water reflectance is approximated by \(R_\infty(\lambda)\propto b_b(\lambda)/a(\lambda)\), with a modest geometry factor \(f\) that changes brightness more than hue. In very clear Case 1 waters, molecular scattering contributes strongly to \(b_b\), and at low chlorophyll it can even dominate the backscattered term.[^morel-maritorena][^lee-remote-sensing][^vliz-water-optics]

Using the Williamson–Hollins Jerlov IB spectral IOPs at your three wavelengths, plus modern/open-ocean backscattering parameterizations, the **elastic** deep-water color comes out **bluer than your current estimate**. A strict derivation based on the Williamson–Hollins spectra, the Hollins 2023 particle split, and Morel-style particle backscattering probabilities gives a **blue-normalized** ratio of roughly **440:550:670 = 1.00 : 0.29 : 0.024**. A simpler “single-table” fallback that assumes the Case 1 particulate backscattering ratio \(b_{bp}/b_p \approx 0.01\) gives **1.00 : 0.39 : 0.045**. An independent chlorophyll-based Case 1 check at Jerlov IB’s typical chlorophyll level of about **0.15–0.16 mg m\(^{-3}\)** gives **1.00 : 0.36 : 0.039**. Taken together, the practical envelope is **G/B \(\approx 0.29\) to \(0.39\)** and **R/B \(\approx 0.024\) to \(0.045\)**.[^williamson-hollins-pubmed][^williamson-hollins-rg][^hollins-chlorophyll][^huot-backscatter][^morel-maritorena]

So, if you want one renderer-ready midpoint for the **deep-water asymptote**, a good working target is:

```glsl
// RGB order = red, green, blue
vec3 WATER = vec3(0.03, 0.32, 1.00);   // normalized chromaticity
```

If you want to preserve your current blue magnitude of **0.185**, the midpoint becomes:

```glsl
vec3 WATER = vec3(0.0059, 0.060, 0.185);
```

That midpoint is physically better grounded than your current `vec3(0.012, 0.075, 0.185)`, and it also explains why your present estimate felt plausible: your **green** was close to the simple one-table Case 1 estimate, but your **red** is high for a true Jerlov IB deep-water asymptote.[^huot-backscatter][^morel-maritorena]

## The optical quantity you actually want

Once the bottom is no longer contributing, the visually relevant quantity is the **radiance or reflectance of a semi-infinite homogeneous water column**. In ocean optics, that asymptotic return is not modeled as “scatter color” alone. Morel and Prieur’s framework, carried forward in later ocean-color work, treats the deep-water return as a function of **backscattering** \(b_b\) against **absorption** \(a\). Morel and Maritorena write this in simplified form as \(R(\lambda)=f[b_b(\lambda)/a(\lambda)]\), with the caveat that if \(b_b\) is not negligible the denominator should be \(a+b_b\). The IOCCG/Lee treatment presents the same physics for subsurface remote-sensing reflectance, again proportional to \(b_b/a\) in clear waters.[^morel-maritorena][^lee-remote-sensing]

That matters for your shader because a Beer–Lambert medium with a hardcoded deep-water color should represent the **net result of repeated backscatter that escapes after being filtered by absorption**, not the raw volume-scattering coefficient itself. If you set your `WATER` constant from \(b(\lambda)\) or from extinction \(\sigma_t(\lambda)\) alone, you will bias the result away from the physically observed asymptote. The asymptote is especially sensitive in Jerlov IB because water’s red absorption is large, while the backscattered signal in the blue remains supported by molecular scattering.[^morel-maritorena][^lee-remote-sensing][^vliz-water-optics]

A practical implication follows. If your shader’s `WATER` term is standing in for the **far-field deep-water source** seen after the bottom vanishes, then \(W(\lambda)\propto b_b(\lambda)/(a(\lambda)+b_b(\lambda))\) is the safest compact target. In Jerlov IB at 440, 550, and 670 nm, \(b_b \ll a\) except only mildly less so in the blue, so \(b_b/a\) and \(b_b/(a+b_b)\) give nearly the same hue; the difference is mainly a small brightness trim in blue.[^morel-maritorena][^lee-remote-sensing]

## How to derive it directly from Williamson and Hollins

The Williamson–Hollins Jerlov IB table gives the key inherent optical properties you need. At the wavelengths relevant to your renderer, the paper’s proposed Jerlov IB coefficients are approximately:

- \(a(440)=0.0423\), \(a(550)=0.0655\), \(a(670)=0.417\ \mathrm{m}^{-1}\)
- \(b(440)=0.136\), \(b(550)=0.122\), \(b(670)=0.113\ \mathrm{m}^{-1}\)[^williamson-hollins-pubmed][^williamson-hollins-rg]

The missing step is that these are **total scattering** values, whereas the asymptotic water color needs **backscattering**. The cleanest way to bridge that gap is to use the follow-on Hollins–Williamson particle decomposition. Their Jerlov model splits scattering into molecular water plus “small” and “large” particle terms:

\[
b(\lambda)=b_w(\lambda)+b_p(\lambda)
\]

\[
b_w(\lambda)=0.00583\left(\frac{400}{\lambda}\right)^{4.322}
\]

\[
b_p(\lambda)=B_s\,1.1513\left(\frac{400}{\lambda}\right)^{1.7}
           +B_l\,0.3411\left(\frac{400}{\lambda}\right)^{0.3}
\]

For Jerlov IB, the fitted values are \(B_s \approx 0.010\) and \(B_l \approx 0.37\). The same paper puts the typical Jerlov IB chlorophyll concentration near **0.15–0.16 mg m\(^{-3}\)**, which is comfortably in the clear-ocean Case 1 regime.[^hollins-chlorophyll]

To turn those scattering terms into **backscattering**, Morel and Maritorena’s Case 1 reappraisal is especially useful because it adopts the same Kopelevich/Haltrin two-particle view and reports characteristic **backscattering probabilities** of about **3.9% for the small-particle population** and **0.064% for the large-particle population**, while pure seawater contributes **half of its molecular scattering to backscatter**. That gives the refined estimator:

\[
b_b(\lambda)\approx 0.5\,b_w(\lambda)+0.039\,b_{p,s}(\lambda)+0.00064\,b_{p,l}(\lambda).
\]

If you want a simpler method that uses only the Williamson–Hollins \(a(\lambda)\) and \(b(\lambda)\) table, Huot et al. report that in Case 1 waters the particulate backscattering ratio \(b_{bp}/b_p\) is typically near **0.01**, spectrally almost neutral, and not strongly chlorophyll-dependent. That yields a reliable one-table fallback:

\[
b_b(\lambda)\approx 0.5\,b_w(\lambda)+0.01\,[\,b(\lambda)-b_w(\lambda)\,].
\]

Then feed \(b_b(\lambda)\) into either \(R_\infty(\lambda)\propto b_b/a\) or \(R_\infty(\lambda)\propto b_b/(a+b_b)\), normalize by blue, and map the three wavelengths into your RGB channels.[^huot-backscatter][^morel-maritorena][^lee-remote-sensing]

## Numerical result for Jerlov IB

The table below applies the Williamson–Hollins Jerlov IB values at 440, 550, and 670 nm and computes the semi-infinite **subsurface** reflectance \(R_\infty\) with the standard \(0.33\,b_b/a\) approximation. The “simple” column uses the Case 1 shortcut \(b_{bp}/b_p=0.01\). The “refined” column uses the Hollins particle split with Morel–Maritorena backscattering probabilities. These are **derived values**, not copied values.[^williamson-hollins-pubmed][^williamson-hollins-rg][^hollins-chlorophyll][^huot-backscatter][^morel-maritorena]

| Wavelength | \(a\) | \(b\) | \(R_\infty\) simple | \(R_\infty\) refined |
|---|---:|---:|---:|---:|
| 440 nm | 0.0423 | 0.136 | 0.0254 | 0.0187 |
| 550 nm | 0.0655 | 0.122 | 0.00978 | 0.00539 |
| 670 nm | 0.417 | 0.113 | 0.00114 | 0.000451 |

From that table, the blue-normalized chromaticities are:

- **Simple one-table fallback:** **1.00 : 0.386 : 0.045** at **440:550:670**
- **Refined Jerlov-specific split:** **1.00 : 0.289 : 0.024** at **440:550:670**[^huot-backscatter][^morel-maritorena][^lee-remote-sensing]

An independent sanity check comes from the updated Morel–Maritorena Case 1 reflectance model evaluated at the Jerlov IB chlorophyll level. Jerlov IB’s median chlorophyll in the Hollins recalibration is about **0.15–0.16 mg m\(^{-3}\)**, and the Morel–Maritorena curves and discussion around that oligotrophic range show blue-to-green reflectance ratios in the same ballpark: clearly several times brighter in the blue than the green, with the red far lower still. Their field/model comparison also explicitly notes a station near **0.150 mg m\(^{-3}\)**. That independent route lands close to **1.00 : 0.36 : 0.039**, which sits between the simple and refined estimates above.[^hollins-chlorophyll][^morel-maritorena]

The central optical reason is straightforward. Between 440 and 670 nm, Williamson–Hollins absorption rises from **0.0423** to **0.417 m\(^{-1}\)**, roughly a tenfold jump, while scattering changes only modestly. So even though some red photons are backscattered, the water column absorbs them so aggressively that the asymptotic return becomes overwhelmingly blue.[^williamson-hollins-rg][^morel-maritorena]

## Renderer-ready recommendation

If you want the **strictest Jerlov-specific answer**, use the refined split as your chromaticity target:

```glsl
// normalized to blue = 1
vec3 WATER = vec3(0.024, 0.289, 1.000);
```

If you want the **easiest method that can be derived from the Williamson–Hollins table alone**, use the simple one-table fallback:

```glsl
// normalized to blue = 1
vec3 WATER = vec3(0.045, 0.386, 1.000);
```

If you want the best single production number from this research packet, I would use the midpoint of the physically plausible envelope:

```glsl
// recommended midpoint
vec3 WATER = vec3(0.032, 0.324, 1.000);
```

That midpoint is the most useful answer for your exact renderer problem because it respects the Williamson–Hollins IOPs, agrees with modern Case 1 reflectance behavior, and acknowledges that the least certain quantity here is the **particulate backscattering partition**, not the absorption spectrum.[^williamson-hollins-pubmed][^hollins-chlorophyll][^huot-backscatter][^morel-maritorena]

If you keep your current blue magnitude of **0.185**, the three practical RGB choices become:

| Choice | Suggested `vec3(R,G,B)` |
|---|---|
| Simple one-table fallback | `vec3(0.0083, 0.0714, 0.185)` |
| Refined Jerlov-specific split | `vec3(0.0045, 0.0535, 0.185)` |
| Recommended midpoint | `vec3(0.0059, 0.0600, 0.185)` |

So, in direct response to your estimate: **your green/blue ratio of about 0.40 is not unreasonable** if you use the simplest Case 1 backscattering shortcut, but once you apply the Jerlov-specific small/large particle split, the physically stricter answer moves lower, into the **0.29–0.36** range. The red channel is the place where your present constant is least consistent with Jerlov IB deep water.[^huot-backscatter][^morel-maritorena]

## What uncertainty still remains

The biggest uncertainty is not in \(a(\lambda)\); it is in how you convert the measured **total scattering** \(b(\lambda)\) into the much smaller and more phase-function-sensitive **backscattering** \(b_b(\lambda)\). Morel and Maritorena explicitly note that parameterizations of \(b_b\) in low-chlorophyll waters can diverge, and they call for field determinations. That is exactly why the simple, refined, and chlorophyll-based routes do not collapse to one identical answer.[^morel-maritorena]

There is also a small inelastic correction. Morel and Maritorena note that when Raman scattering is omitted, predicted clear-water reflectance is underestimated by about **8–10% in the blue-green** and about **15% in the long wavelengths**. That changes brightness more than hue, and it does **not** rescue a large red channel; it only nudges the elastic solution upward slightly. So if you want a tiny perceptual softening of the midpoint for filmic output, a mild green/red lift is defensible, but a deep-water Jerlov IB constant should still stay substantially bluer than your current `vec3(0.012, 0.075, 0.185)`.[^morel-maritorena]

If you later want to move beyond a three-sample RGB proxy, the clean long-term path is to compute \(R_\infty(\lambda)\) across the full Williamson–Hollins 300–800 nm table, then integrate that spectrum against your renderer’s camera/sRGB primaries instead of sampling only 440, 550, and 670 nm. The derivation above is still the right one; only the final spectral-to-RGB reduction changes.[^williamson-hollins-figshare][^morel-maritorena][^lee-remote-sensing]

## Source notes

[^williamson-hollins-pubmed]: Williamson & Hollins, “Measured IOPs of Jerlov water types,” PubMed record for PMID 36606827: <https://pubmed.ncbi.nlm.nih.gov/36606827/>

[^williamson-hollins-rg]: Williamson & Hollins, “Measured IOPs of Jerlov water types,” ResearchGate page: <https://www.researchgate.net/publication/364766106_Measured_IOPs_of_Jerlov_water_types>

[^williamson-hollins-figshare]: Dataset accompanying “Measured inherent optical properties of Jerlov water types,” Figshare: <https://figshare.com/articles/dataset/Dataset_to_accompany_paper_Measured_inherent_optical_properties_of_Jerlov_water_types/20290782>

[^hollins-chlorophyll]: Hollins/Williamson follow-on chlorophyll-based model, ResearchGate page: <https://www.researchgate.net/publication/372427829_Chlorophyll-based_model_underpinned_by_measured_inherent_optical_properties_of_Jerlov_water_types>

[^morel-maritorena]: Morel & Maritorena, Case 1 optical-property and reflectance model PDF: <https://genius.ucsd.edu/Public/MorelMaritorena/Morel_and_Maritorena_JGR_01.pdf>

[^huot-backscatter]: Huot et al., Case 1 particulate backscattering discussion, Biogeosciences PDF: <https://bg.copernicus.org/articles/5/495/2008/bg-5-495-2008.pdf>

[^lee-remote-sensing]: Lee et al./remote-sensing reflectance treatment, Optica abstract: <https://opg.optica.org/ao/abstract.cfm?uri=ao-37-21-4765>

[^vliz-water-optics]: Supplementary ocean optics PDF mirrored at VLIZ: <https://www.vliz.be/imisdocs/publications/363436.pdf>
