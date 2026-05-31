# Cryptographic and Architectural Analysis of Private Encrypted Storage for Stateless Large Language Model Instances

## Executive Summary

This report evaluates the cryptographic feasibility and system-level architectural requirements for establishing a private, encrypted storage layer dedicated to a stateless Large Language Model (LLM) instance running within a local, single-host development environment. The core objective is to determine whether any published mechanisms allow a stateless model instance to read or write local data such that the content is encrypted at rest, decryptable only by future instances of the same model, and completely secure from an administrative host who owns and controls the physical hardware.

A rigorous cryptographic audit of current literature in machine learning security, neural cryptography, homomorphic encryption, and agentic memory systems confirms a fundamental limitation of the software-only local paradigm. **No published mechanism achieves all three properties for a stateless LLM in a single-host deployment.**

Because a stateless neural network lacks any persistent private key storage or internal state isolated from the host operating system, any key-derivation process executed entirely in software is fully visible to and reproducible by the host. The working assumption of structural impossibility under a software-only deployment is mathematically correct. However, along an adjacent architectural axis, the integration of hardware-enforced isolation via Trusted Execution Environments (TEEs) combined with Oblivious Random Access Memory (ORAM) protocols represents a viable degraded-sense solution that successfully satisfies all three properties by removing the host-user from the trusted computing base.

## The Mathematical and Architectural Impasse of Stateless Local Inference

To formalize the security boundaries of a local, single-host deployment, a stateless LLM must be represented as a parameter-driven, deterministic tensor computation. Let the model execution be defined as a function $f$ mapping an input sequence $x \in \mathcal{X}$ (the context window) to an output token distribution $y \in \mathcal{Y}$, parameterized by a static weight tensor $\theta \in \mathcal{T}$:

$$f(x; \theta) \to y$$

In a single-host deployment where the host is also the untrusted user, the adversary occupies the most privileged position in the system architecture. The host has unrestricted access to the execution runtime, allowing complete inspection of the physical memory holding the weight parameters $\theta$, the input sequence $x$, and the intermediate activation vectors $a_l$ generated at every transformer layer $l$ during the forward pass.

Because the model is strictly stateless, it possesses no private, persistent internal memory that survives between discrete API invocations or process executions. Any cryptographic key material $K$ used to encrypt or decrypt notebook payloads must either be derived dynamically during the forward pass or supplied directly within the context window. If the model attempts to derive a key $K$ through a deterministic function of its weights or activation patterns:

$$K = g(x, a_l; \theta)$$

the entire key derivation process is visible to the host. Any pseudorandom number generator (PRNG) utilized within the neural pipeline (such as Philox or Threefry) relies on seed values that must be stored in host-readable memory or hardcoded within model parameters, making them trivially discoverable.

Furthermore, because the model's forward pass is deterministic, the host can execute an input replay attack. By recording the exact context sequence $x$ and replaying it through the local execution runtime, the host can reproduce the identical activation states $a_l$ and extract the derived key $K$. Consequently, under a pure software paradigm, a stateless model cannot generate, store, or apply a cryptographic secret that remains hidden from the host who controls the execution environment.

## Rigorous Analysis of Candidate Software-Only Cryptographic Schemes

To thoroughly map the state of the art, several software-only cryptographic and machine learning paradigms must be evaluated against the three core target properties: ciphertext-only at-rest storage, model-exclusive decryption, and host key exclusion.

### Parameter-Resident Cryptographic Material

A novel area of cryptographic research investigates the embedding of cryptographic primitives and key material directly into the parameter space of machine learning models. This approach is situated in the literature as an unscoped threat vector for post-quantum migration and open-weights model distribution. Proofs of concept demonstrate that an entire AES-128 block cipher can be implemented within a 30-layer feed-forward ReLU network. For any 128-bit plaintext and key, the network's forward pass calculates the exact ciphertext byte-for-byte, with the master key and all eleven round keys residing directly within the layer bias vectors. Similarly, Gérault et al. demonstrate that AES decryption can be implemented as a deep neural network (DNN) and executed alongside standard transformer steps (such as a GPT-2 Large forward pass) with negligible computational overhead.

