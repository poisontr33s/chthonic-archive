# **Local Inference Infrastructure for High-Throughput Batch Classification: Architecture, Optimization, and Deployment on Windows 11**

## **1\. Executive Summary: The Strategic Pivot to On-Premise Intelligence**

The enterprise and developer landscape of 2026 is defined by a rigorous re-evaluation of cloud dependency. For years, the default architectural pattern for Large Language Model (LLM) integration involved making API calls to hosted providers like OpenAI or Hugging Face. While convenient, this model introduces distinct friction points for high-volume data pipelines: unpredictable latency, variable operational costs, and, crucially, data privacy vulnerabilities when handling sensitive codebase repositories. For organizations managing "Polyglot" repositories—codebases interacting with diverse programming languages, legacy systems, and multilingual documentation—the necessity to perform batch classification locally on secure hardware has transitioned from a niche preference to a competitive imperative.

This report serves as a comprehensive architectural blueprint for deploying a robust, high-throughput local inference stack on a consumer-grade yet high-performance workstation: a Windows 11 laptop equipped with an NVIDIA RTX 4090 (16GB VRAM). The analysis specifically addresses the technological ecosystem of early 2026, integrating Python 3.13, CUDA 12.4+, and the latest advancements in model architectures such as Llama 4, Qwen 3, and Kimi K2.5.

The core engineering challenge addressed herein is the optimization of constrained Video RAM (VRAM) against the computational demands of massive batch processing. While the RTX 4090 Laptop GPU is a formidable accelerator, its 16GB memory buffer—significantly smaller than the desktop variant's 24GB—necessitates a sophisticated approach to resource management. The deployment environment, a "Polyglot" repository, implies that the chosen model must possess broad reasoning capabilities across varying syntaxes and semantic structures, rejecting the simplicity of smaller, domain-specific models in favor of generalized intelligence that must be compressed to fit on the edge.

Our exhaustive analysis indicates that while highly specialized runtimes like TensorRT-LLM offer peak theoretical throughput, the pragmatic "sweet spot" for a Windows 11 environment typically lies with **llama-cpp-python** or **ONNX Runtime GenAI**. These backends provide the optimal balance of Python 3.13 compatibility, resistance to memory fragmentation, and support for the GGUF quantization standard, which is essential for fitting 14B-parameter models into limited memory. Furthermore, the requirement for "overnight" processing introduces specific instability risks inherent to Windows, particularly regarding "Session 0" isolation and Task Scheduler resource allocation, which requires a departure from standard service architectures toward interactive session management.

## **2\. Infrastructure Analysis: The Hardware Substrate**

To engineer a reliable batch pipeline, one must first deeply understand the physical constraints of the compute substrate. The "RTX 4090" nomenclature often obfuscates significant architectural differences between desktop and mobile platforms, differences that define the upper limits of local inference capabilities.

### **2.1 The Silicon Reality: AD103 vs. AD102**

The foundation of this infrastructure is the NVIDIA GeForce RTX 4090 Laptop GPU. In the marketing parlance of 2026, it sits at the apex of mobile computing, yet structurally, it differs fundamentally from its desktop namesake. The desktop RTX 4090 utilizes the AD102 silicon, boasting 16,384 CUDA cores and a massive 24GB of GDDR6X memory on a 384-bit bus. In sharp contrast, the Laptop RTX 4090 is built on the AD103 chip—the same silicon found in the desktop RTX 4080—and is strictly limited to 16GB of GDDR6 memory on a narrower 256-bit bus.1

This distinction is not merely academic; it is the primary bottleneck for batch classification. In LLM inference, memory bandwidth determines the speed of token generation, while memory capacity (VRAM) determines the maximum size of the model and the batch of data that can be processed simultaneously. The 16GB VRAM ceiling imposes a hard physical limit on the model parameters. To run a model, the GPU must hold:

1. **Model Weights:** The static parameters of the neural network.  
2. **KV Cache (Key-Value Cache):** The dynamic memory required to store the context of the conversation or document analysis. This scales linearly with the context length and batch size.2  
3. **Activation Overhead:** Temporary buffers for CUDA kernels and cuBLAS workspaces, typically consuming 500MB to 2GB depending on the framework.3

For an overnight pipeline processing 8,000+ files, throughput is a function of batch size. However, increasing the batch size inflates the KV cache consumption. On a 16GB card, running a dense 70B parameter model is mathematically impossible without severe offloading to system RAM (CPU). When layers are offloaded to the CPU, data must travel over the PCIe bus, which, even at Gen 4 speeds, is orders of magnitude slower than the internal GPU memory bandwidth. This "spillover" can reduce inference speeds from a healthy \~40 tokens/second to a crawling \<2 tokens/second, rendering the overnight batch concept unviable.4 Therefore, the infrastructure must target efficient 7B to 14B parameter models or heavily quantized Mixture-of-Experts (MoE) architectures to maintain full GPU residency.

### **2.2 Thermal Constraints and Power Management**

