# **Deep Research Brief: Astrological Nassau and the Computable Celestial Dimension**

---

## **0. Architectural Imperative and the Epistemic Reality**

* The engineering of a real-time Vulkan-based renderer for Nassau and the Bahama Banks—where the celestial sphere is not merely a graphical skybox but a rigorously structured field of semantic, mathematical, and navigational meaning—demands a highly specific architectural approach. The celestial dimension of this project, internally designated as the "Ankhology," requires an uncompromising synthesis of two distinct disciplines. The first is precise, arc-second-accurate astronomical computation, relying on modern orbital mechanics and ephemeris models. The second is historically rigorous, reconstructed astrological study, capturing the mathematical paradigms and interpretative frameworks of ancient cosmologies. This synthesis is divided equally between the Andean cosmological heritage and the Egyptological and Hellenistic tradition.

  * The fundamental challenge governing this dual architecture is a profound epistemic reality. The physical celestial bodies themselves, their orbital mechanics, and the geometric reference frames of the Earth and sky are exactly computable phenomena. Modern astrometry and governmental aerospace data can re-derive the exact position of Jupiter over the Bahama Banks in any given century with near-perfect accuracy.1 Conversely, the advanced mathematics and semantic structuring of historical astrology—such as the decanal stars, the radial geometry of the *ceque* system, the Hellenistic division of houses, and the Babylonian predictive ephemerides—reach the modern era primarily through reconstructed texts, fragmentary citations, and secondary archaeological interpretations.3

  * The foundational text of Hellenistic astrology, attributed to the pseudonymous Nechepso and Petosiris, survives only as fragments scattered across the works of later authors.6 The Andean *ceque* system and the dark-cloud constellations are documented not by their indigenous creators in a phonetic script, but through the post-conquest transcriptions of Spanish chroniclers such as Bernabé Cobo and Polo de Ondegardo, which have subsequently been reconstructed by modern ethnohistorians and archaeoastronomers.5

* Consequently, the foundational mandate of "accuracy, not fiction" requires that the software architecture explicitly classify every data source, software library, and Model Context Protocol (MCP) server as either strictly "computable" (derivable via Newtonian mechanics, spherical trigonometry, and NASA/JPL data) or strictly "attested" (reconstructed humanities corpora that must be cited, referenced, and never procedurally hallucinated). Blurring this boundary risks introducing algorithmic fabrication into the historical record. The following report provides an exhaustive, rigorously cited evaluation of the accessible MCP servers and open-source corpora capable of realizing this 50/50 celestial architecture, prioritizing additions to the existing Rust compute substrate and semantic search stack.

---

## **1. Cluster A: Accessible Model Context Protocol (MCP) Servers**

* The Model Context Protocol (MCP) provides an open standard to securely expose external data and computational capabilities to Large Language Models (LLMs) and intelligent agents.10 For the Astrological Nassau renderer, MCP servers serve as the critical bridge between the raw computational libraries powering the Vulkan engine and the semantic study substrate utilized for historical research. The evaluation of existing servers within the ecosystem reveals a stark divide between thin convenience wrappers and highly authoritative, primary-source-grade computational engines.

---

### **Astronomy and Ephemeris Computation Servers**

* The computational core of any celestial engine requires high-precision planetary positioning. Two primary MCP servers dominate the astrological and astronomical space, each representing a fundamentally different approach to underlying data derivation and licensing architecture.

  * The openephemeris-MCP server, developed under the Spirit-River repository, emerges as a highly authoritative, primary-source-grade implementation specifically tailored for AI agents.13 Backed by the NASA JPL DE440 and DE441 ephemeris models, this server provides sub-arcsecond accuracy across a vast temporal span of 1,100 years.2 Crucially for the project's deep astrological requirements, it exposes an extensive suite of 52 strongly typed tools. These encompass both traditional astronomical calculations (such as sidereal time and delta-T offsets) and complex astrological geometry.

  * The tooling covers traditional natal charts, Vedic sidereal charts, transits, planetary stations, void-of-course lunar phases, and even highly specialized techniques like astrocartography (ACG) power lines and Venus Star Points.13 Its reliance on the ICRF 3.0 reference frame, validated against spacecraft tracking and lunar laser ranging, elevates it above typical commercial astrological software, guaranteeing zero-hallucination data delivery to the LLM substrate.2

  * Conversely, the swiss-ephemeris-mcp-server (developed by dm0lz) provides an alternative approach, relying entirely on the Swiss Ephemeris C library.14 The Swiss Ephemeris itself is historically derived from NASA JPL data but is privately maintained by Astrodienst AG.16 This MCP server is capable of calculating planetary positions, true and mean lunar nodes, asteroids (including Chiron, Ceres, Pallas, Juno, and Vesta), and the 12-house Placidus system.14

  * It exposes four primary tools: calculate_planetary_positions, calculate_transits, calculate_solar_revolution (solar returns), and calculate_synastry for relationship compatibility charts.14

  * While highly accurate and featuring built-in Docker support for standard input (stdio) and HTTP transport modes, the introduction of the Swiss Ephemeris introduces profound architectural and legal complexities. The underlying C library is bound by the AGPL-3.0 license, which presents significant viral open-source risks to proprietary or hybrid codebases unless heavily isolated via network protocols.16 Another implementation, w8s-astro-mcp, offers similar Swiss Ephemeris precision via the pysweph Python wrapper, alongside the added utility of persistent chart history logging utilizing SQLite.18

  * NASA's official open APIs are also encapsulated by community servers such as the NASA-MCP-server (maintained by ProgramComputer) and the nasa-mcp-server (maintained by jezweb).19 These servers grant LLMs standardized access to the Astronomy Picture of the Day (APOD), Mars rover datasets, Space Weather Database Of Notifications (DONKI), and Earth Polychromatic Imaging Camera (EPIC) data.20 While highly valuable for modern observational contexts and aerospace workflows, they lack the specific temporal ephemeris computation required to retro-calculate and reconstruct the night sky over Nassau in antiquity, classifying them as secondary conveniences rather than primary compute engines for this specific historical project.

---

### **Digital Humanities and Primary-Text Servers**

* To seamlessly integrate the "attested" dimension of the celestial sphere, the project's study substrate must interface directly with machine-readable classical texts and archaeological datasets. The Perseus-mcp server (developed by tonyjurg) stands out as an exceptional architectural asset for this purpose.21 

  * It provides direct, programmatic access to the entirety of the Perseus Digital Library, utilizing precise Canonical Text Services (CTS) URNs and the Scaife viewer API.21 The server exposes twelve specialized tools, including get_passage_plaintext and search_perseus, which are uniquely capable of handling Unicode Greek and Beta Code queries (e.g., searching for specific astronomical terminology in ancient Greek).21 This capability is absolute critical infrastructure for indexing and retrieving Hellenistic astronomical texts, allowing the system to instantly query foundational works like Ptolemy's *Almagest* and *Tetrabiblos* without relying on hallucinated summaries.

  * However, for proprietary or highly customized corpora—such as digitized transcriptions of Spanish chroniclers detailing the Andean sky, or bulk data dumps from cuneiform databases—a localized Retrieval-Augmented Generation (RAG) server is necessary. The mcp-local-rag server provides a self-hosted, offline-capable architecture tailored precisely for this kind of bespoke document ingestion.22 It employs entirely local embedding generation utilizing the ONNX Runtime (defaulting to models like Xenova/all-MiniLM-L6-v2), ensuring that proprietary or pre-publication academic data never leaves the host machine.22

  * A critical feature of mcp-local-rag is its smart semantic chunking, which analyzes embedding similarity to locate natural topic boundaries rather than slicing texts using arbitrary character limits.22 Furthermore, it employs a hybrid search mechanism that balances vector similarity with a Full-Text Search (FTS) keyword boost, ensuring that exact astronomical terms or epigraphic registry numbers are not lost in semantic smoothing.22

  * Notably, the server features an optional Vision-Language Model (VLM) mode (utilizing models like SmolVLM-256M-Instruct or Qwen2.5-VL-3B-Instruct-ONNX), which is capable of parsing and captioning visual figures within PDFs.22 This feature is an unparalleled asset when processing scanned archaeological site diagrams of the Inca *ceque* system or manuscript illustrations of the Dendera Zodiac, converting visual spatial data into indexable textual chunks wrapped in specific semantic envelopes.

