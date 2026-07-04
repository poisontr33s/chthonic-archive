# Nassau Renderer Bathymetry Research for the Bahama Banks

## Bottom line

The cleanest answer is this: **your current 0.3° bathymetry is not the native resolution of GEBCO**. OpenTopoData’s own GEBCO page says its `gebco2020` dataset is the global GEBCO 2020 grid at **15 arc-seconds**, not 0.3°. GEBCO’s official newer releases continue that same nominal grid spacing: GEBCO_2024 and the current GEBCO_2026 are both global **15 arc-second** grids. In other words, your present 56×22 bank mesh is a very coarse downstream sampling of a much finer source raster. Moving from sparse point sampling to native GEBCO subsetting is already a major upgrade, even before switching products.[^opentopodata-gebco2020][^gebco-2024][^gebco-gridded]

On the specific provider question, **OpenTopoData** still publicly documents **GEBCO 2020**, and its public service is a **point-query API** with strict sustainability limits. **OpenTopography** is a different service: its current developer documentation requires API keys and lists bathymetric datasets such as **SRTM15Plus** and **GEBCOIceTopo/GEBCOSubIceTopo**, but I did not find an official OpenTopography API listing for a named **GEBCO_2024/2025/2026** endpoint. GEBCO itself, however, now distributes the newer grids directly through its own download app and OPeNDAP access.[^opentopodata-api][^opentopodata-home][^opentopography-developers][^opentopography-gebco2023-news][^gebco-gridded]

If you need a **strictly free, no-key, queryable** alternative that can exceed GEBCO’s nominal ~15-arc-second spacing where local high-resolution data exist, the best fit I found is **GMRT**. Its GridServer supports direct bounding-box subsetting and says it can deliver data up to roughly **100 m per node** where high-resolution content is available; critically, its `topo-mask` layer returns only genuine high-resolution ocean data and leaves other ocean cells blank, which makes it a good immediate coverage test for the Bahama Banks.[^gmrt-gridserver][^gmrt-services]

If you can accept **free access with account login**, the strongest higher-resolution candidate is **Copernicus Marine’s global coastal satellite-derived bathymetry** product. It is described as **global coastal**, **100 m resolution**, Sentinel-2 based, and available through subset/download/map/programmatic access, with separate **quality indicator** variables. For clear tropical carbonate shallows, that is the most promising open-access product I found for actually recovering the broad turquoise flats visually. It is explicitly **not for navigation** and its supported programmatic path is account-based rather than no-key.[^copernicus-sdb-description][^copernicus-sdb-services][^copernicus-login][^copernicus-toolbox-intro][^copernicus-credentials]

## What is actually limiting your current pipeline

The most important technical correction is that **GEBCO 2020 was never a ~30 km bathymetry product**. OpenTopoData’s GEBCO page says the source grid is **15 arc-seconds**, corresponding to about **450 m at the equator**. GEBCO’s official GEBCO_2024 and GEBCO_2026 pages say the same thing: the global grid is distributed on a **15 arc-second interval**. Around Nassau’s latitude, that is on the order of a few hundred meters per cell, not tens of kilometres.[^opentopodata-gebco2020][^gebco-2024][^gebco-gridded]

So the present bottleneck is not only “which bathymetry product,” but also **how you are querying it**. OpenTopoData is designed as a point-elevation API. Its docs describe a single point-query endpoint, and its public service limits are **100 locations per request**, **1 call per second**, and **1000 calls per day**. That is fine for sparse sampling, but it is a poor fit for regenerating a dense bathymetry surface over the Bahama Banks.[^opentopodata-api][^opentopodata-home]

That means there are really two separate gains available to you. The first is immediate and low-risk: **stop sampling GEBCO on a 0.3° lattice** and instead subset the native GEBCO grid directly. The second is the harder one: **replace GEBCO’s generalized shallow-water bathymetry with a genuinely higher-resolution shallow-coastal product** where available. For the Nassau turquoise problem, the second change matters most visually, but the first one is the fastest win and removes a major self-inflicted blur. The inference follows directly from the mismatch between OpenTopoData’s documented 15-arc-second source and your current ~0.3° sampling regime.[^opentopodata-gebco2020][^gebco-gridded]