Unlike a server rack, a laptop is thermally constrained. An "overnight" run implies 8 to 12 hours of sustained load. The RTX 4090 Laptop GPU operates within a Total Graphics Power (TGP) envelope of approximately 150W to 175W. During sustained inference, the GPU will rapidly hit thermal saturation, causing the clock speeds to throttle. While this protects the hardware, it introduces variability in processing time per batch.

Furthermore, Windows 11's power management heuristics are aggressive. The "Modern Standby" (S0 Low Power Idle) state works to suspend background processes to conserve battery, even when plugged in. For a batch process to survive the night, the operating system must be explicitly configured to prioritize the Python process and prevent the PCIe link to the GPU from entering a low-power state, which often results in CUDA errors like "driver not ready" or "illegal memory access" when the GPU attempts to wake up for the next batch.6

### **2.3 System Memory (RAM) and Storage Hierarchy**

While VRAM is the primary constraint, system RAM plays a crucial role in model loading and fallback stability. The "Polyglot" repo analysis likely involves parsing large code files. If the GPU VRAM fills up, the inference engine (especially llama.cpp) will attempt to offload layers to system RAM. Ideally, the laptop should be equipped with at least 32GB, and preferably 64GB, of system RAM to accommodate the OS, the Python runtime, and any model spillover without hitting the disk page file.

Storage speed is equally critical for batch processing. Reading 8,000 small text files can become an I/O bottleneck if not managed correctly. An NVMe SSD (PCIe Gen 4\) is standard for an RTX 4090 laptop, but the access pattern matters. The pipeline should utilize Python generators to lazy-load files, preventing a massive spike in system RAM usage that occurs if all 8,000 files are loaded into memory lists at initialization.

## **3\. The 2026 Model Landscape: Selecting the Brain**

The choice of model dictates the accuracy of classification. In February 2026, the "small model" landscape (models \< 15B parameters) has matured significantly, offering reasoning capabilities that rival the massive GPT-3.5 and GPT-4 class models of previous years. For a classification task on a 16GB card, we must balance parameter count (intelligence) with quantization (size).

### **3.1 The Rise of the "Mid-Size" Titans (12B \- 14B)**

The most significant trend in 2025-2026 has been the optimization of models in the 10B to 14B parameter range. This size is the "Goldilocks" zone for 16GB GPUs—large enough to possess deep reasoning and instruction-following capabilities, yet small enough to fit comfortably in VRAM when quantized.

1. **Qwen 3 & Qwen 2.5 (14B):** The Qwen series from Alibaba has established itself as a leader in coding and structured output tasks. The 14B parameter variant is particularly potent for "Polyglot" repositories because it has been trained on a massive corpus of multilingual code and text.  
   * *VRAM Math:* A 14B model at 4-bit quantization (Q4\_K\_M) requires approximately 9-10GB of VRAM for weights. This leaves roughly 6GB for the KV cache and overhead.  
   * *Context Capacity:* With 6GB of free VRAM, a user can comfortably utilize a context window of 8,192 to 12,000 tokens, which is sufficient for analyzing entire source code files or detailed documentation.5  
2. **Llama 4 (8B):** As the successor to the ubiquitous Llama 3, the Llama 4 8B model represents the cutting edge of dense model efficiency. While smaller than the Qwen 14B, its training on an even larger dataset makes it highly competitive for general classification. An 8B model at extremely high precision (Q8\_0 or FP16) would use roughly 8.5GB to 16GB of VRAM. However, for classification, a Q6\_K or Q8\_0 quantization offers near-lossless performance while fitting easily into memory.8  
3. **Mistral Large 3 / Mistral Small (12B):** Mistral's models are renowned for their efficiency and "dense" reasoning. The 12B class offers a compromise between the 8B and 14B options, often providing a slightly faster token generation rate due to fewer parameters.9  
4. **Kimi K2.5:** A strong contender in the reasoning space, though often associated with larger parameter counts. If a distilled or smaller variant (\~10B) is available, it is a viable candidate, particularly for complex reasoning chains where the classification requires "thinking" before answering.10

### **3.2 Quantization Strategy: The GGUF Standard**

To run these models on 16GB VRAM, quantization is not optional; it is mandatory. The GGUF format (GPT-Generated Unified Format) has become the industry standard for local inference, allowing for flexible memory mapping and CPU/GPU splitting.

* **Q4\_K\_M (4-bit Medium):** This is the recommended baseline for the 14B models (e.g., Qwen 3 14B). It compresses weights to 4 bits with mixed precision for critical layers, resulting in a model size of \~9GB. The perplexity (error rate) increase compared to FP16 is negligible for classification tasks, while the memory savings are massive.11  
* **Q8\_0 (8-bit):** Effectively half-precision. This is recommended for smaller models like Llama 4 8B. It doubles the memory footprint compared to Q4 but preserves 99.9% of the model's accuracy. If the task involves highly nuanced linguistic distinctions, Q8\_0 on an 8B model might outperform Q4\_K\_M on a 14B model.12  
* **Q6\_K:** A middle ground that offers a sweet spot if Q8\_0 pushes the VRAM limit slightly too high (causing OOM errors) but Q4 feels like too much of a compromise.

