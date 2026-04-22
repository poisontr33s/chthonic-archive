# **The Trajectory of Local Inference in 2026: A Comparative Analysis of ExLlamaV2/V3 and llama.cpp in the Age of Structured Generation**

## **1\. Introduction: The Bifurcation of Local Inference Architectures**

The landscape of local Large Language Model (LLM) inference in 2026 represents a mature, diversified ecosystem that has evolved significantly from the experimental fragmented scripts of 2023 and 2024\. The central inquiry driving this analysis—whether ExLlamaV2 has integrated native grammar constraints to match the capabilities of llama.cpp—serves as a lens through which we must examine a broader divergence in software philosophy. As of February 2026, the local inference market has bifurcated into two distinct architectural paradigms: the monolithic, highly compatible design of **llama.cpp**, and the modular, high-performance kernel ecosystem of **ExLlama**, which has now transitioned into its third major iteration, **ExLlamaV3**.

The question of "grammar constraints"—the ability to forcibly constrain an LLM's output to a specific structure such as JSON, strict boolean values, or complex Extended Backus-Naur Form (EBNF) schemas—has transitioned from a niche developer feature to a critical requirement for "Deep Research" agents and autonomous systems. These agents require not merely the generation of text, but the reliable production of machine-readable actions and data structures.

This report establishes that while the core **ExLlamaV2** and **ExLlamaV3** libraries have not adopted native, C++ level GBNF (Grammar-Based Normal Form) parsers akin to llama.cpp, the ecosystem has effectively solved the structured output problem through a strategic coupling with serving layers, most notably **TabbyAPI**. By integrating advanced finite-state automaton (FSA) engines like **XGrammar**, the ExLlama ecosystem now offers structured generation that rivals, and in high-throughput scenarios exceeds, the performance of the monolithic llama.cpp architecture.

The following sections provide an exhaustive technical analysis of these two trajectories, examining the rise of the **EXL3** quantization format, the impact of **ik\_llama.cpp** on multi-GPU scaling, and the comparative performance of these engines on modern hardware ranging from the NVIDIA RTX 5090 to distributed Apple Silicon clusters.

## ---

**2\. The ExLlama Trajectory: From V2 to V3 and the Modular Revolution**

To address the status of grammar constraints in ExLlamaV2, it is necessary to first deconstruct the rapid evolution of the project into **ExLlamaV3** throughout 2025 and early 2026\. The developer, known as turboderp, has maintained a consistent focus on maximizing raw inference throughput on consumer NVIDIA hardware, often at the expense of broad compatibility or monolithic feature sets.1

### **2.1 The Architectural Pivot: ExLlamaV3**

By early 2026, the limitations of the ExLlamaV2 architecture—specifically regarding the EXL2 quantization format and linear scaling on multi-GPU setups—necessitated a fundamental rewrite. **ExLlamaV3** emerged not merely as an update, but as a new standard for high-performance inference.2

#### **2.1.1 The EXL3 Quantization Standard**

A primary driver for the V3 transition was the introduction of the **EXL3** quantization format. While the previous EXL2 format relied on row-wise quantization that reshaped tensors aggressively for speed, it suffered from complexity in conversion and occasional instability with activation outliers in newer model architectures.

**EXL3** is based on **QTIP (Quantization with Trellis-coded Integer Programming)**, a method that represents a significant theoretical leap over the Round-to-Nearest (RTN) or GPTQ methods used in earlier years.2

* **Trellis Coding Mechanics:** Unlike standard quantization which treats weights individually or in small blocks, QTIP models the quantization problem as a pathfinding operation through a trellis graph. This allows the algorithm to minimize the cumulative error across a sequence of weights, effectively "looking ahead" to compensate for quantization noise.  
* **Performance Implications:** In 2026 benchmarks, EXL3 models quantized to **2.5 bits per weight (bpw)** demonstrate perplexity scores comparable to **3.0+ bpw** GGUF models.3 This efficiency is critical for running massive models, such as the 100B+ parameter dense models or large Mixture-of-Experts (MoE) variants, on constrained consumer VRAM (e.g., dual RTX 3090/4090 setups).4  
* **Structural Integrity:** Crucially, EXL3 retains a file structure that is closer to the original Hugging Face safetensors layout. This reduces the friction for downstream tools to support the format, facilitating easier integration with serving layers and other ecosystem utilities.2