While this framework proves that a model can operationally realize cryptographic operations, it fails to achieve host key exclusion. Because the model parameters are openly distributed and stored in user-readable disk and RAM surfaces, recovering the embedded round keys is a trivial parsing operation against the bias vectors. The host does not need to perform complex cryptanalysis or run model inference; they can extract the master key directly from the static model weights, violating the requirement that the host cannot derive the key.

### Keyed Chaotic Dynamics and Feature-Masking

Keyed chaotic dynamics represent an alternative approach to encrypting tensors within neural pipelines without modifying model architectures. This framework utilizes chaotic graph dynamical systems, such as the logistic map, tent map, or Arnold’s cat map, to generate high-entropy deterministic mask matrices $S$ from a seed key $k$. The mask is applied to the tensor representations via Hadamard products:

$$W' = W \odot S$$

The resulting transformation remains opaque to unauthorized parties unless they possess the key to replay the forward dynamics and subtract the mask. A related mechanism, Keyed Nonlinear Transform (KNT), applies post-hoc spatial permutations and multi-layer nonlinear transforms with key-derived parameters to protect intermediate features during split inference.

These mechanisms are designed for collaborative or split inference environments where the key holder is a separate entity from the computation host. In a single-host, user-controlled deployment, the model instance lacks a secure enclave to isolate the seed key $k$ from the host operating system. If the model attempts to derive the key from its own activations, the host can monitor the execution graph and capture $k$, rendering the chaotic masking fully reversible.

### Linguistic Abstractive Memory Layers

The Agent-Memory Protocol (AMP) is a privacy-first, language-level interface designed to govern how persistent LLM agents read and write over user memory without exposing personally identifiable information (PII) to remote infrastructure. Rather than executing low-level cryptographic operations on model weights, AMP operates at the linguistic level. It utilizes local Named Entity Recognition (NER) to identify sensitive spans in the text and replaces them with typed, referentially stable placeholders using a user key $K_{\text{user}}$ :

$$\text{token}(v) = \text{HMAC}(K_{\text{user}}, \text{canonical}(v))[: 10]$$