**Strategic Recommendation:** Begin with **Qwen 2.5 14B (or Qwen 3 14B if available) at Q4\_K\_M**. Its superior performance in structured output generation (JSON) makes it the ideal candidate for classification tasks where the output must be machine-readable.

## **4\. Inference Backend Ecosystem: The Engine Room**

The choice of inference backend—the software that actually runs the model—is the single most significant architectural decision. In 2026, the ecosystem is fragmented, with different tools prioritizing speed, compatibility, or ease of use.

### **4.1 vLLM: The Server-Grade Powerhouse**

**Architecture:** vLLM is designed for high-throughput serving, utilizing PagedAttention to manage the KV cache non-contiguously, reducing memory waste and enabling massive batch sizes.14 **Windows Reality:** Despite its dominance in Linux server environments, vLLM's native Windows support remains experimental and friction-heavy in early 2026\. While a Pull Request for native support exists 15, the primary recommendation for Windows users is still to run it via WSL2 (Windows Subsystem for Linux).16 **The WSL2 Problem:** For a batch pipeline processing thousands of local files, WSL2 introduces a significant I/O bottleneck. Crossing the boundary between the Windows NTFS file system and the Linux EXT4 environment is computationally expensive. Furthermore, managing GPU drivers across this virtualization layer can lead to instability and "driver not ready" errors after system sleep cycles.17 **Verdict:** High risk. The complexity of configuration and potential for memory leaks in long-running processes makes it less suitable for a "set it and forget it" local overnight job.18

### **4.2 TensorRT-LLM: The Speed Demon**

**Architecture:** NVIDIA's own library, which compiles models into highly optimized "engines" specifically tuned for the GPU architecture (Ada Lovelace for the 4090).1 **Throughput:** Benchmarks consistently show TensorRT-LLM outperforming other backends by 30-70% in raw token generation speed.1 **The Rigidity Problem:** TensorRT-LLM trades flexibility for speed. Models must be pre-compiled for the specific hardware and configuration (precision, tensor parallelism). If you want to change the model, or even significantly alter the batch size or context length, you often need to re-build the engine—a process that can take minutes to hours. Installation on Windows is also notoriously difficult, often involving Microsoft MPI and strict dependency versioning (e.g., locking to Python 3.10).21 **Verdict:** Overkill complexity. For an 8,000-file batch that runs overnight, the raw speed advantage (saving perhaps 1-2 hours) is not worth the days of engineering time required to set up and maintain the environment.

### **4.3 ONNX Runtime GenAI: The Integrated Path**

**Architecture:** Microsoft's cross-platform runtime, heavily optimized for Windows via DirectML and CUDA Execution Providers.23 **Pros:** Excellent Python 3.13 support via pre-built wheels.25 It integrates natively with the Windows AI ecosystem. Performance is competitive, particularly for models that have been optimized and exported to ONNX format.26 **Cons:** The primary friction is the need to convert models to ONNX. While tools exist, converting bleeding-edge models (like a brand new Qwen 3 MoE) can be error-prone, leading to operator support issues.27 **Verdict:** A strong runner-up, offering stability and native integration, but lacking the immediate "download and run" flexibility of GGUF-based tools.

### **4.4 llama-cpp-python: The Resilient Workhorse**

**Architecture:** Python bindings for llama.cpp, a C++ inference engine originally built for Apple Silicon but now highly optimized for NVIDIA GPUs via cuBLAS.28 **Pros:**

* **GGUF Ecosystem:** It uses GGUF models, which are ubiquitous and allow for precise quantization control.  
* **Offloading:** Crucially, it supports partial offloading. If a specific batch or context pushes memory usage beyond 16GB, llama.cpp can spill the excess layers to system RAM. While this slows down inference, it *prevents the crash*. For an unattended overnight job, this resilience is infinitely more valuable than raw speed.29  
* **Python 3.13 & CUDA 12.4:** Pre-built wheels are actively maintained, making installation a simple pip command rather than a compilation odyssey.30 **Verdict:** **The Recommended Backend.** It offers the highest reliability, easiest setup, and sufficient performance for the task at hand.

## **5\. Deployment Pipeline: Architecture and Implementation**

Building the software stack involves more than just installing libraries. It requires a resilient architecture capable of handling errors, managing memory, and validating outputs.

### **5.1 The Software Stack: Python 3.13 and uv**

The Python ecosystem in 2026 has embraced **uv**, a Rust-based package manager that replaces pip, poetry, and venv with a tool that is 10-100x faster.32

* **Why uv?** It allows for strict dependency resolution and environment isolation. You can "pin" Python 3.13 for the project and ensure that the exact CUDA-enabled wheels for llama-cpp-python and torch are installed every time, preventing the "it worked yesterday" syndrome.33  
* **Command:** uv run pipeline.py becomes the atomic unit of execution for the Task Scheduler, ensuring the environment is always consistent.35