There is also a shallow-water caveat in GEBCO itself that matters for your shader calibration. GEBCO notes that its global grids assimilate heterogeneous shallow-water sources and that, in some shallow areas, source data may use a vertical datum **other than mean sea level**. On features only **0.5–2 m** deep, datum inconsistencies of that scale can materially affect whether a cell looks “sand-flat turquoise” or “deeper cyan.”[^gebco-gridded]

## The current status of GEBCO in OpenTopoData, OpenTopography, and GEBCO official access

### OpenTopoData

OpenTopoData’s public documentation still points to **GEBCO 2020**. Its dataset page is specifically titled **GEBCO 2020 Bathymetry**, and it describes that product as global at **15 arc-seconds**. I found no official OpenTopoData dataset page for **GEBCO 2024**, **GEBCO 2025**, or **GEBCO 2026**. Its API documentation also presents OpenTopoData as a point-query service, not a raster subsetting service.[^opentopodata-gebco2020][^opentopodata-api][^opentopodata-home]

That matters because even if OpenTopoData eventually updates its backend, it is still architecturally a poor way to pull a dense Bank-wide raster into a renderer. For your use case, OpenTopoData is better thought of as a convenience point sampler than as a production bathymetry endpoint.[^opentopodata-api][^opentopodata-home]

### OpenTopography

OpenTopography’s current developer page lists a **Global Datasets API** that requires **API keys** and exposes datasets including **SRTM15+ V2.1**, **GEBCOIceTopo**, and **GEBCOSubIceTopo**. Its documented request limits for those bathymetry datasets are on very large bounding boxes, which confirms that it can serve regional subsets, but it is **not** a no-key service.[^opentopography-developers]

OpenTopography also published a news item in April 2024 announcing access to **GEBCO_2023** through the portal and its Global Datasets API. But in the current developer documentation I found, the bathymetry datasets are still exposed under the generic OT dataset names above, not as a named public **GEBCO_2024** or later endpoint. So the best reading is: OpenTopography is an API-capable path, but **not a clean no-key upgrade path to a clearly documented GEBCO_2024+ bathymetry endpoint**.[^opentopography-gebco2023-news][^opentopography-developers]

### GEBCO itself

GEBCO’s own official distribution has moved on. Its current gridded bathymetry page says the latest release is **GEBCO_2026**, still on a **15 arc-second** global grid, and that users can download **global files**, **user-defined areas**, and access the grids through **OPeNDAP**. That is the authoritative upgrade path if your goal is “latest GEBCO, native spacing, machine access.”[^gebco-gridded]

GEBCO also now offers a **test multi-resolution grid product**, but the official page says those test areas are currently limited to waters around **Australia**, **New Zealand**, and the **Hawaiian Islands**. I found no indication that the Bahama Banks are part of that test multi-resolution coverage. So there is **no official GEBCO multi-resolution Bahamas shortcut** at the moment.[^gebco-multires][^gebco-gridded]

## Other open-access products that matter for the Bahama Banks

### GMRT

GMRT is the strongest **free/no-key/queryable** option I found. Its overview says it is a multi-resolution DEM with services for **grids, images, points, and profiles**. Its web-services page documents a **GridServer** and a **PointServer**, both with simple HTTP interfaces and no mention of credentials. The GridServer documentation says requests can be made by bbox and that maximum available resolution is about **100 m/node**; the `topo-mask` layer returns only areas with actual high-resolution ocean data and leaves everything else blank.[^gmrt-about][^gmrt-services][^gmrt-gridserver][^gmrt-pointserver]

That last point is exactly what makes GMRT useful for your renderer workflow. You can issue one bbox request over `20–27°N, 79.9–72.7°W` and immediately learn whether the Bahamas region has enough genuinely high-resolution public bathymetry to matter. If `topo-mask` comes back mostly empty over the Bank interior, GMRT is not your solution. If it comes back with continuous coverage over the shallow platforms, then it is your cleanest no-key upgrade.[^gmrt-gridserver][^gmrt-pointserver]

