# Architecting-Visceral-A-Transdisciplinary-Analysis- Technical-Substrates-Aesthetic-Decay-And-Narrative-Systems-For-Macro-Scale-Worldbuilding

> ⚠️ **SSOT-TOOLBOX-FILE-READ-ONLY-RESEARCH-POOL**
> This file is source reference for `Zone_1_REDUX` integrations into `copilot-instructions.md`.
> After ANY `SSOT`, `edit`, `run`: `.\ssot_outline_extractor.ps1 -UpdateIndex`
> See: `.github/instructions/ssot-toolbox.instructions.md` for full toolbox documentation.

## **1. Introduction: The Convergence of Infrastructure and Imaginary**

The endeavor to stabilize and enhance a "macro-prompt-world"—specifically one characterized by "private no-policy nonsense," "NSFW18+++extreme" aesthetics, and a reliance on modern generative automation—requires a rigorous, transdisciplinary architectural approach. This report provides an exhaustive analysis of the foundational elements required to transmute such a chaotic collection of prompts into a cohesive, functioning system. By synthesizing disparate fields—software engineering (specifically the interoperability of modern JavaScript runtimes like Bun with browser automation tools), critical aesthetic theory (focusing on Biopunk, Industrial Maximalism, and the Sociology of Decay), evolutionary psychology (supernormal stimuli in character design), and information architecture (Single Source of Truth methodologies)—we can establish a robust framework for this "world."

The objective is to move beyond disparate, fragile "prompts" into a cohesive, functioning system. This requires addressing the fragility of the technical stack (specifically Windows IPC issues with Bun and Playwright), refining the sensory language of the world (moving beyond generic "slime" to nuanced olfactory and tactile descriptors like "chitinous" and "petrichor"), and establishing a philosophical backbone that embraces, rather than denies, the processes of decay and transformation symbolized by alchemical traditions. The "nonsense" of the prompt is treated here not as gibberish, but as the *Prima Materia*—the chaotic, undifferentiated base matter that, through the alchemical operations of *Nigredo* (blackening/decomposition) and *Albedo* (whitening/purification), can be refined into a sophisticated narrative engine.

## 2.-Technical-Substrate-Runtime-Interoperability-IPC-Architectures

The stability of any digital "world"—whether a simulation, a testing environment, or a generative narrative engine—relies on the robustness of its underlying runtime environment. The current landscape reveals a critical friction point between the emergent, high-performance runtime **Bun** and established automation frameworks, particularly within the **Microsoft Windows** ecosystem. This section analyzes the mechanical failures of this stack and proposes architectural remediation to ensure the "macro-world" can operate without interruption.

### 2.1. The Bun-Web-View

> **⚡ (Bun v1.3.12):** This paradox resolved. `Bun.WebView` shipping natively in Bun v1.3.12, launching Chrome/Chromium via DevTools Protocol **internally** — chthonic-archive gating pipeline (`scripts/hf_gate_playwright.ts`) was rewritten to `Bun.WebView` at commit `efdce1e4`. Key API: `await using view = new Bun.WebView({ backend: "chrome" })` — cookie injection via `view.cdp("Network.setCookie", {...})`, button detection via `view.evaluate(...)` or `view.click(selector)` (CSS selector, auto-waits for actionability). The historical analysis below is preserved as provenance of the problem that drove the Bun.WebView feature.

Bun, designed as a drop-in replacement for Node.js, boasts significant performance improvements in startup time and memory usage due to its JavaScriptCore engine (written in Zig) rather than the V8 engine used by Node.1 However, the integration with Playwright—a premier browser automation tool utilized for rendering and testing the "macro-world's" interfaces—is fraught with instability on Windows platforms.


#### 2.1.1.-The-Child-Process-Divergence-Zombie-Processes

Bun's implementation of `child_process` aims for compatibility but differs in execution. While Bun's `spawn` is benchmarked as significantly faster (up to 60% faster than others in some contexts), the mature edge-case handling for Windows-specific signal passing and stream buffering that the V8-based runtime has refined over a decade.

* **Signal-Handling:** Windows does not support POSIX signals (like SIGTERM or SIGKILL) in the same way Linux does; it relies on TerminateProcess APIs. Node shims this behavior to allow developers to "kill" child processes gracefully. Bun's implementation has shown inconsistencies in propagating these termination signals to child processes on Windows.16 This leads to the "Zombie Process" phenomenon: when the main automation script crashes or is halted, the spawned chrome.exe instances remain running in the background. These "headless" zombies consume system resources (RAM, CPU) and lock files (like user data directories), preventing subsequent runs of the automation script from succeeding due to file access errors.

* **Stream-Encoding:** Differences in how standard output (stdout) and standard error (stderr) streams are buffered can cause the Playwright driver to miss critical startup messages from the browser. If the browser writes its WebSocket debugging URL to stderr but the buffer is not flushed immediately or is encoded differently, the control script waits forever for a "ready" signal that was already sent.17

### **2.2.-Remediation Strategies-Architectural-Workarounds**

To improve the stability of the "macro-prompt-world's" technical backend, specific architectural shifts are necessary. We cannot rely on a "pure Bun" stack on Windows for browser automation at this time.

#### 2.2.1.-The-"Hybrid-Runtime"-Approach

The most immediate and stable solution is to decouple the *orchestration* logic from the *execution* logic. While Bun can be used for high-performance HTTP servers, API aggregation, or utility scripts due to its speed, the specific task of browser automation on Windows should arguably remain delegated to Node.js until Bun's Windows IPC stabilizes.

* **Implementation:** Use Bun as the package manager and task runner (via bun run), but explicitly invoke node for the Playwright scripts. This avoids the IPC mismatch while retaining Bun's speed for dependency installation and script dispatching.3  

* **Configuration:** In the package.json, scripts should be defined to force the Node runtime: "test:e2e": "node tests/playwright\_suite.js". This ensures that the heavy lifting of browser communication uses the mature libuv implementation of named pipes.12

#### 2.2.2.-Model-Context-Protocol-(MCP)-Integration