### **5.2 Structured Output: The Key to Classification**

Standard LLM generation is "chatty." If you ask an LLM to classify a file, it might reply, "Sure\! Based on my analysis, this file appears to be..." This is useless for an automated pipeline. You need clean JSON: {"category": "security\_patch", "risk\_level": "high"}.

* **Instructor:** A library that patches the OpenAI API (which llama-cpp-python mimics) to enforce Pydantic schemas. It works by "retrying" if the model outputs invalid JSON. While effective, retries waste compute.36  
* **Outlines:** A more advanced library that enforces structure at the *logit* level. It uses a Finite State Machine (FSM) to mask the model's vocabulary, making it *impossible* for the model to generate a token that violates the schema. This is faster (no retries) and more deterministic.38  
* **Recommendation:** Use **Outlines** integrated with llama-cpp-python. The efficiency gain from logit masking is significant over 8,000 files.39

### **5.3 Micro-Batching Architecture**

A naive script that loops through 8,000 files in a single process will almost certainly succumb to a memory leak—either in the Python garbage collector or the CUDA driver's memory allocator.18

* **The Solution:** Do not process all files in one run.  
* **Architecture:**  
  1. **Python Worker:** Writes a script that accepts a batch size (e.g., 200 files) and an offset. It loads the model, processes the batch, saves the results, and *terminates*.  
  2. **PowerShell Supervisor:** A wrapper script that loops indefinitely. It calls the Python worker, waits for it to exit, checks the exit code, and then launches the next batch.  
* **Benefit:** When the Python process terminates, the operating system unconditionally reclaims all VRAM and RAM. This guarantees a "clean slate" for every batch, completely neutralizing memory leaks.

### **5.4 Implementation Logic (Conceptual Code)**

**The Python Worker (classifier.py):**

Python

import os  
import sys  
import json  
from pydantic import BaseModel  
from typing import Literal  
\# Using llama\_cpp directly for granular control  
from llama\_cpp import Llama   
from outlines import models, generate

\# 1\. Define the Schema  
class FileClassification(BaseModel):  
    language: Literal\["python", "javascript", "rust", "go", "other"\]  
    purpose: Literal\["test", "logic", "config", "docs"\]  
    criticality: int \# 1-5 scale

\# 2\. Initialize Model (Fresh load every batch)  
\# n\_gpu\_layers=-1 pushes everything to GPU. n\_ctx must be large enough for files.  
llm \= Llama(  
    model\_path="models/qwen2.5-14b-instruct-q4\_k\_m.gguf",  
    n\_gpu\_layers=-1,   
    n\_ctx=8192,   
    verbose=False  
)

\# 3\. Create Outlines Generator  
\# Adapting llama-cpp model to Outlines (conceptual adaptation)  
model \= models.LlamaCpp(llm)   
generator \= generate.json(model, FileClassification)

def process\_batch(files):  
    results \=  
    for filepath in files:  
        with open(filepath, 'r') as f:  
            content \= f.read()\[:20000\] \# Truncate to context limit  
          
        \# Structured Generation  
        try:  
            result \= generator(f"Classify this code:\\n{content}")  
            results.append({"file": filepath, "data": result.dict()})  
        except Exception as e:  
            print(f"Error classifying {filepath}: {e}")  
              
    return results

\# Main execution logic to read batch arguments and save to JSONL

**The PowerShell Supervisor (run\_pipeline.ps1):**

PowerShell

$BatchSize \= 100  
$TotalFiles \= (Get-ChildItem \-Recurse "C:\\Repo").Count  
$Batches \= \[Math\]::Ceiling($TotalFiles / $BatchSize)

For ($i\=0; $i \-lt $Batches; $i\++) {  
    Write-Host "Starting Batch $i of $Batches..."  
      
    \# uv run ensures the correct Python environment is used  
    \# Arguments pass the offset to the script  
    uv run classifier.py \-\-batch-index $i \-\-batch-size $BatchSize  
      
    If ($LASTEXITCODE \-ne 0) {  
        Write-Host "Batch $i failed. Restarting after cool-down..."  
        Start-Sleep \-Seconds 30  
        $i\-- \# Retry this batch  
    }  
      
    \# Optional: Log memory status or rotate logs here  
}

## **6\. Windows 11 24H2 OS Engineering: Securing the Environment**

The final hurdle is the operating system itself. Windows 11 24H2 is designed for interactivity, not background compute.

### **6.1 The "Session 0" Isolation Barrier**

Windows services and scheduled tasks run in "Session 0." By default, Session 0 is isolated from the GPU driver to prevent "shatter attacks" (a legacy security vulnerability). This means a Python script running via Task Scheduler might fail to initialize CUDA, returning cudaGetDeviceCount() \== 0\.41