One caution: GMRT’s high-resolution content is explicitly tied to curated contributions such as swath bathymetry and contributed grids. In the Bahamas-related MGDS records I surfaced, I found examples of **singlebeam** and seismic-era marine geophysics on the Bahama carbonate banks, which suggests there is Bahamas data in the broader ecosystem, but not necessarily a continuous shallow-bank multibeam blanket. That means GMRT is promising enough to test, but I would treat continuous Nassau Bank coverage as **unverified until you query `topo-mask` directly**. This is an inference from GMRT’s service design plus the type of Bahamas-region records I found, not a direct GMRT coverage map for your exact bbox.[^gmrt-gridserver][^marine-geo-rc2311]

### Copernicus Marine global coastal SDB

The most interesting non-GEBCO product is Copernicus Marine’s **Global coastal satellite derived bathymetry static** product. Its official description says it covers the **global coastal area where data retrieval is possible**, at **100 × 100 m** resolution, based on **Sentinel-2**, using a combination of **intertidal SDB**, **physics-based optical SDB**, and **wave-kinematics SDB**. It also exposes separate **quality indicator** variables.[^copernicus-sdb-description]

The corresponding services page says the product is available through **subset forms**, **file browsing**, **WMTS map services**, and the **Copernicus Marine Toolbox** for programmatic access. The programmatic path is free, but it is officially account-based: Copernicus’ own help material says users create an account and then configure credentials for the Toolbox. So this is **free/open**, but **not no-key/no-login** in the strict sense.[^copernicus-sdb-services][^copernicus-login][^copernicus-toolbox-intro][^copernicus-credentials]

For your visual goal, though, it is a serious candidate. The Bahamas are a classic clear-water shallow-carbonate environment, and the product is explicitly designed for global shallow coastal retrieval from optical satellite data. I could not verify from the public metadata alone that every part of your full bbox is populated, but on paper this is the most plausible open-access product for recovering the large shallow flats that drive the Bank’s bright turquoise appearance.[^copernicus-sdb-description][^copernicus-sdb-services][^vliz-dierssen]

### NOAA, USGS, and EMODnet

NOAA and USGS do **not** look like clean solutions for this Bahamas bbox. NOAA’s **BlueTopo** and National Bathymetric Source materials describe their mission and products in terms of **U.S. waters** and **U.S. territorial waters**. USGS **3DEP** is similarly framed around the **United States and its territories**, with official seamless product coverage described for the conterminous U.S., Hawaii, Puerto Rico, other territorial islands, and limited Alaska coverage. That excludes the Bahama Banks.[^noaa-bluetopo][^noaa-nbs][^usgs-3dep][^data-gov-3dep-dem]

EMODnet Bathymetry is also not your answer. Its official geographic coverage says the 2024 European DTM covers European sea regions, and its Caribbean release is bounded by **70°W to 60°W** and **11°N to 19°N**. Your target box is **72.7°W to 79.9°W** and **20°N to 27°N**, so the Bahamas fall outside that published Caribbean DTM extent.[^emodnet]

## What grid resolution is enough for the Nassau turquoise

The answer depends on what you mean by “start to appear.” If you only need the **broad shallow banks** to stop averaging out to implausible 5–10 m depths, then native GEBCO at 15 arc-seconds is already a meaningful step up from your current 0.3° sampling. A ~15-arc-second cell around Nassau is a few hundred meters across, so multi-kilometre flats can begin to resolve as shallow provinces rather than disappearing into 30 km averages.[^opentopodata-gebco2020][^gebco-gridded]

If you want the **visually convincing Bank turquoise** — meaning shelf-edge sharpness, reef-flat boundaries, cuts, channels, and the spatial rhythm of bright shoals against slightly deeper cyan — then **~100 m** is the first resolution tier that is likely to look materially different in a renderer. That is why GMRT’s best-case ~100 m and Copernicus Marine’s 100 m coastal SDB are both potentially important. At that scale you are roughly four times finer than GEBCO in each linear dimension and on the order of twenty times finer in cell area.[^gmrt-gridserver][^copernicus-sdb-description]