A more forward-looking improvement involves abstracting the browser interface entirely using the **Model-Context-Protocol-(MCP)**. MCP servers act as standardized gateways that expose local resources (like a browser) to AI models or other clients.19

* **The-Playwright-MCP Server:** By running an MCP server (potentially in a Docker container to bypass Windows IPC issues entirely, or using a server implementation), the system creates a robust API layer. The control logic sends high-level intents (e.g., "navigate to X," "extract Y") to the MCP server via JSON-RPC over standard HTTP or TCP, bypassing the fragile direct IPC pipes.21  

* **Stealth-Persistence:** Advanced MCP implementations, such as the "Stealth Browser MCP," integrate puppeteer-extra-plugin-stealth logic to evade bot detection. This allows the automation layer to operate undetectable, a crucial feature for data scraping or interacting with modern, sophisticated web applications that might flag standard Playwright traffic.

#### *2.2.3.-VS-Code Extension-Debugging

For development within this environment, the "Bun for Visual Studio Code" extension provides a necessary bridge. However, debugging implies its own set of IPC challenges. The extension communicates with the Bun runtime via the **WebKit Inspector Protocol**.25 To ensure reliability:

* **Bundling:** Utilizing esbuild to bundle extension code minimizes the file I/O overhead and reduces the surface area for runtime resolution errors.26  

* **Configuration:** Explicitly setting the bun.runtime path in settings.json and configuring the launch.json to use the bun type request ensures that the debugger attaches correctly to the Zig-based runtime rather than defaulting to the Node debugger.27

| Feature | Bun Runtime (Windows) | Node.js Runtime (Windows) | Recommendation for Project |
| :---- | :---- | :---- | :---- |
| **Startup-Speed** | Extremely Fast (Zig-based) | Moderate (V8-based) | Use Bun for tooling/scripts |
| **IPC Stability** | ✅ RESOLVED — `Bun.WebView` (v1.3.12) bypasses `child_process` / Named Pipes entirely via internal DevTools Protocol | Mature/Stable (libuv) | Use `Bun.WebView` for browser automation |
| **Browser-Launch** | ✅ RESOLVED — `new Bun.WebView({ backend: "chrome" })` launches Chrome directly, no ENOENT hang | Reliable | Use `Bun.WebView` natively (Bun v1.3.12+) |
| **Package-Mgmt** | Fast (Global Cache) | Slower (NPM/Yarn) | Use Bun (bun install) |
| **Debugging** | WebKit Inspector Protocol | V8 Inspector Protocol | Use VS Code + Bun Ext |

## **3.-The-Aesthetic-Decay-Biopunk-Industrial Maximalism**

Moving from the technical to the sensory, the "macro-world" described requires a distinct aesthetic identity. The prompt implies a fusion of "nonsense NSFW18+++extreme" elements. To "improve" this, we must filter these raw tropes through critical aesthetic theory, aligning them with **Biopunk** and **Industrial Maximalism**. These aesthetics do not merely depict gore or machinery; they interrogate the boundaries between the organic and the synthetic, the living and the decaying, creating a "visceral" reality that is texturally rich and thematically resonant.

### 3.1.-Redefining Biopunk-Beyond-"Goopy"

Standard biopunk is often reduced to "slime, flesh, bones, goo".29 However, to elevate the worldbuilding, one must adopt a more sophisticated visual language that incorporates the "Uncanny Valley" of materials that mimic life but fail to achieve it.

* **Synthetic-Flesh:** The texture of this world should not just be "wet." It requires precise tactile descriptors. Research into "synthetic skin" for robotics describes materials that mimic mechanoreceptors but lack the warmth of life.31 In the fiction, this becomes "Chrome Flesh" or "Synth-skin"—material that looks perfect but feels "wrong" (too cold, too smooth, lacking micro-imperfections).32 It creates a cognitive dissonance in the observer.  
* **Tactile Descriptors:** To improve the writing, replace generic terms with specific textures:  
  * *Chitinous:* Insect-like hardness, brittle yet strong.  
  * *Sebaceous:* Oily, waxy, suggesting biological secretion.  
  * *Tumid:* Swollen, distended, suggesting internal pressure or infection.  
  * *Viscid:* Sticky, adherent, resisting separation.  
  * *Cartilaginous:* Tough but flexible, structural but organic.  
  * *Membranous:* Thin, film-like, translucent barriers.

### 3.2.-Industrial Maximalism-The-Curated-Chaos

**Maximalism** is the "aesthetics of excess." It rejects the "less is more" philosophy of minimalism in favor of "more is more"—complexity, layering, and sensory abundance.33 In an industrial context, this means environments saturated with functional detail.

* **Visual Density:** Spaces should be "cluttered yet curated" 33, filled with the detritus of functionality—cables, vents, hydraulic pumps, bioluminescent fluid tanks, and nutrient feeds. This creates a "sensory hyper-stimulus" 35, overwhelming the viewer with visual data. This mirrors the cognitive overload of the digital age.36  

* **The-"Lived-In"-Dystopia:** It is the rejection of the sterile "Apple-futuristic" minimalism in favor of a layered, decaying technological sprawl.29 Old tech is patched with new tech. A CRT monitor is duct-taped to a bioluminescent vat. The "industrial past" is not hidden but accumulated.37  

* **Textures-Industry:** Descriptors should evoke the passage of time and the degradation of materials: *rust, oil, peeling paint, condensation, wet cement, burnt copper, hardened steel*.38

### 3.3.-Olfactory-Architecture-The Scent-Entropy**

Smell is the most neglected sense in digital worldbuilding, yet it is the most evocative, linking directly to the limbic system and memory.39 To deepen the immersion, the report proposes an "olfactory portrait of industrial decay."

* **Inorganic-Palette:**  
  * *Ozone:* The sharp, electric smell of high-voltage discharge or static.40  
  * *Petrichor:* The scent of rain on dry earth, or in this context, wet cement and dust.41  
  * *Acrid:* The biting smell of burning plastic, rubber, or chemical smoke.42  
  * *Metallic:* The taste/smell of copper, iron, or blood.43  
  * *Sulfurous:* Rotten eggs, volcanic gas, industrial waste.44  
  * *Bituminous:* The heavy, tarry smell of asphalt and pitch.38  