* **The Fix:** You must run the task as a **specific user** (your Admin account), *not* as the SYSTEM account. Furthermore, enabling "Run whether user is logged on or not" can sometimes still trigger Session 0 limitations depending on the driver version.43  
* **The "Interactive" Workaround:** For maximum reliability, configure the laptop to **Auto-Logon** (using Sysinternals Autologon) upon reboot. Then, set a startup script to immediately **Lock the Workstation** (rundll32.exe user32.dll,LockWorkStation). The scheduled task should be set to "Run only when user is logged on." This keeps the session in an interactive state (Session 1\) but secure (locked), ensuring full GPU driver access.44

### **6.2 Hardware Accelerated GPU Scheduling (HAGS) Conflict**

Windows 11 24H2 enables HAGS by default. While beneficial for gaming, HAGS offloads VRAM management to the GPU hardware scheduler. For CUDA compute workloads, this introduces a layer of opacity that can lead to "freezes" or instability during long context switching operations.

* **Registry Remediation:** It is strongly recommended to **Disable HAGS** for this dedicated batch machine. This can be done via Settings \> System \> Display \> Graphics \> Change default graphics settings, or via the registry key HKEY\_LOCAL\_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers (set HwSchMode to 1 for off).6 This forces the OS to use the legacy WDDM scheduler, which is more predictable for CUDA memory allocations.

### **6.3 Task Scheduler Robustness**

To ensure the pipeline recovers from power flickers or crashes:

* **Trigger:** Schedule the task daily (e.g., 2:00 AM).  
* **Conditions:** Uncheck "Start only if on AC power" (if you have battery backup, otherwise check it). Check "Wake the computer to run this task."  
* **Settings:** Enable "If the task fails, restart every: 1 minute." Attempt restart up to 3 times. This ensures that if a random glitch kills the supervisor script, it will self-heal.46

### **6.4 Operational Monitoring: Log Rotation**

Overnight logs can grow massive. A PowerShell script should be scheduled to run weekly to clean up old logs.

* **Script Logic:** Get-ChildItem "C:\\Logs" | Where-Object { $\_.LastWriteTime \-lt (Get-Date).AddDays(-7) } | Remove-Item.48  
* This simple maintenance script prevents disk exhaustion over months of operation.

## **7\. Operational Security and Future Outlook**

### **7.1 Security in the Age of Agentic AI**

While this pipeline is "local," security is still paramount. The rise of agentic tools like "OpenClaw" and "Dola.ai" in 2026 highlights the risks of giving AI autonomy.50 If the code being classified contains malicious prompts (Prompt Injection), a sophisticated model could potentially be tricked into executing code if the pipeline were designed to *execute* rather than just *classify*.

* **Mitigation:** The pipeline is strictly "Read-Only." The LLM analyzes text and outputs JSON. It has no tool use capabilities, no network access (firewalled via Windows Firewall), and no write access to the repository—only to the output JSON file.

### **7.2 Future Proofing**

The local LLM space moves fast.

* **NPU Integration:** Windows 11 24H2 is pushing NPU (Neural Processing Unit) support. Currently, NPUs are too weak for 14B models, but future updates to ONNX Runtime may allow offloading "prefill" (prompt processing) to the NPU, saving GPU resources for generation.52  
* **Model Upgrades:** The use of GGUF and llama-cpp-python makes upgrading easy. When Llama 5 or Qwen 4 drops, it is simply a matter of downloading the new .gguf file and updating the path in the script. The infrastructure remains unchanged.

## **8\. Conclusion and Actionable Recommendation**

For the specific objective of moving an overnight batch classification workload to a Windows 11 RTX 4090 Laptop, the optimal path is one of **simplicity and resilience**.

**Final Recommended Stack:**

* **Hardware:** RTX 4090 Laptop (16GB), HAGS Disabled, High Performance Power Plan.  
* **OS Config:** Windows 11 24H2, Auto-Logon \+ Lock Screen (to bypass Session 0 issues).  
* **Backend:** **llama-cpp-python** with **CUDA 12.4** wheels.  
* **Model:** **Qwen 2.5 14B Instruct (Q4\_K\_M GGUF)**.  
* **Orchestration:** **Python 3.13** managed by **uv**, wrapped in a **PowerShell** micro-batch supervisor script triggered by **Task Scheduler**.

This architecture avoids the fragility of WSL2 and the complexity of TensorRT-LLM, delivering a pipeline that is robust enough to run unattended night after night, turning a consumer laptop into a reliable enterprise-grade classification node.

### **8.1 Implementation Checklist**

1. **Environment:** Install uv. Run uv python install 3.13.  
2. **Drivers:** Install NVIDIA Studio Driver (version 570+ or stable 2026 release). Disable HAGS.  
3. **Dependencies:** uv pip install llama-cpp-python \--extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124.30 Install outlines and pydantic.  
4. **Model:** Download Qwen2.5-14B-Instruct-Q4\_K\_M.gguf from Hugging Face.  
5. **Scripting:** Write the Python worker and PowerShell supervisor.  
6. **Scheduling:** Configure Task Scheduler with the "Interactive/Lock" workaround.  
7. **Test:** Run a small batch (50 files) to validate VRAM usage and output structure.