For true **narrow-bank and patch-scale structure**, though, 100 m is still only the beginning. The Bahamas literature you flagged is consistent with that. The classic Bahamas Banks airborne hyperspectral study reported that bathymetry near Lee Stocking Island was mapped at **meter-scale resolution**, and it noted that benthic distributions varied on **meter scales**. The paper also contrasts that kind of fine-scale structure with coarser satellite products such as 30 m Landsat. The implication is straightforward: **100 m will start to recover broad flats**, **30 m will materially improve bank-edge structure**, and **10 m to meter-scale** is where the Nassau shallows really stop looking generalized.[^vliz-dierssen]

So the practical threshold for your project is this:

- **Native GEBCO 15 arc-second**: enough to stop throwing away most of the available detail; broad banks should start to separate.[^opentopodata-gebco2020][^gebco-gridded]
- **~100 m**: the first tier likely to unlock the large, bright shallow-flat signal convincingly in a rendered map.[^gmrt-gridserver][^copernicus-sdb-description]
- **~30 m or finer**: where narrow shoals, reef margins, and channel geometry begin to read properly rather than as blurred gradients. This is an inference from Bahamas meter-scale mapping results and general image-sampling logic.[^vliz-dierssen]

## Recommended endpoint strategy for Nassau Renderer

If you want the **highest-impact change with the least disruption**, I would separate your options into three tiers.

First, if you want the **fastest immediate improvement** without changing product family, replace the current OpenTopoData-style sparse sampling with **official GEBCO subsetting** at native resolution. GEBCO now officially supports **user-defined area downloads** and **OPeNDAP** access, and the grid remains public-domain. That alone removes the 0.3° bottleneck.[^gebco-gridded]

Second, if your requirement is **strictly free and no-key**, test **GMRT `topo-mask`** over the full Bahamas bbox. If it returns meaningful shallow-bank coverage, switch your `--bathymetry` endpoint to GMRT for the high-resolution zone and use GEBCO offshore as fallback. If it comes back mostly blank over the Banks, GMRT is not the unlock you need. The nice thing is that the service itself is built to make exactly this coverage test cheap.[^gmrt-gridserver][^gmrt-pointserver]

```bash
# GMRT: query only genuine high-resolution ocean data in your bbox
curl "http://www.gmrt.org/services/GridServer?north=27&south=20&west=-79.9&east=-72.7&layer=topo-mask&format=netcdf&resolution=max" -o bahamas_gmrt_mask.nc
```

GMRT documents this bbox-style GridServer interface, its `topo-mask` layer, and maximum available resolution near 100 m/node.[^gmrt-gridserver][^gmrt-services]

Third, if a **free account login is acceptable**, the best upside path is a **hybrid shallow/deep pipeline**: use the Copernicus Marine **merged 100 m coastal SDB** where it has valid data and acceptable quality, then fall back to GEBCO_2026 outside shallow-coastal retrieval coverage. Because Copernicus exposes **quality indicator** variables alongside water depth, you do not have to trust every tile equally.[^copernicus-sdb-description][^copernicus-sdb-services][^copernicus-toolbox-intro][^copernicus-credentials]

```text
Primary shallow-water dataset:
cmems_obs-sdb_glo_phy_comp_my_100m-l4-s2_static

Fallback deep-water dataset:
GEBCO_2026 15-arc-second grid
```

That leaves one final judgment call. If your rule is **strictly no-key**, then I did **not** find a demonstrably better fully open, global, queryable, no-key product than **GMRT plus GEBCO** for the Bahama Banks. If your rule is **free access even with login**, then **Copernicus Marine 100 m coastal SDB** is the most promising route I found to the “correct turquoise.”[^gmrt-gridserver][^gebco-gridded][^copernicus-sdb-description][^copernicus-sdb-services][^copernicus-login]

---

## Source notes

[^opentopodata-gebco2020]: OpenTopoData, “GEBCO 2020 Bathymetry.” <https://www.opentopodata.org/datasets/gebco2020/>