* **Organic/Decay-Palette:**  
  * *Miasmic:* Swamp-like, heavy air filled with suspended particles.45  
  * *Fetid:* The smell of active rot and decomposition.42  
  * *Musty:* Old paper, damp fabric, confined spaces.  
  * *Cloying:* Excessively sweet, sickeningly rich (like rotting fruit or formaldehyde).42  
  * *Rank:* Overgrown vegetation, dense biological growth.

By weaving these descriptors into the narrative, the "world" gains a physical weight. A laboratory doesn't just "look scary"; it smells of "antiseptic overlaid with the copper tang of blood and the sweet, cloying reek of cultured nutrient paste."

## 4.-Alchemical-Symbolism-The-Metaphysics-of-Transformation

To elevate the "nonsense" into "mythos," the report recommends integrating the symbolic language of **Alchemy**. Alchemy is not merely proto-chemistry; it is a system of psychological and material transformation that perfectly mirrors the themes of biopunk (modification) and decay.

### 4.1.-The-Phases-of-the-Magnum-Opus

The alchemical process provides a narrative structure for character arcs and world events.46

1. **Nigredo-(The-Blackening):** The stage of decomposition, chaos, and *putrefaction*. It represents the breaking down of the ego or the material form.  
   * *Symbolism:* The Raven, the Skull (Caput Mortuum), the "viscous black fluid," or "black oil."  
   * *Application:* This is the current state of the "macro-prompt-world"—a chaotic *massa confusa*.49 The "private no-policy nonsense" is the *prima materia*—the raw, chaotic base matter that must be cooked and dissolved to be purified.  
2. **Albedo-(The-Whitening):** Purification and washing. The removal of impurities.  
   * *Symbolism:* The White Swan, the Moon, silver.  
   * *Application:* The "improvement" phase requested by the user. The application of structure (SSOT), technical stability (fixing IPC), and aesthetic coherence.  
3. **Rubedo-(The-Reddening):** The final stage—integration and the creation of the Philosopher's Stone.  
   * *Symbolism:* The Red King, the Phoenix, gold.  
   * *Application:* The realized "world," fully functioning, cohesive, and alive.

### 4.2.-The-Sentience-of-the-Substrate-Bitumen-and-Black-Oil

The snippets reference "bitumen," "pitch," and "black oil" repeatedly. In alchemy and myth, these substances are not just materials; they are *entities*.

* **Bitumen-(Mumia):** Historically used in mummification (preservation) but also associated with "cementing" things together (the Tower of Babel).55 It represents the binding agent of civilization, but also a "viscous black fluid" that can trap and preserve.  
* **The-Black-Oil-(Sentient Fluid):** In modern mythologies (e.g., *The X-Files*), black oil is a viral, sentient substance that invades the body.54 This connects directly to the *Nigredo*—it is the "dark matter" or *prima materia* that possesses intelligence.56  

* **Integration:** The "world" should treat its "viscous black fluids"—whether industrial sludge, nanotech swarms, or alien biological agents—as manifestations of the *prima materia*. They are the chaotic potential from which new forms (monsters, cyborgs) are birthed.

## **5.-Psychological-Frameworks-Supernormal-Stimuli-The Body

The **"NSFW18+++-Extreme"** nature suggests focus on hyper-sexualized, hyper-violent content. To treat this seriously, improve it, we analyze it through **Evolutionary-Psychology** and **Sociology**.

### 5.1.-Supernormal-Stimuli: Hijacking-Brain-Wiring-for-Character-Design

A **"supernormal-stimulus"** is a signal that evolves to be more effective at triggering a behavioral response than the natural stimulus it mimics.

* **The-Mechanism:** Niko Tinbergen found that birds would prefer to sit on giant, brightly polka-dotted plaster eggs rather than their own real eggs. The artificial stimulus "hijacked" the nesting instinct.60  

* **Human-Application-(WHR):** In character design, this manifests as exaggerated **Waist-to-Hip-Ratios-(WHR)**. Evolutionary suggests a cross-cultural preference for a WHR of roughly 0.7 (signaling fertility/health). However, gaming, anime pivot this to impossible extremes (e.g., 0.5 or lower). These are **"supernormal stimuli"—Visuals** designed to trigger a peak shift in attraction response, bypassing cognitive filters.  

* **Critique:** While effective at grabbing attention, reliance on supernormal stimuli can lead to "response exhaustion" or desensitization.36 The "improvement" here is to understand *why* these designs work and to use them intentionally rather than reflexively. Is the character designed this way to trigger attraction, or to comment on the artificiality of the world? The "hyper-stimulus" creates a "neural trap" that the inhabitants of the macro-world might be addicted to.

### 5.2.-The-Sociology-Of-Decay-Body-Positivity-Vs.-Denial

The **"body-horror"** and **"decay"-themes** in the research offer counter-narrative to **"supernormal"-perfection**.

* **The-Denial-Of-Decay:** Modern **"wellness-culture"** and **"body-positivity"** (in its commercialized form) can be interpreted as a **"Refusal-Of-Decay"**. We sanitize death, hide aging, and present the body as a project to be optimized. **"Toxic-Positivity"** enforces narrationing constant improvement, marginalizing the reality of pain and entropy.  
* **Body-Horror-As-Critique:** Films like *The Substance* (referenced implicitly via **"body-horror"** and **"wellness-culture"** critiques) use physical transformation and gore to expose the violence of these beauty standards. The **"monster"** is often the result of trying to halt the natural process of entropy.  
* **Synthesis:** The **"world"** should explore this tension. The **"Industrial-Maximalist"** setting decaying, the inhabitants (perhaps using biopunk tech). desperate to remain **"supernormal"** young. The friction between the **decaying-world-and-the-preserved-body** create rich source horror + drama. The **"body-horror"** is not gore; it's inevitable return of repressed reality, of death.

