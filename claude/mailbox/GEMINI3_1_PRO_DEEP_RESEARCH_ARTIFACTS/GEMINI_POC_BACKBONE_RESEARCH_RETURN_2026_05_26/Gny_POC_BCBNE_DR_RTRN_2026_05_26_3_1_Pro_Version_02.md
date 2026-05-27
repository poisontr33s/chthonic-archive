# **Research Architecture for the Chthonic Archive: Substrate Expansion across Collage, Rendering, and Dialogue Vectors**

## **Architectural Imperative and Contextual Backbone**

The technological scaffolding of the Chthonic Archive represents a critical intersection between high-performance systems engineering and rigid aesthetic dogma. Operating strictly within the `MOLFOLOGICAL ANKHOLOGICAL EGYPTOLOGICAL SOUTH-AMERICAN ABSTRACTION-werk` register, the project's substrate is fundamentally incompatible with the homogenization inherent in commercial game engines. The explicit anti-drift contract demands the total rejection of Unity, Godot, and Unreal Engine architectures. These platforms invariably introduce a monolithic, "paper-weight POC" character defined by asset-store iteration, superficial shader polish, and rigid prefab dependencies. To manifest the K-CUP Hierarchical Trinity—anchored by the Triumvirate of Orackla Nocticula, Madam Umeko Ketsuraku, and Dr. Lysandra Thorne—the engineering must physically embody the themes of architectonic purification and axiomatic truth.  

This exhaustive report addresses three distinct but philosophically intertwined vectors of research designed to break the inheritance of commercial engine defaults. Vector A dissects non-rectangular, lossless collage methodologies to replace generic grid layouts, establishing a deterministic composition pipeline. Vector B evaluates Vulkan and wgpu-native rendering backbones that leverage existing CUDA/TensorRT hardware to achieve AAA-grade painterly-isometric visuals without engine-monolith drift. Vector C dismantles the traditional "paper-RPG" branching dialogue tree, replacing it with a deterministic, LLM-driven narrative substrate governed by constrained decoding and cryptographic truth-chain verification.

## **Vector A: Non-Rectangular Lossless Collage Method**

The reliance on standard rectangular grids for image composition acts as an architectural metonym for the very Unity-esque defaults the Chthonic Archive seeks to escape. A fixed rows × cols grid is computationally trivial but aesthetically sterile, reducing carefully composed 1920×1080 references into a contact sheet rather than a cohesive 2560×1440 wallpaper-grade derivative. The desired methodology must process mixed aspect ratios, ensure deterministic output suitable for continuous integration (CI) pipelines, and preserve absolute lossless quality from input to final encode.

### **Algorithmic Topologies for Image Layout**

The search for a deterministic, scale-invariant, and aesthetically rigorous layout algorithm necessitates evaluating spatial packing and subdivision techniques. The following candidate methodologies have been surveyed and ranked according to their topological features, determinism, and viability within the existing Rust/Python toolchain.

| Method | Topology | Deterministic? | Open-Source Ref Impl (Last Commit) | Variable Cell Aspect? | Variable Cell Size? | Salience-Aware? | Suitable for 16:9 Canvas? | Substrate Fit? |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **Salience-Aware Crop-and-Fit (Bin Packing)** | Non-overlapping orthogonal | Yes | bin-packing (Rust) / rectpack (Python) 1 | Yes | Yes | Native | Excellent | **Yes**. Rust/Python native. Uses Bssf heuristics for deterministic, tight packing.2 |
| **Voronoi Treemap** | Organic, polygonal | Seeded | d3-voronoi-treemap (JS, 4 yrs) 3 / WeightedTreemaps (R) 4 | N/A | Yes | Post-process | Moderate | **No**. Existing implementations are either abandoned JavaScript 3 or R-based.4 |
| **Squarified Treemap** | Near-square, hierarchical | Yes | Custom recursive subdivision | No | Yes | Post-process | Good | **Partial**. Over-penalizes 16:9 source aspects in pursuit of perfect squares. |
| **AutoCollage (Graph-Cut)** | Seamless, blended | Seeded | OpenCV / Graph-cut adaptations (No canonical repo) 5 | Yes | Yes | Native | Excellent | **Moderate**. Highly complex graph-cut optimization 5; computationally intensive. |
| **Quipu / Knot-Record** | Radial/Linear clustered | Yes | quipucamayoc (Python, 2023\) 7 | No | Limited | No | Moderate | **Yes**. Aesthetically aligned with Wedjat-Quipu ornaments, but mathematically better suited for UI/data.7 |
| **Force-Directed Similarity** | N-body clustered | Seeded | 3d-force-graph (JS) 8 / Custom Rust | Yes | Yes | Edge-driven | Moderate | **Moderate**. Physics simulation relaxation risks non-deterministic outputs if not aggressively seeded.8 |
| **Ouroboros / Ring Layout** | Closed loop | Yes | Custom polar coordinate mapping | No | Yes | No | Poor | **No**. Inefficient use of rectangular 16:9 wallpaper canvases; high negative space. |
| **Mandalic / Radial** | Concentric, orbital | Yes | CircularHough\_Grd style (Matlab/Python) 9 | No | Yes | No | Poor | **No**. Radial packing of rectangular images produces excessive overlapping or negative space.9 |