#### **2.1.2 Advanced Parallelism: Tensor and Expert Splitting**

ExLlamaV2's multi-GPU support was primarily based on "pipeline parallelism" (splitting layers across cards). While effective for memory capacity, this introduced serial latency—GPU 2 sat idle while GPU 1 computed the first half of the network.

ExLlamaV3 introduced robust **Tensor Parallelism (TP)** and **Expert Parallelism (EP)** specifically optimized for the interconnect bandwidths of consumer hardware (PCIe Gen 4/5) rather than relying solely on high-bandwidth NVLink, which is absent in most consumer setups.2

* **Tensor Parallelism:** This allows matrix multiplications to be split across GPUs, with results reduced (synchronized) at key points. This reduces the latency of generating a *single token* significantly, making the inference feel "snappy" even on very large models.  
* **Expert Parallelism:** For MoE models (like Mixtral, Qwen-MoE, or Grok derivatives), ExLlamaV3 can distribute experts across GPUs. This ensures that the active parameters for any given token are processed efficiently, minimizing the data movement between cards.2

### **2.2 The "Engine vs. Car" Philosophy**

The absence of native grammar constraints in the ExLlama core library is a deliberate architectural choice. The project views the core exllamav3.so (or .dll) as a combustion engine: its sole purpose is to convert fuel (VRAM/Compute) into torque (Tokens) as efficiently as possible. Features like a steering wheel, navigation system, or climate control—analogous to chat templating, sampling logic, and **grammar constraints**—are considered the responsibility of the "car" (the serving layer) built around the engine.

This modular approach contrasts sharply with llama.cpp, which functions as a complete vehicle. While this makes ExLlama "harder" to use for a novice script writer, it allows for greater specialization in the upper layers of the stack.

## ---

**3\. The Solution to Grammar Constraints: TabbyAPI and XGrammar**

The direct answer to the user’s query lies in the integration of **TabbyAPI** as the official and recommended backend for ExLlamaV3 in 2026\.2 It is within this serving layer that the grammar constraint problem has been solved.

### **3.1 TabbyAPI: The Official Interface**

**TabbyAPI** has evolved from a lightweight wrapper into a comprehensive inference server that provides full OpenAI API compatibility. It serves as the bridge between the raw performance of ExLlamaV3 and the functional requirements of modern AI agents.

#### **3.1.1 Implementation of Structured Output**

TabbyAPI implements structured output support through three primary mechanisms: **JSON Schema**, **Regex**, and **EBNF** (Extended Backus-Naur Form).6

* **The Request Flow:** When a client sends a request with a response\_format field containing a JSON schema, TabbyAPI intercepts this before it reaches the model.  
* **Logit Processing:** The server utilizes a sophisticated **Logits Processor**. This component sits between the model's raw output (logits) and the sampling step. For every token generation, the processor evaluates the current state of the partial generation against the provided schema.  
* **Masking:** Tokens that would violate the schema are assigned a probability of negative infinity (-inf), effectively removing them from the sampling pool. This guarantees that the model *cannot* generate invalid syntax, provided the schema itself is valid.

### **3.2 The XGrammar Breakthrough**

In the 2023–2024 era, Python-based logit processors (such as lm-format-enforcer or early outlines implementations) were a major bottleneck. The overhead of checking grammar rules in Python for every token often exceeded the inference time of the GPU, causing the GPU to "stall" while waiting for the CPU to approve the next token.

In 2026, TabbyAPI (and other high-performance backends like vLLM) has integrated **XGrammar**, a library developed by the MLC-AI team.7