---

### **Matrix A: MCP Servers Evaluation**

| Server Repository | Domain | Transport | Auth / License | Self-Hostable | Data Grade | Fit / Recommendation |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| Spirit-River/openephemeris-MCP | Astronomy / Advanced Astrological Math | stdio, HTTP (SSE) | API Key / MIT | Yes | Primary (JPL DE440/441 backend) 13 | **High**. Authoritative compute layer. Provides zero-hallucination ephemeris without AGPL taint. |
| dm0lz/swiss-ephemeris-mcp-server | Astrological Math | stdio, HTTP | None / Server MIT (underlying AGPL) | Yes (Docker) | Primary (Swiss Eph) 14 | **Moderate**. Excellent architectural tools, but the AGPL taint from the underlying C library remains a critical risk profile. |
| tonyjurg/Perseus-mcp | Classics / Philology | stdio (FastMCP) | None / MIT | Yes | Primary (CTS / Scaife integration) 21 | **High**. Essential infrastructure for retrieving Hellenistic attested fragments directly from Perseus. |
| shinpr/mcp-local-rag | Document Retrieval (RAG) | stdio, CLI | None / MIT | Yes | N/A (Ingests user data) 22 | **High**. The ideal offline study substrate for ingesting CDLI records and Andean PDFs, particularly due to its VLM capabilities. |
| jezweb/nasa-mcp-server | Modern Observational | stdio | NASA API Key | Yes | Secondary Convenience | Low. Focuses heavily on modern terrestrial imagery and rover data rather than historical astronomical ephemerides.19 |
| iamjr15/astrology-mcp-puchai | Vedic Astrology | HTTP | OpenAI Key / Proprietary | No (Render Web Service) | Secondary Convenience 23 | Low. A hosted web service heavily reliant on LLM generation rather than strict ephemeris computation. |

---

## **2. Cluster B: Open Sources and Compute Libraries**

* Evaluating the foundational data structures and software libraries is vital to ensure the Rust/Vulkan engine avoids external dependencies that compromise rendering performance, historical accuracy, or legal standing. The compute engine must be able to calculate orbital positions at a high frame rate, while the study substrate requires clean, machine-readable text files to populate its vector databases.

---

### **Computation Libraries (The Engine Core)**

The established industry standard for astrological and astronomical computation in commercial software is the Swiss Ephemeris, maintained by Astrodienst AG.16 It offers sub-milliarcsecond precision and gracefully handles complex edge cases for thousands of asteroids, hypothetical bodies, and over a dozen different house systems.16 For a Rust-centric ecosystem, crates like swiss-eph and libswisseph-sys provide raw Foreign Function Interface (FFI) bindings to the C library, complete with support for WebAssembly (WASM) compilation for browser-based execution.24  
However, the Swiss Ephemeris is governed by a strict dual-licensing model: it is available under the GNU Affero General Public License version 3 (AGPL-3.0), or via a commercial license costing 700 CHF.17 Using libswisseph-sys directly within the project codebase would trigger the AGPL's viral copyleft provisions, forcing the entire Vulkan renderer—including all proprietary graphical assets and engine logic—to become open-source under the AGPL, or necessitating a commercial license purchase.  
An optimal, highly performant alternative for a pure Rust architecture is the rust-jpl crate (developed by CHINMAYVIVEK).1 This library parses the official NASA Jet Propulsion Laboratory (JPL) DE441 ephemeris data natively within Rust, eliminating the need for C-FFI overhead. It provides high-precision planetary and lunar positions, calendar-to-Julian date conversions, and solar system dynamics based on the ![][image1] and ICRF 3.0 reference frames.1 It is designed explicitly for scientific correctness, orbital mechanics, and astronomical trajectory planning, acting as a legally clean, highly optimized compute core for positional astronomy. To supply this library with the raw binary data files (SPK format), developers can utilize the JPL Horizons system web API and the NAIF SPICE toolkit, which provide the definitive, open-domain standard for planetary vectors.29

### **Machine-Readable Open Corpora (The Attested Substrate)**

* To populate the semantic search stack with historical data, the project requires digitised, open-access scholarly databases that provide bulk-download capabilities.  

  * The **Cuneiform Digital Library Initiative (CDLI)** represents the definitive, globally recognized corpus for Mesopotamian texts, including the Babylonian astronomical diaries, the *Enūma Anu Enlil*, and the *MUL.APIN*. The CDLI database catalogs over 390,000 artifacts from over 1,500 museums, offering deep metadata, transliterations, and translations.30 Crucially for integration into a local RAG pipeline, the CDLI repository (cdli-gh/data) provides daily bulk data dumps accessible via the git-lfs protocol, making it seamlessly indexable.33

  * For Greco-Roman texts and documentary evidence from Roman Egypt, **Papyri.info** serves as an indispensable resource. It aggregates material from the Duke Databank of Documentary Papyri (DDbDP) and the Heidelberger Gesamtverzeichnis (HGV), encompassing published Greek and Latin documents written on papyrus.34 The underlying structured data is hosted in the papyri/idp.data GitHub repository in the EpiDoc (TEI XML) format, allowing for programmatic bulk download, parsing, and automated metadata extraction.35 This corpus contains vast quantities of physical astrological horoscopes cast by practicing astrologers in antiquity, providing the granular "attested" layer for mundane astrological practices.  

  * The **Pleiades Gazetteer** is an essential community-built dataset for standardizing the geographic coordinates of historical observatories, ancient cities, and birthplaces. It provides authoritative, highly structured data on ancient places, available for bulk download in JSON, CSV, KML, and RDF formats via their GitHub repository (isawnyu/pleiades.datasets).38 This ensures that when the compute engine retro-calculates the sky over Alexandria or Cusco, the latitude and longitude parameters are historically accurate.

---

### **Matrix B: Open Sources Evaluation**

| Source / Project | Type | Domain | Access / License | Machine-Readable | Computable / Attested | Recommendation |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| rust-jpl crate | Compute Library | Astronomy | Open / Dual MIT/Apache | Yes (Rust code) | **Computable** 1 | **High**. Clean, native integration for the Vulkan engine's core physics and rendering loop. |
| Swiss Ephemeris (swiss-eph) | Compute Library | Astrological Math | Open / AGPL-3.0 24 | Yes (C-FFI, WASM) | **Computable** | **Low**. The AGPL licensing is a severe architectural blocker for an integrated renderer.16 |
| JPL Horizons System | API / Data Files | Astronomy | Open / Public Domain | Yes (SPK binary) 29 | **Computable** | **High**. The ultimate source of truth for all planetary vectors and epochs. |
| CDLI (cdli-gh/data) | Corpus Dump | Cuneiform Texts | Open / Academic | Yes (Bulk via git-lfs) 33 | **Attested** | **High**. Absolute requirement for reconstructing the Babylonian astronomical origins. |
| Papyri.info (idp.data) | Corpus Dump | Papyrology | Open / CC | Yes (XML/EpiDoc) 36 | **Attested** | **High**. Vital for indexing the raw data of Greco-Roman horoscopic records. |
| Pleiades Gazetteer | Dataset | Geography | Open / CC-BY 41 | Yes (JSON, CSV) | **Computable** | **High**. Required for the geographic coordinate system of historical casting. |
| McMaster AEA Database | Dataset | Egyptian Astronomy | Open / Academic | Yes (HTML Tables) 42 | **Attested** | **Moderate**. Extremely valuable data on decans, though requires custom scraping to format tabular HTML into JSON.43 |