## 6.-Narrative-Architecture-Establishing-A-Single-Source-Of-Truth

Finally, to manage this complex web of technical, aesthetic, and psychological elements, a robust **Information-Architecture** is required. A **"macro-world"** cannot be sustained by disparates; it requires a system of record.

### 6.1.-The-Single-Source-Of-Truth-(SSOT)**

In both **software-engineering-narrative design**, a **SSOT** is definitive data. Without it, **"lore-drift"** occurs—contradictions arise, the world lose coherence.

* **The-World-Bible:** More than **"wiki"**. A **database**. Needing **entity-tracking** (characters, locations, items) and their relationships. 
* **Canonical-Validation:** Just as software systems use validation rules to ensure data integrity, narrative workflows can use "canonical validation" to ensure new story elements fit the established rules (e.g., "Magic A cannot do X because of Rule Y defined in the SSOT").76

### 6.2.-Tooling-Obsidian-vs.-World-Anvil

The research snippets highlight a debate between **Obsidian** and **World Anvil** for narrative management.

* **World-Anvil:** Excellent for visual presentation and RPG stat blocks, but can be rigid, requires an internet connection, and locks data into a specific platform format.80  
* **Obsidian:** Recommended for this project ("Deep Research").  
  * **Local-Control:** Text files are stored locally as Markdown, ensuring future-proof access and privacy.81  
  * **Dataview:** This plugin is the "killer feature." It allows the author to query their own notes as if they were a database. You can write a query like TABLE status, location FROM "Characters" WHERE faction = "Industrialists" and get a dynamically updated list. This enables programmatic consistency checks—crucial for a **"macro-world"**.
  * **Linking-Bi-directionals:** Mimic the brain's associative patterns, allowing for "organic" growth of the lore while maintaining structure.

### 6.3.-Entity-Relationship-Diagrams-(ERDs)

To "improve" the world, one should map it out using **Entity-Relationship-Diagrams-(ERDs)**.

* **Entities:** Define the core nouns of the world: Factions, Species, Technologies, Locations.  
* **Relationships:** Define how they interact: "Member Of," "Enemy Of," "Located In," "Manufactured By."  
* **Cardinality:** Define the rules: Can a Character belong to multiple Factions? (One-to-Many vs. Many-to-Many).  
* **Application:** Creating an ERD (using tools like Mermaid.js within Obsidian) forces the worldbuilder to resolve logical inconsistencies in the world's politics and history before they become narrative problems.86

## 7.-Conclusion-The-Integrated-Macro-World

The "improvement" of the user's "private no-policy nonsense world" is not about removing the "nonsense," but about **architecting** it.

By building a stable **Technical-Substrate** (solving the Windows IPC/Bun conflict via Node wrappers or MCP), the user creates a reliable engine for automation and generation.

By adopting **Industrial-Maximalism** and **Biopunk**, the user moves from generic aesthetics to a rich, sensory-laden experience that leverages the "Uncanny Valley" and the textures of synthetic flesh ("chitinous," "tumid").

By integrating **Alchemical-Symbolism**, the "viscous fluids" and "decay" become meaningful metaphors for psychological transformation (*Nigredo*) and the eternal conflict between preservation (stasis) and rot (change).

By weaponizing **Evolutionary-Psychology**, the user can use "supernormal stimuli" deliberately to evoke specific responses, contrasting them with the horror of inevitable biological decay.

Establishing; **Single-Source-of-Truth** via Obsidian and **ERD's**, ensures that this complex, chaotic, and visceral world remains internally consistent and manageable.

This transdisciplinary approach transforms a collection of "prompts" into a living, breathing, and terrifyingly coherent **Macro-World**.

### **Appendix: Sensory Lexicon for the Macro-World**

| Category | Adjectives | Nouns | Metaphorical Associations |
| :---- | :---- | :---- | :---- |
| **Olfactory (Inorganic)** | *Ozone, Acrid, Metallic, Sulfurous, Astringent, Bituminous* | *Petrichor, Ether, Rust, Asphalt, Gunpowder* | Industry, War, sterility vs. pollution |
| **Olfactory (Organic)** | *Fetid, Miasmic, Cloying, Rank, Musty, Putrid* | *Musk, Rot, Ferment, Bile, Ichor* | Life, Death, Sex, Decay, The *Nigredo* |
| **Tactile (Textures)** | *Viscous, Chitinous, Membranous, Sebaceous, Tumid, Cartilaginous* | *Sludge, Resin, Film, Carapace, Gristle* | The "Abject," The Uncanny, Body Horror |
| **Visual (Maximalist)** | *Labyrinthine, Iridescent, Fractal, Dotted, Cluttered, Layered* | *Sprawl, Detritus, Lattice, Tangle, Aggregate* | Overload, Complexity, History, Entropy |

**Note-Citations:** The analysis above integrates data points from the provided research snippets, specifically referencing technical documentation on Bun, aesthetic theories, alchemical texts, narrative design methodologies, evolutionary psychology papers. All regarding behavior, historical symbolism + psychological theories, derived directly from sources.

#### Referanser