#### **Anti-Recommendation List for Layout Algorithms**

* **HTML/DOM-based Masonry grids:** Inherits a web-browser visual register and relies on CSS layout engines that are inherently non-deterministic across different rendering contexts.  
* **d3-voronoi-treemap:** Do not use. While aesthetically interesting due to its organic, non-rectangular boundaries, it introduces a Node.js/JavaScript dependency layer for a rendering task, and the repository is effectively dormant (last significant activity four years ago).3  
* **Force-Directed Graphs without Strict Seeding:** The stochastic nature of force relaxation algorithms (like ForceAtlas2) inherently violates the requirement for byte-identical CI re-runs unless heavily constrained and artificially seeded.11

#### **Layout Architecture Synthesis**

The optimal solution constructs a composite pipeline: **Salience-Aware Crop-and-Fit utilizing MaxRects**. By leveraging the Rust bin-packing crate or the Python rectpack library 2, the system can accept varying aspect ratios and sizes dynamically. The implementation of Guillotine algorithms, specifically the GuillotineBssfSas (Best Short Side Fit) heuristic, ensures highly efficient, deterministic area utilization without the visual monotony of standard grids.2 To integrate the aesthetic requirements of the Chthonic Archive, this orthogonal packing can be visually masked by a Quipu-inspired spline generation overlay. Utilizing the topological concepts seen in libraries like quipucamayoc 7, the system can draw connecting structural lines between semantically related images, effectively mapping perceptual similarity graphs onto the physical layout and breaking the visual rigidity of the underlying rectangles.

### **Salience Detection: Lossless and Deterministic Processing**

To support the Crop-and-Fit pipeline, the system must detect focal regions (such as UI panels, isometric character figures, and structural landmarks) within painterly sources losslessly. The solution must integrate cleanly into the Python/Rust stack without incurring a massive dependency penalty, specifically avoiding the introduction of heavy machine learning frameworks like full PyTorch installations for a single pipeline step.

1. **Spectral Residual Saliency (Classical)** The Spectral Residual approach, pioneered by Hou & Zhang (2007), operates by analyzing the log spectrum of an image to extract the spectral residual, mapping statistical singularities to detect salience.14  
   * *Substrate Fit:* **Viable.** It is extremely lightweight, deterministic, and requires only numpy and opencv-python to compute the Fast Fourier Transform (FFT).14 However, because it relies heavily on high-contrast contours and statistical anomalies, it may struggle to accurately identify subtle focal points within homogeneously shaded painterly isometric environments.  
2. **U2-Net / TRACER (Deep Learning)** Modern salient object detection relies on nested architectures. U2-Net utilizes a two-level nested U-structure that captures multi-scale features without degrading high-resolution details, achieving state-of-the-art results.16  
   * *Substrate Fit:* **Highly Recommended.** The rembg-rs library provides a Rust-native wrapper over ONNX Runtime for executing the U2-Net model.17 Crucially, this crate avoids memory bloat by utilizing memory-mapped model loading.17 The OS kernel manages virtual memory, pulling the 176MB u2net.onnx model into physical RAM only as needed, avoiding massive memory spikes during CI execution.17 It accepts raw memory bytes or image::DynamicImage types, runs inference via ort, and outputs a deterministic grayscale salience mask based on a configurable threshold (e.g., 0.5 for balanced edge detection).17 This fits the Rust toolchain perfectly, providing advanced AI saliency without PyTorch.  
3. **Compositional Priors**  
   Techniques utilizing simple rule-of-thirds heatmaps, edge-density calculations, or raw color-saliency masking.  
   * *Substrate Fit:* **Anti-Recommended.** These methods are far too brittle and heuristic-driven to reliably process the complex compositions of cRPG screenshots, leading to arbitrary and non-deterministic cropping behavior across varied inputs.

### **Lossless Format Frontier: Beyond WebP**

The pipeline currently emits PNG and lossless WebP. To push the compression ratio and maintain byte-identical lossless quality across the pipeline, modern codec implementations operating natively within the Python/Pillow workflow must be evaluated. The objective is to find a format that outperforms WebP in lossless mode, specifically on photographic and UI-heavy painterly content, while enjoying stable tooling support.

| Format | State (Q2 2026\) | Pillow Plugin Support | Lossless Efficiency vs WebP | Substrate Fit? |
| :---- | :---- | :---- | :---- | :---- |
| **JPEG XL (.jxl)** | Maturing, high browser/OS adoption | pillow-jpegxl-plugin (Active) 18 | \~20-30% smaller file sizes | **Yes**. Rust-bound plugin provides deep, memory-safe integration.18 |
| **AVIF** | Mature, widespread | pillow-heif / pillow-avif-plugin 19 | Slightly worse for pure lossless UI/art | **No**. AVIF excels at lossy compression; its lossless mode is inefficient compared to alternatives. |
| **HEIF** | Mature, mobile-heavy | pillow-heif 20 | Significantly worse 21 | **No**. HEIF compression tops out poorly at the high-end, resulting in larger files and lower quality structural retention.21 |
| **WebP2** | Abandoned | None | N/A | **No**. Google ceased active development on this experimental codec. |
| **OptiPNG / ZopfliPNG** | Legacy mature | Native Python wrappers | Marginally better than standard PNG | **No**. The build-time cost (Zopfli is extremely slow) does not justify the minimal size reduction when compared to next-generation formats. |

