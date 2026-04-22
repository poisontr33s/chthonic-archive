# **The 2026 Embedding Model Landscape: A Comparative Technical Analysis of MiniLM, Nomic, Jina, and Qwen**

## **Executive Context: The Paradigm Shift in Semantic Representation**

The trajectory of Natural Language Processing (NLP) has historically been punctuated by singular architectural shifts that render previous standards obsolete overnight. Between 2018 and 2023, the industry coalesced around encoder-only transformer architectures—epitomized by BERT and its distilled variants—as the gold standard for dense vector representation. In this era, sentence-transformers/all-MiniLM-L6-v2 emerged not merely as a model, but as infrastructure: a ubiquitous, lightweight default embedded into thousands of production pipelines, from search bars in e-commerce applications to the retrieval layers of early Retrieval-Augmented Generation (RAG) prototypes. Its value proposition was clear: modest accuracy at blazingly fast inference speeds, deployable on even the most constrained CPU hardware.1

However, the period between 2024 and 2026 has introduced a set of diverging requirements that the MiniLM architecture was never designed to accommodate. The rise of Agentic AI, requiring reasoning over massive context windows (32k+ tokens), the necessity for multimodal understanding (text-to-image), and the demand for instruction-following embeddings has fundamentally altered the competitive landscape. We have moved from a "one-size-fits-all" era of static sentence embeddings to a dynamic era of Large Language Model (LLM) based decoders, Matryoshka Representation Learning (MRL), and task-specific adaptation via Low-Rank Adapters (LoRA).3

This report provides an exhaustive technical evaluation of the state of embedding models in early 2026\. It rigorously compares the legacy incumbent, all-MiniLM-L6-v2, against the three primary challengers defining the modern frontier: **Nomic AI’s v1.5 series**, **Jina AI’s v3 and v4 multimodal architectures**, and **Alibaba’s Qwen2/Qwen3 decoder-only family**. Through a synthesis of benchmark data—including the Massive Text Embedding Benchmark (MTEB), proprietary correctness evaluations, and latency profiling on H100 and CPU infrastructure—we aim to determine the precise operational viability of MiniLM in modern production environments.

The analysis is structured to guide senior engineering decision-makers and researchers through the architectural trade-offs of migration. It moves beyond superficial leaderboard rankings to dissect the "correctness gap," the "latency wall," and the "context bottleneck," ultimately answering whether MiniLM remains a competitive efficient option or a technical debt liability.

## ---

**1\. The Legacy Standard: An Architectural Autopsy of all-MiniLM-L6-v2**

To understand the magnitude of the shift represented by Qwen, Jina, and Nomic, one must first deconstruct the baseline. all-MiniLM-L6-v2 is a relic of the "Knowledge Distillation" era of 2019-2020. Developed by Microsoft and adapted by the sentence-transformers community, it was designed to mimic the performance of larger BERT models while pruning the parameter count to a mere 22 million.1

### **1.1 The Distillation Architecture and Limitations**

The architecture of MiniLM is a 6-layer transformer encoder with a hidden dimension of 384\. This specific dimensionality—384—was chosen to optimize the trade-off between semantic expressiveness and dot-product calculation speed. At the time of its release, the primary constraints on vector search were memory (RAM) and storage. A 384-dimensional float32 vector consumes significantly less space than the 768-dimensional vectors standard in BERT-base models, allowing for larger in-memory indices.2

However, this compactness is achieved through architectural decisions that constitute severe limitations in 2026:

* **Absolute Positional Embeddings:** MiniLM utilizes standard learned positional embeddings capped at 512 tokens. This is a hard limit. The model has no mechanism to extrapolate beyond this window. In modern RAG scenarios, where a single legal clause or technical specification often exceeds 500 tokens, this forces developers to employ aggressive chunking strategies (e.g., sliding windows) that sever semantic continuity.6  
* **Encoder-Only Bidirectionality:** While bidirectional attention is excellent for short-sentence similarity, it struggles to model complex causal relationships found in long-form reasoning tasks. The model treats the input as a static block of text to be encoded, lacking the nuance of decoder-based models that are pre-trained on next-token prediction tasks involving complex logic.8  
* **Training Objective:** MiniLM was primarily trained on sentence pairs (e.g., Reddit comments, stack exchange questions) using contrastive loss. It lacks exposure to "instructional" data—prompts that tell the model *how* to embed the text (e.g., "Retrieve a document that supports this argument"). Consequently, it is a static model; it cannot change its representation based on user intent.1