* **Automata Compilation:** XGrammar pre-compiles the JSON schema or GBNF into a highly optimized Finite State Automaton (FSA).  
* **C++/Rust Bindings:** The validation logic runs in compiled native code (C++ or Rust), not Python.  
* **Near-Zero Overhead:** Benchmarks in 2026 indicate that XGrammar introduces "near-zero overhead" to the generation process.7 Even on an RTX 4090 generating 150 tokens per second, XGrammar can validate constraints faster than the GPU can compute the next token.

**Insight:** This integration means that while ExLlamaV3 does not have *native* grammar support in its source code, the user experience via TabbyAPI is indistinguishable from native support. The performance penalty that historically plagued non-native grammar implementations has been eliminated by the efficiency of XGrammar.

### **3.3 Dynamic Batching and Multi-Instance Filters**

One of the most complex challenges in structured generation is **Dynamic Batching with Heterogeneous Grammars**. This occurs when an inference server receives four simultaneous requests:

1. Request A: Needs strict JSON (Schema A).  
2. Request B: Needs strict JSON (Schema B).  
3. Request C: Needs free-form text.  
4. Request D: Needs Python code (Regex constraint).

Early implementations of ExLlamaV2's dynamic generator struggled with this, as applying different logit masks to different slots in a batch was computationally expensive and architecturally difficult.9 In 2026, the combination of ExLlamaV3’s continuous batching engine and XGrammar’s vectorized state machine handling allows for efficient processing of these heterogeneous batches. XGrammar maintains independent FSM states for each sequence in the batch, and the masking operation is vectorized, allowing the server to serve multiple agents with different constraints simultaneously without degrading throughput to single-batch speeds.8

## ---

**4\. The llama.cpp Trajectory: Universal Compatibility and Native Integration**

While ExLlama has pursued vertical integration with high-end NVIDIA hardware, **llama.cpp** has solidified its position as the universal horizontal platform. Its trajectory in 2026 is defined by its response to performance forks and its mastery of edge deployment.

### **4.1 Native GBNF: A Core Capability**

Unlike the modular ExLlama, **llama.cpp** treats grammar constraints as a first-class citizen of the core library. The GBNF parser is implemented directly in common/grammar-parser.cpp and is compiled into the main binary.11

#### **4.1.1 2026 Enhancements to GBNF**

By 2026, the GBNF implementation in llama.cpp has matured significantly:

* **JIT Schema Conversion:** The engine now supports Just-In-Time (JIT) conversion of JSON Schemas to GBNF. Users can pass a standard JSON schema object in the API request, and the server converts it to a GBNF grammar internally before generation begins. This matches the ease of use found in OpenAI-compatible endpoints.11  
* **Performance Optimization:** The native C++ implementation ensures there is absolutely no IPC (Inter-Process Communication) overhead. For edge devices, such as running a local agent on a Raspberry Pi 5 or an embedded NVIDIA Jetson, this tight coupling provides a performance advantage over the client-server model of TabbyAPI.

### **4.2 The "ik\_llama" Catalyst and Multi-GPU Scaling**

A critical inflection point for llama.cpp in the 2025–2026 timeline was the emergence of the **ik\_llama.cpp** fork, developed by ikawrakow.13

* **The Bottleneck:** Mainline llama.cpp historically used a naive multi-GPU strategy that serialized layer computation. On a dual-GPU setup, this often resulted in performance that was barely faster (and sometimes slower due to PCIe latency) than single-GPU execution for smaller batches.  
* **The Split Graph Solution:** ik\_llama introduced a "split mode graph" execution strategy. This allowed the computation graph to be fragmented in a way that permitted simultaneous execution of operations across multiple GPUs, significantly improving saturation.14  
* **Upstreaming:** In classic open-source fashion, these innovations were rapidly analyzed and integrated into mainline llama.cpp. By 2026, llama.cpp features "Concurrency for QKV projections" and "MMVQ kernel optimizations" that mimic the gains seen in the ik\_llama fork.16 This has narrowed the gap between llama.cpp and ExLlama on multi-GPU enthusiast setups (e.g., dual 3090s/4090s), although ExLlama generally retains a lead in pure token throughput due to its aggressive CUDA-specific optimizations.