#### **Format Architecture Synthesis**

**JPEG XL (JXL)** is the definitive target for the lossless frontier. The pillow-jpegxl-plugin repository represents the precise hybrid substrate desired by the project: it is written in 54.4% Rust and 45.6% Python, utilizing the inflation/jpegxl-rs library to provide secure, memory-safe bindings.18 By executing img.save("output.jxl", lossless=True) within the Python script 18, the pipeline achieves unparalleled lossless compression ratios on painterly textures and high-frequency UI elements. JPEG XL was explicitly designed to supersede PNG in lossless workflows, mathematically outperforming both PNG and lossless AVIF without the processing overhead associated with aggressive PNG optimizers.

## **Vector B: cRPG Rendering Backbone Beyond Unity**

The foundational imperative of the graphics substrate is to achieve AAA-grade painterly-isometric visuals that surpass the aesthetic polish of games like *Disco Elysium* and *Pillars of Eternity 2*, while explicitly preventing the intrusion of the Unity-esque prefab dependency loop. The existing technology stack—Vulkan 1.3 via ash, wgpu 26, bevy\_ecs, and a TensorRT host—is uniquely positioned to achieve this through a highly decoupled, compute-heavy rendering architecture. The objective is architectural sovereignty: a renderer built from discrete, interoperable libraries rather than a monolithic editor environment.

### **Survey of Vulkan/wgpu-Native cRPG Renderers**

The following graphics frameworks and engines were evaluated against the criteria of AAA capability, Rust/wgpu nativity, and protection against engine-monolith drift.

1. **rend3** While historically a promising Bevy-decoupled wgpu renderer, rend3 is effectively dead. As of mid-2025, the repository was archived by its maintainers and placed in a read-only maintenance mode.22 The community has abandoned it due to structural inefficiencies and the inability to keep pace with wgpu updates.23  
   * *Substrate Fit?* **Explicit Anti-Recommendation.** Building a new project on a deprecated 3D renderer ensures rapid technological debt.  
2. **Bevy 0.18 Renderer**  
   The default renderer shipped with the Bevy engine is highly active and deeply integrated with bevy\_ecs.  
   * *Substrate Fit?* **Anti-Recommended as a Monolith.** While the project successfully utilizes bevy\_ecs for logic 25, adopting the entire Bevy rendering stack introduces the exact monolithic prefab/entity constraints the project is attempting to escape. The overarching goal is a bespoke rendering pipeline, not adherence to a general-purpose engine's specific rendering paradigms.  
3. **Diligent Engine / bgfx / The-Forge** These are mature, battle-tested C++ frameworks with multi-backend support. The-Forge, for instance, is actively used in shipping AAA titles.26  
   * *Substrate Fit?* **Anti-Recommended.** While incredibly powerful, adopting a massive C++ rendering abstraction requires building and maintaining complex, potentially unstable FFI (Foreign Function Interface) bridges to the Rust core. This neutralizes the memory safety and ergonomic benefits of the existing ash and wgpu pipelines.  
4. **Custom ash \+ SPIR-V (The Existing Path)**  
   The project already possesses a working ash Vulkan 1.3 pipeline for compute operations (e.g., runestone decompression). Expanding this to a full forward renderer utilizing dynamic rendering (VK\_KHR\_dynamic\_rendering) bypasses the heavy abstraction of legacy render passes.  
   * *Substrate Fit?* **The Load-Bearing Core.** This represents the highest-performance, lowest-level option, though it requires significant engineering effort to implement standard cRPG features like shadow mapping and screen-space ambient occlusion (SSAO) from scratch.  
5. **Vello (lyon/wgpu)** Vello is a 2D graphics rendering engine written in Rust that leverages GPU compute shaders for sorting, clipping, and prefix-scan algorithms, bypassing traditional CPU bottlenecks.28 It is highly active, with Q2 2026 updates including u8/f32 pipeline switching, overdraw elimination for opaque image fills, and GPU sparse strip rendering.29  
   * *Substrate Fit?* **Highly Recommended for the UI/Overlay Layer.** A painterly-isometric cRPG requires a world-class 2D vector renderer for dialogue trees, inventory panels, and localized annotations. Vello operates directly on wgpu and integrates cleanly over an underlying 3D Vulkan/wgpu world pass, mirroring the hybrid 2D-on-3D aesthetic achieved by *Disco Elysium*.

### **Substrate Composition Matrix**

To satisfy the requirements without exceeding the bandwidth of a small team, the system must compose these elements into a unified architecture.