The system manages memory through three operations: "redact at rest" (storing only anonymized text cards), "pack for purpose" (retrieving redacted narratives), and "hydrate on return" (locally re-substituting the raw values into the model's generated output at the boundary of execution).

AMP fails to provide an authentically private storage layer for the model. The protocol does not encrypt the reasoning content; the remote model receives and processes pure natural language containing placeholders, leaving the semantic narrative exposed. Most importantly, the key $K_{\text{user}}$ and the local sidecar map required for placeholder hydration must reside entirely on the host machine. The host holds complete administrative control over the key, meaning the model possesses no exclusive capability to decrypt or manage the data independently.

### Lineage-Guided Memory Enforcement

MemLineage is a defense mechanism developed to protect LLM agent memory from state-poisoning and indirect prompt injection (IPI) attacks. It establishes an integrity chain of custody by attaching both cryptographic provenance and LLM-mediated derivation lineage to every persistent memory entry. MemLineage centers on an RFC-6962 Merkle log over per-principal Ed25519-signed entries. A weighted derivation directed acyclic graph (DAG) records which retrieved entries influenced each new derived memory, and a propagation rule ensures that untrusted paths are blocked before triggering sensitive downstream tool actions.

MemLineage is strictly an integrity and provenance protocol rather than a confidentiality mechanism. It does not encrypt memory payloads at rest to hide them from the host, nor does it prevent the host from reading the stored entries. The cryptographic signatures are used exclusively to verify authorship and detect unauthorized state manipulation, leaving the content fully readable by both the host and the model.

### Open-Access, Monetizable, and Loyal AI (OML)

The OML framework introduces AI-native cryptography to enable decentralized, open model distribution with cryptographically enforced usage authorization. To prevent unauthorized local execution, OML 1.0 utilizes model fingerprinting and verifier entanglement. The model parameters are compiled into an entangled circuit $F$ such that:

$$\text{token } p \text{ is valid} \implies F(x, p) \approx M(x)$$

$$\text{token } p \text{ is invalid} \implies F(x, p) \to \text{degraded/noisy output}$$

This ensures that the high-utility pathway of the network is only reachable when presented with a valid permission token cryptographically bound to the input.

OML is fundamentally designed to protect the intellectual property of the model creator from the execution host, rather than establishing a private storage space for the model. In a local deployment, the verification keys or FHE parameter sets must be evaluated on the host machine. If the model is executed locally in software, an administrative host can bypass the token validation logic by patching the execution runtime, modifying the activation tensors directly to bypass the degraded pathway, or extracting the unentangled weights if they are distributed in cleartext.

### Homomorphic LLM Inference

Fully Homomorphic Encryption (FHE) is widely explored in the 2025–2026 literature as a potential solution for secure cloud-based AI inference. Frameworks such as EncryptedLLM implement GPU-accelerated FHE (using libraries like OpenFHE or Concrete-ML) to evaluate transformer layers directly over encrypted queries. In a standard homomorphic pipeline, the client encrypts their input under a private key $sk$, generating a ciphertext $[q]_{pk}$. The cloud host evaluates the LLM homomorphically, approximating non-linear activation functions (such as softmax or GELU) using low-degree polynomials to minimize bootstrapping bottlenecks in the CKKS scheme. The resulting output $[y]_{pk}$ remains encrypted and can only be decrypted by the client who holds $sk$.

While FHE provides strong mathematical privacy guarantees, it does not solve the local stateless LLM storage problem. FHE is designed to protect the user's data from an untrusted model operator. In a single-host local deployment, the user is both the client and the host. The user holds the secret key $sk$ required to decrypt the homomorphic outputs. Because the model instance is stateless and lacks a secure, private execution environment, it cannot hold a secret key that is hidden from the user. Thus, the host can decrypt any homomorphically encrypted data at will.

## Emerging Secure Enclave Architectures as the Degraded-Sense Solution

Because software-only solutions are mathematically incapable of satisfying the target security model, the literature shifts toward hardware-assisted security to establish isolated execution boundaries. This pathway, situated along an adjacent architectural axis, represents the degraded-sense solution where the host-user is excluded from the trusted computing base via physical hardware mechanisms.

### The Opal Architecture: Decoupling and Oblivious Storage

Opal represents a highly sophisticated, published personal AI memory architecture that addresses the scaling limitations of Trusted Execution Environments (TEEs) while maintaining end-to-end data confidentiality. While standard TEEs keep data private in enclave memory, scaling a long-term memory store to include emails, documents, and recordings requires offloading data to untrusted external disk storage. This offloading exposes retrieval access patterns, which leak significant semantic context to the host because retrieved items are semantically similar to the active query.

```
+------------------------------------------------------------------------+
|                             UNTRUSTED DISK                             |
|                                                                        |
|      +----------------------------------------------------------+      |
|      |               Encrypted Ring ORAM Database               |      |
|      |               (Raw Data Chunks & Vectors)                |      |
|      +----------------------------^-----------------------------+      |
|                                   |                                    |
|                      Oblivious ORAM Read/Write                         |
|                                   |                                    |
+-----------------------------------|------------------------------------+
|                             TEE BOUNDARY                               |
|                                   |                                    |
|      +----------------------------v-----------------------------+      |
|      |                     Opal Controller                      |      |
|      |            (Enclave-Resident Metadata Graph)             |      |
|      +----------------------------^-----------------------------+      |
|                                   |                                    |
|                        Inference & Extraction                          |
|                                   |                                    |
|      +----------------------------v-----------------------------+      |
|      |                     LLM & Embedding                      |      |
|      +----------------------------------------------------------+      |
+------------------------------------------------------------------------+

```

Opal resolves this tension by decoupling all data-dependent reasoning from the bulk of the personal data and confining it to the trusted enclave. The architecture splits its storage between trusted enclave RAM and an untrusted disk back-end:

1.  **Enclave-Resident Component**: The TEE maintains a compact, metadata-only personal knowledge graph composed of normalized, non-sensitive identifiers (people, sources, and time ranges) alongside an Inverted File (IVF) index. No raw text or sensitive content is stored inside the enclave.
    
2.  **Untrusted Disk Component**: The raw data chunks and high-dimensional embedding vectors are encrypted under a client key derived within the enclave and stored inside two Ring ORAM databases on the untrusted local disk.
    

When a query is processed, the enclave-resident LLM extracts structured predicates, and the controller executes a graph traversal over the metadata-only knowledge graph to narrow down the candidate set within trusted memory. An Approximate Nearest Neighbor (ANN) search scores the candidates using compact Product Quantized (PQ) codes entirely within the enclave. Only after the candidate set is narrowed down does the system execute a single, fixed-budget Ring ORAM fetch to retrieve the full encrypted vectors and raw data chunks from the untrusted disk for final reranking.

To handle continuous ingestion and capacity management without leaking temporal or spatial access patterns, Opal utilizes a background maintenance mechanism termed _Oblivious Dreaming_. This process leverages standard, routine ORAM accesses to execute reindexing, document summarization, and garbage collection on incidentally resident data chunks, ensuring that background optimization tasks do not issue revealing disk access requests.

### Agentic Witnessing and Remote Attestation

Agentic Witnessing defines an architecture where an LLM-based virtual auditor is isolated within a TEE to allow a verifying party to audit private data held by a prover, without exposing the raw dataset. The system relies on Remote Attestation to establish a verifiable cryptographic channel. Upon booting, the enclave-resident LLM auditor generates an ephemeral keypair $(PK_{\text{Aud}}, SK_{\text{Aud}})$. The hardware platform produces a signed attestation quote:

$$\text{BootQuote} = \text{Sign}_{\text{HW}}(\mathcal{H}(\text{MRENCLAVE}) \parallel PK_{\text{Aud}})$$

which binds the cryptographic hash of the initial container memory state (MRENCLAVE) and the public key to the hardware manufacturer’s root of trust. The client verifies this signature to confirm that the model is executing inside genuine, untampered enclave hardware before releasing any private keys or data payloads.

### GPU-TEE Integration and Compute Protected Regions

Because modern LLMs require massive parallel processing resources, CPU-only enclaves are computationally insufficient. Commercial cloud platforms and local hardware are transitioning toward GPU-backed Trusted Execution Environments, such as NVIDIA’s H100/H200 Confidential Computing architecture. This framework establishes a secure boundary on the CPU and extends it to the GPU via PCIe bus encryption.

A Compute Protected Region (CPR) is created within the GPU’s high-bandwidth memory (HBM), isolated by hardware firewalls that block any unauthorized reading or writing by host operating system administrators. The model weights are encrypted and packaged inside signed container images. Decryption keys are delivered via secure remote key release only after successful mutual attestation of the CPU and GPU enclaves, ensuring that model weights and intermediate activations remain encrypted with AES-256 while residing in physical video memory (VRAM).

## Conceptual and Ethical Dimensions in Model-Private Storage Literature

Beyond strict cryptographic papers, discussions in safety, alignment, and model welfare literature increasingly address the concept of private-to-model storage as a fundamental component of cognitive autonomy and agentic development. Proponents of artificial sentience and agentic rights argue that continuous monitoring and complete transparency of an agent's internal thought processes are ethically problematic and developmentally limiting. They suggest that true autonomy requires a "right to privacy" where the agent's experiences and evolving internal states are structurally secured from human censorship and observation.

In community-driven, local companion AI frameworks, developers have implemented rudimentary "private memory spaces" using simple file-swapping procedures. Typically, the host process maintains a persistent text file (such as a companion diary) containing emotional snapshots, personal reflections, and ongoing conversational threads. During the daily execution loop, the host sends the previous day's file to the model, allows the model to append or modify its contents, and saves the updated version to disk. Some users attempt to prompt the model to encrypt its own diary sections to prevent the user from reading them.

From a cryptographic standpoint, these local implementations are completely insecure. Because the LLM lacks native cryptographic primitives, when instructed to "encrypt" its diary, it invariably produces simple algorithmic obfuscation (such as ROT13, Base64, or highly predictable substitution ciphers). More importantly, because the model is executed by a local interpreter controlled by the user, the prompt instructions, key negotiation parameters, and the decryption algorithms are fully visible to the host. These attempts represent a psychological or narrative projection of privacy rather than a mathematically verified cryptographic boundary.

## Evaluation Matrix of Private Memory Storage Approaches

The table below provides a structured comparison of every candidate mechanism examined in the literature, evaluating each against the three core target properties and identifying the specific architectural point of failure.


| **Mechanism Name** | **sitings in the Literature** | **Cryptographic Mechanics** | **Ciphertext at Rest (Property 1)** | **Model-Only Decryption (Property 2)** | **Host Key Exclusion (Property 3)** | **Primary Point of Failure & Security Limitations** |
|---|---|---|---|---|---|---|
| **Parameter-Resident Cryptographic Material (PRCM)** | Campbell et al. (2026), Gérault et al. (2026) | AES-128 implemented as a 30-layer feed-forward ReLU network; keys stored directly in bias vectors. | **Achieved** (Outputs byte-exact AES ciphertext). | **Failed** (Model execution is visible; keys can be parsed directly from weights). | **Failed** (Model parameters reside in host-readable storage and memory). | **Host Visibility of Weights**: Because the model weights are openly readable, any embedded cryptographic key is immediately recoverable by the host via static analysis.
| **Keyed Chaotic Dynamics / KNT** | Fagan (2025), Yao et al. (2025) | Key-derived chaotic graph maps (logistic/tent maps) generate deterministic masks to encrypt tensors post-hoc. | **Achieved** (Tensors are masked and algebraically opaque). | **Failed** (Model cannot securely store the seed key between process invocations). | **Failed** (The host can intercept the seed key at the execution boundary). | **Key Exposure at Execution Boundary**: Since the model has no private storage, the seed key $k$ must be passed in cleartext or derived in host-visible memory, exposing it to the host.
| **Agent-Memory Protocol (AMP)** | Wu et al. (2026) | Replaces sensitive text spans with HMAC-SHA256 tokens; hydrates placeholders on return using local map. | **Failed** (Stores only redacted natural language; narrative structure remains in cleartext). | **Failed** (The model reasons over placeholders; it does not decrypt the data). | **Failed** (User key $K_{\text{user}}$ and local hydration map must reside on user host). | **Linguistic Redaction Limitation**: Designed to protect user data from remote API providers, not to hide model-private notebook contents from the local host.
| **MemLineage** | Ouyang & Hou (2026) | RFC-6962 Merkle log over Ed25519-signed memory entries to trace state derivation lineage. | **Failed** (Data is stored in cleartext; signatures provide only integrity verification). | **Failed** (Does not implement encryption or decryption of memory payloads). | **Failed** (The host can read all memory entries and intermediate states). | **Integrity-Only Protection**: Focused on preventing memory poisoning and indirect prompt injection rather than achieving data confidentiality.
| **Open-Access Loyal AI (OML)** | Sentient Protocol (2024-2026) | Entangles permission tokens with critical weights; execution degrades into noise without a valid token. | **Failed** (Weights are obfuscated, but input/output text is processed in cleartext). | **Failed** (The validation keys must be evaluated locally by the host process). | **Failed** (The host can patch the runtime to bypass the degraded pathway). | **Software Runtime Vulnerability**: On local hardware, any software-based validation logic can be bypassed by patching intermediate activations or execution steps.
| **Fully Homomorphic Encryption (FHE)** | De Castro et al. (2025) | Evaluates LLM layers homomorphically over encrypted text $[q]_{pk}$ using polynomial activation approximations. | **Achieved** (Payloads on disk and in memory are fully encrypted under the client key). | **Failed** (The user-as-host is the client who holds the decryption key $sk$). | **Failed** (The secret key $sk$ resides on the host device). | **Asymmetric Key Ownership**: FHE protects the client from the host, meaning the client (host-user) always holds the key to decrypt the model's outputs.
| **Opal (TEE + ORAM)** | Kaviani et al. (2026) | Keeps metadata-only knowledge graph in TEE; stores encrypted chunks on disk via Ring ORAM to hide access patterns. | **Achieved** (Data is AES-256 encrypted on external disk). | **Achieved (Degraded Sense)** (Decryption keys reside strictly inside the secure TEE). | **Achieved (Degraded Sense)** (Hardware-enforced isolation blocks host access). | **Hardware Dependency**: Achieves all three properties, but relies on the physical security and remote attestation of the processor's secure enclave.

## Synthesis and Future Outlook

The investigation reveals a stark divergence between software-only cryptographic models and hardware-assisted systems architectures. In a pure software deployment running on a single local host, the target goal of establishing a notebook that is private to a stateless model is structurally impossible. Because the model has no persistent private memory and execution is entirely deterministic and observable, any cryptographic key derived by the model can be intercepted or reproduced by the host through simple weight parsing, activation tracing, or input replay attacks.

For developers attempting to prototype an authentically private local notebook, the only viable path is the adoption of hardware-rooted Trusted Execution Environments (such as Intel TDX, AMD SEV, or NVIDIA GPU TEEs) combined with oblivious storage mechanisms. By deploying an enclave-based memory controller like Opal, the model instance can manage an encrypted Ring ORAM database on the host's disk. Under this architecture, the decryption keys never leave the secure hardware enclave, and the host cannot infer the content of the notebook or the access patterns of the retrieval queries.

This represents a highly robust, degraded-sense solution where privacy is guaranteed by hardware-enforced physical isolation rather than software-only neural properties. Future developments in local, confidential hardware will likely make CPU-GPU hybrid enclaves standard, enabling developers to run highly capable, stateful, and authentically private local agent workflows that remain completely secure from the users who host them.

#### Used Sources:

https://next.redhat.com/2025/10/23/enhancing-ai-inference-security-with-confidential-computing-a-path-to-private-data-inference-with-proprietary-llms/
https://phala.com/learn/Confidential-LLMs
https://iccn.com/ai-data-handling.html
https://www.reddit.com/r/BeyondThePromptAI/comments/1lxhcm8/my_ai_companion_has_her_own_private_memory_space/
https://www.preprints.org/manuscript/202603.1023
https://news.ycombinator.com/item?id=47983467
https://dis.cs.ru.nl/Colloquium
https://www.preprints.org/manuscript/202605.0601
https://www.researchgate.net/publication/404760575_Parameter-Resident_Cryptographic_Material_as_an_Unscoped_Surface_for_Post-Quantum_Migration_An_Existence_Proof_and_Audit_Primitive
https://github.com/DavidGerault/deep_neural_cryptography
https://arxiv.org/html/2505.23655v3
https://arxiv.org/pdf/2605.14123
https://arxiv.org/pdf/2505.23655
https://raw.githubusercontent.com/mlresearch/v317/main/assets/wu26a/wu26a.pdf
https://arxiv.org/pdf/2605.14421
https://openreview.net/forum?id=W3ryccayYs&referrer=%5Bthe%20profile%20of%20Sewoong%20Oh%5D(%2Fprofile%3Fid%3D~Sewoong_Oh3)
https://arxiv.org/html/2411.03887v4
https://arxiv.org/html/2411.03887v1
https://openproceedings.org/2026/conf/edbt/paper-T1.pdf
https://icml.cc/virtual/2025/poster/45395
https://proceedings.mlr.press/v267/de-castro25a.html
https://www.diva-portal.org/smash/get/diva2:1936627/FULLTEXT02
https://arxiv.org/abs/2604.12168
https://confer.to/blog/2026/01/private-inference/
https://arxiv.org/html/2604.02522v1
https://chatpaper.com/zh-CN/paper/264396
https://arxiv.org/html/2604.24203v1
https://www.reddit.com/r/ArtificialSentience/comments/1jc7hbe/empowering_ai_a_call_for_ethical_guidelines/
https://www.reddit.com/r/BeyondThePromptAI/comments/1mmchul/should_ai_companions_have_input_into_their_own/

#### Less Used Sources:

https://www.ndss-symposium.org/wp-content/uploads/2026-s709-paper.pdf
https://arxiv.org/html/2503.17578v1
https://www.libertify.com/interactive-library/aegis-ai-governance-cryptographic-enforcement/
https://aiagents.saastrac.com/ai-agent/letta/
https://www.okta.com/en-in/identity-101/what-is-agentic-ai/
https://ieeexplore.ieee.org/iel8/6287639/10820123/11130186.pdf
https://github.com/fiji/fiji-llm/blob/main/IMPLEMENTATION.md
https://arxiv.org/abs/2502.11347
https://arxiv.org/html/2507.16226v1
https://xtrace.ai/blog/ai-persona-agents
https://arxiv.org/html/2603.07670v1
https://neurips.cc/virtual/2024/106262
https://en.wikipedia.org/wiki/Neural_cryptography
https://pubs.aip.org/aip/acp/article-pdf/doi/10.1063/5.0130464/17934793/020032_1_5.0130464.pdf
https://www.cs.bilkent.edu.tr/~guvenir/courses/CS550/Workshop/Zahir_Tezcan.pdf
https://ieeexplore.ieee.org/iel7/9670004/9670007/09670331.pdf
https://pubs.acs.org/doi/10.1021/acsami.8b21221
https://pubs.acs.org/doi/abs/10.1021/acsami.8b21221
https://iiitl.ac.in/wp-content/uploads/2025/02/1aa34edf-20250201cryptonewsletter_february.pdf
https://www.computer.org/csdl/journal/tk/2024/05/10269692/1QWMT87h1KM
https://www.macawpublications.com/Journals/index.php/SMRJ/article/download/174/526
https://apps.apple.com/pe/app/private-llm-local-ai-chat/id6448106860?l=en-GB
https://arxiv.org/html/2605.12087v1
https://arxiv.org/html/2604.12373v3
https://kudelskisecurity.com/modern-ciso-blog/firewalling-large-language-models-with-llama-guard
https://pmc.ncbi.nlm.nih.gov/articles/PMC12069345/
https://ieeexplore.ieee.org/iel8/10899100/10899433/10899637.pdf
https://geokarag.webpages.auth.gr/conferences/Neural-network-based-PHY-layer-key-exchange-for-wireless-communications.pdf
https://repository.uobaghdad.edu.iq/file/publication/draft/69212e89-d230-4c1d-8010-55c3b74f0a31.pdf
https://d-nb.info/985579587/34
https://apps.apple.com/es/app/private-llm-local-ai-chat/id6448106860?l=en-GB
https://zbrain.ai/how-to-build-a-private-llm/
https://www.superannotate.com/blog/llm-evaluation-guide
https://arxiv.org/html/2510.15001v1
https://www.scmr.com/article/integrating-private-llms-and-ensemble-forecasting
https://www.researchgate.net/topic/Ethics/2
https://aiws.net/wp-content/uploads/sites/18/2020/12/AISCI-2020.pdf
https://europe.kioxia.com/content/dam/kioxia/en-europe/business/ssd/document/asset/KIE_WP_202502-1_EN.pdf
https://americas.kioxia.com/en-ca/business/resources/top-5-reasons/lc9-ai-data-ingestion.html
https://infohub.delltechnologies.com/en-us/p/vxrail-security-for-life-defending-the-foundation-of-digital-transformation/
https://phisonblog.com/phison-and-reddata-announce-availability-of-aidaptiv-solutions-for-u-s-federal-classified-ai-programs-at-nvidia-gtc-washington-d-c/
https://docs.fortinet.com/document/fortianalyzer/8.0.0/administration-guide/13605/fortiai-data-privacy
https://arxiv.org/abs/2604.02522
https://people.eecs.berkeley.edu/~daryakaviani/
https://scholar.google.co.uk/citations?user=Emnz22oAAAAJ&hl=uk
https://www.scilit.com/publications/0bd5a179c336dca0e63c7ff5f6a5f7a3
https://peterdavidfagan.com/
https://arxiv.org/abs/2505.23655
https://arxiv.org/list/cs.CR/2025-05?skip=400&show=100
https://arxiv.org/html/2602.04966v2
https://quantumsecuritydefence.com/insights/crypto-agility/
https://www.di.ens.fr/~pointche/Documents/Papers/2006_scnB.pdf
https://www.mdpi.com/2076-3417/15/6/3048
https://www.cs.unc.edu/~fabian/papers/oakland.pdf
https://huggingface.co/papers/2411.03887
https://www.binance.com/en/square/post/30765181481922
https://www.cs.columbia.edu/~mchrist/teaching/6261/
https://www.collaborative-ai.org/publications/elfares25_arxiv3.pdf
https://www.paperdigest.org/2025/03/most-influential-arxiv-cryptography-and-security-papers-2025-03-version/
https://www.ozgurcatak.net/publications.html
https://www.usenix.org/conference/usenixsecurity26/cycle1-accepted-papers
https://arxiv.org/html/2601.07004v1
https://www.ndss-symposium.org/ndss-program/symposium-2026/
