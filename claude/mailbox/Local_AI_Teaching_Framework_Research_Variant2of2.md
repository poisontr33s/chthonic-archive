# **Local AI Distillation Framework: Engineering the Teacher-Student Pipeline for Domain-Specific Structured Extraction**

## **Executive Overview**

The deployment of a highly specialized, localized artificial intelligence framework for domain-specific structured extraction necessitates the intricate orchestration of cloud-based teacher models and resource-constrained student models. Operating within the strict confines of a single consumer-grade graphical processing unit (GPU) equipped with 24GB of Video Random Access Memory (VRAM) while running a Mixture-of-Experts (MoE) architecture introduces severe memory, computational, and architectural bottlenecks. Furthermore, establishing a continuous, automated distillation loop—where a superior, highly capable model generates synthetic training signals to iteratively update a local student model—requires advanced mitigation strategies against catastrophic forgetting and expert routing collapse.

The primary operational objective involves parsing creative role-playing game (cRPG) content characterized by mature, highly specific thematic elements. This encompasses a dual aesthetic vocabulary integrating an Egyptian axis (incorporating motifs such as the Ankh, Wedjat, Shen Ring, Scarab, Djed, Ma'at Feather, Tyet, and Uraeus derived from pre-3100 BCE sources) and an Andean axis (incorporating the Quipu, Chakana, Tocapu, Tinku, Pachakuti, Huaca, Nazca Lines, and Inti from pre-3000 BCE sources). The framework must enforce a strict 50/50 balance mandate between these axes while evaluating against a defined MILFological baseline featuring specific axioms (Alchemical Actualization, Panoptic Re-contextualization, WHR:MAX Optimization, and Ma'at Checksum) and archetypal character vocabularies (Orackla, Umeko, Sister Ferrum Scoriae, Claudine Sin'claire, and Spectra Chroma). The local student model must execute genre extraction, motif classification, aesthetic balance auditing, and multi-tiered content classification (ranging from none to extreme) to produce rigid JSON metadata.

The subsequent analysis indicates that fine-tuning a 30.5-billion parameter MoE model on 24GB VRAM is highly feasible when leveraging 4-bit Quantized Low-Rank Adaptation (QLoRA) paired with highly optimized custom Triton kernels. Furthermore, the combination of Supervised Fine-Tuning (SFT) and Inference-Time Constrained Decoding via context-free grammars creates a highly synergistic environment that drastically improves JSON schema compliance for these complex, nested data structures, enabling a robust, co-evolving nightly pipeline.

## **Query 1: QLoRA Fine-Tuning Feasibility for Qwen3 MoE on 24GB VRAM**

### **Executive Summary**

Fine-tuning the Qwen3-30B-A3B Mixture-of-Experts architecture on a single 24GB RTX 4090 is demonstrably feasible, requiring approximately 17.5GB of VRAM when utilizing 4-bit quantization and specialized memory-scheduling optimizations.1 The Unsloth framework provides the necessary Triton kernels to facilitate this, whereas standard HuggingFace or DeepSpeed pipelines will inevitably trigger memory exhaustion or require system RAM offloading that destroys throughput. The most critical architectural mandate for this process is freezing the MoE router layers during adaptation to prevent expert collapse and preserve the model's foundational capabilities.1

### **Framework Comparison for Mixture-of-Experts Fine-Tuning**

| Framework | Qwen3 MoE Support | Windows 11 Support | VRAM Requirement (30B MoE) | Latest Advancements / Notes |
| :---- | :---- | :---- | :---- | :---- |
| **Unsloth** | Native (Custom MoE Kernels) | Yes (Native via PyTorch & WSL2) | **\~17.5GB (4-bit QLoRA)** | 12x faster MoE training, dynamic 4-bit quantization, 8x context extension support.2 |
| **LLaMA-Factory** | Native | Yes | **Marginal** (\>24GB without aggressive offload) | Extensive graphical interface, robust algorithm support (GaLore, PiSSA, DoRA).5 |
| **Axolotl** | Yes | WSL2 Recommended | **No** (Fails without DeepSpeed CPU offload) | Excellent for dense models; heavily reliant on multi-GPU architectures for 30B+ MoE networks. |
| **MS-Swift** | Yes | Yes | **Marginal** (OOM prone on single 24GB) | Supports Megatron-LM MoE parallelization, engineered primarily for A100/H100 data center clusters.7 |

### **Hardware constraints and MoE Architectural Dynamics**

The Qwen3-30B-A3B model represents a significant architectural shift from traditional dense language models. It features a total parameter count of 30.5 billion, but relies on a sparse activation strategy, executing only 3.3 billion parameters during the forward pass of any single token.9 The internal structure consists of 48 layers with 128 fine-grained experts, where a routing mechanism selects the top 8 experts to process each token.9 This allows the model to maintain the broad knowledge representations of a massive 30B class model while operating with the inference latency and computational profile of a highly efficient 3B model.9

However, when transitioning from inference to Parameter-Efficient Fine-Tuning (PEFT), the VRAM consumption is dictated by the *total* parameter count, not the active parameter count. The PyTorch computational graph, optimizer states (such as AdamW moments), gradient checkpoints, and the LoRA adapter weights must account for all 30.5 billion parameters simultaneously in memory. A standard 16-bit full fine-tuning of this architecture would require upwards of 60GB to 80GB of VRAM.7 Implementing QLoRA (Quantized Low-Rank Adaptation) resolves this bottleneck. By utilizing the BitsAndBytes library to quantize the base model footprint to 4-bit precision (specifically NormalFloat4), the 30.5B static weights can be compressed to occupy roughly 16GB to 17.5GB of VRAM.2 The remaining 6.5GB of the RTX 4090's capacity is then allocated to the 16-bit LoRA adapter updates, the 8-bit paged optimizer states, and the activation memory required for the context window.

#### **The Expert Routing Conundrum and Specialization Loss**

Fine-tuning Mixture-of-Experts models introduces a unique mathematical failure mode absent in dense models: routing drift and expert collapse. Standard LoRA updates applied indiscriminately across all layers can disrupt the delicate gating network that routes tokens to specialized experts.3 The routing network calculates a probability distribution across the 128 experts; if the gradients from the fine-tuning data heavily favor specific pathways, the model experiences "routing collapse," where a disproportionate number of tokens are sent to a handful of "hot" experts, functionally degrading the MoE into a highly inefficient, bottlenecked dense model and destroying pre-trained specialization.13

To circumvent this architectural decay, the empirical consensus dictates freezing the router/gating layers entirely during Supervised Fine-Tuning. Advanced frameworks automatically disable router-layer fine-tuning by default.1 Instead, LoRA adapters should be injected exclusively into the attention projections (q\_proj, k\_proj, v\_proj, o\_proj) and the expert multi-layer perceptrons (gate\_proj, up\_proj, down\_proj).3 Recent methodologies, such as HELLoRA (Hot-Experts Layer-level Low-Rank Adaptation), suggest attaching LoRA modules only to the most frequently activated experts to further reduce parameter counts and stabilize routing throughput.16 Similarly, the SafeMoE methodology introduces a penalty loss to calculate the gap between the routing weights of the fine-tuned model and the initial aligned model to force the preservation of expert pathways.12 For the local distillation pipeline, relying on static, frozen routers while applying QLoRA strictly to the expert linear layers remains the most stable and accessible path.1

#### **Format Conversion Constraints: GGUF vs. Safetensors**

The existing local inference stack utilizes the GGUF format (Qwen3-30B-A3B-Instruct-abliterated-GGUF), which is highly optimized for llama.cpp CPU/GPU offloading. However, GGUF is an inherently quantized, serialized inference format that cannot be directly fine-tuned using standard PyTorch autograd mechanics.17 While reverse-conversion utilities such as gguf\_to\_safetensors.py exist to extract tensor architectures from a GGUF file, attempting to dequantize a mathematically destructive format like Q4\_K\_M back into FP16 (or utilizing it as a base for 4-bit QLoRA) yields significant gradient degradation and catastrophic loss of fidelity.18

The mathematically sound approach requires completely bypassing the existing GGUF file for the training phase. The distillation pipeline must download the unquantized Safetensors format of Qwen3-30B-A3B, load it into VRAM directly in 4-bit precision via BitsAndBytes, train the 16-bit LoRA adapters, merge the trained adapters into the base weights, and finally execute llama-cli llama-quantize to export the newly minted, updated model back to the GGUF format for production deployment.17

#### **The Abliteration Variable**

The specific base model targeted for this pipeline has undergone "abliteration"—a vector-rejection technique used to orthogonally project away the model's refusal directions, effectively bypassing safety filters to allow processing of explicit MILFological and mature thematic content.21 Research indicates that abliteration fundamentally alters the hidden representations and latent-space geometry of the model. Fine-tuning an abliterated model can be highly unstable; the model is prone to "healing" the abliteration if safety-aligned data is present in the training set, or suffering from accelerated coherence degradation due to the modified vector space.23

Consequently, to maintain the uncensored nature of the model while adapting it for JSON extraction, the learning rate for the LoRA adapter must be kept exceptionally low (e.g., 2e-5 to 5e-6), and the rank (r) should be heavily constrained (e.g., r=8 or r=16) to prevent overwriting the orthogonal projections applied during the initial abliteration process.6

### **Windows 11 and MSVC Build Chain Considerations**

Operating strictly on a Windows 11 host with MSVC 18 and a Vulkan SDK introduces specific environment considerations. Modern large language model training relies heavily on OpenAI's Triton language to compile custom, fused CUDA kernels on the fly, which drastically accelerates attention mechanisms and minimizes memory fragmentation.3 Native Windows support for Triton has historically been poor, often resulting in ModuleNotFoundError or MSVC compilation failures during runtime.26

While some training libraries have recently introduced Windows support via pre-compiled .whl files, the most stable path for automated, unattended nightly operations remains the Windows Subsystem for Linux (WSL2).28 WSL2 allows for direct hardware pass-through of the RTX 4090 while providing a native Ubuntu Linux environment, guaranteeing seamless Triton kernel compilation and eliminating the dependency conflicts inherent in native Windows PyTorch compilations.28

### **Recommended Path**

1. **Environment Initialization:** Establish a WSL2 (Ubuntu 22.04+) environment to guarantee Triton compilation stability and bypass MSVC dependency conflicts.28  
2. **Toolchain Installation:**  
   Bash  
   sudo apt update && sudo apt install build-essential cmake ccache ninja-build pkg-config libgoogle-perftools-dev \-y  
   pip install torch torchvision torchaudio \--index-url https://download.pytorch.org/whl/cu121  
   pip install "unsloth\[colab-new\] @ git+https://github.com/unslothai/unsloth.git"  
   pip install \--no-deps trl peft accelerate bitsandbytes

3. **Training Configuration:** Implement Unsloth's FastLanguageModel targeting the HuggingFace Safetensors repository, utilizing a batch size of 1 with 4 to 8 gradient accumulation steps. Enable gradient checkpointing to enforce a strict memory ceiling below the 24GB hardware limit.15 Ensure full\_finetuning=False and the MoE router layers are frozen.2  
4. **Post-Training Export:** Following the nightly distillation update, merge the LoRA weights into the base model and utilize llama.cpp's convert\_hf\_to\_gguf.py followed by llama-quantize to output the new production Q4\_K\_M GGUF.17

### **Known Blockers and Workarounds**

* **Blocker:** Out of Memory (OOM) exceptions during the backward pass when the MoE routing mechanisms generate sudden memory spikes.  
* **Workaround:** Implement aggressive gradient checkpointing, restrict max\_seq\_length to 2048 or 4096 (do not attempt to extend the context window during the LoRA update), and utilize the paged\_adamw\_8bit optimizer to dynamically offload optimizer states to system RAM during computation spikes.1  
* **Blocker:** DeepSpeed ZeRO-3 incompatibility. Frameworks like LLaMA-Factory default to ZeRO-3 partitioning, which distributes model parameters across GPUs. This fundamentally breaks gradient flow when LoRA adapters are added to an MoE architecture, resulting in RuntimeError regarding missing gradients.31  
* **Workaround:** Given the single-GPU architecture, DeepSpeed must be avoided entirely. Rely exclusively on Unsloth's native memory management and BitsAndBytes 4-bit quantization, which maintain parameters locally.2

## ---

**Query 2: Knowledge Distillation Pipelines — Cloud Teacher to Local Student**

### **Executive Summary**

Establishing a closed-loop "Agentic Knowledge Distillation" pipeline requires utilizing the Claude API as the teacher to evaluate, correct, and synthesize task-specific JSON outputs from the local Qwen3 student.32 To conduct automated nightly micro-LoRA updates without inducing catastrophic forgetting of the complex cRPG and Egypto-Andean domain knowledge, the pipeline must implement a Prioritized Experience Replay buffer and utilize regularization algorithms to protect previously learned latent representations.34 Supervised Fine-Tuning (SFT) remains the most data-efficient paradigm for strict schema compliance, requiring a tightly curated dataset to align the local model's token probabilities.36

### **Knowledge Distillation Framework Comparison**

| Framework | Automated Eval-Driven Loops | Windows / Single GPU Support | MoE Architecture Support | Primary Optimization Paradigm |
| :---- | :---- | :---- | :---- | :---- |
| **Distilabel (Argilla)** | **Excellent** (Built-in LLM-as-a-judge & data generation) | Yes (Python API) | Yes (via HuggingFace PEFT) | Multi-teacher synthesis, complex data curation, AI feedback routing.37 |
| **Distil-CLI (Distil Labs)** | Very Good (Claude integration) | Yes | Yes (Automated GGUF export) | Conversational SLM creation, zero-configuration distillation pipelines.38 |
| **NeMo Curator / Designer** | Good | Linux/WSL2 Required | Yes | Massive scale synthetic data generation, enterprise pipeline processing.40 |
| **OpenRLHF** | Average (Complex setup) | Linux/WSL2 Required | Yes | RLHF, DPO, GRPO heavy; excessively complex for fundamental JSON SFT. |

### **Synthetic Data Generation and Diversity Strategies**

The fundamental risk of transferring knowledge from a highly capable cloud model (Claude) to a 3B-active parameter local model is "model collapse" and stylistic overfitting. If the local model is trained exclusively on Claude's corrected outputs without variation, it will learn to mimic Claude's verbosity, tonal markers, and specific linguistic quirks rather than the underlying structured extraction logic.36 The student model will absorb the teacher's style rather than the substance of the SFS and MILFological theme extractions.

To generate high-quality JSONL training data, the pipeline must employ Adaptive Data Selection and Instruction Mutation:

1. **Mutation Algorithms:** Frameworks like DSPy and GEPA (Reflective Prompt Evolution) systematically simulate instruction variations to ensure the local model sees the identical schema requested in hundreds of different linguistic formulations.42 This forces the model to learn the invariant data extraction task rather than memorizing a specific prompt template.  
2. **Contextual Diversity:** The daemon must sample evenly across the SFS-MILF domain. If the daemon only pulls "Andean" motif texts (focusing on Quipu and Chakana) for a week, the model will rapidly unlearn the "Egyptian" axis (Ankh, Wedjat) due to domain drift.40 The synthetic data generation must be seeded across all aesthetic vocabularies evenly.  
3. **Teacher Evaluation (LLM-as-a-Judge):** Claude should be prompted to score the local model's output via an evaluation rubric before correcting it.37 Only examples where the local model fails, and Claude corrects it perfectly (scoring 100% on the JSON schema compliance and motif extraction), should be injected into the training queue.

### **Dataset Sizing and Training Paradigms**

For the explicit task of structured JSON extraction—mapping unstructured cRPG text into the predefined FileGenreProfile schema—the model does not require generalized "intelligence" improvements; it strictly requires syntax alignment and logical mapping.33

While Direct Preference Optimization (DPO), Odds Ratio Preference Optimization (ORPO), and Generative Reward Optimization (GRPO) represent the state-of-the-art for reasoning, mathematics, and conversational behavior, **Supervised Fine-Tuning (SFT)** remains the most data-efficient and reliable paradigm for strict schema compliance.36 SFT utilizes cross-entropy loss to force the model's token probabilities directly toward the desired JSON keys, enums, and structural markers. Distillation based on soft-targets (teacher logits) is effective, but for JSON formatting, hard-label SFT from teacher-generated outputs provides the necessary rigidity.36

**Dataset Sizing:**

* **Prompt Optimization (Few-Shot):** 15 to 50 highly curated examples are sufficient to align the initial prompt logic via algorithms like DSPy.42  
* **SFT Convergence:** To establish highly reliable schema compliance (exceeding 98% validity), research indicates a heavily curated dataset of 1,000 to 3,000 diverse examples is the minimum effective threshold.46 Beyond 5,000 examples, returns diminish rapidly for a static, invariant schema.

### **Incremental Training and Catastrophic Forgetting**

Executing automated "nightly micro-LoRA updates" (e.g., integrating 50-100 new examples gathered by the daemon's daily run) introduces the severe architectural risk of Catastrophic Forgetting. In neural networks, catastrophic forgetting occurs when learning a new task or processing a shifted data distribution causes an abrupt, dramatic performance drop on previously learned tasks. Mechanistically, this happens because the new gradients overwrite the shared weight configurations in the low-rank matrices that supported the older skills.48 In a nightly loop, a batch of exclusively "Extreme/Explicit" NSFW texts might entirely overwrite the model's ability to classify "None-tier" texts correctly, or tuning heavily on Claudine Sin'claire archetypes might erase the Orackla aesthetic vocabulary.

#### **Mitigation Strategies**

1. **Experience Replay Buffer:** The most robust and empirically proven method to prevent forgetting in continuous learning pipelines is Experience Replay.34 The nightly training batch must *never* consist solely of the new 50-100 examples. The pipeline must maintain a curated "Golden Dataset" (the replay buffer) covering all domain axes, SFS archetypes, and NSFW tiers evenly. Every nightly training batch must be constructed by sampling a minority of new data (e.g., 25%) and a majority of randomly sampled data from the Golden Replay Buffer (e.g., 75%) to anchor the previously learned representations.34  
2. **Orthogonal Projection LoRA (OPLoRA):** Advanced regularization techniques like OPLoRA mitigate forgetting by decomposing the frozen pre-trained weights via Singular Value Decomposition (SVD) and mathematically constraining the new LoRA parameter updates to lie entirely within the orthogonal complement of the pre-trained knowledge's dominant directions. This guarantees that the nightly updates do not mathematically interfere with the model's core representations of grammar and reasoning.52  
3. **Weight-Space Regularization (LaLoRA / O-LoRA):** Applying a Laplace approximation to the LoRA weights estimates the model's confidence in each parameter, constraining updates in high-curvature directions to preserve prior knowledge while allowing the new JSON extraction logic to embed safely in low-curvature, unutilized dimensions.53

### **Curriculum Design**

Curriculum learning theory dictates that neural networks adapt more efficiently and achieve deeper convergence when presented with a gradually increasing level of difficulty, rather than a randomized distribution of complex tasks. The distillation pipeline should explicitly structure the training sequence logically:

* **Phase 1 (Foundational):** Train exclusively on clean, clearly defined "None" tier texts with overt aesthetic vocabularies and explicit Egyptian/Andean markers.  
* **Phase 2 (Intermediate):** Introduce "Suggestive" texts and cross-referential motif matching, requiring the model to balance the 50/50 SFS aesthetic mandate.  
* **Phase 3 (Advanced):** Expose the model to "Explicit/Extreme" texts involving deep metaphor, body-as-architecture themes, and obscure FA¹-FA⁴ MILFological interpolations.

### **Recommended Path**

1. **Distilabel Integration:** Implement a Python daemon utilizing the distilabel library. The daemon routes failed or low-confidence local extractions to the Claude API. Claude acts as a TextGeneration and evaluation task to output the perfected JSON metadata.37  
2. **Replay Buffer Construction:** Store Claude's verified outputs in a local SQLite database, tagging each entry by domain axis (Egyptian/Andean), character archetype, and NsfwTier to ensure balanced sampling.  
3. **Nightly Script Execution:** A scheduled task aggregates the 50 new samples, retrieves 150 stratified random samples from the Replay Buffer, formats them into a strictly structured {"instruction": "...", "output": "{...}"} JSONL file, and triggers the Unsloth SFT script.51

### **Known Blockers and Workarounds**

* **Blocker:** Overfitting on the micro-batch, causing the model to collapse into predicting only the specific characters or tropes present in the previous day's data acquisition run.  
* **Workaround:** Implement strict Early Stopping mechanisms. Track a hold-out validation set of 200 highly diverse examples during the nightly run. If validation loss increases while training loss decreases, abort the update, discard the adapter, and wait for a larger data accumulation.43

## ---

**Query 3: Structured Output Training \+ Grammar Enforcement Interaction**

### **Executive Summary**

When targeting absolute JSON schema reliability (exceeding 98% validity), Supervised Fine-Tuning (SFT) and Grammar-Based Constrained Decoding (GBNF) are not adversarial techniques; they are fundamentally complementary and synergistic.57 Relying solely on GBNF grammar at inference forces the model into syntax compliance but can cause severe logical hallucinations if the model's internal token probabilities favor unstructured text. Conversely, SFT aligns the model's internal probability distributions with the required schema logic, drastically reducing the instances where the GBNF engine must "force" the sampling, thereby optimizing both inference speed and cognitive accuracy.57

### **Methodology Comparison**

| Methodology | Schema Adherence | Logical Accuracy | Latency Profile | Implementation Complexity |
| :---- | :---- | :---- | :---- | :---- |
| **Pure Prompt Engineering** | Low (\~85%) | High | Fast | Low |
| **Pure GBNF Grammar** | 100% | Medium (Prone to logical collapse) | Slower (Logit masking overhead) 59 | Medium |
| **Pure SFT** | High (\~95%) | High | Fast | High (Requires pipeline) |
| **SFT \+ GBNF Grammar** | **100%** | **Highest** | **Fastest** (Masks rarely triggered) | Highest |

### **The Interaction Dynamics of SFT and Constrained Decoding**

To comprehend why SFT and constrained generation do not "fight" each other, one must examine the mechanics of autoregressive token generation. The llama-cpp-python engine enforces JSON schemas using context-free grammars (GBNF). At every token generation step, the engine evaluates the model's predicted logit distribution. Any token that would violate the specified JSON schema (for instance, generating alphabetical text when a bracket \`

If a base model is un-tuned, its internal state might heavily favor generating conversational filler (e.g., "Here is the extracted summary based on the SFS theme:"). The GBNF engine masks out all those alphabetical letters, forcing the model to select {. Because the model's internal hidden states and self-attention matrices were actively preparing for conversational text, forcing a { fundamentally disrupts its context. This dissonance causes subsequent generations to become logically disjointed, resulting in a syntactically valid JSON that is semantically hallucinatory.57

By fine-tuning the model via SFT to natively output raw JSON without conversational wrappers, the model's highest-probability tokens will naturally align with the GBNF grammar. The grammar enforcement then acts merely as a lightweight, invisible "guardrail," catching the rare 1-2% of instances where the model attempts to hallucinate a broken enum or omit a trailing quote, rather than constantly wrestling with the model's core logic.57 This synergy prevents the degradation of the model's reasoning capabilities during extraction.

### **Schema Training Data Formatting**

The training JSONL data must reflect the exact string representations the model will emit during inference. While Qwen3-Instruct models are inherently trained with specific chat templates and complex function-calling capabilities, utilizing an agentic tool-use format for a targeted, single-shot extraction task introduces unnecessary overhead.9 It is vastly superior to train the model to output the raw JSON payload directly as its conversational response.

#### **Pydantic Integration**

The Pydantic library serves as the optimal bridge between Python application logic and LLM training data. The specific FileGenreProfile schema, encompassing the nested GenreTag arrays and the enums for NsfwTier, GenreCategory, and GenreConfidence, can be dynamically converted to a strict, compliant JSON Schema utilizing Pydantic's BaseModel.model\_json\_schema() method.62

The training JSONL dataset should be formatted precisely to match the Qwen ChatML template:

JSON

{  
  "messages":"  
    },  
    {  
      "role": "assistant",  
      "content": "{\\"NsfwTier\\": \\"EXPLICIT\\", \\"GenreCategory\\": \\"MYTHIC\_FANTASY\\", \\"GenreTags\\": \[{\\"tag\\": \\"Alchemical Actualization\\", \\"confidence\\": \\"HIGH\\"}\], \\"Motifs\\": {\\"Egyptian\\": \[\\"Ankh\\", \\"Uraeus\\"\], \\"Andean\\": \[\\"Chakana\\"\]}}"  
    }  
  \]  
}

By ensuring the content of the assistant's role is a perfectly escaped, valid JSON string containing the exact Enums and nested arrays defined in the Pydantic model, the MoE layers learn the deep statistical correlations between the unstructured input text and the strict, nested schema structures.63

#### **Schema Diversity vs Schema Rigidity**

For this highly specific use case, the model learns best from seeing **many variations of input text mapping to the identical, rigid schema**. Introducing diverse, rotating schemas during the distillation process dilutes the model's focus and consumes valuable parameter capacity.46 Because the goal is to achieve \>98% compliance on the FileGenreProfile schema specifically, every single training row in the dataset should utilize that exact schema definition in the system prompt. The required dataset diversity must come entirely from the variance in the *input texts* (SFS archetypes, varying NSFW tiers, conflicting motifs) and the varied *values* populated within the JSON, not from the structural definition of the JSON itself.40

### **Recommended Path**

1. **Schema Generation:** Define the FileGenreProfile utilizing pydantic.BaseModel. Export the schema definition using .model\_json\_schema() and embed this deterministic string directly into the system prompt of the training data.62  
2. **Dataset Creation:** The Claude teacher model generates the target output. Serialize it using model.model\_dump\_json(). Format the prompt-response pair into the ChatML JSONL format required by Unsloth.  
3. **Inference Execution:** Load the newly SFT-trained LoRA adapter using llama-cpp-python. Pass the exact same Pydantic schema to the inference engine utilizing the built-in constrained decoding parameters:  
   Python  
   response \= llm.create\_chat\_completion(  
       messages=messages,  
       response\_format={  
           "type": "json\_object",  
           "schema": FileGenreProfile.model\_json\_schema()  
       }  
   )

   This configuration guarantees 100% syntactical validity via the underlying GBNF engine, while the SFT guarantees the semantic accuracy and motif classification.57

### **Known Blockers and Workarounds**

* **Blocker:** GBNF grammar compilation overhead. Highly nested JSON schemas with multiple Enums and complex arrays can result in massive finite-state machines, causing llama-cpp-python to freeze or take significant computational time to calculate the grammar graph prior to generating the first token.58  
* **Workaround:** Ensure the JSON schema is tightly bounded. Do not use open-ended recursive definitions. Pre-compile the grammar string utilizing llama.cpp's json-schema-to-grammar.py utility offline and cache the result, passing the raw GBNF string to LlamaGrammar.from\_string() rather than compiling the Pydantic schema dynamically on every single daemon request.58  
* **Blocker:** Invalid JSON due to token truncation. If the model exceeds the predefined max\_new\_tokens limit during generation, the JSON output will be cut off prematurely, breaking the grammar constraint and causing a catastrophic parsing failure in the Python application.66  
* **Workaround:** Always assign a sufficiently high max\_tokens ceiling (e.g., 2048 or 4096\) in the inference call, as the grammar engine relies entirely on the model successfully generating the final closing } and subsequent End-Of-Sequence (EOS) token to gracefully terminate the sequence state machine.66