| Architecture | Substrate Components | Additional Dependencies | Eng. Effort | Unity-Drift Risk | Fits Substrate? |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **1\. The Hybrid Vector-World** | ash (Forward 3D) \+ Vello (2D UI/Overlay) | vello, ash | High | None | **Yes**. Best match for Disco Elysium’s painted-2.5D aesthetic. The 3D world is rendered natively in Vulkan, while Vello handles high-res vector UI scaling.28 |
| **2\. The Pure Compute Pipeline** | ash Compute Shaders Only (Ray/Path Tracing) | None | Extreme | None | **Moderate**. The RTX 4090 supports this, but building a software rasterizer or full real-time path tracer in pure compute exceeds small-team viability. |
| **3\. Wgpu-Core with Compute Post-Processing** | wgpu 26 \+ Custom WGSL Post-FX | wgpu | Medium | Low | **Yes**. Uses the wgpu forward renderer for the heavy lifting, reserving custom compute passes for aesthetic painterly effects. |

#### **Recommended Architecture: The Wgpu-Core with Compute Post-Processing**

Given the presence of wgpu 26 and bevy\_ecs, the most viable composition is to construct a thin forward renderer in wgpu driven by bevy\_ecs queries, completely bypassing the official Bevy rendering crate.  
To achieve the AAA painterly aesthetic without requiring tens of thousands of hand-painted textures, the rendering pipeline must implement an **Anisotropic Kuwahara Filter** in WGSL as a compute-shader post-processing pass. The Kuwahara filter operates by analyzing the structure tensor of the image using a Dirac delta window function, smoothing homogenous regions while mathematically preserving and sharpening directional edges.30 This specific transformation converts standard 3D PBR renders into organic, brush-stroke-like painterly outputs in real-time.31 Executing this complex convolution in WGSL at 60+ FPS is computationally trivial for an RTX 4090, fundamentally baking the MOLFOLOGICAL aesthetic into the mathematics of the renderer rather than relying on superficial asset-store shaders.

### **Leveraging CUDA/TensorRT in the Asset Pipeline**

A 24 GB VRAM RTX 4090 provides immense offline and real-time processing power. The asset pipeline must weaponize this hardware to bypass the visual homogeny of the Unity Asset Store.  
**Real-ESRGAN Neural Upscaling:** Instead of purchasing generic high-resolution asset packs, the pipeline can ingest low-resolution, highly stylized curated art (e.g., bespoke pixel art or low-res paintings) and utilize Real-ESRGAN for neural upscaling. Python implementations utilizing ONNX and TensorRT (vsrealesrgan or RealESRGAN-trt-win) allow for ultra-fast, blind super-resolution that preserves the aesthetic intent of the original painted artifact while scaling it to 4K.33 This process is run deterministically at build-time, injecting the high-res assets directly into the payload.  
**Stable Diffusion Texture Synthesis:**  
For environment assets, the pipeline can utilize Diffusion-driven texture synthesis locked to a specific aesthetic LoRA (e.g., an Ankhological/South-American Abstraction model). Executed offline via TensorRT, this generates infinite style-locked variations of ground textures and architectural elements without requiring manual painting, fundamentally breaking the asset-store iteration loop.  
**The Canonical Format: glTF 2.0** The project must rely exclusively on **glTF 2.0**, processed natively in Rust using the gltf-rs crate (v1.4+).25 gltf-rs provides safe, deterministic loading of scene hierarchies, binary payloads, and materials.25 The pipeline will deserialize the JSON scene layout, map the TensorRT-upscaled textures, and load them directly into the wgpu buffers. By adhering strictly to the glTF specification and processing it via Rust, the pipeline circumvents proprietary editor formats and locks the visual aesthetic into an open, auditable standard.

## **Vector C: Dialogue System Beyond Paper-RPG Emulation**

The rejection of "paper-RPG emulation" necessitates abandoning the standard *Pillars of Eternity* or *Pathfinder* dialogue model. Branching dialogue trees gated by simple skill checks (e.g., \[Persuasion 45\] Tell me the truth) reduce complex psychological and philosophical interactions to binary statistical tests. This pattern is the definition of a "paper-weight POC" mechanic—it simulates depth through branching volume rather than systemic interaction. The dialogue mechanics of the Chthonic Archive must function as a true engineering substrate, integrated directly with the Lysandra Truth Chain and the Reconciliation Engine.

### **Survey of Non-Tree Narrative Architectures**

To establish a new paradigm, we must evaluate shipping implementations that have successfully discarded or subverted the rigid branching tree.

1. **Quality-Based Narrative (Storylets)**  
   * *Data Model:* Instead of a hardcoded, directed acyclic graph (A \-\> B \-\> C), the narrative is composed of independent, atomic nodes called "storylets." Each storylet contains prerequisites (qualities) that must be met for it to be active, and updates the world state upon completion.35  
   * *Precedents:* *Fallen London*, *Sunless Sea*.36  
   * *Mechanic:* The engine evaluates a pool of thousands of storylets and presents the player only with those currently valid. This enables highly non-linear, episodic narratives that remember state without combinatorial explosion.36  
   * *Open-Source Implementations:* Dendry / DendryNexus (JavaScript, heavily updated Q1 2026, supports card-deck paradigms) 38, storylets-rs (Rust narrative engine) 39, Throne (Rust rules engine).40  