---

## **3. The 50/50 Ankhology: Structuring the Heavens**

* The Astrological Nassau celestial renderer is explicitly designed to hold two distinct traditions in perfect equilibrium: the Andean cosmology and the Egyptological/Hellenistic heritage. This 50/50 split forms the "Ankhology," requiring equivalent research weight and architectural support. Both traditions mapped the exact same computed sky (the celestial sphere), but their structuring principles, focal points, and mathematical semantics were vastly divergent. Understanding this divergence dictates how the software must render and index the data.

---

### **3.1 The Andean Dimension: Ceques and Dark Clouds**

* Andean astronomy fundamentally differs from Western and Near Eastern models by integrating the horizon's physical topography directly into its celestial mechanics, and by prioritizing the dark rifts of the Milky Way over luminescent stellar constellations. The epistemic reality is highly challenging: the Inca had no phonetic writing system, relying instead on the *khipu* (a complex system of knotted cords) to record calendrical and statistical data.8 Consequently, the entire system is reconstructed primarily from the post-conquest transcriptions of Spanish chroniclers—most notably Bernabé Cobo, Polo de Ondegardo, and Guaman Poma de Ayala.5

  * **The *Ceque* System:** The heart of Inca astronomical, religious, and social organization was the *ceque* system of the capital city, Cusco. Originally documented in profound detail by Polo de Ondegardo in 1559 and later transcribed and expanded by Cobo, the system consists of an intricate geometry radiating outward from the Qorikancha (the central Temple of the Sun).5 Ethnohistorian Tom Zuidema and archaeologist Brian Bauer pioneered the modern reconstruction of this network, identifying it as a colossal cosmogram mapped onto the physical landscape.5 The system comprises 41 or 42 imaginary lines (*ceques*) extending outward into the four *suyus* (quarters) of the Inca empire.9 Arranged precisely along these lines were 328 *huacas* (sacred shrines, springs, rock formations, and caves).5

  * This system is inherently mathematical and calendrical, representing a massive physical computer. The 328 *huacas* map perfectly onto the lunar-stellar calendar (![][image2]), with each individual *huaca* requiring specific ritual attention on dedicated days.44 The lines also dictated exact sightlines for observing solstice and equinox events across the mountainous Cusco horizon.8

  * To render this computationally over Nassau, the engine must transpose the geometric logic of the 42 radial lines and 328 nodes onto the Bahama Banks topography. The vector geometry defining the sightlines is highly **computable**, but the religious semantics, names, and social hierarchies attached to each specific node are purely **attested** history. Databases such as the Andean Archaeological Data Project and the Rune Sim C14 Database provide crucial, geolocated coordinates for surviving archaeological sites, aligning with Bauer's exhaustive field mapping.48

  * **The Dark Cloud Constellations:** While Western astronomy plays "connect the dots" with bright stars, the Andean tradition focuses heavily on the *Yana Phuyu*—the dark, opaque clouds of interstellar dust that block the light of the Milky Way (known as *Mayu*, the celestial river).47 Anthropologist Gary Urton identified the definitive list of these dark-cloud animal constellations based on enduring indigenous ethnography: *Machacuay* (the Serpent), *Hanp'atu* (the Toad), *Yutu* (the Tinamou/Partridge), *Yacana* (the Llama), *Uñallamacha* (the Baby Llama), *Atoq* (the Fox), and *Michij* (the Shepherd).52

  * These constellations are not arbitrary; they are tied directly to terrestrial seasons and biological cycles. For example, the emergence of the *Yacana* constellation in the night sky correlates directly with terrestrial llama birthing patterns 51, and the *Machacuay* (Serpent) is prominent during the heavy rainy season.55 Furthermore, the general orientation of the Milky Way's NE-SW axis was routinely mirrored in terrestrial architecture, such as at the site of Caral.56 

  * For a rendering engine, the precise bounds of these dark clouds must be mapped using modern astrometry. Open datasets from the Gaia Data Release 2 and Hipparcos-2 star catalogs provide the 1.7 billion-star datasets required to generate the Milky Way backdrop volumetrically, allowing the dark rifts to naturally emerge in ICRF/J2000 geocentric right ascension and declination.54 The polygon mapping and identification of the constellations is **attested** (based on Urton's fieldwork), while the exact astronomical positioning of the Milky Way dust lanes is **computable**.

---

### **3.2 The Egyptological Dimension: Decans, Clocks, and Hellenistic Synthesis**

* The Egyptological half of the "Ankhology" provides the direct, mathematically rigorous ancestral lineage to Western astrology. It originated in meticulous chronometric observation of the stars and evolved into complex predictive mathematics following the Hellenistic conquest of Egypt.  

  * **The Decans and Diagonal Star Tables:** The foundational architecture of ancient Egyptian timekeeping relies entirely on the decans—a series of 36 small asterisms or individual stars that rise heliacally (emerging from the sun's glare just before dawn) every ten days. These decans seamlessly divided the ![][image3] ecliptic into ![][image4] segments.3 The earliest attestations of this system are the Diagonal Star Tables (formerly known as star clocks) found painted on the wooden lids of Middle Kingdom coffins, predominantly from the region of Asyut.3 These tables schematically trace the motion of stars to mark the specific hours of the night. The McMaster Ancient Egyptian Astronomy (AEA) database has exhaustively compiled these records, dividing the surviving artifacts into the "K-tables" and "T-tables" families, and providing structured, archetypal lists of the ancient decans (such as *knmt*, *smd*, and *srt*).42

  * **Ramesside Star Clocks:** By the era of the New Kingdom, Egyptian timekeeping evolved to utilize meridian transit observations rather than heliacal risings. The Ramesside star clocks mapped the meridian transits of 47 highly specific "hour stars".60 In a deeply localized, embodied form of astronomy, these observations were visually aligned against the physical body parts of a seated figure (acting as a human targeting reticle). For example, a star might be recorded passing over the *ı͗rt wnmy* (right eye), the *msḏr ı͗ꜣby* (left ear), or the *ḳꜥḥ wnmy* (right shoulder) to accurately measure the passage of nocturnal time.61 The mathematical calculation of these stellar transits over the meridian is **computable**, but the specific 47 stars utilized and the embodied physical measurement framework are deeply **attested** cultural artifacts.61

  * **The Dendera Zodiac:** Carved into the sandstone ceiling of the pronaos (entrance hall) of the Hathor Temple at Dendera around 50 BCE, the Dendera Zodiac marks the profound, monumental synthesis of native Egyptian astronomy with Babylonian and Hellenistic astrological systems.62 Uniquely circular rather than rectilinear (the traditional Egyptian format), it portrays the 12 familiar Greco-Mesopotamian zodiacal signs (Taurus, Libra, Scorpio) intimately intertwined with the 36 Egyptian decans and the five visible planets.62 The exact positions of the carved planets denote a specific celestial alignment that occurred between June 15 and August 15, 50 BCE, making this celestial snapshot exactly **computable** to retro-calculate in the Vulkan engine.62 However, its specific iconographic representations—such as depicting Aquarius not as a Greek youth, but as the Egyptian flood god Hapi holding water vases—is entirely **attested**.64

  * **The Hellenistic Synthesis:** The eventual convergence of the Egyptian decanal system with the advanced predictive mathematics of the Babylonian ephemerides generated the practice of Hellenistic horoscopic astrology in Alexandria. The foundational, foundational text of this tradition is attributed to the pseudonymous figures Nechepso (an Egyptian king) and Petosiris (a high priest of Thoth), composed circa 150-120 BCE.6 This massively influential manual introduced core predictive concepts that remain in use today, such as the Lot of Fortune (Klêros tês Týchēs), geometric planetary aspects, and the dodekatropos (the 12 astrological houses).6

---

## **4. The Fragmentary Corpus: Tracing the Lost Astrological Lineage**

* Because the mandate of "accuracy, not fiction" rigorously governs the project, it is critical to outline exactly where the textual authorities reside. The Hellenistic and Egyptian astrological corpus is defined by catastrophic historical losses, necessitating an almost exclusive reliance on modern critical editions of ancient fragments. If the LLM study substrate is to be honest, it must ingest these specific scholarly reconstructions rather than relying on modern new-age summaries.

1. **Nechepso and Petosiris (Lost Primary):** The *Astrologoumena*, written in a blend of Greek iambic trimeters and prose, survives exclusively as fragmentary quotations and citations embedded in the works of later classical authors, primarily Vettius Valens and the physician Galen.6  
   * *Where to find the fragments:* The fragments were first systematically collected and translated into Latin by Ernst Riess in his seminal work *Nechepsonis et Petosiridis fragmenta magica* (published in Philologus, Supplement 6, 1891–1893, pp. 325-394).6 Scanned PDFs of this collection are currently open-access.7 A secondary collection of fragments, particularly concerning the numerological divination technique known as the "Petosiris Circle," has been translated into English and is available online.66 Stephan Heilen provided modern updates and metrical analysis of the fragments in 2011.65  
2. **Dorotheus of Sidon (Reconstructed Primary):** His foundational *Carmen Astrologicum* (composed in the 1st century CE) was originally an instructional Greek poem, which is now completely lost in the original language.7  
   * *Where to find the reconstruction:* It survives entirely through an Arabic translation of a much later Persian (Pahlavi) translation. The definitive modern critical edition is David Pingree's 1976 Teubner edition (*Dorothei Sidonii Carmen Astrologicum*).7  
3. **Vettius Valens (Surviving Primary):** The 2nd-century *Anthologies* is the longest surviving practical manual of ancient astrology, famously containing over a hundred practical example charts cast by Valens himself for his students.68  
   * *Where to find the text:* The foundational Greek text is available in the Wilhelm Kroll (1908) and David Pingree (1986) scholarly editions.7 Crucially for digital indexing, a complete, machine-readable English translation by Professor Mark Riley is open-access and fully formatted in LaTeX, making it an ideal ingestion target for the RAG server.69  
4. **Firmicus Maternus & Manilius (Poetic/Prose Survival):** Firmicus Maternus's *Mathesis* and Manilius's *Astronomica* survive relatively intact in classical Latin manuscripts.  
   * *Where to find the text:* These texts are easily indexable via the Perseus Digital Library and are highly accessible via the programmatic Perseus-mcp server.21  
5. **Babylonian Texts (Clay Tablets):** The *Astronomical Diaries* and the omen series *MUL.APIN* and *Enūma Anu Enlil*.  
   * *Where to find the text:* The CDLI database provides transliterated and translated text files for these clay tablets, available via daily bulk dumps.33

---

## **5. The Computable vs. Attested Classification Map**

* This classification boundary is the non-negotiable core of the software architecture. If an element is defined as computable, the Rust/Vulkan engine calculates it live using Newtonian physics and orbital parameters. If an element is defined as attested, the engine fetches it from the local RAG corpus to provide cultural context, strictly without treating it as an absolute mathematical law.

| Celestial Element | Classification | Rationale and Epistemic Source |
| :---- | :---- | :---- |
| Planetary Positions (RA/Dec) | **Computable** | Calculated via NASA JPL DE440/441 algorithms; constantly verified against modern aerospace telemetry and lunar laser ranging.1 |
| Astrological Houses (Placidus/Porphyry) | **Computable** | Represents pure spherical trigonometry applied to geographic coordinates and local sidereal time.14 |
| Milky Way Dust Lane Positioning | **Computable** | Volumetrically derived from the Gaia DR2 and Hipparcos-2 star catalog datasets mapped in galactic and celestial coordinates.57 |
| Solstice / Equinox Sightlines | **Computable** | Arising azimuths can be mathematically deduced for any historical epoch considering the procession of the equinoxes. |
| The 36 Decan Intervals | **Computable** | **![][image4]** divisions of the ecliptic are purely mathematical partitions of a circle. |
| Inca *Ceque* Radial Geometry | **Computable** | The cartographic projection of 41/42 lines outward from a central geographical node is mathematically deterministic. |
| **--- THE EPISTEMIC BOUNDARY ---** | **------------------** | **---------------------------------------------------------------------------------------------------------** |
| *Ceque* Node Semantics (*Huacas*) | **Attested** | The religious names, tribal associations, and assigned ritual days rely entirely on the post-conquest Polo/Cobo chronicles.5 |
| Dark Cloud Constellation Bounds | **Attested** | Identifying the specific shape of the *Yacana* (Llama) or *Machacuay* (Serpent) relies strictly on Urton's indigenous ethnography.54 |
| Decanal Star Identifications | **Attested** | Identifying the specific physical star associated with an ancient Egyptian decan (e.g., matching *knmt* to a modern star) is highly debated by Egyptologists (McMaster Database).42 |
| Nechepso's Lot of Fortune Meaning | **Attested** | The interpretative and predictive meaning of the Lot relies on fragmentary transmission by Vettius Valens.6 |
| Ramesside "Body Part" Transits | **Attested** | The cultural framework of observing specific stars over the "left ear" is derived entirely from art within specific New Kingdom tombs.61 |

---

## **6. Licensing Register: The AGPL Complexity and Rust Integration**

* In developing a high-performance Rust and Vulkan rendering engine, licensing is not a tangential administrative concern; it dictates the fundamental software architecture and memory layout. The most significant legal hazard in the astronomical domain is the **Swiss Ephemeris**.

  * **Swiss Ephemeris (swisseph)**: This C library is dual-licensed under the GNU Affero General Public License version 3 (AGPL-3.0) and a commercial license.17 The AGPL is a highly viral, copyleft license specifically designed to close the "Application Service Provider loophole" for network services. If the Astrological Nassau Rust engine statically or dynamically links against the Swiss Ephemeris (via wrapper crates like libswisseph-sys or swiss-eph), the *entire* renderer application—including proprietary Vulkan shaders and game logic—must be open-sourced under the AGPL.16 The only exemption is purchasing an unrestricted commercial license from Astrodienst AG for a flat fee of 700 CHF.17

  * **The Architectural Mitigation**: To maintain a proprietary or permissively licensed codebase, the engine must completely bypass the Swiss Ephemeris within the compiled Rust client. Instead, it must utilize the **rust-jpl** crate.27 This library reads the binary NASA JPL SPK files natively. It relies on standard, permissive open-source licenses (MIT/Apache), entirely avoiding the AGPL contamination while maintaining NASA-grade scientific accuracy.1

  * **Corpus Licensing (CC vs. Academic)**: The study substrate's data sources are highly permissive. The Pleiades Gazetteer is licensed under Creative Commons Attribution (CC-BY), allowing free use, modification, and adaptation.41 Papyri.info's raw text data is similarly open.36 The historical Nechepso fragments (compiled by Riess in 1891) and Kroll's 1908 Valens edition have lapsed into the public domain.7

  * **Self-Hosted Security Architectures**: Emerging tools within the MCP ecosystem, such as licensify and Ephemera, demonstrate that modern AI-driven architectures heavily favor self-hosted, air-gapped data execution.72 Deploying MCP servers locally completely circumvents API telemetry harvesting, protecting both API budgets and intellectual property.

---

## **7. Recommended Minimal Stack and Action Plan**

*To fulfill the rigorous requirements of the Astrological Nassau renderer—achieving sub-arcsecond astronomical precision while maintaining a deep, machine-readable repository of the 50/50 Andean/Egyptological heritage—the following minimal architecture stack is recommended:* 

* **1. The Compute Core (In-Engine): rust-jpl** Bypass the AGPL-tainted Swiss Ephemeris entirely. Implement the rust-jpl crate directly into the Vulkan engine's physics loop.1 Download the SPK binary kernels (DE440/441) directly from the JPL Horizons system.29 This architecture handles all continuous, real-time positional logic (planets, moon, sidereal time) seamlessly within the native application, ensuring maximum framerates without network latency.
  
  * **2. The Advanced Astrology Compute Node: openephemeris-MCP** For complex, discontinuous astrological calculations that do not need to be computed sixty times a second (e.g., generating a full traditional natal chart, calculating composite midpoints, or scanning for electional timing windows), spin up the openephemeris-MCP server locally via stdio.13 Because it runs out-of-process via the Model Context Protocol, it acts as an isolated microservice. It passes high-level astrological geometry back to the engine via JSON, without bloating the Vulkan core or introducing architectural dependencies.

  * **3. The Primary Text Fetcher: Perseus-mcp** Run the tonyjurg/Perseus-mcp FastMCP server locally to grant the LLM study substrate direct, structured access to the Perseus Digital Library.21 This provides the AI agent with immediate capability to cross-reference classical astrological poetry (Manilius) and prose (Ptolemy) via precise CTS URNs, ensuring that questions about Hellenistic house systems are answered with primary citations rather than generic summaries.21

  * **4. The Offline "Attested" Substrate: mcp-local-rag** Deploy shinpr/mcp-local-rag as the proprietary knowledge base.22 Utilizing its ONNX semantic chunking and Vision-Language Model (VLM) capabilities, this server represents the ultimate repository for the "attested" layer, capable of reading both translated texts and visual archaeological diagrams.

---

### **Immediate Action Plan ("What We'd Do First")**

* 1. **Establish the Ephemeris Baseline:** Fork and configure the rust-jpl crate. Ingest the DE441 SPK binary file. Write a rigorous unit test that verifies the engine's calculation of the sun's position on June 15, 50 BCE against the official JPL Horizons web interface to guarantee the baseline arithmetic is sound before any graphics are rendered.1

  * 2. **Construct the Attested Ingestion Pipeline:** Spin up the mcp-local-rag server locally. Download the Ernst Riess PDF containing the Nechepso-Petosiris fragments 7 and the Mark Riley LaTeX translation of Vettius Valens.70 Feed them into the RAG engine to generate the initial local ONNX embeddings.22

  * 3. **Map the Andean Horizon:** Extract the CSV latitude and longitude coordinates of the existing Inca *huacas* from the Andean Archaeological Data Project.48 Write a Python script to procedurally cast the 41/42 lines of the *ceque* system from a central defined point in the Nassau terrain map, creating the physical wireframe of the Andean geometry for the Vulkan engine to render.46

  * 4. **Ingest the Egyptian Decans:** Programmatically scrape the T-tables and K-tables HTML data from the McMaster Ancient Egyptian Astronomy database.59 Format these archetypal decan lists into clean, machine-readable JSON to serve as structured metadata inside the RAG database, allowing the engine to associate visual rendering of stars with their attested Egyptian nomenclature.42

---

#### **Referanser**

* 1. GitHub - CHINMAYVIVEK/rust-jpl: The Rust JPL Ephemeris Reader is a Rust project designed to read NASA JPL ephemeris data and provide planetary positions based on a given Julian date., brukt juni 15, 2026, [https://github.com/CHINMAYVIVEK/rust-jpl](https://github.com/CHINMAYVIVEK/rust-jpl)

  * 2. libephemeris - PyPI, brukt juni 15, 2026, [https://pypi.org/project/libephemeris/0.7.0/](https://pypi.org/project/libephemeris/0.7.0/)

  * 3. Decan - Wikipedia, brukt juni 15, 2026, [https://en.wikipedia.org/wiki/Decan](https://en.wikipedia.org/wiki/Decan)

  * 4. Nechepso and Petosiris: The Lost Founders of Western Astrology | Wilfred Hazelwood Clinic, brukt juni 15, 2026, [https://www.wilfredhazelwood.com/nechepso-and-petosiris-the-lost-founders-of-western-astrology](https://www.wilfredhazelwood.com/nechepso-and-petosiris-the-lost-founders-of-western-astrology)

  * 5. The sacred landscape of the Inca: the Cusco ceque system - eHRAF Archaeology, brukt juni 15, 2026, [https://ehrafarchaeology.yale.edu/document?id=se80-014](https://ehrafarchaeology.yale.edu/document?id=se80-014)

  * 6. Nechepso - Brill Reference Works, brukt juni 15, 2026, [https://referenceworks.brill.com/display/entries/NPOE/e818880.xml](https://referenceworks.brill.com/display/entries/NPOE/e818880.xml)

  * 7. Hellenistic Astrology Website - AWOL - The Ancient World Online, brukt juni 15, 2026, [http://ancientworldonline.blogspot.com/2010/12/open-access-hellenistic-astrological.html](http://ancientworldonline.blogspot.com/2010/12/open-access-hellenistic-astrological.html)

  * 8. On the astronomical content of the sacred landscape of Cusco in Inka times. - arXiv, brukt juni 15, 2026, [https://arxiv.org/pdf/physics/0408037](https://arxiv.org/pdf/physics/0408037)

  * 9. Bauer - 2016 (The Ceque System) | PDF | Inca Empire | Peru - Scribd, brukt juni 15, 2026, [https://www.scribd.com/document/602356228/Bauer-2016-The-ceque-system](https://www.scribd.com/document/602356228/Bauer-2016-The-ceque-system)

  * 10. punkpeye/awesome-mcp-servers - GitHub, brukt juni 15, 2026, [https://github.com/punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)

  * 11. What is the Model Context Protocol (MCP)? - Model Context Protocol, brukt juni 15, 2026, [https://modelcontextprotocol.io/docs/getting-started/intro](https://modelcontextprotocol.io/docs/getting-started/intro)

  * 12. Introducing the Model Context Protocol - Anthropic, brukt juni 15, 2026, [https://www.anthropic.com/news/model-context-protocol](https://www.anthropic.com/news/model-context-protocol)

  * 13. GitHub - Spirit-River/openephemeris-MCP: MCP server and API ..., brukt juni 15, 2026, [https://github.com/Spirit-River/openephemeris-MCP](https://github.com/Spirit-River/openephemeris-MCP)

  * 14. GitHub - ducrouxolivier/swiss-ephemeris-mcp-server: Swiss ..., brukt juni 15, 2026, [https://github.com/dm0lz/swiss-ephemeris-mcp-server](https://github.com/dm0lz/swiss-ephemeris-mcp-server)

  * 15. Swiss Ephemeris MCP Server - LobeHub, brukt juni 15, 2026, [https://lobehub.com/mcp/dm0lz-swiss-ephemeris-mcp-server](https://lobehub.com/mcp/dm0lz-swiss-ephemeris-mcp-server)

  * 16. Swiss Ephemeris Explained for Developers: The Engine Behind Astrology Software, brukt juni 15, 2026, [https://roxyapi.com/blogs/swiss-ephemeris-explained-developers](https://roxyapi.com/blogs/swiss-ephemeris-explained-developers)

  * 17. Swiss Ephemeris price list and order - Astrodienst, brukt juni 15, 2026, [https://www.astro.com/swisseph/swephprice_e.htm](https://www.astro.com/swisseph/swephprice_e.htm)  

  * 18. W8s Astro Mcp | MCP Servers, brukt juni 15, 2026, [https://claudemarketplaces.com/mcp/w8s/w8s-astro-mcp](https://claudemarketplaces.com/mcp/w8s/w8s-astro-mcp)  

  * 19. NASA MCP Server - Comprehensive access to NASA's open APIs including APOD, Mars rovers, asteroids, and Earth imagery - GitHub, brukt juni 15, 2026, [https://github.com/jezweb/nasa-mcp-server](https://github.com/jezweb/nasa-mcp-server)  

  * 20. A Model Context Protocol (MCP) server for NASA APIs, providing a standardized interface for AI models to interact with NASA's vast array of data sources. - GitHub, brukt juni 15, 2026, [https://github.com/ProgramComputer/NASA-MCP-server](https://github.com/ProgramComputer/NASA-MCP-server)  

  * 21. MCP server for the Perseus Digital Library — giving AI models direct access to ancient Greek texts, CTS passages, and Scaife search. - GitHub, brukt juni 15, 2026, [https://github.com/tonyjurg/Perseus-mcp](https://github.com/tonyjurg/Perseus-mcp)  

  * 22. shinpr/mcp-local-rag: Local-first RAG server for developers ... - GitHub, brukt juni 15, 2026, [https://github.com/shinpr/mcp-local-rag](https://github.com/shinpr/mcp-local-rag)

  * 23. iamjr15/astrology-mcp-puchai - GitHub, brukt juni 15, 2026, [https://github.com/iamjr15/astrology-mcp-puchai](https://github.com/iamjr15/astrology-mcp-puchai)

  * 24. swiss_eph - Rust - Docs.rs, brukt juni 15, 2026, [https://docs.rs/swiss-eph](https://docs.rs/swiss-eph)

  * 25. fusionstrings/swiss-eph - GitHub, brukt juni 15, 2026, [https://github.com/fusionstrings/swiss-eph](https://github.com/fusionstrings/swiss-eph)

  * 26. libswisseph-sys — system library interface for Rust // Lib.rs, brukt juni 15, 2026, [https://lib.rs/crates/libswisseph-sys](https://lib.rs/crates/libswisseph-sys)

  * 27. rust-jpl - crates.io: Rust Package Registry, brukt juni 15, 2026, [https://crates.io/crates/rust-jpl](https://crates.io/crates/rust-jpl)  
  * 28. rust_jpl - Rust - Docs.rs, brukt juni 15, 2026, [https://docs.rs/rust-jpl](https://docs.rs/rust-jpl)

  * 29. Download Ephemerides - JPL Solar System Dynamics, brukt juni 15, 2026, [https://ssd.jpl.nasa.gov/ephem.html](https://ssd.jpl.nasa.gov/ephem.html)

  * 30. Cuneiform Digital Library Initiative (CDLI) | Faculty of Asian and Middle Eastern Studies, brukt juni 15, 2026, [https://www.ames.ox.ac.uk/cuneiform-digital-library-initiative-cdli](https://www.ames.ox.ac.uk/cuneiform-digital-library-initiative-cdli)

  * 31. Cuneiform Digital Library Initiative: A free database of all cuneiform texts - Lund University, brukt juni 15, 2026, [https://portal.research.lu.se/en/activities/cuneiform-digital-library-initiative-a-free-database-of-all-cunei-2/](https://portal.research.lu.se/en/activities/cuneiform-digital-library-initiative-a-free-database-of-all-cunei-2/)

  * 32. The Cuneiform Digital Library Initiative: A Primer, brukt juni 15, 2026, [https://iaassyriology.com/the-cuneiform-digital-library-initiative-a-primer/](https://iaassyriology.com/the-cuneiform-digital-library-initiative-a-primer/)

  * 33. GitHub - cdli-gh/data: This is a copy of the daily dump of catalogue and ATF data from the Cuneiform Digital Library Initiative (http://cdli.ucla.edu), brukt juni 15, 2026, [https://github.com/cdli-gh/data](https://github.com/cdli-gh/data)
  
  * 34. Papyri.info, brukt juni 15, 2026, [https://papyri.info/](https://papyri.info/)  

  * 35. Duke Databank of Documentary Papyri (DDbDP), brukt juni 15, 2026, [https://papyri.info/docs/ddbdp](https://papyri.info/docs/ddbdp)  

  * 36. papyri/idp.data: Data from the Integrating Digital Papyrology project - GitHub, brukt juni 15, 2026, [https://github.com/papyri/idp.data](https://github.com/papyri/idp.data)  

  * 37. papyri.info - GitHub, brukt juni 15, 2026, [https://github.com/papyri](https://github.com/papyri)  

  * 38. Pleiades Datasets - NYU Faculty Digital Archive, brukt juni 15, 2026, [https://archive.nyu.edu/handle/2451/34305](https://archive.nyu.edu/handle/2451/34305)  

  * 39. Pleiades gazetteer: "Export Updates 2026-02-03: Ple…" - hcommons.social, brukt juni 15, 2026, [https://hcommons.social/@pleiades_gazetteer/116006927573254188](https://hcommons.social/@pleiades_gazetteer/116006927573254188)  
  
  * 40. isawnyu/pleiades.datasets: Platform-independent versions of Pleiades gazetteer data - GitHub, brukt juni 15, 2026, [https://github.com/isawnyu/pleiades.datasets](https://github.com/isawnyu/pleiades.datasets)

  * 46. The Cusco ceque system as shown in the Exsul immeritus Blas Valera populo suo, brukt juni 15, 2026, [https://www.researchgate.net/publication/301938350_The_Cusco_ceque_system_as_shown_in_the_Exsul_immeritus_Blas_Valera_populo_suo](https://www.researchgate.net/publication/301938350_The_Cusco_ceque_system_as_shown_in_the_Exsul_immeritus_Blas_Valera_populo_suo)  
  
  * 47. Astronomy in Cusco: Inca Sky, Milky Way, and Stargazing Guide - Uros Expeditions, brukt juni 15, 2026, [https://www.urosexpeditions.com/blog/astronomy-in-cusco](https://www.urosexpeditions.com/blog/astronomy-in-cusco)  

  * 48. Images | Andean Archaeological Data Project | University of South Florida, brukt juni 15, 2026, [https://digitalcommons.usf.edu/andean_adp/index.11.html](https://digitalcommons.usf.edu/andean_adp/index.11.html)

  * 49. Databases - CEAcusco, brukt juni 15, 2026, [https://ceacusco.com/en/95-2/bases-de-datos/](https://ceacusco.com/en/95-2/bases-de-datos/)

  * 50. Inca Huacas and Cosmology Insights | PDF | Inca Empire | Machu Picchu - Scribd, brukt juni 15, 2026, [https://www.scribd.com/document/266930358/the-Cosmology-of-Inca-Huacas-Apendice-y-Bibliografia](https://www.scribd.com/document/266930358/the-Cosmology-of-Inca-Huacas-Apendice-y-Bibliografia)

  * 51. The Constellations - International Astronomical Union | IAU, brukt juni 15, 2026, [https://iauarchive.eso.org/public/themes/constellations/](https://iauarchive.eso.org/public/themes/constellations/)

  * 52. Inca Astronomy: Dark constellations in the sky - Salkantay Trekking, brukt juni 15, 2026, [https://www.salkantaytrekking.com/blog/inca-astronomy-dark-constellations-sky/](https://www.salkantaytrekking.com/blog/inca-astronomy-dark-constellations-sky/)

  * 53. The Constellations - International Astronomical Union (IAU), brukt juni 15, 2026, [https://www.iau.org/IAU/Iau/Science/What-we-do/The-Constellations.aspx](https://www.iau.org/IAU/Iau/Science/What-we-do/The-Constellations.aspx)

  * 54. (left) Seven Inca dark constellations identified according to Garry... | Download Scientific Diagram - ResearchGate, brukt juni 15, 2026, [https://www.researchgate.net/figure/left-Seven-Inca-dark-constellations-identified-according-to-Garry-Urtons-publication_fig1_375462192](https://www.researchgate.net/figure/left-Seven-Inca-dark-constellations-identified-according-to-Garry-Urtons-publication_fig1_375462192)

  * 55. The dark cloud constellations identified by Urton (Source: Urton 1982) - ResearchGate, brukt juni 15, 2026, [https://www.researchgate.net/figure/The-dark-cloud-constellations-identified-by-Urton-Source-Urton-1982_fig3_225158055](https://www.researchgate.net/figure/The-dark-cloud-constellations-identified-by-Urton-Source-Urton-1982_fig3_225158055)

  * 56. Andean Cosmology and the Ceque System | PDF | Inca Empire | Milky Way - Scribd, brukt juni 15, 2026, [https://www.scribd.com/document/679576659/Andean-Cosmos](https://www.scribd.com/document/679576659/Andean-Cosmos)

  * 57. Deep Star Maps 2020 - NASA SVS, brukt juni 15, 2026, [https://svs.gsfc.nasa.gov/4851/](https://svs.gsfc.nasa.gov/4851/)

  * 58. In Search of Lost Time - ArcGIS StoryMaps, brukt juni 15, 2026, [https://storymaps.arcgis.com/stories/eea3fbc9c05b40948563ffd0ccfab59d](https://storymaps.arcgis.com/stories/eea3fbc9c05b40948563ffd0ccfab59d)

  * 59. Database - Ancient Egyptian Astronomy, brukt juni 15, 2026, [https://aea.mcmaster.ca/index.php/en/database](https://aea.mcmaster.ca/index.php/en/database)

  * 60. Ancient Egyptian astronomy: timekeeping and cosmography in the new kingdom, brukt juni 15, 2026, [https://figshare.le.ac.uk/articles/thesis/Ancient_Egyptian_astronomy_timekeeping_and_cosmography_in_the_new_kingdom/10097984](https://figshare.le.ac.uk/articles/thesis/Ancient_Egyptian_astronomy_timekeeping_and_cosmography_in_the_new_kingdom/10097984)

  * 61. Chapter 1 Sun and Stars: Astronomical Timekeeping in Ancient Egypt in - Brill, brukt juni 15, 2026, [https://brill.com/display/book/edcoll/9789004416291/BP000010.xml?language=en](https://brill.com/display/book/edcoll/9789004416291/BP000010.xml?language=en)

  * 62. Dendera Zodiac - Greco-Roman Period Monuments - Rosicrucian Egyptian Museum, brukt juni 15, 2026, [https://egyptianmuseum.org/explore/greco-and-roman-period-monuments-dendera-zodiac](https://egyptianmuseum.org/explore/greco-and-roman-period-monuments-dendera-zodiac)

  * 63. The Dendera Zodiac - Egypt Museum, brukt juni 15, 2026, [https://egypt-museum.com/the-dendera-zodiac/](https://egypt-museum.com/the-dendera-zodiac/)

  * 64. Dendera zodiac - Wikipedia, brukt juni 15, 2026, [https://en.wikipedia.org/wiki/Dendera_zodiac](https://en.wikipedia.org/wiki/Dendera_zodiac)

  * 65. some metrical fragments from nechepsos and petosiris - Stud.IP, brukt juni 15, 2026, [https://studip.uni-osnabrueck.de/sendfile.php?type=0&file_id=b028493e15bfc88fcf31a1f4a518c670&file_name=Heilen+2011+Some+metrical+fragments+excerpt+Conclusions.pdf](https://studip.uni-osnabrueck.de/sendfile.php?type=0&file_id=b028493e15bfc88fcf31a1f4a518c670&file_name=Heilen+2011+Some+metrical+fragments+excerpt+Conclusions.pdf)

  * 66. THE LATIN TRADITION OF THE EPISTOLA PETOSIRIDIS The epistle of Petosiris to Nechepso describes a method of divina tion which c - Brepols Online, brukt juni 15, 2026, [https://www.brepolsonline.net/doi/pdf/10.1484/J.MSS.3.1031](https://www.brepolsonline.net/doi/pdf/10.1484/J.MSS.3.1031)

  * 67. Petosiris to Nechepso: links to translation - Attalus.org, brukt juni 15, 2026, [https://www.attalus.org/info/petosiris.html](https://www.attalus.org/info/petosiris.html)

  * 68. The Anthology - Valens, Vettius: 9780998588919 - AbeBooks, brukt juni 15, 2026, [https://www.abebooks.com/9780998588919/Anthology-Valens-Vettius-0998588911/plp](https://www.abebooks.com/9780998588919/Anthology-Valens-Vettius-0998588911/plp)

  * 69. The Anthology book by Vettius Valens - ThriftBooks, brukt juni 15, 2026, [https://www.thriftbooks.com/w/anthology/37543597/](https://www.thriftbooks.com/w/anthology/37543597/)

  * 70. Vettius Valens Anthologies, translated by Mark T. Riley - GitHub, brukt juni 15, 2026, [https://raw.githubusercontent.com/janegca/latex-valens/main/Valens-Anthologies-Annotated.pdf](https://raw.githubusercontent.com/janegca/latex-valens/main/Valens-Anthologies-Annotated.pdf)

  * 71. Cuneiform Digital Library Initiative: Home, brukt juni 15, 2026, [https://cdli.earth/](https://cdli.earth/)

  * 72. melihbirim/licensify: Self-hosted licensing + API key protection for AI-powered applications. - GitHub, brukt juni 15, 2026, [https://github.com/melihbirim/licensify](https://github.com/melihbirim/licensify)

  * 73. Ephemera: Self-hosted, air-gapped SSH CA with JIT access and no cloud dependencies, brukt juni 15, 2026, [https://www.reddit.com/r/selfhosted/comments/1pp7sat/ephemera_selfhosted_airgapped_ssh_ca_with_jit/](https://www.reddit.com/r/selfhosted/comments/1pp7sat/ephemera_selfhosted_airgapped_ssh_ca_with_jit/)

---

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEcAAAAaCAYAAADloEE2AAAEwUlEQVR4AeyYWchWRRjHTyvtC+071UUrFNFy0UZUVEQEFRRFdBMVXRQULRRFBO6ioKjojaCoiCsqiHohKoKi4oYLLrhvuO/78vsd3vl8v3nnnPegt+fj+Z/nmWdmnnfmP8+ZmfNdmdV/hQzU5BRSk2U1OTU5JQyUVBVlzg30GQFOgfNNmIl9B1Cu5/ElGAL6gXfAVSCWW3D8DGz3D/o+EMsVOF4BxhmI/hBcaiy6JuUJvD2B43Dcjp9isRSRc4wuX4FrQVcgQe+i3wJ7wa1A8m5E9wD6pqGnAOtQuTzCcw4w3k/ohWAWeBkEkZjfKDjwvmgJdPCDsK8BQarECm1j/SmOCWAk+AU8BSaB5rFS7CxF5IRWN2G8CjaDVSDI1xhHwGiwHvwPJPF99A9AuZqHE12LHgpOgKlgDLB9WLkXKP8K/gYbgETb7z3st4FSNZZtYzyEozvoApYAx90HfRtwHqi0tCPnbrqZjivQDhqVy0s8DfwtWjGzXInjFMwwM+phbF+PBegzIMgijNfB00D5hIfESTJmLrt5uiCfo82sqrFo3iJv4LkfrAZBDmCsAZ8BEwDVKu3IkZh76TYbOAFULqboSqzlIMg5DElylZ3QY5TvAbGcxuGe9iT6OvA8iMU4Z3E+C1zhKrFomhT3srjC+C6Y8zMB4vq83I6c12hlIFcbs0MmYj0DZoAgTtZJ29bU9bWRpFAf6wdxSKRZhpkUBy6BVWIlA+As21c8LG6nTVLKyHHQsm56N+83qUAO4Hsq3F88cTCz8NpoF+FmKh4F7aRKrFQMXxk38lRdW18ZOb4SZke838RBzQ6J8b3+mMpNQPH1UZfBV9H0LmtjXZVYtoth1leJH/fLy2Xk+L6n9pu8Y9PDDfUjyt5zmjPMLMJdKkep3QLaSZVYqRjG35aqqOIL5Hif8OxXh36+UjLvHhJ8sfb+4Illxmyk0jT2fuQ+sZ9y2ao5YTf5PbQrEl9p968qsYpibC2qwG/cXeikSI6b4jBqPX08njEzJ5m631gX4EXOrPkCxz6geKfQf5KCdxZX7QHsLLv48PWzvVkmeR71/p6nUmgluXdRWAwOgyqxaJaL20G4xeuYz8N4zRuv5TvxLwWFiyM5brxuit4zHCjtMy9gktOfghNEdRKzzNumdxqPc1dYzKWVK23GbcceDiTLDRszMzO92E2nYOagsnE8vB89hw5ifMkZ1XBUjeXRvIw+Tto5YWaOyez35LUsPCn9Pcdn9uprgeQcwjseuEpO4l9svz/+QoeTB7OT/EnpceAEzJYAV8cMpCqToN4YZonxPsAeDMwcPxfMGorZOh5+WnRDfwe+Abb7Dz0PKFVjucfspIMXPn8XM/Py+iOGcX9He/GTdD9/XBhcaZEcf7gX1V7f3YAdkJcufUWnhD/kKZWCP0q4XA7ydLP2u8kMHUD5TRDvAy7Oi/h3ACflDdoPUMeGK5cqsYxrRng42D7vyMNvOg8YPx9cFLeDP/AXzY+qrOP/OQ7C6/RYvKZ8c2BclyXedE1rY6stpwK6wpOpENqYLWJfY7SL1dIRh1nl3LzAVjkhO8ihby0xA75Wsa8uNxioyWkQkVI1OSlWGr6anAYRKVWTk2Kl4avJaRCRUhcAAAD//9Y3NjsAAAAGSURBVAMAnWgFRLNKuUMAAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,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>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACcAAAAZCAYAAACy0zfoAAADMUlEQVR4AeyVWaiOQRjHx5qlLCFLtiRbtjt7cosLWUqyRbKUvWxZIgoXLoQLhCS7SKG4IETILrKVpWzZ9+y/39eZ4/3OOZ3v63QS+r7+v3meeWa+eZ935p2ZsuEv/uWSK+ni/DMzV403nAxrYSG0gDJQlFoSXA72HYAtB0lVpjIEbLef/anmy/bp1A7CfPDZmHTFmetAeD9chpnwCK7BNEgmWIH6XNgCO2ApjIQxEFUdx7FaY/3/Vuxe8CUwwfHG4tinN3YVTAQTxvxWTG40oR7gG7zC7gQTnYNtBVH2G0FlEJwHZ6QvtgtEjcOpASvgPVyCJbAY6kItqAK3Qb2keAJNIU0xua9E9etg1TeKz+BMVcSqRhQuxSHsPVCnKObBGlA1KQbCdfAlMSndovT/nbCO6/iOTTU1kz7DJK3nY0JWZlGY2CasakLRFi7AXVDdKJrDGagE9eE7OCPGcEM9imZQUD8IuJwm52yepu7/fMYM/AfwFNIUk3PmntPiw1za2fjvYAo4GCZ0tQCXeR22P5yEZRBnweUycUJFqmFe9AR2AbyA1XAACikmZ0NViu3gRuiM9SO/io3yQ9f32xyP46B+e8PxJ4FqQGGCmIxyeR/TK748brqSyX2gaTA0hj6wEVxmk8bN1za8OKCD36Q+CmqD3xKmdJRMLjmiDzxKYCgMA+XSaz1mtEncaX6nzwh+hFKRyfm9TGU00ccNPymugIrHhDvQenG4Q98W08GXLqY5vcnk2hNy54g+1ZTapMoQ3uRZd9gXfDcMJk0eLfeJOHMm4BInN4ZHjC9+lj5Zy+Qc0KXaxb/ugPKg9IR/TcVvDxM8TA+HEHpBeVAeJx7EG6i42/0W1+O3A9swwSOkJ47H0jls1jK5h/R2t3XHeiO4KTbj+1Dvx4v46hOFZ5JHinemt8UeYvtgJUR5rXk0mHA/govAY8ebI64CocwyOXt56nsgat1xnl0ujXXbIzdwvIfdxT7I22ACsbhZcIO+Me9PZ/gIwY7gzGOyV0zOf3juHMPZDcfBh2AKybjt9vNacvMU7GTMNvvY1/8U7JOxnkwuY+c/3SGXXElnPDdz/+XM/QIAAP//RsSfvgAAAAZJREFUAwAh8p8zUaXzSAAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABkAAAAWCAYAAAA1vze2AAABtklEQVR4AeyUTShEURTHh1GIfJQs5GN2Uj4WFjayslFWKFKysLOUkGyVLGRjYyusZJKVZGehKB8LUpJ8pYhiohC//9SpydzpvTcLC5n+v3vOvefee+add9/NDP3C7z9JoCK7yhVhhx5IpWoC0zAPvZALidL6OQbWoRPClqSGziBswRm0gUtatEpgCYZA69awhSCV0ugPDmPb4Ra6LQl+6IZmAhTAJKmCkSmYhH14gRkogj6Q6mkUe8VKhzQRS3JMJwrn8AkutTBYBidgesI5hS7Ih0fIA1M2TsyS4HuqyTHji7EP0HtSqQ7w9cQD2EYYg2iQJFZ31iWpgJFiUMJZ7ApcwThc+E2iUlSxwK9Uxjsmv0PIbxIri9YExm+SGDtfQ1rym0Sbq8ayLnSqVB5XzHe5tHiHJgf0gjFxqV+Cp1N1j3Uq1ZNkMTsDErVNZw+awVSO0wAL8AZOWZJWoiqHqMTXnfSM1Rdbh5UeaHT19GNHQB/gMnYRdGQxblmSTcL6V2GsnkDo2OqaOGLMtItTC7o69E104I9C/KhinbIkzmCKQZ20DWK6hi6xnkonieemPyf8nSTfAAAA//9QuJu2AAAABklEQVQDAD2bSi0KLOf5AAAAAElFTkSuQmCC>

---