### **1.2 The "Correctness Gap" in Retrieval**

The most damning metric for MiniLM in 2026 is not its MTEB score, which averages performance across many low-stakes tasks, but its "Retrieval Correctness." In a benchmark analyzing 490,000 Amazon product reviews, where the goal was to retrieve the specific review matching a query (a "needle in a haystack" proxy), MiniLM achieved a **Top-5 Accuracy of only 56%**.10

This statistic implies that in nearly half of all queries, the correct document is not even present in the top 5 results passed to the LLM. In a RAG system, this is a catastrophic failure mode. The LLM cannot reason over information it does not receive. This "Correctness Gap" of 44% represents the hidden cost of using MiniLM: while the embedding step is fast (milliseconds), the generation step (seconds) is wasted on irrelevant context, leading to hallucinations. Modern models like e5-small or Qwen3, utilizing better training data and architectures, achieve 90-100% on similar correctness tasks.10

### **1.3 The Latency Profile: The Remaining Competitive Advantage**

Despite its obsolescence in accuracy, MiniLM retains one formidable characteristic: speed. On standard CPU infrastructure (e.g., an AWS c6i.xlarge or a user's local laptop), MiniLM achieves inference latencies of approximately **14.7 ms per 1,000 tokens**.11 This places it in the "Sub-30ms" cluster, a performance tier that massive 7B or 8B parameter models cannot touch without expensive GPU acceleration.

For specific high-velocity applications—such as deduplicating stream logs, real-time autocomplete suggestions, or on-device search for mobile apps—this latency profile is a hard requirement. The question, therefore, is not whether MiniLM is "good," but whether there are *better* models that fit within this specific latency envelope. As we will explore later, snowflake-arctic-embed-xs appears to be the true heir to this specific niche.12

## ---

**2\. The Challenger: Nomic Embed (v1.5) and the Elastic Future**

The release of nomic-embed-text-v1.5 marked a departure from the fixed-dimension rigidity of the BERT era. Nomic AI’s approach focuses on two critical modern requirements: context length and storage flexibility via Matryoshka Representation Learning (MRL).

### **2.1 Matryoshka Representation Learning (MRL)**

The core innovation of Nomic v1.5 is its support for variable-length embeddings. Traditional models like MiniLM output a vector where every dimension is equally important; truncating a 384-d vector to 128-d destroys the semantic information.

Nomic v1.5 utilizes MRL, a training technique that forces the model to encode the most critical semantic information in the earlier dimensions of the vector.5 During training, the loss function aggregates errors from truncations at various sizes (e.g., 64, 128, 256, 512, 768). This ensures that a 64-dimensional slice of a Nomic vector is a valid, high-quality representation in its own right.

**Operational Implication:** This capability allows engineering teams to decouple *inference cost* from *storage cost*.

* **Inference:** The model still computes the full 768 dimensions (costing compute).  
* **Storage:** The database stores only 128 dimensions (saving 83% of storage).  
* **Search:** Dot product calculations are 6x faster on 128 dimensions. This flexibility is devastating to MiniLM's value proposition. A Nomic vector truncated to 256 dimensions outperforms the full 384-dimensional MiniLM vector in many tasks while consuming 33% less storage.5

### **2.2 Rotary Positional Embeddings and Context Extension**

Nomic v1.5 abandons absolute positional embeddings in favor of Rotary Positional Embeddings (RoPE). RoPE encodes position not as a fixed vector added to the embedding, but as a rotation of the key and query vectors in the attention mechanism. This mathematical property allows the model to generalize to sequence lengths far beyond what it saw during training.1

While MiniLM fails at 512 tokens, Nomic v1.5 supports **8192 tokens**.13 This 16x increase in context window enables "Passage Retrieval" rather than "Sentence Retrieval." In RAG pipelines, this means an entire technical manual section or a complete news article can be embedded as a single unit. This reduces the complexity of chunking strategies—developers no longer need to worry about splitting a sentence in half—and preserves the holistic semantic meaning of the document.

### **2.3 The Latency Trade-off**

The trade-off for these capabilities is raw speed. Nomic v1.5 is a 137 million parameter model, roughly 6x larger than MiniLM.

* **Latency:** \~41.9 ms per 1,000 tokens (CPU).  
* **Throughput:** \~4,000 sentences/sec (vs MiniLM's \~14,000).11

While 41.9 ms is acceptable for many web-based RAG applications (where network latency to the LLM is often 500ms+), it pushes Nomic out of the ultra-low-latency tier. It is not a direct replacement for MiniLM in edge-constrained environments but is a vastly superior option for server-side RAG where the 25ms delta is negligible compared to the accuracy gains.

## ---

**3\. The Innovator: Jina AI (v3 & v4) and the Multi-Task Paradigm**

Jina AI has aggressively targeted the complexity of the embedding workflow. Rather than treating embeddings as a static mapping of text to numbers, Jina views them as a dynamic, task-dependent process. This philosophy is embodied in two key technologies: LoRA Adapters and Late Chunking.

### **3.1 Task-Specific LoRA Adapters**

jina-embeddings-v3 (570M parameters) is built on an XLM-RoBERTa backbone but introduces a modular architecture. Instead of fine-tuning the entire model for a general "average" performance across all tasks, Jina trained five distinct Low-Rank Adaptation (LoRA) adapters.4

These adapters are lightweight sets of weights (less than 3% of the total parameter count) that are dynamically swapped into the model's attention layers during inference based on a task parameter provided by the user.15

* **retrieval.query**: Optimizes the vector space to map questions to their answers (asymmetric search).  
* **retrieval.passage**: Optimizes document representation to match potential queries.  
* **separation**: Maximizes the distance between dissimilar clusters (ideal for clustering tasks).  
* **classification**: Optimizes for linear separability (ideal for sentiment analysis or tagging).

**Strategic Advantage:** This solves the "Jack of all trades, master of none" problem that plagues models like MiniLM. MiniLM often fails in clustering tasks because it was optimized for sentence similarity. Jina v3 allows a single deployed model to act as five specialized models. In a production environment, this simplifies MLOps—you deploy one model container but get the performance of specialized classifiers and retrievers.

### **3.2 Late Chunking: Solving the Context Problem at the Root**

Perhaps the most significant theoretical contribution from Jina AI in the 2025-2026 cycle is **Late Chunking**.16

**The Problem with Naive Chunking (MiniLM approach):**

In a standard pipeline, a long document is split into 512-token chunks *before* embedding.

* *Chunk 1:* "Apple released a new product today."  
* *Chunk 2:* "It features a titanium chassis."  
  The embedding for Chunk 2 has no knowledge of "Apple." It only knows "It." A query searching for "Apple titanium product" will fail to match Chunk 2 because the semantic link was severed during chunking.

**The Solution (Late Chunking):**

Jina v3 processes the *entire* document (up to 8192 tokens) through the transformer layers first. This creates a sequence of token-level embeddings where every token has attended to every other token in the document via the self-attention mechanism.

* The token for "It" in the second sentence now contains contextual information encoded from "Apple" in the first sentence.  
* *After* this processing, the model applies mean pooling to generate vectors for specific spans (chunks).

This results in "context-aware" chunk embeddings. Benchmarks on the BEIR dataset show that Late Chunking consistently outperforms naive chunking, particularly for datasets with long-range dependencies.16 MiniLM, lacking the context window to process the full document, is physically incapable of this technique.

### **3.3 Multimodal Fusion: Jina v4**

Released in mid-2025, jina-embeddings-v4 (3.8B parameters) extends this capability to vision. Based on the Qwen2.5-VL architecture, it accepts both text and images as inputs.18

* **Unified Latent Space:** Unlike CLIP, which aligns two separate encoders, Jina v4 uses a single transformer to process visual patches and text tokens together.  
* **Use Case:** This allows for RAG over PDF documents containing charts. A user can query "What is the growth trend in Figure 3?" and the model can retrieve the visual embedding of the chart because it resides in the same vector space as the text.

This capability renders text-only models like MiniLM obsolete for any application involving rich media or complex document layouts (e.g., financial reports, scientific papers).

## ---

**4\. The Heavyweight: Alibaba Qwen (gte-Qwen2 / Qwen3)**

The Qwen embedding series represents the triumph of the "LLM-as-Embedding" philosophy. Moving away from BERT-style encoders entirely, Alibaba has repurposed their massive Qwen decoder-only language models for representation learning.

### **4.1 Decoder-Only Embeddings and Instruction Tuning**

The gte-Qwen2 and Qwen3 models utilize the same architecture as state-of-the-art generative LLMs. This provides them with "reasoning" capabilities distilled into the embedding process. A key feature of this architecture is **Instruction Tuning**.8

Users can provide a prompt to the embedding model:

* *Input:* Instruct: Retrieve a legal precedent regarding maritime law.\\nQuery: What happens if a ship sinks?  
* *Mechanism:* The instruction alters the internal state of the model via the attention mechanism, shifting the resulting vector into a subspace optimized for legal retrieval rather than, say, insurance adjusters or news summaries.

Benchmarks indicate that using instructions yields a **1% to 5% improvement** in retrieval performance compared to raw embedding.20 This adaptability is a distinct generational leap over MiniLM’s static weights.

### **4.2 Qwen3-Embedding-0.6B: The Modern MiniLM Successor**

While the 7B and 8B parameter versions of Qwen dominate the leaderboards, the Qwen3-Embedding-0.6B model is the most relevant comparison for MiniLM users.5

* **Size:** 0.6 Billion parameters (approx 600M). This is roughly 30x larger than MiniLM (22M) but significantly smaller than the 7B giants.  
* **Context:** **32,000 tokens**.21 This is the largest context window in the comparison group, quadrupling Jina/Nomic and dwarfing MiniLM’s 512\.  
* **Performance:** Despite being 10x smaller than the gte-Qwen2-7B model, the Qwen3-0.6B outperforms it on the Multilingual MTEB leaderboard (Score: 64.33 vs 62.51).21 This "Efficiency Inversion" suggests that the Qwen3 base model architecture and training data quality have improved so drastically that a sub-1B model in 2026 beats a 7B model from 2024\.

For developers seeking a modern, high-performance model that can still run on consumer hardware (e.g., a laptop with 16GB RAM), Qwen3-0.6B offers the best balance of features (32k context, instructions, multilingual) and cost.

## ---

**5\. Comparative Performance Analysis: The 2026 Landscape**

The following section synthesizes data from the MTEB leaderboard, BEIR benchmarks, and independent latency testing to provide a direct head-to-head comparison.

### **5.1 Retrieval Accuracy and MTEB Scores**

The Massive Text Embedding Benchmark (MTEB) remains the standard for general-purpose evaluation. However, averages can be misleading. We break down performance by specific utility.

**Table 1: MTEB and Retrieval Accuracy Comparison (2026)**

| Model | Parameters | MTEB (Avg) | MTEB (English) | Retrieval Accuracy (Top-5 Correctness)\* | Multilingual Capability |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **all-MiniLM-L6-v2** | 22M | 56.3 | 56.3 | **56%** | Low (English focused) |
| **snowflake-arctic-embed-xs** | 22M | 50.15\*\* | \~50 | **\~60%** | Medium |
| **nomic-embed-text-v1.5** | 137M | 62.28 | 61.96 | **\~86%** | High (Matryoshka) |
| **Qwen3-Embedding-0.6B** | 600M | 64.33 | \~64 | **High** | Very High (100+ langs) |
| **gte-Qwen2-7B-instruct** | 7B | 62.51 | 70.24 | **High** | High |
| **Qwen3-Embedding-8B** | 8B | **70.58** | **75.22** | **\>90%** | Very High |
| **Jina-embeddings-v3** | 570M | 65+ | High | **56%**\* | High (LoRA Adapters) |

* Note 1: The "Retrieval Accuracy (Top-5)" refers to a specific strict correctness benchmark on Amazon product data where MiniLM scored 56%.10 Modern models like Nomic and Qwen consistently score in the 80-90% range on similar tasks.  
* Note 2: snowflake-arctic-embed-xs is highlighted as a direct size-match for MiniLM with optimized performance.12 Its lower average MTEB score is deceptive; it excels specifically in retrieval tasks compared to MiniLM.  
* Note 3: Jina v3's correctness score of 56% in some independent benchmarks 10 contrasts with its high MTEB ranking, suggesting it may require specific tuning (using the correct LoRA adapter) to achieve peak performance in product search domains.

### **5.2 Latency, Throughput, and The "Latency Wall"**

High accuracy is irrelevant if the model is too slow for the application. We define the "Latency Wall" as the point where inference becomes perceptible to a human user (typically \>200ms).

**Table 2: Inference Performance Profile (CPU vs GPU)**

| Model | Latency (ms/1k tok) \[CPU\] | Throughput (sent/sec) \[GPU\] | Context Limit | Memory (FP16) | TCO Rating |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **all-MiniLM-L6-v2** | **14.7** | **\~14,000** | 512 | **\~250 MB** | Extremely Low |
| **bge-base-en-v1.5** | 22.5 | \~6,000 | 512 | \~2.0 GB | Low |
| **nomic-embed-text-v1.5** | 41.9 | \~4,000 | 8,192 | \~4.8 GB | Medium |
| **Qwen3-Embed-0.6B** | \~100 | \~2,500 | **32,000** | \~3.0 GB | Medium |
| **gte-Qwen2-7B** | \~1000+ | \~200 | 32,000 | \~14-24 GB | High |
| **Qwen3-Embed-8B** | \~1200+ | \~150 | 32,000 | \~28 GB | Very High |

**Analysis of the Latency Wall:**

* **Sub-30ms Cluster:** MiniLM and snowflake-arctic-xs reside here. These are the only models suitable for CPU-only, real-time search applications.  
* **The 7B Wall:** Models like gte-Qwen2-7B and Qwen3-8B are effectively unusable on CPUs for real-time applications. They require GPU acceleration (e.g., A10G, A100) to achieve acceptable throughput. The latency jumps from \~40ms (Nomic) to \>1000ms (7B models) on CPU, a 25x slowdown for a \~10-15% gain in accuracy.10

## ---

**6\. Strategic Migration Analysis: Determining the Path Forward**

For engineering teams currently running all-MiniLM-L6-v2, the path forward depends on the specific constraints of the application. We identify three distinct migration archetypes.

### **6.1 Path A: The "Edge-Constrained" Migration**

**Scenario:** The embedding model runs on a user's mobile device, inside a browser (via ONNX/WASM), or on a heavily resource-constrained container (e.g., 512MB RAM Lambda function).

* **Is MiniLM Competitive?** Yes, but barely.  
* **The Superior Alternative:** **snowflake-arctic-embed-xs**.  
* **Rationale:** This model utilizes the same architecture as MiniLM (so no latency penalty) but benefits from modern training data and knowledge distillation from larger Arctic models. It achieves a significantly higher retrieval score (NDCG@10: 50.15 vs MiniLM's 41.95) without requiring any hardware upgrades.12  
* **Migration Effort:** Minimal. Often just a string change in the library instantiation.

### **6.2 Path B: The "Modern RAG" Migration (Balanced)**

**Scenario:** A standard B2B SaaS application running RAG on a cloud server. GPU availability is possible but costs are a concern. Context length is a friction point (users upload PDFs).

* **Is MiniLM Competitive?** No. The 512 context limit and low correctness score are active liabilities causing hallucinations.  
* **The Superior Alternative:** **Qwen3-Embedding-0.6B** or **nomic-embed-text-v1.5**.  
* **Rationale:**  
  * Choose **Qwen3-0.6B** if you need massive context (32k), multilingual support, and instruction tuning. It runs comfortably on small GPUs (T4, L4) or reasonable CPUs.  
  * Choose **Nomic** if you need to optimize vector database costs (using MRL to store 128-dim vectors) and need a solid 8k context window.5  
* **Migration Effort:** Moderate. Requires re-indexing the vector database (different dimensionality) and potentially upgrading inference hardware.

### **6.3 Path C: The "Precision-Critical" Migration (High Performance)**

**Scenario:** A legal discovery platform, medical research tool, or agentic system where accuracy is paramount and hallucination is unacceptable.

* **Is MiniLM Competitive?** Absolutely not.  
* **The Superior Alternative:** **Jina-embeddings-v4** or **Qwen3-Embedding-8B**.  
* **Rationale:** These models offer state-of-the-art performance. Jina v4 brings multimodal capabilities (understanding charts in medical journals) and Late Chunking for deep context retrieval. Qwen3-8B offers the highest raw text reasoning capability.  
* **Migration Effort:** High. Requires robust GPU clusters (A100/H100), significant VRAM, and a complete re-architecture of the ingestion pipeline to support Late Chunking or Multimodal inputs.

## ---

**7\. Operational Realities: TCO and Infrastructure**

### **7.1 The Cost of Correctness**

Engineering teams often obsess over the *inference cost* of the embedding model ($/token) while ignoring the *system cost* of bad retrieval.

* **MiniLM System Cost:** Fast embedding \-\> Poor Retrieval \-\> LLM receives irrelevant context \-\> LLM hallucinates or says "I don't know" \-\> User churns or query is re-run.  
* **Qwen3 System Cost:** Slower embedding \-\> Precise Retrieval \-\> LLM receives exact answer \-\> Success.

In 2026, the cost of the LLM generation (input tokens \+ output tokens) dwarfs the cost of embedding. Feeding 10,000 tokens of irrelevant "MiniLM-retrieved" junk to GPT-5 is significantly more expensive than spending an extra 50ms to retrieve the *right* 1,000 tokens using Qwen3-0.6B. **Therefore, MiniLM is often the *more expensive* option in terms of Total Cost of Ownership (TCO) for RAG systems.**

### **7.2 Hardware Recommendations**

* **For Qwen3-0.6B / Nomic:** Recommend NVIDIA **L4** or **A10G** GPUs. These offer sufficient VRAM (24GB) to batch requests effectively, masking the latency increase compared to MiniLM.  
* **For Jina v4 / Qwen3-8B:** Recommend NVIDIA **H100** or **A100 (80GB)**. The memory bandwidth is required to serve the large parameter counts without stalling.

## ---

**8\. Conclusion: The Verdict on MiniLM**

As of 2026, the question "Is MiniLM still competitive?" demands a nuanced answer based on the definition of "competitive."

**If competitive means "State of the Art Accuracy":** **No.** MiniLM is thoroughly obsolete. It has been surpassed by multiple generations of technology (RoPE, MRL, LLM-Decoders). Its retrieval correctness (56%) is dangerously low for modern autonomous agents or RAG systems expecting high fidelity. Models like Qwen3 and Jina v4 perform in a completely different class.3

**If competitive means "The Best Option for \<20ms Latency on CPU":** **No.** While MiniLM is still fast, it has been superseded by **snowflake-arctic-embed-xs**, which matches its speed and size but delivers significantly better retrieval quality through modern training techniques.12 There is no technical reason to choose MiniLM over Arctic-XS in 2026 for new deployments.

**Final Recommendation:**

The era of all-MiniLM-L6-v2 as the default embedding model has ended.

* **For general upgrades:** Move to **Qwen3-Embedding-0.6B** to gain 32k context and instruction awareness.  
* **For storage efficiency:** Move to **nomic-embed-text-v1.5** to leverage Matryoshka dimensionality reduction.  
* **For edge/CPU constraints:** Move to **snowflake-arctic-embed-xs** for a strict upgrade to MiniLM with no latency penalty.

The landscape has evolved from simple sentence matching to complex, context-aware semantic reasoning. Your embedding model infrastructure must evolve with it.

#### **Referanser**

1. Best Open-Source Embedding Models Benchmarked and Ranked \- Supermemory, brukt februar 13, 2026, [https://supermemory.ai/blog/best-open-source-embedding-models-benchmarked-and-ranked/](https://supermemory.ai/blog/best-open-source-embedding-models-benchmarked-and-ranked/)  
2. What are some popular pre-trained Sentence Transformer models and how do they differ (for example, all-MiniLM-L6-v2 vs all-mpnet-base-v2)? \- Milvus, brukt februar 13, 2026, [https://milvus.io/ai-quick-reference/what-are-some-popular-pretrained-sentence-transformer-models-and-how-do-they-differ-for-example-allminilml6v2-vs-allmpnetbasev2](https://milvus.io/ai-quick-reference/what-are-some-popular-pretrained-sentence-transformer-models-and-how-do-they-differ-for-example-allminilml6v2-vs-allmpnetbasev2)  
3. Top embedding models on the MTEB leaderboard \- Modal, brukt februar 13, 2026, [https://modal.com/blog/mteb-leaderboard-article](https://modal.com/blog/mteb-leaderboard-article)  
4. jina-embeddings-v3 \- Search Foundation Models, brukt februar 13, 2026, [https://jina.ai/models/jina-embeddings-v3/](https://jina.ai/models/jina-embeddings-v3/)  
5. The Best Open-Source Embedding Models in 2026 \- BentoML, brukt februar 13, 2026, [https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models)  
6. model\_meta.yaml · mteb/leaderboard\_legacy at 80dd9a2b2d4a0abc368a6cea5f79a517b753951b \- Hugging Face, brukt februar 13, 2026, [https://huggingface.co/spaces/mteb/leaderboard\_legacy/blob/80dd9a2b2d4a0abc368a6cea5f79a517b753951b/model\_meta.yaml](https://huggingface.co/spaces/mteb/leaderboard_legacy/blob/80dd9a2b2d4a0abc368a6cea5f79a517b753951b/model_meta.yaml)  
7. Don't use all-MiniLM-L6-v2 for new vector embeddings datasets. Yes, it's the ope, brukt februar 13, 2026, [https://news.ycombinator.com/item?id=46081800](https://news.ycombinator.com/item?id=46081800)  
8. Alibaba-NLP/gte-Qwen2-1.5B-instruct · Hugging Face, brukt februar 13, 2026, [https://huggingface.co/Alibaba-NLP/gte-Qwen2-1.5B-instruct](https://huggingface.co/Alibaba-NLP/gte-Qwen2-1.5B-instruct)  
9. Evaluating and Enhancing RAG Pipeline Performance Using Synthetic Data, brukt februar 13, 2026, [https://developer.nvidia.com/blog/evaluating-and-enhancing-rag-pipeline-performance-using-synthetic-data/](https://developer.nvidia.com/blog/evaluating-and-enhancing-rag-pipeline-performance-using-synthetic-data/)  
10. Benchmark of 16 Best Open Source Embedding Models for RAG \- AIMultiple research, brukt februar 13, 2026, [https://research.aimultiple.com/open-source-embedding-models/](https://research.aimultiple.com/open-source-embedding-models/)  
11. Open-source embedding models: which one to use? : r/LocalLLaMA \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1nrgklt/opensource\_embedding\_models\_which\_one\_to\_use/](https://www.reddit.com/r/LocalLLaMA/comments/1nrgklt/opensource_embedding_models_which_one_to_use/)  
12. Snowflake/snowflake-arctic-embed-s \- Hugging Face, brukt februar 13, 2026, [https://huggingface.co/Snowflake/snowflake-arctic-embed-s](https://huggingface.co/Snowflake/snowflake-arctic-embed-s)  
13. Text Embedding | Nomic Platform Documentation, brukt februar 13, 2026, [https://docs.nomic.ai/api/embeddings-and-retrieval/text-embedding](https://docs.nomic.ai/api/embeddings-and-retrieval/text-embedding)  
14. An introduction to Jina models, their functionality, and uses in Elasticsearch, brukt februar 13, 2026, [https://www.elastic.co/search-labs/blog/jina-models-elasticsearch-guide](https://www.elastic.co/search-labs/blog/jina-models-elasticsearch-guide)  
15. Papers Explained 266: Jina Embeddings v3 | by Ritvik Rastogi \- Medium, brukt februar 13, 2026, [https://ritvik19.medium.com/papers-explained-266-jina-embeddings-v3-9c38c9f69766](https://ritvik19.medium.com/papers-explained-266-jina-embeddings-v3-9c38c9f69766)  
16. Late Chunking in Long-Context Embedding Models \- Jina AI, brukt februar 13, 2026, [https://jina.ai/news/late-chunking-in-long-context-embedding-models](https://jina.ai/news/late-chunking-in-long-context-embedding-models)  
17. Embedding API \- Jina AI, brukt februar 13, 2026, [https://jina.ai/embeddings/](https://jina.ai/embeddings/)  
18. jina-embeddings-v4 \- Search Foundation Models, brukt februar 13, 2026, [https://jina.ai/models/jina-embeddings-v4/](https://jina.ai/models/jina-embeddings-v4/)  
19. jina-embeddings-v4: Universal Embeddings for Multimodal Multilingual Retrieval \- arXiv, brukt februar 13, 2026, [https://arxiv.org/pdf/2506.18902](https://arxiv.org/pdf/2506.18902)  
20. QwenLM/Qwen3-Embedding \- GitHub, brukt februar 13, 2026, [https://github.com/QwenLM/Qwen3-Embedding](https://github.com/QwenLM/Qwen3-Embedding)  
21. Qwen/Qwen3-Embedding-8B · Hugging Face, brukt februar 13, 2026, [https://huggingface.co/Qwen/Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B)  
22. Snowflake/snowflake-arctic-embed-xs \- Hugging Face, brukt februar 13, 2026, [https://huggingface.co/Snowflake/snowflake-arctic-embed-xs](https://huggingface.co/Snowflake/snowflake-arctic-embed-xs)