2. **Internal Psychological Probability (Disco Elysium)**  
   * *Data Model:* While structurally built on Articy Draft (a branching middleware), the *mechanic* relies on passive skill checks injecting intrusive thoughts into the dialogue flow.41  
   * *Mechanic:* It functions less as a tree and more as a multi-agent debate where the player's internal state constantly alters the available branches, though it ultimately still relies on a backend branching structure.  
3. **Poetics-as-Mechanic (Kentucky Route Zero)**  
   * *Data Model:* Linear state progression with reflective branching.  
   * *Mechanic:* Choices do not alter the world state or branch the narrative. Instead, choices define the *interiority* and *perspective* of the characters. The mechanic is purely aesthetic and reflective, escaping the trap of "optimizing" a dialogue choice for mechanical gain.  
4. **Dice as Currency (Citizen Sleeper)**  
   * *Data Model:* Action-pool expenditure.  
   * *Mechanic:* Dice are rolled at the start of a cycle and used as a resource to activate nodes, fundamentally separating the act of choice from the probability of success.

#### **Anti-Recommendation List for Dialogue**

* **Ink / Inkle:** Do not use as the primary structural engine. While highly regarded and excellent for narrative text, Ink's data model is fundamentally a sophisticated branching weave. It is not a substrate for programmatic rule engines and enforces a "choose your own adventure" paradigm.43  
* **Articy Draft / Chat Mapper:** Commercial middleware that enforces the visual-scripting, flowchart metaphor explicitly rejected by the project.41  
* **Unconstrained AI Generation:** Utilizing off-the-shelf APIs (e.g., Inworld, standard ChatGPT) to generate dialogue dynamically results in severe hallucination, breaking the precise ANKHOLOGICAL linguistic mandates and violating the anti-drift contract.

### **Deterministic LLM Dialogue via Constrained Decoding**

To build a dialogue system that is computationally alive but absolutely constrained against hallucination or drift, the system must integrate Large Language Models (LLMs) at runtime. However, free-form LLM generation is strictly forbidden. The architectural solution is **Constrained Decoding** using finite-state automata (FSA) and context-free grammars (CFG) to physically force the LLM to output valid game-state logic, JSON schemas, or specific linguistic patterns.

| Framework | Implementation | Approach | JSON Schema Coverage | Substrate Fit? |
| :---- | :---- | :---- | :---- | :---- |
| **llguidance** | Rust / C-FFI | Earley parser, runtime token masking 44 | Extremely High 46 | **Yes**. Generates token masks in \~50μs. Deeply integrated with Rust and capable of enforcing Lark-like grammars.45 |
| **outlines-core** | Rust / Python | Regex to Finite-State Automata 47 | High | **Yes**. Pre-computes masks for FSA states. Officially supports Rust natively and integrates easily with LLM inference engines.48 |
| **LMQL** | Python | Control flow, AST parsing | Moderate | **No**. Heavily Python-dependent, making it difficult to embed cleanly into a high-performance Rust game loop. |

#### **Architectural Synthesis for Dialogue Generation**

The engine must utilize **outlines-core** or **llguidance** executed natively in Rust. By defining a strict JSON schema that maps directly to the bevy\_ecs component state and the Lysandra Truth Chain protocol, the LLM is physically prevented from outputting invalid tokens.45  
For example, if the engine requires the LLM to output a response governed by the Madam Umeko Ketsuraku persona profile, llguidance computes a token mask—a set of allowed tokens from the model's vocabulary—that forces the output to conform to the specified grammar.45 This mask computation takes approximately 50μs of single-core CPU time.45 If a generated dialogue line attempts to invent lore outside the K-CUP Triumvirate register, the grammar engine masks those tokens at the logits level, forcing the model back into the canonical probability space.45 This guarantees deterministic, auditable constraints on runtime generation.

### **The Truth-Chain Integration Protocol**

The most profound realization of the Chthonic Archive's aesthetic is to weaponize the Lysandra Truth Chain as the core gameplay loop. Instead of rolling a simulated 20-sided die to determine if an NPC believes the player, the dialogue system functions as a cryptographic verifier chain. Dialogue becomes an act of mathematical compilation.

#### **Design Sketch 1: The Sampling Verifier Loop**

**Mechanism:** Every claim made by an NPC is generated by the LLM via constrained decoding, but it must ship with a verifier. The engine employs a Sampling Verifier.50 When the player interacts with a dialogue node, the LLM proposes an assertion. The Rust backend immediately checks this assertion against the Throne rule engine's state graph.40 If the assertion contradicts known axioms (e.g., claiming a false relationship in the Triumvirate), the engine rejects the token sequence, triggering a "refusal-on-drift" response where the NPC mathematically corrects themselves in real-time.

#### **Design Sketch 2: Structural-Boundary Verification (Proof Construction)**

**Mechanism:** The player does not choose pre-written dialogue options from a list. Instead, the player selects *evidence nodes* or *axioms* from their inventory (managed as storylet qualities 35) to construct a valid logical proof.