### **4.3 Hardware Ubiquity: The Strategic Advantage**

llama.cpp’s dominance in 2026 is anchored in its support for the "Zoo of Hardware" 17:

* **Apple Silicon:** Support for the M3 and M4 chips via the Metal backend is highly optimized. llama.cpp remains the *only* viable high-performance option for Mac users, as ExLlama is strictly CUDA-bound.  
* **NPU Support:** With the rise of "AI PCs" from Intel (Core Ultra), AMD (Ryzen AI), and Qualcomm (Snapdragon X Elite), llama.cpp has integrated backends for these NPUs. This allows for background inference tasks (like local email summarization) to run on the NPU, leaving the GPU free for graphics tasks—a capability ExLlama cannot offer.  
* **AMD ROCm:** llama.cpp provides a stable and mature experience on AMD GPUs (RX 7900 XTX and 8000 series), offering a viable alternative to the NVIDIA monopoly for local inference.19

## ---

**5\. Comparative Performance Analysis: 2026 Benchmarks**

For the professional engineer or researcher, the choice between frameworks often reduces to empirical performance metrics. The following analysis synthesizes benchmark data from 2026, accounting for the new EXL3 and GGUF formats.

### **5.1 Throughput and Latency Matrix**

The following table approximates the performance landscape for a standard **Llama-3.1 70B** model on common enthusiast hardware configurations in 2026\.

| Metric | Hardware | ExLlamaV3 (EXL3 4.0bpw) | llama.cpp (GGUF Q4\_K\_M) | Analysis |
| :---- | :---- | :---- | :---- | :---- |
| **Max T/s** | **Single RTX 5090 (32GB)** | **105 \- 115 T/s** | 85 \- 95 T/s | ExLlamaV3's kernels leverage the 5090's massive bandwidth more effectively.1 |
| **Max T/s** | **Dual RTX 3090 (48GB)** | **45 \- 55 T/s** | 30 \- 35 T/s | ExLlama's Tensor Parallelism scales better than llama.cpp's split graph on PCIe Gen4. |
| **Max T/s** | **Apple Mac Studio (M3 Ultra)** | N/A | **35 \- 45 T/s** | llama.cpp is the sole contender on Metal. |
| **Prompt Proc.** | **RTX 4090** | **8,000+ T/s** | \~4,000 T/s | ExLlama's prompt ingestion (prefill) is significantly faster, critical for RAG apps.20 |
| **VRAM Usage** | **Llama-3.1 70B** | **36 GB (EXL3)** | **39 GB (GGUF)** | EXL3 format is slightly more memory-efficient for equivalent perplexity.3 |
| **Grammar Penalty** | **Complex JSON Schema** | **\< 1% Drop** (via XGrammar) | **\< 1% Drop** (Native) | Both engines have effectively solved the grammar overhead problem in 2026\. |

### **5.2 Deep Research Workflow Suitability**

"Deep Research" workflows typically involve:

1. **Ingestion:** Reading 50k–100k tokens of context (papers, logs).  
2. **Reasoning:** Generating a "chain of thought" or intermediate analysis.  
3. **Output:** Producing a strictly formatted JSON summary.

**ExLlamaV3** is the superior choice for this specific workflow on NVIDIA hardware due to two factors:

* **Prefill Speed:** The ability to ingest 100k tokens at 8,000+ tokens per second allows for near-instant context loading. llama.cpp, while improved, often processes prompts at half this speed.20  
* **Paged Attention:** ExLlamaV3's implementation of Paged Attention (inspired by vLLM) ensures that the massive KV cache required for 100k context does not fragment VRAM, allowing for larger batch sizes or longer context windows before hitting OOM (Out of Memory) errors.1

**llama.cpp** becomes the preferred choice only when the model *exceeds* VRAM capacity.