This approach transforms the "Polyglot" repository analysis from a costly cloud dependency into a secure, owned asset.

#### **Referanser**

1. Benchmarking NVIDIA TensorRT-LLM \- Jan.ai, brukt februar 13, 2026, [https://www.jan.ai/post/benchmarking-nvidia-tensorrt-llm](https://www.jan.ai/post/benchmarking-nvidia-tensorrt-llm)  
2. Llama 4 GPU System Requirements (Scout, Maverick, Behemoth) \- ApX Machine Learning, brukt februar 13, 2026, [https://apxml.com/posts/llama-4-system-requirements](https://apxml.com/posts/llama-4-system-requirements)  
3. The Best GPUs for Local LLM Inference in 2025, brukt februar 13, 2026, [https://localllm.in/blog/best-gpus-llm-inference-2025](https://localllm.in/blog/best-gpus-llm-inference-2025)  
4. Why is ollama not utilizing my GPU (RTX 4090\) during inference? \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/ollama/comments/1d880b0/why\_is\_ollama\_not\_utilizing\_my\_gpu\_rtx\_4090/](https://www.reddit.com/r/ollama/comments/1d880b0/why_is_ollama_not_utilizing_my_gpu_rtx_4090/)  
5. Context Kills VRAM: How to Run LLMs on consumer GPUs | by Lyx | Medium, brukt februar 13, 2026, [https://medium.com/@lyx\_62906/context-kills-vram-how-to-run-llms-on-consumer-gpus-a785e8035632](https://medium.com/@lyx_62906/context-kills-vram-how-to-run-llms-on-consumer-gpus-a785e8035632)  
6. How to Disable Hardware Accelerated GPU Scheduling in Windows 11 \- YouTube, brukt februar 13, 2026, [https://www.youtube.com/watch?v=Vk0iChm8mnQ](https://www.youtube.com/watch?v=Vk0iChm8mnQ)  
7. qwen2.5:14b-instruct-q4\_K\_M \- Ollama, brukt februar 13, 2026, [https://ollama.com/library/qwen2.5:14b-instruct-q4\_K\_M](https://ollama.com/library/qwen2.5:14b-instruct-q4_K_M)  
8. Ollama VRAM Requirements: Complete 2026 Guide to GPU Memory for Local LLMs, brukt februar 13, 2026, [https://localllm.in/blog/ollama-vram-requirements-for-local-llms](https://localllm.in/blog/ollama-vram-requirements-for-local-llms)  
9. Top 5 Local LLM Tools and Models in 2026 \- DEV Community, brukt februar 13, 2026, [https://dev.to/lightningdev123/top-5-local-llm-tools-and-models-in-2026-1ch5](https://dev.to/lightningdev123/top-5-local-llm-tools-and-models-in-2026-1ch5)  
10. How to Run Kimi K2.5 Locally \- DataCamp, brukt februar 13, 2026, [https://www.datacamp.com/tutorial/how-to-run-kimi-k2-5-locally](https://www.datacamp.com/tutorial/how-to-run-kimi-k2-5-locally)  
11. Tested some popular GGUFs for 16GB VRAM target : r/LocalLLM \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLM/comments/1if3vn3/tested\_some\_popular\_ggufs\_for\_16gb\_vram\_target/](https://www.reddit.com/r/LocalLLM/comments/1if3vn3/tested_some_popular_ggufs_for_16gb_vram_target/)  
12. Q5 vs Q6 : r/LocalLLaMA \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1gu71lm/q5\_vs\_q6/](https://www.reddit.com/r/LocalLLaMA/comments/1gu71lm/q5_vs_q6/)  
13. My Learning Notes: Choosing the Right AI Model and Hardware \- DEV Community, brukt februar 13, 2026, [https://dev.to/mitchell\_cheng/my-learning-notes-choosing-the-right-ai-model-and-hardware-237](https://dev.to/mitchell_cheng/my-learning-notes-choosing-the-right-ai-model-and-hardware-237)  
14. vLLM, brukt februar 13, 2026, [https://docs.vllm.ai/](https://docs.vllm.ai/)  
15. PR for native Windows support was just submitted to vLLM : r/LocalLLaMA \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1jct1lk/pr\_for\_native\_windows\_support\_was\_just\_submitted/](https://www.reddit.com/r/LocalLLaMA/comments/1jct1lk/pr_for_native_windows_support_was_just_submitted/)  
16. Finding the Best Docker Image for vLLM Inference on CUDA 12.4 GPUs \- Runpod, brukt februar 13, 2026, [https://www.runpod.io/articles/guides/best-docker-image-vllm-inference-cuda-12-4](https://www.runpod.io/articles/guides/best-docker-image-vllm-inference-cuda-12-4)  
17. is there a performance difference in running ollama in windows vs wsl2? \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/ollama/comments/1gep2hb/is\_there\_a\_performance\_difference\_in\_running/](https://www.reddit.com/r/ollama/comments/1gep2hb/is_there_a_performance_difference_in_running/)  
18. Heaps do lie: debugging a memory leak in vLLM. \- Mistral AI, brukt februar 13, 2026, [https://mistral.ai/news/debugging-memory-leak-in-vllm](https://mistral.ai/news/debugging-memory-leak-in-vllm)  
19. Experiencing Memory Leak Issues with vLLM in Python: Seeking Advice and Solutions : r/LocalLLaMA \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1b7b4ak/experiencing\_memory\_leak\_issues\_with\_vllm\_in/](https://www.reddit.com/r/LocalLLaMA/comments/1b7b4ak/experiencing_memory_leak_issues_with_vllm_in/)  
20. NVIDIA/TensorRT-LLM: TensorRT LLM provides users with an easy-to-use Python API to define Large Language Models (LLMs) and supports state-of-the-art optimizations to perform inference efficiently on NVIDIA GPUs. TensorRT LLM also contains components to create Python and C++ runtimes that orchestrate the inference execution in a performant way. \- GitHub, brukt februar 13, 2026, [https://github.com/NVIDIA/TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM)  
21. TensorRT-LLM/windows/README.md at main \- GitHub, brukt februar 13, 2026, [https://github.com/nyunAI/TensorRT-LLM/blob/main/windows/README.md](https://github.com/nyunAI/TensorRT-LLM/blob/main/windows/README.md)  
22. NoGetting vLLM v0.9.2 working on CUDA 12.4 on QNAP (Driver 550.76) | by Daniel Voyce, brukt februar 13, 2026, [https://medium.com/@voycey/getting-vllm-v0-9-2-working-on-cuda-12-4-on-qnap-driver-550-76-37cdf3f04942](https://medium.com/@voycey/getting-vllm-v0-9-2-working-on-cuda-12-4-on-qnap-driver-550-76-37cdf3f04942)  
23. Install ONNX Runtime | onnxruntime, brukt februar 13, 2026, [https://onnxruntime.ai/docs/install/](https://onnxruntime.ai/docs/install/)  
24. ONNX Runtime | Home, brukt februar 13, 2026, [https://onnxruntime.ai/](https://onnxruntime.ai/)  
25. onnxruntime-genai \- PyPI, brukt februar 13, 2026, [https://pypi.org/project/onnxruntime-genai/](https://pypi.org/project/onnxruntime-genai/)  
26. Accelerating Phi-2, CodeLlama, Gemma and other Gen AI models with ONNX Runtime, brukt februar 13, 2026, [https://onnxruntime.ai/blogs/accelerating-phi-2](https://onnxruntime.ai/blogs/accelerating-phi-2)  
27. \`onnxruntime-genai\` generation speed very slow on int4 · Issue \#1098 \- GitHub, brukt februar 13, 2026, [https://github.com/microsoft/onnxruntime-genai/issues/1098](https://github.com/microsoft/onnxruntime-genai/issues/1098)  
28. Python bindings for llama.cpp \- GitHub, brukt februar 13, 2026, [https://github.com/abetlen/llama-cpp-python](https://github.com/abetlen/llama-cpp-python)  
29. Struggling with vLLM. The instructions make it sound so simple to run, but it's like my Kryptonite. I give up. : r/LocalLLaMA \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1loo2u3/struggling\_with\_vllm\_the\_instructions\_make\_it/](https://www.reddit.com/r/LocalLLaMA/comments/1loo2u3/struggling_with_vllm_the_instructions_make_it/)  
30. dougeeai/llama-cpp-python-wheels \- Hugging Face, brukt februar 13, 2026, [https://huggingface.co/dougeeai/llama-cpp-python-wheels](https://huggingface.co/dougeeai/llama-cpp-python-wheels)  
31. llama-cpp-python · PyPI, brukt februar 13, 2026, [https://pypi.org/project/llama-cpp-python/](https://pypi.org/project/llama-cpp-python/)  
32. astral-sh/uv: An extremely fast Python package and project manager, written in Rust. \- GitHub, brukt februar 13, 2026, [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv)  
33. Installation Guide for ExLlamaV2 (+ROCm) on Linux : r/LocalLLaMA \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1j7uxz0/installation\_guide\_for\_exllamav2\_rocm\_on\_linux/](https://www.reddit.com/r/LocalLLaMA/comments/1j7uxz0/installation_guide_for_exllamav2_rocm_on_linux/)  
34. Installing and managing Python | uv \- Astral Docs, brukt februar 13, 2026, [https://docs.astral.sh/uv/guides/install-python/](https://docs.astral.sh/uv/guides/install-python/)  
35. uv python install \--reinstall 3.13 \- Simon Willison's Weblog, brukt februar 13, 2026, [https://simonwillison.net/2025/Jan/7/uv-python-reinstall/](https://simonwillison.net/2025/Jan/7/uv-python-reinstall/)  
36. Why Instructor is the Best Library for Structured LLM Outputs, brukt februar 13, 2026, [https://python.useinstructor.com/blog/2024/03/05/zero-cost-abstractions/](https://python.useinstructor.com/blog/2024/03/05/zero-cost-abstractions/)  
37. Classifying Confidential Data with Local AI Models \- Instructor, brukt februar 13, 2026, [https://python.useinstructor.com/examples/local\_classification/](https://python.useinstructor.com/examples/local_classification/)  
38. dottxt-ai/outlines: Structured Outputs \- GitHub, brukt februar 13, 2026, [https://github.com/dottxt-ai/outlines](https://github.com/dottxt-ai/outlines)  
39. OpenAI's structured output vs. instructor and outlines \- Paul Simmering, brukt februar 13, 2026, [https://simmering.dev/blog/openai\_structured\_output/](https://simmering.dev/blog/openai_structured_output/)  
40. Large batch sizes memory leak in llama.cpp? \#5696 \- GitHub, brukt februar 13, 2026, [https://github.com/ggerganov/llama.cpp/discussions/5696](https://github.com/ggerganov/llama.cpp/discussions/5696)  
41. Windows Server 2025 – GPU Passthrough (DDA/GPU-P) not visible in Windows Admin Center \- Microsoft Learn, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/answers/questions/5566155/windows-server-2025-gpu-passthrough-(dda-gpu-p)-no](https://learn.microsoft.com/en-us/answers/questions/5566155/windows-server-2025-gpu-passthrough-\(dda-gpu-p\)-no)  
42. RDS sessions do not use the GPU with Microsoft Windows Server as guest OS, brukt februar 13, 2026, [https://docs.nvidia.com/vgpu/latest/known-issues/bug-no-id-no-gpu-utilization-windows-server-guests.html](https://docs.nvidia.com/vgpu/latest/known-issues/bug-no-id-no-gpu-utilization-windows-server-guests.html)  
43. Task Scheduler failed to start. Additional Data: Error Value: 2147943726 \- Stack Overflow, brukt februar 13, 2026, [https://stackoverflow.com/questions/44348330/task-scheduler-failed-to-start-additional-data-error-value-2147943726](https://stackoverflow.com/questions/44348330/task-scheduler-failed-to-start-additional-data-error-value-2147943726)  
44. Microsoft Windows Server \- NVIDIA Docs, brukt februar 13, 2026, [https://docs.nvidia.com/vgpu/18.0/grid-vgpu-release-notes-microsoft-windows-server/index.html](https://docs.nvidia.com/vgpu/18.0/grid-vgpu-release-notes-microsoft-windows-server/index.html)  
45. Performance decreases after upgrading from windows 10 to windows 11, brukt februar 13, 2026, [https://forums.developer.nvidia.com/t/performance-decreases-after-upgrading-from-windows-10-to-windows-11/255036](https://forums.developer.nvidia.com/t/performance-decreases-after-upgrading-from-windows-10-to-windows-11/255036)  
46. How to solve a Windows 10 Scheduler error \[closed\] \- Stack Overflow, brukt februar 13, 2026, [https://stackoverflow.com/questions/48255882/how-to-solve-a-windows-10-scheduler-error](https://stackoverflow.com/questions/48255882/how-to-solve-a-windows-10-scheduler-error)  
47. Windows Scheduled task succeeds but returns result 0x1 \- Stack Overflow, brukt februar 13, 2026, [https://stackoverflow.com/questions/18370547/windows-scheduled-task-succeeds-but-returns-result-0x1](https://stackoverflow.com/questions/18370547/windows-scheduled-task-succeeds-but-returns-result-0x1)  
48. Powershell Script to clean up logs on a Monthly Basis \- Stack Overflow, brukt februar 13, 2026, [https://stackoverflow.com/questions/65604374/powershell-script-to-clean-up-logs-on-a-monthly-basis](https://stackoverflow.com/questions/65604374/powershell-script-to-clean-up-logs-on-a-monthly-basis)  
49. How to delete a log every 7 days? : r/PowerShell \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/PowerShell/comments/35abkn/how\_to\_delete\_a\_log\_every\_7\_days/](https://www.reddit.com/r/PowerShell/comments/35abkn/how_to_delete_a_log_every_7_days/)  
50. OpenClaw Is a Preview of Why Governance Matters More Than Ever \- CloudBees, brukt februar 13, 2026, [https://www.cloudbees.com/blog/openclaw-is-a-preview-of-why-governance-matters-more-than-ever](https://www.cloudbees.com/blog/openclaw-is-a-preview-of-why-governance-matters-more-than-ever)  
51. Built a comparison: OpenClaw vs memory-first local agent \[results inside\] \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1qy2fwe/built\_a\_comparison\_openclaw\_vs\_memoryfirst\_local/](https://www.reddit.com/r/LocalLLaMA/comments/1qy2fwe/built_a_comparison_openclaw_vs_memoryfirst_local/)  
52. GPU Comparison \- LLM Tracker, brukt februar 13, 2026, [https://llm-tracker.info/GPU-Comparison](https://llm-tracker.info/GPU-Comparison)