#### **Referanser**

1. Unsloth \- Qwen \- Read the Docs, brukt februar 24, 2026, [https://qwen.readthedocs.io/en/latest/training/unsloth.html](https://qwen.readthedocs.io/en/latest/training/unsloth.html)  
2. Qwen3 Fine-tuning now in Unsloth \- 2x faster with 70% less VRAM : r/LocalLLaMA \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1kd531l/qwen3\_finetuning\_now\_in\_unsloth\_2x\_faster\_with\_70/](https://www.reddit.com/r/LocalLLaMA/comments/1kd531l/qwen3_finetuning_now_in_unsloth_2x_faster_with_70/)  
3. Fine-tune MoE Models 12x Faster with Unsloth, brukt februar 24, 2026, [https://unsloth.ai/docs/new/faster-moe](https://unsloth.ai/docs/new/faster-moe)  
4. Run & Fine-tune Qwen3 \- Unsloth AI, brukt februar 24, 2026, [https://unsloth.ai/blog/qwen3](https://unsloth.ai/blog/qwen3)  
5. hiyouga/LlamaFactory: Unified Efficient Fine-Tuning of 100+ LLMs & VLMs (ACL 2024\) \- GitHub, brukt februar 24, 2026, [https://github.com/hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory)  
6. LLaMA-Factory \- Qwen, brukt februar 24, 2026, [https://qwen.readthedocs.io/en/latest/training/llama\_factory.html](https://qwen.readthedocs.io/en/latest/training/llama_factory.html)  
7. \[Fine-tuning\] Qwen3-MoE Megatron Training Implementation and Best Practices \#1301 \- GitHub, brukt februar 24, 2026, [https://github.com/QwenLM/Qwen3/discussions/1301](https://github.com/QwenLM/Qwen3/discussions/1301)  
8. Which training framework is the best for fine-tuning the Qwen3 30B MoE model? \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1lulbd7/which\_training\_framework\_is\_the\_best\_for/](https://www.reddit.com/r/LocalLLaMA/comments/1lulbd7/which_training_framework_is_the_best_for/)  
9. Qwen/Qwen3-30B-A3B \- Hugging Face, brukt februar 24, 2026, [https://huggingface.co/Qwen/Qwen3-30B-A3B](https://huggingface.co/Qwen/Qwen3-30B-A3B)  
10. Qwen3-30B-A3B: Specifications and GPU VRAM Requirements \- ApX Machine Learning, brukt februar 24, 2026, [https://apxml.com/models/qwen3-30b-a3b](https://apxml.com/models/qwen3-30b-a3b)  
11. OPLoRA: Orthogonal Projection LoRA Prevents Catastrophic Forgetting during Parameter-Efficient Fine-Tuning \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2510.13003v2](https://arxiv.org/html/2510.13003v2)  
12. Defending MoE LLMs against Harmful Fine-Tuning via Safety Routing Alignment \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2509.22745v1](https://arxiv.org/html/2509.22745v1)  
13. NeurIPS Poster Advancing Expert Specialization for Better MoE, brukt februar 24, 2026, [https://neurips.cc/virtual/2025/poster/116506](https://neurips.cc/virtual/2025/poster/116506)  
14. Are MoE models harder to Fine-tune? : r/LocalLLaMA \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1pfwu8t/are\_moe\_models\_harder\_to\_finetune/](https://www.reddit.com/r/LocalLLaMA/comments/1pfwu8t/are_moe_models_harder_to_finetune/)  
15. Findings from LoRA Finetuning for Qwen3 : r/LocalLLaMA \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1kkl39r/findings\_from\_lora\_finetuning\_for\_qwen3/](https://www.reddit.com/r/LocalLLaMA/comments/1kkl39r/findings_from_lora_finetuning_for_qwen3/)  
16. HELLoRA: Hot Experts Layer-level Low-Rank Adaptation for MOE Model | OpenReview, brukt februar 24, 2026, [https://openreview.net/forum?id=CsHahbRAFZ](https://openreview.net/forum?id=CsHahbRAFZ)  
17. Saving to GGUF | Unsloth Documentation, brukt februar 24, 2026, [https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf)  
18. Convert Safetensors HF Model to GGUF for Llama.cpp \- YouTube, brukt februar 24, 2026, [https://www.youtube.com/watch?v=wRB8IXuW90g](https://www.youtube.com/watch?v=wRB8IXuW90g)  
19. purinnohito/gguf\_to\_safetensors: Script to convert from GGUF format to safetensors \- GitHub, brukt februar 24, 2026, [https://github.com/purinnohito/gguf\_to\_safetensors](https://github.com/purinnohito/gguf_to_safetensors)  
20. The easiest way to convert a model to GGUF and Quantize | by Damien Berezenko | Medium, brukt februar 24, 2026, [https://medium.com/@qdrddr/the-easiest-way-to-convert-a-model-to-gguf-and-quantize-91016e97c987](https://medium.com/@qdrddr/the-easiest-way-to-convert-a-model-to-gguf-and-quantize-91016e97c987)  
21. An Embarrassingly Simple Defense Against LLM Abliteration Attacks \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2505.19056v2](https://arxiv.org/html/2505.19056v2)  
22. wangkanai/qwen3-vl-30b-a3b-instruct \- Hugging Face, brukt februar 24, 2026, [https://huggingface.co/wangkanai/qwen3-vl-30b-a3b-instruct](https://huggingface.co/wangkanai/qwen3-vl-30b-a3b-instruct)  
23. Insights on performance degradation for Qwen3 30B3A? : r/LocalLLaMA \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1ncn4sa/insights\_on\_performance\_degradation\_for\_qwen3/](https://www.reddit.com/r/LocalLLaMA/comments/1ncn4sa/insights_on_performance_degradation_for_qwen3/)  
24. An Embarrassingly Simple Defense Against LLM Abliteration Attacks \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2505.19056v1](https://arxiv.org/html/2505.19056v1)  
25. Development repository for the Triton language and compiler \- GitHub, brukt februar 24, 2026, [https://github.com/triton-lang/triton](https://github.com/triton-lang/triton)  
26. Direct Windows support for Unsloth\! · unslothai unsloth · Discussion ..., brukt februar 24, 2026, [https://github.com/unslothai/unsloth/discussions/1849](https://github.com/unslothai/unsloth/discussions/1849)  
27. Stop Struggling: Quick & Easy Triton Installation on Windows \- YouTube, brukt februar 24, 2026, [https://www.youtube.com/watch?v=Ghx7p2pdvoo](https://www.youtube.com/watch?v=Ghx7p2pdvoo)  
28. Guide to use unsloth on windows \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/unsloth/comments/1qk1qy4/guide\_to\_use\_unsloth\_on\_windows/](https://www.reddit.com/r/unsloth/comments/1qk1qy4/guide_to_use_unsloth_on_windows/)  
29. Qwen3‑Next‑80B‑A3B‑Instruct (FP8) on Windows 11 WSL2 \+ vLLM \+ Docker (Blackwell) : r/LocalLLaMA \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1nh9pc9/qwen3next80ba3binstruct\_fp8\_on\_windows\_11\_wsl2/](https://www.reddit.com/r/LocalLLaMA/comments/1nh9pc9/qwen3next80ba3binstruct_fp8_on_windows_11_wsl2/)  
30. Install Unsloth on Windows, brukt februar 24, 2026, [https://unsloth.ai/docs/get-started/install/windows-installation](https://unsloth.ai/docs/get-started/install/windows-installation)  
31. Fine-Tuning Qwen/Qwen3-VL-30B-A3B MoE Architecture with LoRA \- Medium, brukt februar 24, 2026, [https://medium.com/@ishaafsalman/fine-tuning-qwen-qwen3-vl-30b-a3b-moe-architecture-with-lora-2365359e870f](https://medium.com/@ishaafsalman/fine-tuning-qwen-qwen3-vl-30b-a3b-moe-architecture-with-lora-2365359e870f)  
32. Agentic Knowledge Distillation: Autonomous Training of Small Language Models for SMS Threat Detection \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2602.10869v1](https://arxiv.org/html/2602.10869v1)  
33. Introduction to model distillation: Efficient knowledge transfer for AI applications \- Nebius, brukt februar 24, 2026, [https://nebius.com/blog/posts/model-distillation-intro](https://nebius.com/blog/posts/model-distillation-intro)  
34. Analyzing Mitigation Strategies for Catastrophic Forgetting in End-to-End Training of Spoken Language Models \- ISCA Archive, brukt februar 24, 2026, [https://www.isca-archive.org/interspeech\_2025/hsiao25\_interspeech.pdf](https://www.isca-archive.org/interspeech_2025/hsiao25_interspeech.pdf)  
35. evertonaleixo/effects-of-lora-on-catastrophic-forgetting: Repository of code to study the impacts of LoRA and ConvLoRa in terms of avoiding Catastrophic Forgetting to Dynamic Networks group. \- GitHub, brukt februar 24, 2026, [https://github.com/evertonaleixo/effects-of-lora-on-catastrophic-forgetting](https://github.com/evertonaleixo/effects-of-lora-on-catastrophic-forgetting)  
36. LLM distillation: tutorial with code | by Ajay A, Technical Manager & Senior Data Scientist, brukt februar 24, 2026, [https://medium.com/data-science-collective/llm-distillation-tutorial-with-code-641c861a87a7](https://medium.com/data-science-collective/llm-distillation-tutorial-with-code-641c861a87a7)  
37. argilla-io/distilabel: Distilabel is a framework for synthetic data and AI feedback for engineers who need fast, reliable and scalable pipelines based on verified research papers. \- GitHub, brukt februar 24, 2026, [https://github.com/argilla-io/distilabel](https://github.com/argilla-io/distilabel)  
38. Train your SLM with distill-cli Claude Skill \- distil labs, brukt februar 24, 2026, [https://www.distillabs.ai/blog/train-your-slm-with-distil-claude-skill](https://www.distillabs.ai/blog/train-your-slm-with-distil-claude-skill)  
39. Knowledge distillation with Claude as the interface: trained a 0.6B model to match GPT-class performance on Text2SQL in a singe conversation : r/LocalLLaMA \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1qiu6jo/knowledge\_distillation\_with\_claude\_as\_the/](https://www.reddit.com/r/LocalLLaMA/comments/1qiu6jo/knowledge_distillation_with_claude_as_the/)  
40. How to Build License-Compliant Synthetic Data Pipelines for AI Model Distillation, brukt februar 24, 2026, [https://developer.nvidia.com/blog/how-to-build-license-compliant-synthetic-data-pipelines-for-ai-model-distillation/](https://developer.nvidia.com/blog/how-to-build-license-compliant-synthetic-data-pipelines-for-ai-model-distillation/)  
41. Prompting best practices \- Claude API Docs, brukt februar 24, 2026, [https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)  
42. Teaching Local Models to Call Tools Like Claude \- Tomasz Tunguz, brukt februar 24, 2026, [https://tomtunguz.com/distilling-claude-into-local-models/](https://tomtunguz.com/distilling-claude-into-local-models/)  
43. distil-cli | Skills Marketplace \- LobeHub, brukt februar 24, 2026, [https://lobehub.com/ru/skills/distil-labs-distil-cli-skill](https://lobehub.com/ru/skills/distil-labs-distil-cli-skill)  
44. LLM distillation demystified: a complete guide | Snorkel AI, brukt februar 24, 2026, [https://snorkel.ai/blog/llm-distillation-demystified-a-complete-guide/](https://snorkel.ai/blog/llm-distillation-demystified-a-complete-guide/)  
45. Distilling Reasoning into Student LLMs: Local Naturalness for Selecting Teacher Data, brukt februar 24, 2026, [https://arxiv.org/html/2510.03988v1](https://arxiv.org/html/2510.03988v1)  
46. Fine tuning LLMs for Enterprise: Practical Guidelines and Recommendations \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2404.10779v1](https://arxiv.org/html/2404.10779v1)  
47. Seeking Advice on Fine-Tuning a Model for Generating JSON Outputs from Real Estate Descriptions (Instructor / pydantic) : r/LLMDevs \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LLMDevs/comments/1dt4acf/seeking\_advice\_on\_finetuning\_a\_model\_for/](https://www.reddit.com/r/LLMDevs/comments/1dt4acf/seeking_advice_on_finetuning_a_model_for/)  
48. Avoiding Amnesia: Some Practical Guides to Mitigate Catastrophic Forgetting in LLMs Post-training | by Baicen Xiao | Medium, brukt februar 24, 2026, [https://medium.com/@baicenxiao/avoiding-amnesia-some-practical-guides-to-mitigate-catastrophic-forgetting-in-llms-post-training-6a23e4f064cb](https://medium.com/@baicenxiao/avoiding-amnesia-some-practical-guides-to-mitigate-catastrophic-forgetting-in-llms-post-training-6a23e4f064cb)  
49. \[D\] does LORA actually mitigate catastrophic forgetting when fine tuning llms? \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/MachineLearning/comments/13rp5sa/d\_does\_lora\_actually\_mitigate\_catastrophic/](https://www.reddit.com/r/MachineLearning/comments/13rp5sa/d_does_lora_actually_mitigate_catastrophic/)  
50. Analyzing Mitigation Strategies for Catastrophic Forgetting in End-to-End Training of Spoken Language Models \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2505.17496v1](https://arxiv.org/html/2505.17496v1)  
51. SuRe: Surprise-Driven Prioritised Replay for Continual LLM Learning \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2511.22367v1](https://arxiv.org/html/2511.22367v1)  
52. OPLoRA: Orthogonal Projection LoRA Prevents Catastrophic Forgetting during Parameter-Efficient Fine-Tuning \- arXiv, brukt februar 24, 2026, [https://arxiv.org/html/2510.13003v1](https://arxiv.org/html/2510.13003v1)  
53. Mitigating Forgetting in Low Rank Adaptation \- OpenReview, brukt februar 24, 2026, [https://openreview.net/forum?id=f9M9LgE5kt](https://openreview.net/forum?id=f9M9LgE5kt)  
54. Mitigating Catastrophic Forgetting in Fine-Tuned Large Language Models: An Experimental Study of LoRA and O-LoRA | Artificial Intelligence and Digital Technology \- SOAP, brukt februar 24, 2026, [https://soapubs.com/index.php/AIDT/article/view/1380](https://soapubs.com/index.php/AIDT/article/view/1380)  
55. Distilabel Docs, brukt februar 24, 2026, [https://distilabel.argilla.io/](https://distilabel.argilla.io/)  
56. Prepare your training datasets for distillation \- Amazon Bedrock, brukt februar 24, 2026, [https://docs.aws.amazon.com/bedrock/latest/userguide/distillation-prepare-datasets.html](https://docs.aws.amazon.com/bedrock/latest/userguide/distillation-prepare-datasets.html)  
57. Structured Output Generation in LLMs: JSON Schema and Grammar-Based Decoding | by Emre Karatas | Medium, brukt februar 24, 2026, [https://medium.com/@emrekaratas-ai/structured-output-generation-in-llms-json-schema-and-grammar-based-decoding-6a5c58b698a6](https://medium.com/@emrekaratas-ai/structured-output-generation-in-llms-json-schema-and-grammar-based-decoding-6a5c58b698a6)  
58. Using grammars to constrain llama.cpp output \- Ian Maurer's Notes, brukt februar 24, 2026, [https://www.imaurer.com/blog/posts/2023-09-06-llama-cpp-grammars/](https://www.imaurer.com/blog/posts/2023-09-06-llama-cpp-grammars/)  
59. Tools for restricting output to a given grammar \- LocalLLaMA \- Reddit, brukt februar 24, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1ci2xoh/tools\_for\_restricting\_output\_to\_a\_given\_grammar/](https://www.reddit.com/r/LocalLLaMA/comments/1ci2xoh/tools_for_restricting_output_to_a_given_grammar/)  
60. Qwen3 30B A3B Instruct 2507 \- API, Providers, Stats | OpenRouter, brukt februar 24, 2026, [https://openrouter.ai/qwen/qwen3-30b-a3b-instruct-2507](https://openrouter.ai/qwen/qwen3-30b-a3b-instruct-2507)  
61. JSON Schema \- Pydantic Validation, brukt februar 24, 2026, [https://docs.pydantic.dev/latest/concepts/json\_schema/](https://docs.pydantic.dev/latest/concepts/json_schema/)  
62. How to Use Pydantic for LLMs: Schema, Validation & Prompts description, brukt februar 24, 2026, [https://pydantic.dev/articles/llm-intro](https://pydantic.dev/articles/llm-intro)  
63. Controlling Large Language Model Output with Pydantic | by Matt Chinnock \- Medium, brukt februar 24, 2026, [https://medium.com/@mattchinnock/controlling-large-language-model-output-with-pydantic-74b2af5e79d1](https://medium.com/@mattchinnock/controlling-large-language-model-output-with-pydantic-74b2af5e79d1)  
64. Using the json grammar with ./server and Python · ggml-org llama.cpp · Discussion \#3268 · GitHub, brukt februar 24, 2026, [https://github.com/ggerganov/llama.cpp/discussions/3268](https://github.com/ggerganov/llama.cpp/discussions/3268)  
65. Using llama-cpp-python grammars to generate JSON \- Simon Willison: TIL, brukt februar 24, 2026, [https://til.simonwillison.net/llms/llama-cpp-python-grammars](https://til.simonwillison.net/llms/llama-cpp-python-grammars)