1. The player arranges Axiom A and Axiom B.  
2. The outlines-core index 47 compiles this logical structure into a specific regular expression or JSON schema.  
3. The LLM is prompted to generate the character's verbal response, constrained *entirely* by the regex generated by the player's proof.  
4. If the proof is topologically invalid, the resulting regex forces the LLM to output a specific failure linguistic pattern defined by the LINGUISTIC\_PROFILE\_PROTOCOL.

#### **Design Sketch 3: Storylet-Driven Axiom Economies**

**Mechanism:** Integrating the Quality-Based Narrative model of storylets-rs 39, truth itself becomes the resource. The player accumulates "Verified Axioms" as qualities. When confronting a Tier 1 entity like Orackla Nocticula, the dialogue interface does not show skill checks; it shows the storylet prerequisites. The player must "spend" the cryptographic proof of a verified axiom to unlock the next generation tier. The LLM then synthesizes the spent axiom into the generated text, ensuring the narrative constantly reflects the mechanical state of the truth chain.  
This architecture transforms dialogue from a superficial branching tree into an *active compilation process*. The narrative succeeds only if the verifier loop evaluates to true, physically instantiating the Lysandra Thorne (Truth/Axiomatic) protocol as the engine's core mechanical algorithm.

## **Conclusion**

The structural integrity of the Chthonic Archive relies on a fundamental rejection of commercial game engine defaults. By aggressively composing discrete, high-performance Rust, Vulkan, and Python libraries, the project achieves an engineering substrate that perfectly mirrors its aesthetic mandates.

1. **Vector A (Collage):** The tyranny of the grid is resolved by a deterministic, salience-aware Crop-and-Fit algorithm. Driven by U2-Net (rembg-rs) and max\_rects, it packs varied aspect ratios intelligently while emitting hyper-compressed JPEG XL files via memory-safe Rust bindings, ensuring CI determinism and lossless fidelity.  
2. **Vector B (Rendering):** The Unity asset-store loop is bypassed by combining a thin wgpu forward renderer with the Vello 2D compute-engine for UI. By heavily relying on Anisotropic Kuwahara WGSL compute shaders and offline Real-ESRGAN TensorRT upscaling, the engine computationally generates the MOLFOLOGICAL painterly aesthetic from raw, untextured glTF 2.0 geometry, relying on mathematics rather than manual asset bloat.  
3. **Vector C (Dialogue):** The paper-RPG branching tree is entirely dismantled. Utilizing a Quality-Based Narrative (Storylet) engine written in Rust, and driving character dialogue via outlines-core and llguidance constrained decoding, real-time LLM outputs are forced to compile against the Lysandra Truth Chain. This manifests the narrative's abstract themes as physical code constraints, ensuring absolute sovereign control over the project's mechanical and aesthetic destiny.

#### **Referanser**