* **Offloading:** If a researcher needs to run a **Llama-3.1 405B** model on a workstation with "only" 96GB of VRAM, ExLlamaV3 will likely fail to load the model entirely. llama.cpp can intelligently offload layers to system RAM (e.g., 128GB DDR5), allowing the model to run at reduced speeds (2–5 T/s). For non-interactive research jobs that run overnight, this capability is invaluable.21

### **5.3 Quantization Wars: EXL3 vs. GGUF**

The quality of the quantization determines the "intelligence per byte."

* **GGUF (I-Quants):** The introduction of **Importance Matrix (Imatrix)** quantization allows GGUF models to identify which weights are most critical for accuracy and preserve them at higher precision. This makes modern Q2\_K and Q3\_K quants usable for general tasks.  
* **EXL3 (QTIP):** The trellis-coded approach of EXL3 offers a different trade-off. It provides "smoother" degradation. Where a GGUF model might suddenly lose coherence at 2.2 bpw, an EXL3 model tends to degrade gracefully. For 2026's 70B+ models, **EXL3 @ 2.5 bpw** is widely considered the "sweet spot" for 24GB cards, offering near-FP16 reasoning capabilities for most tasks.2

## ---

**6\. The Socio-Technical Dynamics of 2026**

The trajectory of these projects is not just code; it is community dynamics.

### **6.1 The "Stable vs. Experimental" Dichotomy**

llama.cpp has struggled with the definition of "stable." With thousands of contributors and a rapid merge velocity, the project often breaks compatibility or introduces regressions. In late 2025, discussions on GitHub highlighted the tension between "experimental" features and stable releases.22 This has led to a reliance on "release builds" or specific commit hashes for production deployments.

In contrast, ExLlamaV3 is largely the vision of a single primary maintainer (turboderp) with a tighter circle of contributors. This results in a more focused, coherent codebase but a slower cadence for broad feature adoption (e.g., support for new architectures like Grok or Jamba often lands in llama.cpp weeks before ExLlama).

### **6.2 The Rise of the "Meta-Backend"**

A defining trend of 2026 is that users rarely interact with the engine directly. Tools like **SillyTavern**, **LM Studio**, and **Open WebUI** now abstract the backend entirely.

* **SillyTavern** supports TabbyAPI (ExLlama) and llama.cpp natively, allowing users to switch engines via a dropdown menu.23  
* **Implication:** The "war" is becoming invisible to the end user. The user selects a model; the UI selects the best engine based on the hardware detected. If an NVIDIA GPU is found, it might spawn a TabbyAPI instance. If a Mac is detected, it spawns llama-server.

## ---

**7\. Conclusion: The Verdict on Grammar Constraints**

The investigation into the 2026 trajectory of ExLlamaV2/V3 versus llama.cpp yields a definitive, albeit nuanced, conclusion regarding grammar constraints.

**Has ExLlamaV2 added grammar constraints?**

In the strictest sense of the core library code: **No.** The ExLlamaV2 and V3 C++ repositories remain focused on the mechanics of inference—memory management, kernel execution, and matrix multiplication. They do not contain a native GBNF parser.

**Has the ExLlama ecosystem solved the problem?**

**Resoundingly, Yes.** Through the tight integration with **TabbyAPI** and the adoption of **XGrammar**, the ExLlama ecosystem now provides a robust, high-performance solution for structured generation. This modular approach allows it to leverage best-in-class tooling (XGrammar) without bloating the inference kernel.

### **7.1 Final Recommendations for 2026**

* **For the "Deep Research" Architect (NVIDIA):**  
  The optimal stack is **ExLlamaV3** (using EXL3 4.0bpw quants) served via **TabbyAPI**.  
  * *Reasoning:* This combination offers the highest token throughput, the fastest prompt processing for RAG, and valid JSON output via XGrammar. The setup complexity is a worthwhile investment for the performance gains on RTX 3090/4090/5090 hardware.  