1. Bun for Visual Studio Code, brukt januar 26, 2026, [https://marketplace.visualstudio.com/items?itemName=oven.bun-vscode](https://marketplace.visualstudio.com/items?itemName=oven.bun-vscode)  
2. Setting up WSL with VSCode running Bun | by Fredrik Erasmus - Medium, brukt januar 26, 2026, [https://medium.com/@fredrik\_erasmus/setting-up-wsl-with-vscode-running-bun-182436f2b8b2](https://medium.com/@fredrik_erasmus/setting-up-wsl-with-vscode-running-bun-182436f2b8b2)  
3. \[Feature\] Compatibility with `bun` · Issue \#27139 · microsoft/playwright - GitHub, brukt januar 26, 2026, [https://github.com/microsoft/playwright/issues/27139](https://github.com/microsoft/playwright/issues/27139)  
4. Under Windows, spawning a `pwsh` child process using `spawn` and `detached: true` does not work · Issue \#51018 · nodejs/node - GitHub, brukt januar 26, 2026, [https://github.com/nodejs/node/issues/51018](https://github.com/nodejs/node/issues/51018)  
5. c# - Example named pipes IPC with read/write timeout - Stack Overflow, brukt januar 26, 2026, [https://stackoverflow.com/questions/9536337/example-named-pipes-ipc-with-read-write-timeout](https://stackoverflow.com/questions/9536337/example-named-pipes-ipc-with-read-write-timeout)  
6. issue of running playewright using bunjs - Stack Overflow, brukt januar 26, 2026, [https://stackoverflow.com/questions/79836631/issue-of-running-playewright-using-bunjs](https://stackoverflow.com/questions/79836631/issue-of-running-playewright-using-bunjs)  
7. Playwright does not work on Bunjs environment · Issue \#10120 · oven-sh/bun - GitHub, brukt januar 26, 2026, [https://github.com/oven-sh/bun/issues/10120](https://github.com/oven-sh/bun/issues/10120)  
8. playwright on windows doesn't work · Issue \#13543 · oven-sh/bun - GitHub, brukt januar 26, 2026, [https://github.com/oven-sh/bun/issues/13543](https://github.com/oven-sh/bun/issues/13543)  
9. Whispers in the Code: Inter Process Communication (IPC) and Named Pipes For Covert C2, brukt januar 26, 2026, [https://securitymaven.medium.com/whispers-in-the-code-inter-process-communication-ipc-and-named-pipes-for-covert-c2-0a84f2ea4f95](https://securitymaven.medium.com/whispers-in-the-code-inter-process-communication-ipc-and-named-pipes-for-covert-c2-0a84f2ea4f95)  
10. How to: Use Named Pipes for Network Interprocess Communication \- .NET | Microsoft Learn, brukt januar 26, 2026, [https://learn.microsoft.com/en-us/dotnet/standard/io/how-to-use-named-pipes-for-network-interprocess-communication](https://learn.microsoft.com/en-us/dotnet/standard/io/how-to-use-named-pipes-for-network-interprocess-communication)  
11. Named Pipes - Win32 apps \- Microsoft Learn, brukt januar 26, 2026, [https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipes](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipes)  
12. Node child\_process.spawn bad file descriptor on windows with ipc - Stack Overflow, brukt januar 26, 2026, [https://stackoverflow.com/questions/63303200/node-child-process-spawn-bad-file-descriptor-on-windows-with-ipc](https://stackoverflow.com/questions/63303200/node-child-process-spawn-bad-file-descriptor-on-windows-with-ipc)  
13. How to Use Bun for Playwright Tests in 2026? | BrowserStack, brukt januar 26, 2026, [https://www.browserstack.com/guide/bun-playwright](https://www.browserstack.com/guide/bun-playwright)  
14. playwright cannot run chromium.launch() · Issue #15679 · oven-sh/bun - GitHub, brukt januar 26, 2026, [https://github.com/oven-sh/bun/issues/15679](https://github.com/oven-sh/bun/issues/15679)  
15. Spawn - Bun, brukt januar 26, 2026, [https://bun.com/docs/runtime/child-process](https://bun.com/docs/runtime/child-process)  
16. Segmentation fault crash on Windows 11 in VS Code extension v2.0.29+ (Bun v1.3.1 runtime crash) · Issue #11201 · anthropics/claude-code - GitHub, brukt januar 26, 2026, [https://github.com/anthropics/claude-code/issues/11201](https://github.com/anthropics/claude-code/issues/11201)  
17. Playwright Chromium launch fails with native Bun runtime · Issue #23826 - GitHub, brukt januar 26, 2026, [https://github.com/oven-sh/bun/issues/23826](https://github.com/oven-sh/bun/issues/23826)  
18. Installation | Playwright, brukt januar 26, 2026, [https://playwright.dev/docs/intro](https://playwright.dev/docs/intro)  
19. MCP Bun Server - LobeHub, brukt januar 26, 2026, [https://lobehub.com/mcp/carlosedp-mcp-bun](https://lobehub.com/mcp/carlosedp-mcp-bun)  
20. microsoft/playwright-mcp: Playwright MCP server - GitHub, brukt januar 26, 2026, [https://github.com/microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)  
21. Playwright MCP Server - GitHub Pages, brukt januar 26, 2026, [https://executeautomation.github.io/mcp-playwright/docs/intro](https://executeautomation.github.io/mcp-playwright/docs/intro)  
22. Top Model Context Protocol (MCP) Servers for Test Automation, brukt januar 26, 2026, [https://testguild.com/top-model-context-protocols-mcp/](https://testguild.com/top-model-context-protocols-mcp/)  
23. Stealth Browser MCP - Model Context Protocol Integration for Cursor IDE | MCPCursor, brukt januar 26, 2026, [https://mcpcursor.com/server/stealth-browser-mcp](https://mcpcursor.com/server/stealth-browser-mcp)  
24. A MCP Server that provides browser access through playwright with "stealth mode" enabled. - GitHub, brukt januar 26, 2026, [https://github.com/brian-ln/stealth-browser-mcp](https://github.com/brian-ln/stealth-browser-mcp)  
25. Debugging Bun with the VS Code extension, brukt januar 26, 2026, [https://bun.com/docs/guides/runtime/vscode-debugger](https://bun.com/docs/guides/runtime/vscode-debugger)  
26. Bundling Extensions - Visual Studio Code, brukt januar 26, 2026, [https://code.visualstudio.com/api/working-with-extensions/bundling-extension](https://code.visualstudio.com/api/working-with-extensions/bundling-extension)  
27. How to debug JavaScript / Typescript in VSCode using Bun.sh - Stack Overflow, brukt januar 26, 2026, [https://stackoverflow.com/questions/75187929/how-to-debug-javascript-typescript-in-vscode-using-bun-sh](https://stackoverflow.com/questions/75187929/how-to-debug-javascript-typescript-in-vscode-using-bun-sh)  
28. bun + vscode (debugging)? - oven-sh bun - Discussion #8104 - GitHub, brukt januar 26, 2026, [https://github.com/oven-sh/bun/discussions/8104](https://github.com/oven-sh/bun/discussions/8104)  
29. Other types of biopunk aesthetics : r/worldbuilding - Reddit, brukt januar 26, 2026, [https://www.reddit.com/r/worldbuilding/comments/1iktnq0/other\_types\_of\_biopunk\_aesthetics/](https://www.reddit.com/r/worldbuilding/comments/1iktnq0/other_types_of_biopunk_aesthetics/)  
30. Beautiful Biopunk : r/worldbuilding - Reddit, brukt januar 26, 2026, [https://www.reddit.com/r/worldbuilding/comments/rne5nl/beautiful\_biopunk/](https://www.reddit.com/r/worldbuilding/comments/rne5nl/beautiful_biopunk/)  
31. Biologically inspired multi-layered synthetic skin for tactile feedback in prosthetic limbs, brukt januar 26, 2026, [https://pure.johnshopkins.edu/en/publications/biologically-inspired-multi-layered-synthetic-skin-for-tactile-fe/](https://pure.johnshopkins.edu/en/publications/biologically-inspired-multi-layered-synthetic-skin-for-tactile-fe/)  
32. Shadowrun Chrome Flesh - www.yic.edu.et, brukt januar 26, 2026, [https://www.yic.edu.et/index\_htm\_files/libweb/Nq7wco/ShadowrunChromeFlesh.pdf](https://www.yic.edu.et/index_htm_files/libweb/Nq7wco/ShadowrunChromeFlesh.pdf)  
33. Understanding the Concept of Maximalism | Coldharbour Lights, brukt januar 26, 2026, [https://coldharbourlights.com/en-us/blogs/news/understanding-the-concept-of-maximalism](https://coldharbourlights.com/en-us/blogs/news/understanding-the-concept-of-maximalism)  
34. Minimalism vs Maximalism: A Cultural Shift in Design Choices - Pearl Academy, brukt januar 26, 2026, [https://www.pearlacademy.com/blog/product-design/minimalism-vs-maximalism-consumer-product-aesthetics](https://www.pearlacademy.com/blog/product-design/minimalism-vs-maximalism-consumer-product-aesthetics)  
35. Marketing Design Trends of 2022 | Part 2: Maximalism - Enventys Partners, brukt januar 26, 2026, [https://enventyspartners.com/blog/2022-design-trends-part-2/](https://enventyspartners.com/blog/2022-design-trends-part-2/)  
36. A Dystopia of the Sign: Dystopian Themes in the Work of William Gibson - La Trobe, brukt januar 26, 2026, [https://opal.latrobe.edu.au/ndownloader/files/38772756](https://opal.latrobe.edu.au/ndownloader/files/38772756)  
37. Picturing our industrial past | Art UK, brukt januar 26, 2026, [https://artuk.org/learn/learning-resources/picturing-our-industrial-past](https://artuk.org/learn/learning-resources/picturing-our-industrial-past)  
38. Deus ex Machina Perfume, brukt januar 26, 2026, [https://alkemiaperfumes.com/products/deus-ex-machina-perfume-oil-motor-oil-steel-wet-cement-copper-wires-grey-amber](https://alkemiaperfumes.com/products/deus-ex-machina-perfume-oil-motor-oil-steel-wet-cement-copper-wires-grey-amber)  
39. Writing About Smell - Rue Baldry - WordPress.com, brukt januar 26, 2026, [https://ruebaldry.wordpress.com/2019/04/01/writing-about-smell/](https://ruebaldry.wordpress.com/2019/04/01/writing-about-smell/)  
40. Alkemia - Chelsea Komschlies, brukt januar 26, 2026, [https://www.komschlies.com/music/alkemia](https://www.komschlies.com/music/alkemia)  
41. Master List of Scents, for Writers - Bryn Donovan, brukt januar 26, 2026, [https://www.bryndonovan.com/2025/07/07/master-list-of-scents-for-writers/](https://www.bryndonovan.com/2025/07/07/master-list-of-scents-for-writers/)  
42. 75 Words That Describe Smells - A Resource For Writers, brukt januar 26, 2026, [https://www.writerswrite.co.za/75-words-that-describe-smells/](https://www.writerswrite.co.za/75-words-that-describe-smells/)  
43. Vocabulary for describing scents? : r/Incense - Reddit, brukt januar 26, 2026, [https://www.reddit.com/r/Incense/comments/w3a12l/vocabulary\_for\_describing\_scents/](https://www.reddit.com/r/Incense/comments/w3a12l/vocabulary_for_describing_scents/)  
44. Sulphur - Encyclopedia of Smell History and Heritage, brukt januar 26, 2026, [https://encyclopedia.odeuropa.eu/items/show/20](https://encyclopedia.odeuropa.eu/items/show/20)  
45. The Odour of Sanctity: When the Dead Smell Divine - Death Scent, brukt januar 26, 2026, [https://deathscent.com/2022/01/12/odour-of-sanctity/](https://deathscent.com/2022/01/12/odour-of-sanctity/)  
46. Caput Mortuum — After the Fire | Exhibition | Arthub - art-hub.co.uk, brukt januar 26, 2026, [https://www.art-hub.co.uk/ex/frake22](https://www.art-hub.co.uk/ex/frake22)  
47. The 7 Steps of Alchemical Transformation: A Path to Wholeness and Healing, brukt januar 26, 2026, [https://www.wocrecovery.com/steps-of-alchemical-transformation/](https://www.wocrecovery.com/steps-of-alchemical-transformation/)  
48. The Seven Stages of Spiritual Alchemy: A Step-by-Step Guide | TheCollector, brukt januar 26, 2026, [https://www.thecollector.com/spiritual-alchemy-occult/](https://www.thecollector.com/spiritual-alchemy-occult/)  
49. Chaos, Solvent & Stone * - TRANSMODERN ALCHEMY *, brukt januar 26, 2026, [http://transmodernalchemy.iwarp.com/whats_new_5.html](http://transmodernalchemy.iwarp.com/whats_new_5.html)  
50. The Collected Works of C.G. Jung: Volume 13: Alchemical Studies - Association of Jungian Analysts, brukt januar 26, 2026, [https://www.jungiananalysts.org.uk/wp-content/uploads/2018/07/C.-G.-Jung-Collected-Works-Volume-13_-Alchemical-Studies.pdf](https://www.jungiananalysts.org.uk/wp-content/uploads/2018/07/C.-G.-Jung-Collected-Works-Volume-13_-Alchemical-Studies.pdf)  
51. List of alchemical substances - Wikipedia, brukt januar 26, 2026, [https://en.wikipedia.org/wiki/List_of_alchemical_substances](https://en.wikipedia.org/wiki/List_of_alchemical_substances)  
52. Alchemic Symbol for Tar/Pitch? : r/alchemy - Reddit, brukt januar 26, 2026, [https://www.reddit.com/r/alchemy/comments/6fknic/alchemic\_symbol\_for\_tarpitch/](https://www.reddit.com/r/alchemy/comments/6fknic/alchemic_symbol_for_tarpitch/)  
53. shemot | rabbisylviarothschild, brukt januar 26, 2026, [https://rabbisylviarothschild.com/tag/shemot/](https://rabbisylviarothschild.com/tag/shemot/)  
54. It came from outer space: the virus, cultural anxiety, and speculative fiction - LSU Scholarly Repository, brukt januar 26, 2026, [https://repository.lsu.edu/cgi/viewcontent.cgi?article=5084\&context=gradschool\_dissertations](https://repository.lsu.edu/cgi/viewcontent.cgi?article=5084&context=gradschool_dissertations)  
55. Mummies and the Usefulness of Death | Science History Institute, brukt januar 26, 2026, [https://www.sciencehistory.org/stories/magazine/mummies-and-the-usefulness-of-death/](https://www.sciencehistory.org/stories/magazine/mummies-and-the-usefulness-of-death/)  
56. Prima materia - Wikipedia, brukt januar 26, 2026, [https://en.wikipedia.org/wiki/Prima_materia](https://en.wikipedia.org/wiki/Prima_materia)  
57. resurrection of evolutionary psychology in gaming \- Magnanimitas, brukt januar 26, 2026, [https://www.magnanimitas.cz/ADALTA/1102/papers/A_mago.pdf](https://www.magnanimitas.cz/ADALTA/1102/papers/A_mago.pdf)  
58. (PDF) Supernormal Stimuli in the Media - ResearchGate, brukt januar 26, 2026, [https://www.researchgate.net/publication/263926111_Supernormal_Stimuli_in_the_Media](https://www.researchgate.net/publication/263926111_Supernormal_Stimuli_in_the_Media)  
59. Irresistible by Design: AI Companions as Psychological Supernormal Stimuli - Punya Mishra, brukt januar 26, 2026, [https://punyamishra.com/2025/03/29/irresistible-by-design-ai-companions-as-psychological-supernormal-stimuli/](https://punyamishra.com/2025/03/29/irresistible-by-design-ai-companions-as-psychological-supernormal-stimuli/)  
60. Supernormal Stimuli: How Primal Urges Overran Their Evolutionary Purpose - Rorotoko, brukt januar 26, 2026, [https://www.rorotoko.com/08/20100719-barrett-deirdre-on-supernormal-stimuli-primal-urges-evolutionary](https://www.rorotoko.com/08/20100719-barrett-deirdre-on-supernormal-stimuli-primal-urges-evolutionary)  
61. Waist-to-Hip Ratio as Supernormal Stimuli: Effect of Contrapposto Pose and Viewing Angle, brukt januar 26, 2026, [https://www.researchgate.net/publication/333857290_Waist-to-Hip_Ratio_as_Supernormal_Stimuli_Effect_of_Contrapposto_Pose_and_Viewing_Angle](https://www.researchgate.net/publication/333857290_Waist-to-Hip_Ratio_as_Supernormal_Stimuli_Effect_of_Contrapposto_Pose_and_Viewing_Angle)  
62. The Supernormal Stimuli of Sex Dolls: A Novel Source of Evidence for Men's Unconstrained Mate Preferences | Evolutionary \- UT Psychology Labs, brukt januar 26, 2026, [https://labs.la.utexas.edu/buss/files/2025/07/The-Supernormal-Stimuli-of-Sex-Dolls-WC-1.pdf](https://labs.la.utexas.edu/buss/files/2025/07/The-Supernormal-Stimuli-of-Sex-Dolls-WC-1.pdf)  
63. Waist-to-Hip Ratio as Supernormal Stimuli: Effect of Contrapposto Pose and Viewing Angle - PubMed, brukt januar 26, 2026, [https://pubmed.ncbi.nlm.nih.gov/31214904/](https://pubmed.ncbi.nlm.nih.gov/31214904/)  
64. Rot's Progress: Gastronomy according to Peter Greenaway - ENGL328, brukt januar 26, 2026, [https://engl328.files.wordpress.com/2017/09/brinkema-gastronomy-and-greenaway.pdf](https://engl328.files.wordpress.com/2017/09/brinkema-gastronomy-and-greenaway.pdf)  
65. The Decay-Life of Things | Comparative Studies in Society and History | Cambridge Core, brukt januar 26, 2026, [https://www.cambridge.org/core/journals/comparative-studies-in-society-and-history/article/decaylife-of-things/912652B31E40DE60F29AE4E0A25D7039](https://www.cambridge.org/core/journals/comparative-studies-in-society-and-history/article/decaylife-of-things/912652B31E40DE60F29AE4E0A25D7039)  
66. Toxic Positivity vs. Genuine Optimism: Understanding the Difference - Lemon8, brukt januar 26, 2026, [https://www.lemon8-app.com/jostybell/7299957713235362310?region=us](https://www.lemon8-app.com/jostybell/7299957713235362310?region=us)  
67. Processing Feedback: We Can Lift Without Putting Others Down, brukt januar 26, 2026, [https://thespacebetweenstories.com/2019/05/03/processing-feedback-we-can-lift-without-putting-others-down/](https://thespacebetweenstories.com/2019/05/03/processing-feedback-we-can-lift-without-putting-others-down/)  
68. Respecting the Balance – Establishing Shot \- IU Blogs, brukt januar 26, 2026, [https://blogs.iu.edu/establishingshot/2025/01/28/respecting-the-balance/](https://blogs.iu.edu/establishingshot/2025/01/28/respecting-the-balance/)  
69. The Substance and the Pseudoscience of Perfection | HALOSCOPE, brukt januar 26, 2026, [https://www.haloscope.org/post/the-substance-and-the-pseudoscience-of-perfection](https://www.haloscope.org/post/the-substance-and-the-pseudoscience-of-perfection)  
70. GONE BUT NOT FORGOTTEN: ATMOSHERES, DEATH, AND AESTHETICS OF GOTH - Aaltodoc, brukt januar 26, 2026, [https://aaltodoc.aalto.fi/bitstreams/fefb0b4f-274d-4f7c-883a-dd701da67976/download](https://aaltodoc.aalto.fi/bitstreams/fefb0b4f-274d-4f7c-883a-dd701da67976/download)  
71. What Is a Single Source of Truth (SSOT)? - Vista Projects, brukt januar 26, 2026, [https://www.vistaprojects.com/what-is-single-source-of-truth-ssot/](https://www.vistaprojects.com/what-is-single-source-of-truth-ssot/)  
72. What Is a Single Source of Truth and How to Build One for Seamless Data Management - Strapi, brukt januar 26, 2026, [https://strapi.io/blog/what-is-single-source-of-truth](https://strapi.io/blog/what-is-single-source-of-truth)  
73. The Essential Guide to Game Asset Workflows - Artstash, brukt januar 26, 2026, [https://www.artstash.io/resources/essential-guide-to-game-asset-workflows](https://www.artstash.io/resources/essential-guide-to-game-asset-workflows)  
74. Entity Hierarchy | Evergine Doc, brukt januar 26, 2026, [https://docs.evergine.com/2023.3.1/manual/basics/component\_arch/entities/entity\_hierarchy.html](https://docs.evergine.com/2023.3.1/manual/basics/component_arch/entities/entity_hierarchy.html)  
75. Help with designing a generic database for a world : r/worldbuilding - Reddit, brukt januar 26, 2026, [https://www.reddit.com/r/worldbuilding/comments/156hln/help\_with\_designing\_a\_generic\_database\_for\_a\_world/](https://www.reddit.com/r/worldbuilding/comments/156hln/help_with_designing_a_generic_database_for_a_world/)  
76. © 2024 Mantas Mazeika - IDEALS, brukt januar 26, 2026, [https://www.ideals.illinois.edu/items/131475/bitstreams/436956/data.pdf](https://www.ideals.illinois.edu/items/131475/bitstreams/436956/data.pdf)  
77. Hammurabi: A Framework for Pluggable, Logic-Based X.509 Certificate Validation Policies - andrew.cmu.ed, brukt januar 26, 2026, [https://www.andrew.cmu.edu/user/bparno/papers/hammurabi.pdf](https://www.andrew.cmu.edu/user/bparno/papers/hammurabi.pdf)  
78. Notion vs. Obsidian for Worldbuilding and Fantasy Writing — Quill\&Steel, brukt januar 26, 2026, [https://www.quillandsteel.com/blogs/writing-tips/notion-vs-obsidian-worldbuilding](https://www.quillandsteel.com/blogs/writing-tips/notion-vs-obsidian-worldbuilding)  
79. Page 2 – The mutterings of a half-mad Canuck who (sometimes) writes stuff - I Really Should Be Writing, brukt januar 26, 2026, [https://www.msmanz.com/page/2/](https://www.msmanz.com/page/2/)  
80. World Anvil vs Obsidian : r/worldbuilding - Reddit, brukt januar 26, 2026, [https://www.reddit.com/r/worldbuilding/comments/1png8uz/world\_anvil\_vs\_obsidian/](https://www.reddit.com/r/worldbuilding/comments/1png8uz/world_anvil_vs_obsidian/)  
81. Best practices for tracking characters, locations and timeline etc. in a novel? - Help, brukt januar 26, 2026, [https://forum.obsidian.md/t/best-practices-for-tracking-characters-locations-and-timeline-etc-in-a-novel/33990](https://forum.obsidian.md/t/best-practices-for-tracking-characters-locations-and-timeline-etc-in-a-novel/33990)  
82. Plugins - Obsidian, brukt januar 26, 2026, [https://obsidian.md/plugins](https://obsidian.md/plugins)  
83. Anyone using BASES instead of DATAVIEW for organizing writing a novel? If so, what's your experience? : r/ObsidianMD - Reddit, brukt januar 26, 2026, [https://www.reddit.com/r/ObsidianMD/comments/1o4tmiz/anyone\_using\_bases\_instead\_of\_dataview\_for/](https://www.reddit.com/r/ObsidianMD/comments/1o4tmiz/anyone_using_bases_instead_of_dataview_for/)  
84. How to Draw an ER Diagram: A Step-by-Step Guide - Miro, brukt januar 26, 2026, [https://miro.com/diagramming/how-to-draw-an-er-diagram/](https://miro.com/diagramming/how-to-draw-an-er-diagram/)  
85. 2.2. Entity-relationship diagrams — A Practical Introduction to Databases, brukt januar 26, 2026, [https://runestone.academy/ns/books/published/practical\_db/PART2\_DATA\_MODELING/02-ERD/ERD.html](https://runestone.academy/ns/books/published/practical_db/PART2_DATA_MODELING/02-ERD/ERD.html)  
86. Entity Relationship Diagram (ERD) Tutorial and EXAMPLE - YouTube, brukt januar 26, 2026, [https://www.youtube.com/watch?v=wMgirP7z4k8](https://www.youtube.com/watch?v=wMgirP7z4k8)

---
