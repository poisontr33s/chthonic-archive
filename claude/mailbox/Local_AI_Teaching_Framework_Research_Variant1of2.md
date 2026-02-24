# **System Architecture and Feasibility Report: Local AI Distillation and Task-Specific Parameter-Efficient Fine-Tuning**

## **Introduction and Strategic Context**

The operationalization of multi-agent development workspaces frequently encounters critical friction points when processing highly specialized or mature domain content. Cloud-based Large Language Models (LLMs), bound by stringent alignment protocols and generalized content policies, systematically refuse or self-censor execution requests involving mature archetypes or esoteric visual vocabularies. This architectural limitation necessitates the deployment of local, uncensored inference engines to handle specialized metadata extraction tasks.

Within the current deployment framework, the Sister Ferrum Scoriae (SFS) Theme System relies heavily on a dual aesthetic vocabulary. This vocabulary mandates a strict equilibrium between an Egyptian axis—incorporating pre-3100 BCE motifs such as the Ankh, Wedjat, Shen Ring, Scarab, Djed, Ma'at Feather, Tyet, and Uraeus—and an Andean axis—utilizing pre-3000 BCE elements including the Quipu, Chakana, Tocapu, Tinku, Pachakuti, Huaca, Nazca Lines, and Inti. Furthermore, the domain requires the enforcement of a MILFOLOGICAL baseline governed by four discrete axioms: FA¹ (Alchemical Actualization), FA² (Panoptic Re-contextualization), FA³ (WHR:MAX Optimization), and FA⁴ (Ma'at Checksum). The extraction targets include specific character archetypes (Orackla, Umeko, SFS, Claudine Sin'claire, Spectra Chroma) and require rigorous NSFW tier classification ranging from none to extreme.

To process this creative cRPG content, the infrastructure currently relies on a local Qwen3-30B-A3B-Instruct-abliterated model operating in GGUF format via the llama-cpp-python binding. While the 30B Mixture-of-Experts (MoE) architecture demonstrates sufficient foundational capability, it suffers from a 15% execution failure rate during constrained decoding tasks. These failures manifest as hallucinated file references, inconsistent thematic classifications, and abrupt generation collapses resulting in "Summary unavailable" outputs.

To systematically eradicate these inefficiencies, a continuous knowledge distillation pipeline is required. This report exhaustively analyzes the feasibility of establishing a teacher-student architectural loop wherein a highly capable cloud model generates precise training signals—comprising corrected outputs, preference pairs, and improved structural exemplars—to incrementally optimize the local MoE student. The implementation of this pipeline corresponds directly to the new Local AI Teaching (LAT) tracking metric, integrating as a parallel lane alongside KCP-4.0, which has been formally logged in the KCP\_SESSION\_CHECKPOINT.md governance document. The subsequent sections rigorously evaluate hardware constraints, distillation methodologies, and grammar interaction paradigms required to execute this deployment on a single consumer-grade 24GB VRAM GPU.

## ---

**Query 1: QLoRA Fine-Tuning Feasibility for Qwen3 MoE on 24GB VRAM**

### **Executive Summary**

The parameter-efficient fine-tuning (PEFT) of the Qwen3-30B-A3B Mixture-of-Experts model on a single 24GB RTX 4090 GPU is entirely feasible, provided strict memory management protocols are enforced. Utilizing the Unsloth framework with dynamic 4-bit quantization, the 30B MoE requires exactly 17.5GB of VRAM for QLoRA adaptation.1 Successful execution requires bypassing legacy GGUF-to-Safetensors reverse conversion scripts, compiling CUDA-accelerated dependencies specifically for Windows 11 MSVC environments, and strictly freezing the MoE router layer to prevent mode collapse during optimization.

### **Architectural Mechanics of Mixture-of-Experts Fine-Tuning**

The fundamental challenge of deploying a 30B parameter model on consumer hardware lies in memory economics. A standard dense 30B model loaded in 16-bit precision (FP16 or BF16) demands approximately 60GB of VRAM, drastically exceeding the 24GB constraint of the RTX 4090\. The Qwen3-30B-A3B architecture circumvents this computational density through sparsity. While the model encapsulates 30.5 billion total parameters, its routing mechanism activates only 3.3 billion parameters per token during the forward pass.4

However, during backpropagation and weight optimization, the optimizer states and gradients must still account for the entire parameter space. To resolve this, Quantized Low-Rank Adaptation (QLoRA) is mandatory. QLoRA mitigates memory overhead by projecting the parameter updates into low-rank matrices while maintaining the foundational model weights in a frozen, 4-bit quantized state (such as NormalFloat4). Advanced implementations of this methodology, particularly the "Dynamic 2.0" quantization schema engineered by the Unsloth framework, reduce the total VRAM footprint of the Qwen3-30B-A3B model to 17.5GB.1

This 17.5GB allocation leaves approximately 6.5GB of VRAM available for activations and gradient checkpoints. By leveraging Flash Attention 2 and strategically managing the per-device batch size, the remaining VRAM allows for context windows extending up to 8,192 tokens during training.1 This length is more than sufficient for processing extensive creative cRPG documents while simultaneously analyzing the complex interactions between the FA¹-FA⁴ axioms and the Egypto-Andean vocabularies.

### **Framework Comparison and Selection**

The selection of the training framework is the single most critical variable determining deployment success on a 24GB GPU. Standard open-source implementations frequently fail to optimize MoE gradient accumulation, resulting in immediate Out-of-Memory (OOM) exceptions.

| Framework Name | Qwen3 MoE Architectural Support | Windows 11 Native Compatibility | VRAM Requirement (30B MoE) | Deployment Suitability for 24GB Hardware |
| :---- | :---- | :---- | :---- | :---- |
| **Unsloth** | Native, featuring optimized router handling and dynamic 4-bit memory pooling.1 | Supported, requires MSVC 2022 and custom Triton compilation.6 | 17.5GB 2 | Optimal. The only framework guaranteeing execution well below the 24GB threshold. |
| **LLaMA-Factory** | Supported via generalized Hugging Face Transformers abstractions.9 | High, executes via standard Python environments with standard dependencies. | \~22.0GB \- 24.5GB | Marginal. Highly susceptible to OOM spikes during long-context gradient accumulation. |
| **Axolotl** | Partial, MoE support fluctuates across development branches. | Poor, predominantly Linux/WSL dependent for memory optimizations. | \> 24.0GB | Inviable. Exceeds hardware constraints during backward pass execution. |
| **vLLM / PEFT** | Experimental, specific issues tracking MoE LoRA integration.10 | Non-native, strictly requires WSL or Linux virtualization.11 | Variable | Inviable for unified native Windows deployment pipelines. |

The evidence overwhelmingly supports Unsloth as the mandatory framework for this pipeline. It explicitly advertises a 70% reduction in VRAM usage for the Qwen3 architecture and dramatically accelerates the fine-tuning process by bypassing standard Hugging Face bottlenecks.1

### **The Format Conversion Bottleneck: Safetensors vs. GGUF**

The local execution daemon relies on the llama-cpp-python engine, which strictly consumes the GGUF (GPT-Generated Unified Format) binary format. Specifically, the current deployment utilizes the qwen3-vl-30b-a3b-instruct-abliterated-q4-k-m.gguf file.12 A significant procedural error in many continuous learning pipelines involves attempting to dequantize this GGUF file back into Hugging Face Safetensors for fine-tuning.

Mathematical analysis of the llama.cpp quantization logic reveals that while dequantization (reverse conversion) of block-quantized types like Q4\_K\_M is technically defined in scripts such as quants.py, it is inherently a lossy transformation.13 Dequantizing a 4-bit block back into FP16 or BF16 tensors introduces severe quantization noise, fundamentally distorting the latent representations carefully established during the pre-training and abliteration phases. Furthermore, community-developed scripts designed for reverse conversion (e.g., gguf\_to\_safetensors) have officially ceased development and explicitly fail to parse the complex tensor hierarchies of modern MoE architectures like Qwen3.14

The optimal pipeline completely bypasses reverse conversion. The training system must fetch the pristine, unquantized (or Unsloth's native 4-bit dynamically quantized) Safetensors directly from the model repository (e.g., unsloth/Qwen3-30B-A3B).1 The LoRA adapter is trained on these pristine weights. Following optimization, Unsloth natively supports merging the low-rank adapters into the base weights and executing a forward conversion directly into the q4\_k\_m.gguf format via the model.save\_pretrained\_gguf() function.15 This unidirectional conversion paradigm ensures that quantization degradation occurs only once, strictly at the final deployment stage.

### **Expert Routing Dynamics and Mode Collapse Mitigation**

The MoE architecture introduces a structural complexity absent in dense models like the Qwen2.5-14B: the router network. The Qwen3-30B-A3B model utilizes a gating network that assigns probabilities to 128 distinct experts, activating the top 8 for any given token.5 When applying PEFT, the decision of whether to target the router layer with LoRA adapters is highly consequential.

Extensive empirical evaluations and benchmarking data strongly discourage fine-tuning the router layer.1 Applying LoRA to the router frequently destabilizes the probability distribution, leading to "mode collapse." In this state, the router begins disproportionately favoring a narrow subset of experts across all inputs, effectively crippling the model's sparsity benefits and reducing its reasoning capacity to that of a diminutive dense model.16 Consequently, Unsloth disables router fine-tuning by default.1

However, freezing the router does not freeze the model's ability to specialize. Methodologies aligned with Routing Manifold Alignment (RoMA) dictate that fine-tuning only the linear layers of the experts (q\_proj, k\_proj, v\_proj, o\_proj, gate\_proj, up\_proj, down\_proj) allows the model to alter the latent representations within the experts themselves.18 Because the output of one expert dictates the input to the next layer, the frozen router organically begins to route tokens differently based on the shifting activations.16

For the SFS theme system, this is a distinct advantage. As the experts are trained to differentiate the alchemical actualization (FA¹) of an Egyptian Ankh from the panoptic re-contextualization (FA²) of an Andean Quipu, the frozen router will naturally map these distinct semantic clusters to specialized, highly optimized expert pathways.18

### **Windows 11 Native Compilation Constraints**

The physical execution environment—Windows 11 with the Microsoft Visual C++ (MSVC) 18 toolchain, CMake 4.2.1, and Python 3.13—presents a hostile ecosystem for machine learning frameworks predominantly optimized for Linux. The primary compilation friction centers on bitsandbytes (required for 4-bit quantization) and memory-efficient attention libraries like xformers or flash-attn.

Python 3.13 is fully supported by the recent iterations of the unsloth library.8 The critical path requires meticulously aligning the CUDA 13.x drivers with the MSVC build tools. Building bitsandbytes natively on Windows requires invoking CMake with highly specific compiler flags dictating the compute capability of the RTX 4090 (-DCOMPUTE\_CAPABILITY=89).22 Given the fragility of compiling these libraries from source on Windows, utilizing pre-compiled Windows wheels provided by the community for bitsandbytes (e.g., version 0.43.0.dev0 compiled for Windows) is heavily recommended to avoid catastrophic build failures.24 Alternatively, isolating the Python environment via the uv package manager and strictly pulling from PyTorch's cu130 index provides the most stable foundation.8

### **Recommended Path and Implementation**

| Step | Action | Required Command / Configuration |
| :---- | :---- | :---- |
| **1\. Environment Isolation** | Utilize uv or Conda to isolate Python 3.13, preventing global dependency drift.8 | conda create \--name lat\_env python==3.13 \-y conda activate lat\_env |
| **2\. PyTorch CUDA Alignment** | Install PyTorch explicitly targeting CUDA 13.x to match the underlying driver architecture.8 | pip3 install torch torchvision torchaudio \--index-url https://download.pytorch.org/whl/cu130 |
| **3\. Framework Installation** | Deploy Unsloth and force recompilation of dependencies.1 | pip install \--upgrade \--force-reinstall \--no-cache-dir unsloth unsloth\_zoo |
| **4\. Model Initialization** | Load the dynamic 4-bit safetensors directly, bypassing GGUF reverse conversion.1 | FastModel.from\_pretrained("unsloth/Qwen3-30B-A3B", load\_in\_4bit=True) |
| **5\. PEFT Configuration** | Apply LoRA to expert linear layers exclusively; maintain frozen router.2 | target\_modules \= \["q\_proj", "k\_proj", "v\_proj", "o\_proj", "gate\_proj", "up\_proj", "down\_proj"\] |
| **6\. GGUF Export** | Merge LoRA weights and execute forward conversion to GGUF format for llama.cpp deployment.15 | model.save\_pretrained\_gguf("sfs\_model", tokenizer, quantization\_method="q4\_k\_m") |

### **Known Blockers and Systemic Workarounds**

| Blocker | Manifestation | Systemic Workaround |
| :---- | :---- | :---- |
| **MSVC Compilation Failure** | bitsandbytes or xformers fail to compile, citing missing headers or ABI mismatches.22 | Abandon source compilation. Fetch pre-compiled .whl files explicitly patched for Windows CUDA 13\.24 If irreconcilable, deploy the training script exclusively within a WSL2 container using GPU passthrough, while leaving the inference daemon native.11 |
| **MoE Mode Collapse** | The loss curve plateaus immediately, and the model outputs generic, repetitive tokens.16 | Audit the PEFT configuration to ensure the router or gate network of the MoE layer is entirely excluded from the target\_modules list.1 |
| **Quantization Degradation** | Re-quantizing the model leads to severe hallucination on the FA¹-FA⁴ axioms. | Ensure the pipeline does not utilize intermediate FP16 dumps. Use Unsloth's native save\_pretrained\_gguf which handles quantization mapping securely.15 |

## ---

**Query 2: Knowledge Distillation Pipelines — Cloud Teacher to Local Student**

### **Executive Summary**

The establishment of an Agentic Knowledge Distillation pipeline enables a highly capable cloud model (Claude) to act as an autonomous machine learning engineer, iteratively refining the local Qwen3-30B-A3B student model. By analyzing daily daemon outputs, generating corrected schema pairs, and employing semantic deduplication (SemDeDup), the pipeline can leverage Supervised Fine-Tuning (SFT) to enforce rigid Egypto-Andean structural mapping. To prevent catastrophic forgetting during nightly micro-LoRA updates, the architecture mandates a robust replay buffer mixing historical successes with general reasoning datasets, requiring as few as 100 highly curated examples per cycle to achieve convergence.

### **Distillation Mechanics and Synthetic Data Generation**

The transition from a static foundation model to a co-evolving specialist requires formalizing the teacher-student relationship. In this architecture, Claude does not transfer generalized intelligence; rather, it distills task-specific reasoning pathways and structural constraints. The problem outlined—hallucinated file references and inconsistent NSFW tier classifications—is a function of latent probability misalignment, which distillation corrects by providing mathematically perfect target vectors.

The distillation loop must operate autonomously. When the nightly daemon discovers creative cRPG files and processes them through the local MoE, it invariably records a percentage of outputs containing structural anomalies. The pipeline extracts these failure states and submits them to Claude alongside the pristine FileGenreProfile schema and the source text. Operating as an LLM-as-a-Judge, Claude evaluates the local model's output against the 50/50 balance mandate and the FA¹-FA⁴ axioms.26 Claude then generates a synthetically perfect correction, establishing the training signal.27

A critical vulnerability in synthetic data generation is "model collapse" or stylistic overfitting, where the local student becomes overly biased toward the syntactic quirks of the teacher model rather than learning the underlying logic. To counteract this, data curation algorithms are strictly necessary. Semantic Deduplication (SemDeDup) and Cluster-and-Retrieve (CaR) algorithms must be applied to the aggregated daily data.27 By clustering the corrections based on embedding vectors and filtering redundant examples, the pipeline ensures the training dataset maintains maximum diversity, covering edge cases across the entire spectrum of Character Archetypes (from Orackla to Spectra Chroma) without bloating the training time.27

### **Training Optimization Paradigms: SFT, DPO, and ORPO**

Translating the curated dataset into model weights requires selecting an optimal training paradigm. The algorithmic choice dictates memory overhead and final adherence to the SFS domain mandates.

* **Supervised Fine-Tuning (SFT):** SFT utilizes a traditional cross-entropy loss function. It forces the model to maximize the likelihood of generating the exact tokens present in Claude's corrected output. SFT is highly deterministic and excels at enforcing structured formatting, such as predicting exact JSON keys and nested arrays.29  
* **Direct Preference Optimization (DPO):** DPO aligns model behavior by utilizing pairwise comparisons—a "chosen" (Claude's output) and a "rejected" (the local model's hallucination) response. The algorithm modifies the policy to favor the chosen distribution.31 However, mathematical constraints render DPO largely inviable for this hardware constraint; DPO inherently requires loading both the policy model being trained and a frozen reference model into memory simultaneously, functionally doubling the VRAM requirement and instantly exceeding the 24GB RTX 4090 capacity.31  
* **Odds Ratio Preference Optimization (ORPO):** ORPO represents a paradigm shift in preference alignment. It merges the SFT cross-entropy loss with an odds-ratio penalty directed at the rejected response, completely eliminating the need for an external reference model.31 ORPO is highly memory efficient and excels at stylistic alignment, punishing the model for generating specific hallucinations (e.g., heavily weighting the Andean axis when the text demands an Egyptian balance).33

While ORPO is theoretically sophisticated, comprehensive benchmarks regarding structural extraction tasks demonstrate that high-quality SFT remains superior for rigid schema adherence.30 The deterministic nature of SFT ensures that the mandatory fields of the FileGenreProfile are explicitly learned. ORPO should only be deployed if the model exhibits persistent stylistic drift that SFT cannot correct.

### **Framework Comparison for Distillation Automation**

To manage the automated data curation and training execution, several toolkits offer specialized distillation abstractions.

| Distillation Framework | Automated Eval-Driven Loops | Windows 11 Native Compatibility | Architectural Focus | Systemic Suitability |
| :---- | :---- | :---- | :---- | :---- |
| **Distilabel (Argilla)** | Comprehensive. Native LLM-as-a-Judge integration and data synthesis pipelines.34 | High (Python-native execution). | Teacher-student pairwise generation.35 | High. Excellent for constructing the initial Claude-to-JSONL data pipeline. |
| **Unsloth (SFTTrainer)** | None. Strictly a training execution engine.36 | High (with MSVC dependencies).7 | Extreme VRAM optimization and fast PEFT.1 | Mandatory for the execution phase; must be paired with Distilabel or custom logic for data generation. |
| **distil-cli** | Integrated. Wraps data conversion, teacher evaluation, and packaging in a single CLI.28 | High. | Automated SLM alignment via cloud interfaces.28 | Moderate. Useful for prototyping, but may lack the granular control required for strict SFS schema enforcement. |

### **Dataset Sizing and Curriculum Development**

The hypothesis that LLMs require millions of examples to learn a new paradigm is mathematically flawed when applied to parameter-efficient task optimization. Research utilizing frameworks like DSPy and Reflective Prompt Evolution (GEPA) indicates that task-specific alignment—specifically teaching a model to utilize tools or map structural schemas accurately—can transition from a 12% baseline match rate to a 93% match rate using as few as 100 to 115 highly curated examples.27

Similarly, the ScrapeGraphAI-100k dataset analysis proves that for mapping hierarchical schemas, diversity vastly outweighs volume.37 The pipeline should implement a progressive curriculum:

1. **Bootstrapping:** The initial training run should utilize 150-200 pristine examples of NONE and SUGGESTIVE tier files, establishing the baseline Egypto-Andean 50/50 balance and fundamental JSON structure.  
2. **Complexity Scaling:** Subsequent nightly updates must shift focus to the EXPLICIT and EXTREME tiers, where dense, evocative language surrounding body-as-architecture aesthetics typically degrades the MoE's routing attention, causing the "Summary unavailable" error.  
3. **Convergence:** The cloud evaluator must continuously monitor the local model's success rate. When schema compliance plateaus above 98%, the training loop must automatically throttle to prevent overfitting.26

### **Mitigating Catastrophic Forgetting in Micro-LoRA Updates**

Executing nightly micro-LoRA updates introduces the severe risk of catastrophic forgetting. As the model parameters are continuously adjusted to perfectly conform to the FileGenreProfile schema, the underlying semantic comprehension algorithms degrade. The mathematical relationship between the number of parameter update steps and the decay of foundational pre-trained knowledge strictly follows a shifted power law.38 While LoRA naturally mitigates this by restricting updates to a low-rank subspace, it does not offer complete immunity.38

If the model forgets its pre-trained linguistic nuances, it will fail to comprehend the complex alchemical actualization (FA¹) metaphors required by the SFS theme system.40 To architecturally block catastrophic forgetting, the nightly daemon must construct a dynamic **Replay Buffer**.41 The nightly training dataset must never consist exclusively of the previous day's failures. A strict mathematical ratio must be enforced:

* **50% Curated Corrections:** The immediate synthetic data generated by Claude addressing recent failures.  
* **25% Historical Successes:** Previously verified extractions from the SFS domain to anchor the schema structure.  
* **25% General Reasoning Data:** Inclusions of chain-of-thought logic datasets (e.g., Open-Math or FineTome conversational data) to ensure the MoE experts retain their general analytic capabilities and do not collapse into rigid, brittle JSON templates.1

### **Recommended Path and Implementation**

| Step | Action | Execution Logic |
| :---- | :---- | :---- |
| **1\. Target Aggregation** | Daemon identifies local MoE failures (JSON syntax errors, hallucinated arrays). | Execute nightly Python script parsing llama-cpp logs. |
| **2\. Teacher Evaluation** | Claude API analyzes failures against SFS rules and generates ground-truth JSON.28 | Prompt Claude: "Evaluate the text against the FA¹-FA⁴ axioms. Correct the provided extraction failure into pristine JSON." |
| **3\. Replay Buffer Assembly** | Apply Semantic Deduplication to corrections and merge with historical/general data.27 | Combine new data (50%) with SFS archives (25%) and general logic data (25%) into a unified JSONL format. |
| **4\. Micro-LoRA Execution** | Invoke Unsloth SFTTrainer on the dataset for 1-2 epochs to ensure gradual gradient shifts.42 | trainer.train() with learning rate constrained to ![][image1] to prevent radical weight displacement.42 |
| **5\. Performance Evaluation** | Daemon validates new LoRA adapter against a held-out test suite.26 | If accuracy exceeds baseline, merge and deploy; if degraded, discard adapter update. |

### **Known Blockers and Systemic Workarounds**

| Blocker | Manifestation | Systemic Workaround |
| :---- | :---- | :---- |
| **Teacher Style Overfitting** | Local model begins hallucinating Claude's specific semantic idiosyncrasies (e.g., apologizing, excessive verbosity) inside the JSON arrays. | Strictly filter Claude's outputs before assembly. Enforce SemDeDup to ensure high variance in the training dataset.27 |
| **Catastrophic Forgetting** | Model achieves 100% JSON compliance but loses the ability to recognize subtle Quipu or Chakana references.40 | Increase the percentage of the Replay Buffer and lower the LoRA learning rate. Ensure general domain reasoning data is present in every nightly batch.40 |
| **DPO VRAM OOM** | Attempting DPO causes an immediate crash due to reference model memory allocation.31 | Abandon standard DPO. Rely exclusively on SFT for structural tasks 30, or pivot to ORPO if negative preference signaling is absolutely required.33 |

## ---

**Query 3: Structured Output Training and Grammar Enforcement Interaction**

### **Executive Summary**

The interaction between latent probability distributions and grammar-constrained decoding requires precise alignment to eradicate the 15% execution failure rate. While llama-cpp-python successfully utilizes Grammar-Based Next-Token Filtering (GBNF) to force JSON compliance, it clashes violently with the local model's internal logits if the model fundamentally attempts to output natural language. To achieve \>98% schema compliance, the training dataset must leverage a two-stage reasoning token strategy (the \<think\> block) embedded within SFT, teaching the model the deterministic pathway from creative text to the Pydantic FileGenreProfile schema, thereby aligning the model's natural logits with the strict GBNF filter.

### **The Latent Distortion of Constrained Decoding**

The current operational architecture utilizes the response\_format={"type": "json\_object", "schema":...} parameter within llama-cpp-python. This mechanism relies on Grammar-Based Next-Token Filtering (GBNF) or similar logits-masking algorithms. GBNF guarantees syntactic compliance by mathematically analyzing the allowed transitions within a Context-Free Grammar (CFG) and aggressively masking (setting to ![][image2]) the logits of any token that violates the schema.43

However, this mechanical enforcement does not alter the model's internal reasoning or semantic comprehension. If the Qwen3-30B MoE determines that the highest probability response to a dense, evocative text regarding "body-as-architecture aesthetics" is a natural language explanation (e.g., "The aesthetic themes present indicate an intersection of..."), the GBNF grammar will systematically block every natural language token because the schema demands a JSON opening brace { or a specific key like "nsfw\_tier".

When the model's primary predicted tokens are masked, it is forced to sample from the heavily suppressed, low-probability tail of its distribution. This continuous algorithmic coercion distorts the subsequent latent states.45 The model inevitably loses semantic coherence, resulting in the generation of syntactically valid JSON that contains logically hallucinated file references, incorrect classifications, or an abrupt collapse where the model generates an \<eos\> token prematurely, manifesting as the dreaded "Summary unavailable" error.45

Fine-tuning for schema compliance resolves this conflict by rewiring the model's foundational probabilities. When the LoRA adapter is active, the model's highest unmasked probability naturally aligns with the { token and the specific Pydantic keys. Consequently, GBNF transitions from a coercive, destructive filter into a passive safety net. The MoE and the grammar operate in perfect symbiosis, exponentially increasing stability.30

### **Framework Comparison for Constrained Decoding**

| Framework / Implementation | Constrained Decoding Methodology | Interaction with LoRA Alignment | Systemic Overhead |
| :---- | :---- | :---- | :---- |
| **llama.cpp GBNF** | Direct logits masking based on Context-Free Grammars compiled from JSON schemas.43 | Highly symbiotic if the model is fine-tuned to naturally predict the grammar structure.45 | Low latency, natively integrated into the existing llama-cpp-python daemon.43 |
| **Outlines / Guidance** | Finite State Machine (FSM) guided generation acting on the sampler. | Effective, but frequently requires specific model integrations that may lag behind custom MoE GGUF architectures. | Moderate to High, requires independent inference server logic. |
| **OpenAI JSON Mode** | Server-side grammar translation.43 | N/A (Cloud only). | N/A |

### **Pydantic Schema Formulation and the Reasoning Token Strategy**

To effectively train the Qwen3 MoE to output the complex FileGenreProfile schema, the training data must not merely consist of the raw input text paired with the final JSON object. Presenting only the final answer forces the model to execute complex cross-referential motif matching and aesthetic balance auditing entirely within its hidden states, which frequently exceeds the capacity of a 30B model on mature cRPG texts.

The optimal training formulation leverages a two-stage generative process within a single output sequence, a methodology highly effective in recent reasoning models.30 The prompt template must be engineered to instruct the model to produce a \<think\> block for overt natural language reasoning, immediately followed by an \<answer\> block containing the final JSON object.30

**Exemplar JSONL Training Structure for SFS Domain:**

JSON

{  
  "instruction": "Extract the SFS aesthetic profile from the provided text. Maintain the 50/50 Egypto-Andean balance mandate and apply FA¹-FA⁴ axioms. Output strictly conforming to the FileGenreProfile schema.",  
  "input": "",  
  "output": "\<think\>\\n1. Analyzing FA¹ Alchemical Actualization: The presence of the Ankh establishes the Egyptian baseline. The Quipu fulfills the Andean axis. Balance is established at 50/50.\\n2. Evaluating Character Archetype: Umeko is explicitly identified.\\n3. Classifying NsfwTier: The text contains explicit descriptions of body-as-architecture, mapping the NSFW tier to 'EXTREME'.\\n4. Synthesizing Schema: Mapping 'GenreTag' to valid enums. Setting 'GenreConfidence' to HIGH based on explicit motif presence.\\n\</think\>\\n\<answer\>\\n{\\n  \\"nsfw\_tier\\": \\"EXTREME\\",\\n  \\"aesthetic\_balance\\": {\\"egyptian\_ratio\\": 0.5, \\"andean\_ratio\\": 0.5},\\n  \\"motifs\\": \[\\"Ankh\\", \\"Quipu\\"\],\\n  \\"character\\": \\"Umeko\\"\\n}\\n\</answer\>"  
}

This SFT strategy is paramount. It permits the MoE experts to perform the required semantic analysis—evaluating the MILFOLOGICAL axioms and balancing the Egyptian/Andean vocabularies—in an unconstrained, natural language latent space. Only after the reasoning is explicitly resolved in the \<think\> block is the model required to transition into the strict JSON syntax of the \<answer\> block.30 This methodology directly addresses and eliminates the root cause of inconsistent classifications and hallucinations.30

### **Thresholds for High-Fidelity Schema Adherence**

Empirical studies on large-scale structural extraction datasets, such as the ScrapeGraphAI-100k analysis, demonstrate sharp, non-linear failure thresholds as schema depth and key count increase.37 For a schema of moderate complexity like FileGenreProfile (containing nested arrays like GenreTag and strict string enums like GenreCategory), the absolute volume of training data is significantly less critical than the variance and complete coverage of the schema constraints.37

To elevate the model's reliable compliance rate from the current 85% to the target \>98%, the training curriculum must expose the model to highly diverse permutations of the schema architecture:

* Instances where GenreConfidence is evaluated as LOW due to deliberately ambiguous text, forcing the model to explicitly justify the low confidence in the \<think\> block.  
* A comprehensive spread across all NsfwTier enums (NONE, SUGGESTIVE, EXPLICIT, EXTREME) to ensure the model does not disproportionately bias toward mature tags.  
* Complex edge cases where the 50/50 balance mandate is mathematically violated in the source text, requiring the model to explicitly flag an FA⁴ Ma'at Checksum failure within the reasoning trace before logging the imbalance in the final JSON output.

A meticulously curated dataset of 500 to 1,000 preference pairs, completely free of formatting errors and generated by Claude, is mathematically sufficient to permanently rewire the output distribution of the Qwen3-30B MoE.27 This finite data threshold allows the local agent to achieve \>98% native schema compliance, effectively eliminating the friction between the model's logits and the GBNF parser.

### **Recommended Path and Implementation**

| Step | Action | Execution Logic |
| :---- | :---- | :---- |
| **1\. Prompt Restructuring** | Inject the \<think\> and \<answer\> block requirement into the system prompt.30 | Provide reasoning inside \<think\>\</think\> tags, followed by the final JSON inside \<answer\>\</answer\> tags. |
| **2\. Data Formulation** | Ensure Claude generates training JSONL that strictly adheres to the two-stage \<think\> format.30 | The pipeline must parse and validate Claude's outputs to ensure the reasoning block logically connects to the final JSON keys. |
| **3\. Inference Configuration** | Maintain GBNF grammar enforcement in llama-cpp-python during inference.43 | response\_format={"type": "json\_object", "schema": FileGenreProfile.schema()} |
| **4\. Logit Alignment** | Execute LoRA SFT on the formatted dataset.30 | The LoRA weights will rapidly align the MoE's highest probabilities with the structural rules dictated by the Pydantic schema. |

### **Known Blockers and Systemic Workarounds**

| Blocker | Manifestation | Systemic Workaround |
| :---- | :---- | :---- |
| **Grammar Deadlocks** | The GBNF parser occasionally freezes during the transition from the \<think\> block to the JSON object due to unexpected whitespace tokenization.45 | Ensure the GBNF grammar explicitly permits flexible whitespace and newline characters (ws ::= \[ \\t\\n\]+) before the opening { of the JSON structure.44 |
| **Reasoning Truncation** | The model reaches its maximum token limit before completing the JSON object, corrupting the extraction. | Set the max\_tokens inference parameter to comfortably exceed the maximum expected length of both the reasoning trace and the JSON output combined, typically \>1024 tokens. |

## ---

**Synthesis and Deployment Execution**

The transition from a generalized inference engine to a highly specialized "warlock and familiar" architecture is structurally sound and mathematically feasible under the specified hardware constraints. By deploying an Agentic Knowledge Distillation loop, the Qwen3-30B-A3B MoE model will autonomously evolve, progressively internalizing the complex metaphysical mappings of the Egypto-Andean cosmology and the MILFOLOGICAL baseline.

### **The Nightly Daemon Workflow**

The successful implementation of this parallel Local AI Teaching (LAT) lane relies on a rigorous, automated lifecycle executed sequentially during off-peak processing hours:

1. **Inference and Flagging (Local Phase):** The static Qwen3 MoE (operating as q4\_k\_m.gguf via llama-cpp-python with GBNF enabled) executes daily extraction tasks on creative cRPG files. The daemon actively logs any generation that triggers a grammar conflict, hallucination, or "Summary unavailable" error.  
2. **Teacher Evaluation (Cloud Phase):** The daemon packages these failure states and forwards them to Claude via API. Claude evaluates the text against the FA¹-FA⁴ axioms and constructs a perfect \<think\> reasoning trace paired with a flawless JSON \<answer\>.  
3. **Curriculum Assembly (Local Phase):** The daemon aggregates Claude's corrections, applies Semantic Deduplication (SemDeDup) to ensure variance, and injects a 50% replay buffer consisting of historical SFS successes and general domain reasoning data to inoculate against catastrophic forgetting.  
4. **Parameter-Efficient Fine-Tuning (Local Phase):**  
   * The llama-cpp daemon is terminated to free VRAM.  
   * The Unsloth training script is invoked within an isolated Python 3.13 environment.  
   * Unsloth allocates exactly 17.5GB of VRAM to load the dynamic 4-bit unsloth/Qwen3-30B-A3B Safetensors from disk.  
   * A micro-LoRA Supervised Fine-Tuning (SFT) update is executed over 1 to 2 epochs, targeting only the linear expert layers while explicitly freezing the router mechanism.  
5. **Adapter Merging and Export:** Unsloth automatically merges the updated LoRA weights into the base parameter matrices and executes a direct forward conversion, saving the newly optimized model as a q4\_k\_m.gguf binary.  
6. **Redeployment:** The daemon unloads the training dependencies, reloads the newly compiled GGUF model into the llama-cpp-python engine, and prepares for the next operational cycle.

### **Strategic Implications for the SFS Theme System**

Through this constrained, parameter-efficient pipeline, the local agent systematically transcends its initial limitations. It ceases to fight against the rigid GBNF constraints, instead developing a native latent probability distribution that naturally predicts perfect JSON syntax. More critically, the MoE architecture's frozen router organically specializes, dedicating specific neural pathways to the nuanced distinction between the Egyptian and Andean aesthetic axes. This continuous distillation loop guarantees that the local execution environment will achieve and maintain the necessary \>98% compliance threshold, rendering the multi-agent development workspace fully autonomous, uncensored, and structurally infallible.

#### **Referanser**

1. unsloth.ai, brukt februar 24, 2026, [https://unsloth.ai/docs/models/qwen3-how-to-run-and-fine-tune](https://unsloth.ai/docs/models/qwen3-how-to-run-and-fine-tune)  
2. Run & Fine-tune Qwen3 \- Unsloth AI, brukt februar 24, 2026, [https://unsloth.ai/blog/qwen3](https://unsloth.ai/blog/qwen3)  
3. Qwen3 Fine-tuning now in Unsloth \- 2x faster with 70% less VRAM : r/LocalLLaMA \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1kd531l/qwen3\_finetuning\_now\_in\_unsloth\_2x\_faster\_with\_70/](https://www.reddit.com/r/LocalLLaMA/comments/1kd531l/qwen3_finetuning_now_in_unsloth_2x_faster_with_70/)  
4. Advice on running Qwen3-Coder-30B-A3B locally : r/LocalLLaMA \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1mi9i1g/advice\_on\_running\_qwen3coder30ba3b\_locally/](https://www.reddit.com/r/LocalLLaMA/comments/1mi9i1g/advice_on_running_qwen3coder30ba3b_locally/)  
5. Qwen/Qwen3-30B-A3B \- Hugging Face, brukt februar 24, 2026, [https://huggingface.co/Qwen/Qwen3-30B-A3B](https://huggingface.co/Qwen/Qwen3-30B-A3B)  
6. unslothai/unsloth: Fine-tuning & Reinforcement Learning for LLMs. Train OpenAI gpt-oss, DeepSeek, Qwen, Llama, Gemma, TTS 2x faster with 70% less VRAM. \- GitHub, brukt februar 24, 2026, [https://github.com/unslothai/unsloth](https://github.com/unslothai/unsloth)  
7. I got unsloth running in native windows. · Issue \#210 \- GitHub, brukt februar 24, 2026, [https://github.com/unslothai/unsloth/issues/210](https://github.com/unslothai/unsloth/issues/210)  
8. unsloth \- PyPI, brukt februar 24, 2026, [https://pypi.org/project/unsloth/](https://pypi.org/project/unsloth/)  
9. hiyouga/LlamaFactory: Unified Efficient Fine-Tuning of 100+ LLMs & VLMs (ACL 2024\) \- GitHub, brukt februar 24, 2026, [https://github.com/hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory)  
10. \[Feature\]: Qwen 3 MoE Lora adapter support. · Issue \#18120 · vllm-project/vllm \- GitHub, brukt februar 24, 2026, [https://github.com/vllm-project/vllm/issues/18120](https://github.com/vllm-project/vllm/issues/18120)  
11. Install Unsloth on Windows | Unsloth Documentation, brukt februar 24, 2026, [https://unsloth.ai/docs/get-started/install/windows-installation](https://unsloth.ai/docs/get-started/install/windows-installation)  
12. wangkanai/qwen3-vl-30b-a3b-instruct \- Hugging Face, brukt februar 24, 2026, [https://huggingface.co/wangkanai/qwen3-vl-30b-a3b-instruct](https://huggingface.co/wangkanai/qwen3-vl-30b-a3b-instruct)  
13. Converting GGUF to HF Safetensors · ggml-org llama.cpp ... \- GitHub, brukt februar 24, 2026, [https://github.com/ggml-org/llama.cpp/discussions/9410](https://github.com/ggml-org/llama.cpp/discussions/9410)  
14. purinnohito/gguf\_to\_safetensors: Script to convert from GGUF format to safetensors \- GitHub, brukt februar 24, 2026, [https://github.com/purinnohito/gguf\_to\_safetensors](https://github.com/purinnohito/gguf_to_safetensors)  
15. Saving to GGUF | Unsloth Documentation, brukt februar 24, 2026, [https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf)  
16. Fine-Tuning Qwen3-Coder-30B-A3B MoE: Expert Targeting vs Router Training in Unsloth, brukt februar 24, 2026, [https://www.reddit.com/r/unsloth/comments/1qawche/finetuning\_qwen3coder30ba3b\_moe\_expert\_targeting/](https://www.reddit.com/r/unsloth/comments/1qawche/finetuning_qwen3coder30ba3b_moe_expert_targeting/)  
17. Are MoE models harder to Fine-tune? : r/LocalLLaMA \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1pfwu8t/are\_moe\_models\_harder\_to\_finetune/](https://www.reddit.com/r/LocalLLaMA/comments/1pfwu8t/are_moe_models_harder_to_finetune/)  
18. Routing Manifold Alignment Improves Generalization of Mixture-of-Experts LLMs \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2511.07419v1](https://arxiv.org/html/2511.07419v1)  
19. Instal Unsloth via pip and uv, brukt februar 24, 2026, [https://unsloth.ai/docs/get-started/install/pip-install](https://unsloth.ai/docs/get-started/install/pip-install)  
20. Time to enable Python 3.13 support · Issue \#3109 · unslothai/unsloth \- GitHub, brukt februar 24, 2026, [https://github.com/unslothai/unsloth/issues/3109](https://github.com/unslothai/unsloth/issues/3109)  
21. Releases · unslothai/unsloth \- GitHub, brukt februar 24, 2026, [https://github.com/unslothai/unsloth/releases](https://github.com/unslothai/unsloth/releases)  
22. adding unsupported NVIDIA Maxwell/Pascal/Volta architectures when using CMake \>=3.23.0 with CUDA13 \#1779 \- GitHub, brukt februar 24, 2026, [https://github.com/bitsandbytes-foundation/bitsandbytes/issues/1779](https://github.com/bitsandbytes-foundation/bitsandbytes/issues/1779)  
23. \[AMD GPU installation\] The Rocm-bitsandbytes installation issues \#1608 \- GitHub, brukt februar 24, 2026, [https://github.com/bitsandbytes-foundation/bitsandbytes/issues/1608](https://github.com/bitsandbytes-foundation/bitsandbytes/issues/1608)  
24. Error installing on windows · Issue \#2309 · vllm-project/vllm \- GitHub, brukt februar 24, 2026, [https://github.com/vllm-project/vllm/issues/2309](https://github.com/vllm-project/vllm/issues/2309)  
25. Guide to use unsloth on windows \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/unsloth/comments/1qk1qy4/guide\_to\_use\_unsloth\_on\_windows/](https://www.reddit.com/r/unsloth/comments/1qk1qy4/guide_to_use_unsloth_on_windows/)  
26. arxiv.org, brukt februar 24, 2026, [https://arxiv.org/html/2602.10869v1](https://arxiv.org/html/2602.10869v1)  
27. Teaching Local Models to Call Tools Like Claude | Tomasz Tunguz, brukt februar 24, 2026, [https://tomtunguz.com/distilling-claude-into-local-models/](https://tomtunguz.com/distilling-claude-into-local-models/)  
28. Knowledge distillation with Claude as the interface: trained a 0.6B ..., brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1qiu6jo/knowledge\_distillation\_with\_claude\_as\_the/](https://www.reddit.com/r/LocalLLaMA/comments/1qiu6jo/knowledge_distillation_with_claude_as_the/)  
29. Fine tuning AI techniques: choosing between SFT, DPO, and RFT (with a practical DPO guide) | CleverX Blog, brukt februar 24, 2026, [https://cleverx.com/blog/fine-tuning-ai-techniques-choosing-between-sft-dpo-and-rft-with-a-practical-dpo-guide/](https://cleverx.com/blog/fine-tuning-ai-techniques-choosing-between-sft-dpo-and-rft-with-a-practical-dpo-guide/)  
30. Think Inside the JSON: Reinforcement Strategy for Strict LLM Schema Adherence \- arXiv, brukt februar 24, 2026, [https://arxiv.org/pdf/2502.14905](https://arxiv.org/pdf/2502.14905)  
31. From SFT to RL: Demystifying the Post-Training Pipeline for LLM-based Vulnerability Detection \- arXiv.org, brukt februar 24, 2026, [https://arxiv.org/html/2602.14012v1](https://arxiv.org/html/2602.14012v1)  
32. Fine-Tuning Techniques \- Choosing Between SFT, DPO, and RFT (With a Guide to DPO), brukt februar 24, 2026, [https://developers.openai.com/cookbook/examples/fine\_tuning\_direct\_preference\_optimization\_guide/](https://developers.openai.com/cookbook/examples/fine_tuning_direct_preference_optimization_guide/)  
33. ORPO Outperforms SFT+DPO | Train Phi-2 with ORPO | by Zain ul Abideen \- Medium, brukt februar 24, 2026, [https://medium.com/@zaiinn440/orpo-outperforms-sft-dpo-train-phi-2-with-orpo-3ee6bf18dbf2](https://medium.com/@zaiinn440/orpo-outperforms-sft-dpo-train-phi-2-with-orpo-3ee6bf18dbf2)  
34. Semi-Supervised Reward Modeling via Iterative Self-Training \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2409.06903v1](https://arxiv.org/html/2409.06903v1)  
35. Why Your AI Agents Need Memory and Expertise: Graph RAG \+ Fine-tuning | by Kruk Matias, brukt februar 24, 2026, [https://iotforce.medium.com/why-your-ai-agents-need-memory-and-expertise-graph-rag-fine-tuning-757163f4d0e2](https://iotforce.medium.com/why-your-ai-agents-need-memory-and-expertise-graph-rag-fine-tuning-757163f4d0e2)  
36. Fine-tuning LLMs Guide | Unsloth Documentation, brukt februar 24, 2026, [https://unsloth.ai/docs/get-started/fine-tuning-llms-guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide)  
37. ScrapeGraphAI-100k: A Large-Scale Dataset for LLM-Based Web Information Extraction, brukt februar 24, 2026, [https://arxiv.org/html/2602.15189v1](https://arxiv.org/html/2602.15189v1)  
38. Scaling Laws for Forgetting When Fine-Tuning Large Language Models \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2401.05605v1](https://arxiv.org/html/2401.05605v1)  
39. What I learned the hard way about catastrophic forgetting | by kirouane Ayoub \- Medium, brukt februar 24, 2026, [https://medium.com/@ayoubkirouane3/what-i-learned-the-hard-way-about-catastrophic-forgetting-0793878ff96b](https://medium.com/@ayoubkirouane3/what-i-learned-the-hard-way-about-catastrophic-forgetting-0793878ff96b)  
40. How to Alleviate Catastrophic Forgetting in LLMs Finetuning? Hierarchical Layer-Wise and Element-Wise Regularization \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2501.13669v2](https://arxiv.org/html/2501.13669v2)  
41. Avoiding Amnesia: Some Practical Guides to Mitigate Catastrophic Forgetting in LLMs Post-training | by Baicen Xiao | Medium, brukt februar 24, 2026, [https://medium.com/@baicenxiao/avoiding-amnesia-some-practical-guides-to-mitigate-catastrophic-forgetting-in-llms-post-training-6a23e4f064cb](https://medium.com/@baicenxiao/avoiding-amnesia-some-practical-guides-to-mitigate-catastrophic-forgetting-in-llms-post-training-6a23e4f064cb)  
42. Practical guide: fine-tuning Qwen3 with LoRA. KL-anchored SFT and β-tuned DPO | by Ivan, brukt februar 24, 2026, [https://blog.ivan.digital/finetuning-qwen3-with-lora-done-right-94d6343e1814](https://blog.ivan.digital/finetuning-qwen3-with-lora-done-right-94d6343e1814)  
43. Well, there goes one of the big advantages of open-source models... For a long t... | Hacker News, brukt februar 24, 2026, [https://news.ycombinator.com/item?id=41173787](https://news.ycombinator.com/item?id=41173787)  
44. llama.cpp/grammars/README.md · Steven10429/apply\_lora\_and\_quantize at main, brukt februar 24, 2026, [https://huggingface.co/spaces/Steven10429/apply\_lora\_and\_quantize/blob/main/llama.cpp/grammars/README.md](https://huggingface.co/spaces/Steven10429/apply_lora_and_quantize/blob/main/llama.cpp/grammars/README.md)  
45. PSA : Your JSON GBNF Grammar file is broken : r/LocalLLaMA \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1b78tdz/psa\_your\_json\_gbnf\_grammar\_file\_is\_broken/](https://www.reddit.com/r/LocalLLaMA/comments/1b78tdz/psa_your_json_gbnf_grammar_file_is_broken/)  
46. Sample Size Considerations for Fine-Tuning Large Language Models for Named Entity Recognition Tasks: Methodological Study \- JMIR AI, brukt februar 24, 2026, [https://ai.jmir.org/2024/1/e52095/](https://ai.jmir.org/2024/1/e52095/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD4AAAAUCAYAAADV9o4UAAABkElEQVR4AeyWu0pDQRCGVwVbEbS0EbQR30CwsfAG3jotbBRUUFARCwUFray08wHEWnwCK+3tLVVQUPASEkJIvj+wcBJyIWRJhpOE/8ts9uSE+ZmdOel0LfpqG2+1wrcrHql4N+teiLWiFe/A6SBcwz7EWt74Mi6f4AZWoB9iLW/8DpfTMA/fEHt54wmcfkEGatUoN+jEaDawLJDaZ4ydRTAlb7yepF64eQhOIGpepqfY2wC1EcGOQhjXaTnHUhesg8zL9DhrnYRt4juYUgjjMqQWOWMxAKcwB2twACZnRijj+HP/vB3DCFzBIZirNDnlFdK4jvcSv5qGW9gCHXuCPYUyLtOT2FsA9bkq/8dax92k+RDGZVrP/1WM7oJ6Wj2v497D5+Jpz1bz5Y1rKGkCH5FSH2gi7xBnoVrFhvnODGxCtKc17S/Y+wU91gjODN54ioze4B4mQM/eZ6L+1GSJlfTKxT1QpQkFUuUv2XkEU/LGP8jqoQRKWMOKS2WlXv4pe9W5JNc+wZS8cVNJNSKZHAAAAP//Gf/X0AAAAAZJREFUAwCjjj0pKk073QAAAABJRU5ErkJggg==>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACIAAAAXCAYAAABu8J3cAAABx0lEQVR4AeyTOyhGYRjHj/tlIRaKwf0SySIpjAYxKRmUQSiLlEwyuEXJhmQWg8HoUmKkkNjcMiEp5W7g9z+c0+edvs73DV86+v/e53le3/ue/3ne90RbEfLnGzEPwu+I3xGzA2b97+5IEm9YAW1QCslgKoGJPGiFMkgEV+HoSC67rcAIyMgBcQeUxxKjoAaWYRCyoAnGIAdshWpED+ljpylo/qWemA2L0Ah6exmVkW7qaZgA/b+DaMsxkkkll8FQx2/jQSpiUMv3iY72SNSNR+IczIK6JTNf5I7OSVIhHyyvRuK0GMrhDN7BkR62TdEP6ZAGa2Dqg4kbKAHXiM61i4lgGOV3zyDdM6gjOiLSPzqiuoViGALHPKktrdGlflLldES5F05ZVAD6agiuYsh0HKvEY+iBXgh8Xgq1Oqo93I4w50l3rNqFFtC90VuqAwvUnyAz7cRDUD5OrIJqGIYt0B4hG2Efa4khAy7hGjbgBDrhAfTGDcR50L3ZJK6D7oe+HFIrLEZe2UmfbyGxFhRniC8g6fLK0ACFjqOSqK90kvgGtgLPzJ4IYdAFvmK9uzm5KZm+YNIxSfqjcBr52dHj6BsxGxcxHfkGAAD//wQQAJwAAAAGSURBVAMACzFULzHMxsEAAAAASUVORK5CYII=>