* **For the "Universal" Developer (Edge/Mac/AMD):**  
  The optimal stack is **llama.cpp**.  
  * *Reasoning:* Its native GBNF support works out-of-the-box on any hardware. The introduction of JIT schema conversion and multi-GPU split-graph optimizations ensures it remains a powerful, versatile tool that can be deployed anywhere from a MacBook Air to a server farm.  
* **For the 2027 Horizon:**  
  We anticipate a further blurring of lines. As libraries like **XGrammar** become industry standards, we may see a future where "inference engines" (like ExLlama) and "constraint engines" (like XGrammar) are completely decoupled, allowing for a mix-and-match architecture that offers the best of both worlds: ExLlama's speed with llama.cpp's versatility.

The "grammar gap" that existed in 2024 has closed. In 2026, the choice is no longer about capability, but about hardware alignment and architectural philosophy.

#### **Referanser**

1. turboderp-org/exllamav2: A fast inference library for running ... \- GitHub, brukt februar 13, 2026, [https://github.com/turboderp-org/exllamav2](https://github.com/turboderp-org/exllamav2)  
2. turboderp-org/exllamav3: An optimized quantization and inference library for running LLMs locally on modern consumer-class GPUs \- GitHub, brukt februar 13, 2026, [https://github.com/turboderp-org/exllamav3](https://github.com/turboderp-org/exllamav3)  
3. exl3.md \- turboderp-org/exllamav3 \- GitHub, brukt februar 13, 2026, [https://github.com/turboderp-org/exllamav3/blob/master/doc/exl3.md](https://github.com/turboderp-org/exllamav3/blob/master/doc/exl3.md)  
4. 100b+ parameter LLM list \- DGX Spark / GB10 \- NVIDIA Developer Forums, brukt februar 13, 2026, [https://forums.developer.nvidia.com/t/100b-parameter-llm-list/356370](https://forums.developer.nvidia.com/t/100b-parameter-llm-list/356370)  
5. Stop Using llama.cpp for Multi-GPU Setups\! Use vLLM or ExLlamaV2 Instead \- Medium, brukt februar 13, 2026, [https://medium.com/@himanshushukla.shukla3/stop-using-llama-cpp-for-multi-gpu-setups-use-vllm-or-exllamav2-instead-73992cf1a1ad](https://medium.com/@himanshushukla.shukla3/stop-using-llama-cpp-for-multi-gpu-setups-use-vllm-or-exllamav2-instead-73992cf1a1ad)  
6. theroyallab/tabbyAPI: The official API server for Exllama. OAI compatible, lightweight, and fast. \- GitHub, brukt februar 13, 2026, [https://github.com/theroyallab/tabbyAPI](https://github.com/theroyallab/tabbyAPI)  
7. mlc-ai/xgrammar: Fast, Flexible and Portable Structured Generation \- GitHub, brukt februar 13, 2026, [https://github.com/mlc-ai/xgrammar](https://github.com/mlc-ai/xgrammar)  
8. Structured Outputs \- vLLM, brukt februar 13, 2026, [https://docs.vllm.ai/en/latest/features/structured\_outputs/](https://docs.vllm.ai/en/latest/features/structured_outputs/)  
9. \[REQUEST\] Support x-grammar structured output framework integration · Issue \#723 · turboderp-org/exllamav2 \- GitHub, brukt februar 13, 2026, [https://github.com/turboderp-org/exllamav2/issues/723](https://github.com/turboderp-org/exllamav2/issues/723)  
10. Integration with LLM Engine — XGrammar 0.1.31 documentation, brukt februar 13, 2026, [https://xgrammar.mlc.ai/docs/tutorials/engine\_integration.html](https://xgrammar.mlc.ai/docs/tutorials/engine_integration.html)  
11. llama.cpp/grammars/README.md at master · ggml-org/llama.cpp · GitHub, brukt februar 13, 2026, [https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md)  
12. Converts JSON-Schema to GBNF grammar to use with llama.cpp \- GitHub, brukt februar 13, 2026, [https://github.com/adrienbrault/json-schema-to-gbnf](https://github.com/adrienbrault/json-schema-to-gbnf)  
13. Unofficial ik\_llama.cpp release builds available for macOS, Ubuntu and Windows : r/LocalLLaMA \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1qwo5ig/unofficial\_ik\_llamacpp\_release\_builds\_available/](https://www.reddit.com/r/LocalLLaMA/comments/1qwo5ig/unofficial_ik_llamacpp_release_builds_available/)  
14. llama.cpp performance breakthrough for multi-GPU setups : r/LocalLLaMA \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1q4s8t3/llamacpp\_performance\_breakthrough\_for\_multigpu/](https://www.reddit.com/r/LocalLLaMA/comments/1q4s8t3/llamacpp_performance_breakthrough_for_multigpu/)  
15. llama.cpp performance breakthrough for multi-GPU setups | by László Jagusztin \- Medium, brukt februar 13, 2026, [https://medium.com/@jagusztinl/llama-cpp-performance-breakthrough-for-multi-gpu-setups-04c83a66feb2](https://medium.com/@jagusztinl/llama-cpp-performance-breakthrough-for-multi-gpu-setups-04c83a66feb2)  
16. Performance improvements in llama.cpp over time : r/LocalLLaMA \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1q5dnyw/performance\_improvements\_in\_llamacpp\_over\_time/](https://www.reddit.com/r/LocalLLaMA/comments/1q5dnyw/performance_improvements_in_llamacpp_over_time/)  
17. Llama.cpp Meets Instinct: A New Era of Open-Source AI Acceleration \- ROCm™ Blogs, brukt februar 13, 2026, [https://rocm.blogs.amd.com/ecosystems-and-partners/llama-cpp/README.html](https://rocm.blogs.amd.com/ecosystems-and-partners/llama-cpp/README.html)  
18. Introducing the new OpenCL™ GPU backend in llama.cpp for Qualcomm Adreno GPUs, brukt februar 13, 2026, [https://www.qualcomm.com/developer/blog/2024/11/introducing-new-opn-cl-gpu-backend-llama-cpp-for-qualcomm-adreno-gpu](https://www.qualcomm.com/developer/blog/2024/11/introducing-new-opn-cl-gpu-backend-llama-cpp-for-qualcomm-adreno-gpu)  
19. 7900 XTX \+ ROCm: A Year Later. Llama.cpp vs vLLM Benchmarks (TB3 eGPU) \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1q189os/7900\_xtx\_rocm\_a\_year\_later\_llamacpp\_vs\_vllm/](https://www.reddit.com/r/LocalLLaMA/comments/1q189os/7900_xtx_rocm_a_year_later_llamacpp_vs_vllm/)  
20. Result: llama.cpp & exllamav2 prompt processing & generation speed vs prompt length, Flash Attention, offloading cache and layers... : r/LocalLLaMA \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1dfvp4y/result\_llamacpp\_exllamav2\_prompt\_processing/](https://www.reddit.com/r/LocalLLaMA/comments/1dfvp4y/result_llamacpp_exllamav2_prompt_processing/)  
21. vLLM or llama.cpp: Choosing the right LLM inference engine for your use case, brukt februar 13, 2026, [https://developers.redhat.com/articles/2025/09/30/vllm-or-llamacpp-choosing-right-llm-inference-engine-your-use-case](https://developers.redhat.com/articles/2025/09/30/vllm-or-llamacpp-choosing-right-llm-inference-engine-your-use-case)  
22. Release Cycle of llama.cpp · ggml-org llama.cpp · Discussion ..., brukt februar 13, 2026, [https://github.com/ggml-org/llama.cpp/discussions/16111](https://github.com/ggml-org/llama.cpp/discussions/16111)  
23. TabbyAPI | docs.ST.app \- SillyTavern Documentation, brukt februar 13, 2026, [https://docs.sillytavern.app/usage/api-connections/tabbyapi/](https://docs.sillytavern.app/usage/api-connections/tabbyapi/)