[^opentopodata-api]: OpenTopoData, “API docs.” <https://www.opentopodata.org/api/>

[^opentopodata-home]: OpenTopoData, home page and public dataset listing. <https://www.opentopodata.org/>

[^gebco-2024]: GEBCO, “The GEBCO_2024 Grid.” <https://www.gebco.net/data-products-gridded-bathymetry-data/gebco2024-grid>

[^gebco-gridded]: GEBCO, “Gridded Bathymetry Data.” <https://www.gebco.net/data-products/gridded-bathymetry-data>

[^gebco-multires]: GEBCO, “GEBCO multi-resolution grid product.” <https://www.gebco.net/data-products/gridded-bathymetry-data/multi-res>

[^opentopography-developers]: OpenTopography, “OpenTopography for Developers.” <https://opentopography.org/developers>

[^opentopography-gebco2023-news]: OpenTopography, “GEBCO Global Bathymetry and Topography Dataset Available.” <https://opentopography.org/news/gebco-global-bathymetry-and-topography-dataset-available>

[^gmrt-about]: GMRT, “GMRT Overview.” <https://www.gmrt.org/about/>

[^gmrt-services]: GMRT, “Services.” <https://www.gmrt.org/services/index.php>

[^gmrt-gridserver]: GMRT, “GridServer Information.” <https://www.gmrt.org/services/gridserverinfo.php>

[^gmrt-pointserver]: GMRT, “PointServer Information.” <https://www.gmrt.org/services/pointserverinfo.php>

[^marine-geo-rc2311]: Marine Geoscience Data System, “RC2311.” <https://www.marine-geo.org/tools/entry/RC2311>

[^copernicus-sdb-description]: Copernicus Marine Service, “Global coastal satellite derived bathymetry static — Description.” <https://data.marine.copernicus.eu/product/BATHYMETRY_GLO_PHY_COASTAL_L4_MY_016_001/description>

[^copernicus-sdb-services]: Copernicus Marine Service, “Global coastal satellite derived bathymetry static — Services.” <https://data.marine.copernicus.eu/product/BATHYMETRY_GLO_PHY_COASTAL_L4_MY_016_001/services>

[^copernicus-login]: Copernicus Marine Help Center, “How to log in, log out or change the password of my Copernicus Marine account.” <https://help.marine.copernicus.eu/en/articles/4444552-how-to-log-in-log-out-or-change-the-password-of-my-copernicus-marine-account>

[^copernicus-toolbox-intro]: Copernicus Marine Help Center, “Copernicus Marine Toolbox — Introduction.” <https://help.marine.copernicus.eu/en/articles/7949409-copernicus-marine-toolbox-introduction>

[^copernicus-credentials]: Copernicus Marine Help Center, “Copernicus Marine Toolbox — Credentials configuration.” <https://help.marine.copernicus.eu/en/articles/8185007-copernicus-marine-toolbox-credentials-configuration>

[^noaa-bluetopo]: NOAA Office of Coast Survey, “BlueTopo™.” <https://nauticalcharts.noaa.gov/data/bluetopo.html>

[^noaa-nbs]: NOAA Office of Coast Survey, “National Bathymetric Source.” <https://nauticalcharts.noaa.gov/learn/nbs.html>

[^usgs-3dep]: USGS, “3D Elevation Program.” <https://www.usgs.gov/3d-elevation-program>

[^data-gov-3dep-dem]: Data.gov, “1/3rd arc-second Digital Elevation Models (DEMs) — USGS National Map 3DEP Downloadable Data Collection.” <https://catalog.data.gov/dataset/1-3rd-arc-second-digital-elevation-models-dems-usgs-national-map-3dep-downloadable-data-co>

[^emodnet]: EMODnet, “Bathymetry.” <https://emodnet.ec.europa.eu/en/bathymetry>

[^vliz-dierssen]: Dierssen, H. M., and Zimmerman, R. C. “Ocean color remote sensing of seagrass and bathymetry in the Bahamas Banks by high-resolution airborne imagery.” <https://www.vliz.be/imisdocs/publications/322115.pdf>