1. bin-packing \- Keywords \- crates.io: Rust Package Registry, brukt mai 26, 2026, [https://crates.io/keywords/bin-packing](https://crates.io/keywords/bin-packing)  
2. secnot/rectpack: Python 2D rectangle packing library · GitHub \- GitHub, brukt mai 26, 2026, [https://github.com/secnot/rectpack](https://github.com/secnot/rectpack)  
3. Kcnarf/d3-voronoi-treemap \- GitHub, brukt mai 26, 2026, [https://github.com/Kcnarf/d3-voronoi-treemap](https://github.com/Kcnarf/d3-voronoi-treemap)  
4. m-jahn/WeightedTreemaps: Create Voronoi and Sunburst Treemaps from Hierarchical data \- GitHub, brukt mai 26, 2026, [https://github.com/m-jahn/WeightedTreemaps](https://github.com/m-jahn/WeightedTreemaps)  
5. AutoCollage \- Microsoft Research, brukt mai 26, 2026, [https://www.microsoft.com/en-us/research/publication/autocollage/?lang=zh-cn](https://www.microsoft.com/en-us/research/publication/autocollage/?lang=zh-cn)  
6. AutoCollage \- Microsoft Research, brukt mai 26, 2026, [https://www.microsoft.com/en-us/research/publication/autocollage/](https://www.microsoft.com/en-us/research/publication/autocollage/)  
7. potatodax/quipucamayoc: A high-level quipu visualization library for Python \- GitHub, brukt mai 26, 2026, [https://github.com/potatodax/quipucamayoc](https://github.com/potatodax/quipucamayoc)  
8. 3D Force-Directed Graph (ThreeJS) \- GitHub Gist, brukt mai 26, 2026, [https://gist.github.com/d6bdebe62b40bd124e9c4e1b75283c8a](https://gist.github.com/d6bdebe62b40bd124e9c4e1b75283c8a)  
9. gradschool\_matlab/CircularHough\_Grd.m at master \- GitHub, brukt mai 26, 2026, [https://github.com/ajdecon/gradschool\_matlab/blob/master/CircularHough\_Grd.m](https://github.com/ajdecon/gradschool_matlab/blob/master/CircularHough_Grd.m)  
10. d3-voronoi-treemap/.gitignore at master \- GitHub, brukt mai 26, 2026, [https://github.com/Kcnarf/d3-voronoi-treemap/blob/master/.gitignore](https://github.com/Kcnarf/d3-voronoi-treemap/blob/master/.gitignore)  
11. FLOW-MAP: a graph-based, force-directed layout algorithm for trajectory mapping in single-cell time course datasets \- PMC, brukt mai 26, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC7897424/](https://pmc.ncbi.nlm.nih.gov/articles/PMC7897424/)  
12. GitHub \- seandavi/awesome-single-cell: Community-curated list of software packages and data resources for single-cell, including RNA-seq, ATAC-seq, etc., brukt mai 26, 2026, [https://github.com/seandavi/awesome-single-cell](https://github.com/seandavi/awesome-single-cell)  
13. bin-packing \- Lib.rs, brukt mai 26, 2026, [https://lib.rs/crates/bin-packing](https://lib.rs/crates/bin-packing)  
14. opencv-python-blueprints/chapter5/saliency.py at master \- GitHub, brukt mai 26, 2026, [https://github.com/mbeyeler/opencv-python-blueprints/blob/master/chapter5/saliency.py](https://github.com/mbeyeler/opencv-python-blueprints/blob/master/chapter5/saliency.py)  
15. Image Saliency Detection using OpenCV \- GitHub, brukt mai 26, 2026, [https://github.com/ivanred6/image\_saliency\_opencv](https://github.com/ivanred6/image_saliency_opencv)  
16. The code for our newly accepted paper in Pattern Recognition 2020: "U^2-Net: Going Deeper with Nested U-Structure for Salient Object Detection." \- GitHub, brukt mai 26, 2026, [https://github.com/xuebinqin/u-2-net](https://github.com/xuebinqin/u-2-net)  
17. WarRaft/rembg-rs: A Rust utility for removing backgrounds ... \- GitHub, brukt mai 26, 2026, [https://github.com/warraft/rembg-rs](https://github.com/warraft/rembg-rs)  
18. Isotr0py/pillow-jpegxl-plugin: Pillow plugin for JPEG-XL ... \- GitHub, brukt mai 26, 2026, [https://github.com/Isotr0py/pillow-jpegxl-plugin](https://github.com/Isotr0py/pillow-jpegxl-plugin)  
19. Image file formats \- Pillow (PIL Fork) 12.2.0 documentation, brukt mai 26, 2026, [https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)  
20. pillow\_heif/CHANGELOG.md at master \- GitHub, brukt mai 26, 2026, [https://github.com/bigcat88/pillow\_heif/blob/master/CHANGELOG.md](https://github.com/bigcat88/pillow_heif/blob/master/CHANGELOG.md)  
21. Using AVIF and HEIF images with Python / PIL \- Code Calamity, brukt mai 26, 2026, [https://codecalamity.com/using-avif-and-heif-images-with-python-pil/](https://codecalamity.com/using-avif-and-heif-images-with-python-pil/)  
22. BVE-Reborn/rend3: MAINTENCE MODE \---- Easy to use ... \- GitHub, brukt mai 26, 2026, [https://github.com/BVE-Reborn/rend3](https://github.com/BVE-Reborn/rend3)  
23. Zed editor switching graphics lib from blade to wgpu \- Hacker News, brukt mai 26, 2026, [https://news.ycombinator.com/item?id=47002825](https://news.ycombinator.com/item?id=47002825)  
24. 3D rendering: GPU buffer allocation vs. safety boundary \- community \- Rust Users Forum, brukt mai 26, 2026, [https://users.rust-lang.org/t/3d-rendering-gpu-buffer-allocation-vs-safety-boundary/121489](https://users.rust-lang.org/t/3d-rendering-gpu-buffer-allocation-vs-safety-boundary/121489)  
25. gltf-rs/gltf: A crate for loading glTF 2.0 · GitHub \- GitHub, brukt mai 26, 2026, [https://github.com/gltf-rs/gltf](https://github.com/gltf-rs/gltf)  
26. GitHub \- isala404/forge: Rust framework that compiles entire infrastructure into one binary, brukt mai 26, 2026, [https://github.com/isala404/forge](https://github.com/isala404/forge)  
27. awesome-graphics-libraries/README.md at main \- GitHub, brukt mai 26, 2026, [https://github.com/jslee02/awesome-graphics-libraries/blob/master/README.md](https://github.com/jslee02/awesome-graphics-libraries/blob/master/README.md)  
28. vello \- Rust \- Docs.rs, brukt mai 26, 2026, [https://docs.rs/vello](https://docs.rs/vello)  
29. Linebender in December 2025 \- Linebender, brukt mai 26, 2026, [https://linebender.org/blog/tmil-24/](https://linebender.org/blog/tmil-24/)  
30. VFX-software-prefs/Nuke/Kuwahara/df\_kuwahara\_tensor.cpp at main \- GitHub, brukt mai 26, 2026, [https://github.com/sharktacos/VFX-software-prefs/blob/main/Nuke/Kuwahara/df\_kuwahara\_tensor.cpp](https://github.com/sharktacos/VFX-software-prefs/blob/main/Nuke/Kuwahara/df_kuwahara_tensor.cpp)  
31. \[Media\] Kuwahara Filter Running with Rust \+ WGSL \- Reddit, brukt mai 26, 2026, [https://www.reddit.com/r/rust/comments/1ndtaxi/media\_kuwahara\_filter\_running\_with\_rust\_wgsl/](https://www.reddit.com/r/rust/comments/1ndtaxi/media_kuwahara_filter_running_with_rust_wgsl/)  
32. jkyprian/gpuakf: Image and Video Abstraction by Anisotropic Kuwahara Filtering \- GitHub, brukt mai 26, 2026, [https://github.com/jkyprian/gpuakf](https://github.com/jkyprian/gpuakf)  
33. vsrealesrgan \- PyPI, brukt mai 26, 2026, [https://pypi.org/project/vsrealesrgan/](https://pypi.org/project/vsrealesrgan/)  
34. phineas-pta/RealESRGAN-trt-win: Real-ESRGAN with TensorRT on Windows \- GitHub, brukt mai 26, 2026, [https://github.com/phineas-pta/RealESRGAN-trt-win](https://github.com/phineas-pta/RealESRGAN-trt-win)  
35. UC Santa Cruz \- eScholarship.org, brukt mai 26, 2026, [https://escholarship.org/content/qt0r9246gd/qt0r9246gd.pdf](https://escholarship.org/content/qt0r9246gd/qt0r9246gd.pdf)  
36. quality-based narrative \- Emily Short's Interactive Storytelling, brukt mai 26, 2026, [https://emshort.blog/category/quality-based-narrative/](https://emshort.blog/category/quality-based-narrative/)  
37. 50 years of Text Games: From Oregon Trail to AI Dungeon \[1 ed.\] 9798985966138, 9798985966145 \- DOKUMEN.PUB, brukt mai 26, 2026, [https://dokumen.pub/50-years-of-text-games-from-oregon-trail-to-ai-dungeon-1nbsped-9798985966138-9798985966145.html](https://dokumen.pub/50-years-of-text-games-from-oregon-trail-to-ai-dungeon-1nbsped-9798985966138-9798985966145.html)  
38. aucchen/dendrynexus: Re-implementation of various ... \- GitHub, brukt mai 26, 2026, [https://github.com/aucchen/dendrynexus](https://github.com/aucchen/dendrynexus)  
39. storylets \- crates.io: Rust Package Registry, brukt mai 26, 2026, [https://crates.io/crates/storylets](https://crates.io/crates/storylets)  
40. t-mw/throne: Scripting language for game prototyping and story logic \- GitHub, brukt mai 26, 2026, [https://github.com/t-mw/throne](https://github.com/t-mw/throne)  
41. Disco Elysium Dialogue System : r/unrealengine \- Reddit, brukt mai 26, 2026, [https://www.reddit.com/r/unrealengine/comments/1r3dwpm/disco\_elysium\_dialogue\_system/](https://www.reddit.com/r/unrealengine/comments/1r3dwpm/disco_elysium_dialogue_system/)  
42. Implementing a "Disco Elysium" dialogue system \- YouTube, brukt mai 26, 2026, [https://www.youtube.com/watch?v=oimMfjTE5mM](https://www.youtube.com/watch?v=oimMfjTE5mM)  
43. Fountain Movie Script Parser — JavaScript, Python, C\#, C++ | by Ian Thomas \- Medium, brukt mai 26, 2026, [https://wildwinter.medium.com/fountain-movie-script-parser-javascript-python-c-c-ca088d63d298](https://wildwinter.medium.com/fountain-movie-script-parser-javascript-python-c-c-ca088d63d298)  
44. llguidance \- Rust \- Docs.rs, brukt mai 26, 2026, [https://docs.rs/llguidance](https://docs.rs/llguidance)  
45. guidance-ai/llguidance: Super-fast Structured Outputs ... \- GitHub, brukt mai 26, 2026, [https://github.com/guidance-ai/llguidance](https://github.com/guidance-ai/llguidance)  
46. docs/llguidance.md · rohan23998/llama-cpp-model at main \- Hugging Face, brukt mai 26, 2026, [https://huggingface.co/rohan23998/llama-cpp-model/blob/main/docs/llguidance.md](https://huggingface.co/rohan23998/llama-cpp-model/blob/main/docs/llguidance.md)  
47. GitHub \- dottxt-ai/outlines-core: Faster structured generation, brukt mai 26, 2026, [https://github.com/dottxt-ai/outlines-core](https://github.com/dottxt-ai/outlines-core)  
48. Structured generation with Outlines, now in Rust : r/LocalLLaMA \- Reddit, brukt mai 26, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1g9pb7r/structured\_generation\_with\_outlines\_now\_in\_rust/](https://www.reddit.com/r/LocalLLaMA/comments/1g9pb7r/structured_generation_with_outlines_now_in_rust/)  
49. Two Shots Are Enough: Reliable Constrained Generation with LLMs, brukt mai 26, 2026, [https://exascale.info/assets/pdf/mondal2025bigdata.pdf](https://exascale.info/assets/pdf/mondal2025bigdata.pdf)  
50. BEAVER: An Efficient Deterministic LLM Verifier \- arXiv, brukt mai 26, 2026, [https://arxiv.org/html/2512.05439v2](https://arxiv.org/html/2512.05439v2)