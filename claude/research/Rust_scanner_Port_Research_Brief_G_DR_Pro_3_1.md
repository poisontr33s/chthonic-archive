# **Research Brief — Scanner V2.2 to Rust Port: Bias Validation, Limitations, and Canonical Choices**

## **Architectural Context and Baseline Assessment**

* *The transition of a polyglot workspace scanner from Bun (V2.2) to Rust represents a fundamental shift in systems architecture. The existing implementation operates within an asynchronous, event-loop-driven JavaScript runtime backed by native C/C++ bindings (specifically Node's crypto module and libuv for filesystem access). This V2.2 Bun scanner has demonstrated formidable performance characteristics, capitalizing on a warm-cache hit rate of 99.5% and completing sub-second scans across a massive 158 GiB, 52,212-file workspace spanning 21 projects and diverse paradigms ranging from Rust and Python to CUDA, Vulkan, and Unity game engine assets.*

* *The pervasive assumption that rewriting a high-performance JavaScript or TypeScript implementation in Rust will yield immediate, uniform, order-of-magnitude speedups is a profound architectural bias that requires rigorous empirical deconstruction. In workloads fundamentally constrained by cryptographic hashing and persistent disk I/O, interpreted or Just-In-Time (JIT) compiled languages often serve merely as a thin orchestration layer over the exact same underlying hardware-accelerated C libraries and operating system-level system calls. Therefore, identifying the precise bottlenecks—whether they manifest as CPU limitations, memory allocation overhead, operating system virtual memory paging, or file system filter drivers—is paramount to ensuring the Rust port provides tangible advantages rather than redundant engineering overhead.*

* *This comprehensive research report systematically unpacks the architectural boundaries of the intended V2.2 port. It evaluates the specific substrate requirements for the V2.3 (MinHash, tree-sitter) and V2.4 (wgpu compute) roadmap extensions, delivering concrete canonical library selections, expected performance differentials, and named failure modes across six major investigative clusters.*

## **1. Performance Differentials: Deconstructing the Rust Advantage**

* *A critical objective in porting the spread scanner is isolating which operations within the Bun runtime are already operating at the theoretical hardware limits of the target Windows 11 x64 environment, and which genuinely suffer from the overhead of the V8 JavaScript engine.*

### **1.1 SHA-256 Throughput and Hardware Acceleration**

* *The assumption that Rust's native cryptographic hashing will inherently outpace Bun's crypto module is fundamentally flawed. Bun relies on Node.js's underlying cryptography bindings, which are deeply integrated with OpenSSL via N-API.1 OpenSSL is a highly optimized, battle-tested C library that natively utilizes hardware-accelerated instructions, specifically the SHA-NI (Secure Hash Algorithm Native Instructions) extension available on modern AMD and Intel x86_64 processors.2 Consequently, the actual heavy computational lifting in the Bun scanner is executed directly at the hardware level, largely bypassing the JavaScript engine's typical runtime overhead.*

* *Within the Rust ecosystem, achieving parity with OpenSSL requires explicit architectural decisions. A pure-Rust SHA-256 implementation, devoid of compiler-specific hardware intrinsics, is highly dependent on general LLVM optimizations. Without explicit instruction set flags, a pure-Rust SHA-256 implementation can execute significantly slower than hardware-accelerated C code, sometimes requiring 1.6 seconds to hash a 257 MB file compared to the 0.8 seconds achieved by highly optimized native binaries.3 To match or exceed the OpenSSL baseline established by Bun, the Rust implementation must be explicitly configured to utilize hardware intrinsics.*
  
**The canonical choices within the Rust cryptography ecosystem are ring and sha2:**

| Cryptography Library | Implementation Architecture | Throughput Profile | Integration Complexity |
| :---- | :---- | :---- | :---- |
| **ring** | Assembly/C core wrapped in Rust | Exceptionally high (up to 1.18 GiB/s for SHA-256). ^4^ | Requires C/Assembly compilation toolchain; excellent on Windows x64 but complicates cross-compilation. ^5^ |
| **sha2** (RustCrypto) | Pure Rust with optional intrinsics | Moderate by default; high when asm feature is enabled.3 | Pure Rust toolchain. Requires explicit compilation flags (-C target-cpu=native) or the asm feature to engage SHA-NI. ^2^ |

**Verdict on Hashing Overhead:** *The existing Bun implementation is highly efficient for the raw cryptographic hashing phase because it effectively executes OpenSSL C code. The Rust port will not yield a massive order-of-magnitude speedup in pure hashing throughput. **Canonical Choice:** To match the Bun baseline, the Rust port must wire in the ring crate, or alternatively, the sha2 crate explicitly compiled with the asm feature. ^3^ **Failure Mode:** A critical failure mode for the Rust port occurs if sha2 is utilized and compiled without hardware intrinsics in a standard release build. This results in CPU-bound bottlenecks where the compiled Rust binary operates strictly slower than the interpreted Bun script due to the absence of SHA-NI utilization.* ^3^

### **1.2 File Walking and System Call Amplification**

* *File traversal in the V2.2 Bun scanner relies on node:fs.readdirSync, which binds to the libuv event notification library. While libuv is highly efficient for asynchronous, event-driven architectures, synchronous directory reading in a JavaScript context operates iteratively. The runtime must continually marshal string paths and file metadata between the C++ abstraction layer and the V8 heap, generating significant garbage collection pressure and memory allocation overhead when traversing 50,000 to 500,000 files.* 

* *Rust offers direct system call access without garbage collection overhead, but the choice of directory walking library dictates the ultimate performance ceiling. The ecosystem provides three primary candidates: walkdir, ignore, and jwalk.*

| Walking Library | Concurrency Model | Target Use Case | Disadvantages |
| :---- | :---- | :---- | :---- |
| **walkdir** | Single-threaded | Simple, sequential traversal with low memory overhead. | Becomes heavily I/O bound on deeply nested directories; lacks work-stealing parallelization. ^6^ |
| **ignore** | Multi-threaded (Rayon) | Built for tools like ripgrep; respects .gitignore rules by default. | Parsing complex ignore rules creates CPU overhead. Disabling ignore logic negates its primary architectural advantage. ^8^ |
| **jwalk** | Multi-threaded (Rayon) | High-performance parallel traversal; streams sorted results; allows custom filtering.10 | Requires careful thread pool configuration to prevent operating system lock contention on specific file systems. ^11^ |

* For the specific requirements of the *chthonic-archive* scanner—where .gitignore processing is explicitly bypassed per the conductor directive, and high-performance, parallel traversal of complex polyglot repositories is required—the optimal choice is clear.  

 * **Verdict on File Walking:** **jwalk** is the canonical choice. **Rationale:** Benchmarks consistently demonstrate that jwalk executes recursive directory walks approximately 4x to 7.5x faster than single-threaded Rust (walkdir) and equivalent C++ standard library recursive iterators. ^7^ By leveraging the rayon work-stealing thread pool, jwalk parallelizes read_dir system calls across multiple CPU cores, effectively saturating the file system's metadata reading capabilities. ^6^

### **1.3 Disk I/O Ceilings and the NTFS Bottleneck**

* *Regardless of the language runtime utilized, the physical limitations of the host's NVMe Solid State Drive (SSD) and the architectural constraints of the Windows NTFS file system dictate a rigid throughput floor.*
  
* *Modern NVMe drives utilize the PCIe bus to provide exceptional bandwidth for large sequential reads. However, they suffer measurable performance degradation during high-volume random reads of small files (e.g., 50,000 files under 32 KB). Furthermore, NTFS implements global locks during directory enumeration and Master File Table (MFT) metadata access. Parallelizing CreateFile and CloseHandle Windows API system calls across 16 threads can paradoxically result in thread contention within the OS kernel, stalling throughput.* ^12^

* *A critical, often-overlooked bottleneck on Windows 11 architectures is Windows Defender (and other third-party Anti-Virus software) operating in synchronous real-time protection mode. Filesystem filter drivers intercept every CreateFile and CloseHandle operation to scan the file buffer for malicious signatures. This interception can add between 1 to 10 milliseconds of latency per single file access.* ^13^

**Verdict on Disk I/O:** *No programmatic language choice can circumvent the NTFS metadata lock and filter driver bottleneck. If the workspace resides on a standard NTFS volume actively monitored by Defender, reading 50,000 small files will hit a hard physical wall. The language overhead of Bun's string marshalling is negligible compared to a 10-millisecond anti-virus interception.13 **Actionable Insight:** To maximize the Rust port's capability, the scanner architecture should detect the file system type and advise the user to utilize a Windows Dev Drive (which utilizes ReFS formatting with asynchronous AV scanning optimizations) or automatically prompt the user to add the workspace to Windows Defender exclusion paths.* ^13^

### **1.4 Cache Serialization and Deserialization Thresholds**

* *The V2.2 Bun scanner utilizes an append-only NDJSON (Newline Delimited JSON) format for its .spread/file_index.ndjson cache. Modern JavaScript engines, specifically V8, are profoundly optimized for parsing JSON strings, meaning Bun's JSON.parse operates at near-native speeds. Transitioning to Rust and utilizing serde_json to parse this data line-by-line will result in strict memory safety and predictably lower RAM utilization, but it will not drastically outpace V8's specialized JSON parsing capabilities for a dataset of 50,000 rows.*

* *However, as the row count scales toward the 5,000,000+ marker required for full workspace and OS-level AppData indexing, JSON string parsing becomes entirely CPU-bound.15 The overhead of converting ASCII characters to floating-point numbers and allocating dynamic string structures becomes untenable. A binary format is strictly necessary for the V2.3 and V2.4 roadmaps. (This specific architectural shift is analyzed in detail in Section 4).*

## **2. Hashing Strategy: Fingerprinting and Memory Mapping**

* *The current V2.2 implementation executes a full SHA-256 hash on the entirety of every file under 50 MB. This is architecturally wasteful, especially for large binary assets, game engine binaries, or heavily modified codebases where the probability of exact byte-for-byte collisions without corresponding metadata shifts is infinitesimally low.*

### **2.1 The "Cheap Fingerprint" Canon**

* A full SHA-256 pass over a 40 MB file requires reading all 40 MB into physical memory and processing it continuously through the cryptographic hash function. A canonical "cheap fingerprint" strategy utilizes file metadata combined with sparse content sampling to generate a high-confidence uniqueness signature without reading the entire file payload.*

* The most robust fingerprint tuple pattern for this domain is:*
**+ + +**

* *This strategy requires reading at most 8 KB per file, dramatically slashing disk read volume for medium-to-large files. If two files possess identical sizes, identical modification timestamps, and identical edge byte structures, they are placed into a potential collision bucket. Only files residing within a collision bucket are subjected to a full SHA-256 deep hash.*
 
**False-Collision Rate:** *The false collision rate for this specific heuristic is statistically insignificant for standard source code and asset repositories. It provides massive I/O savings while ensuring deterministic deduplication.*

### **2.2 Memory Mapping (memmap2) vs User-Space Reads (std::fs::read)**

* *When a full hash is unequivocally required for files in the 1 MB to 50 MB range, reading the file via std::fs::read forces the operating system to read the file into a kernel-space page cache, and subsequently execute a memory copy into a user-space buffer (e.g., a Rust Vec<u8>). This memory copy incurs CPU cycles and memory bandwidth overhead.  
Memory-mapped I/O, achieved via the **memmap2** crate, maps the file's contents directly into the process's virtual address space.16 The OS manages the loading of physical memory pages dynamically on demand (page faults).*

* **Performance Differential:** *The benchmark data demonstrates staggering differences in raw buffer availability. Loading a 2.5 GB dataset via standard vector reads requires approximately 10 seconds, whereas mapping the exact same data via memmap2 completes the virtual memory mapping in approximately 0.05 seconds.18 While executing the hash function will still force the OS to page the memory in from disk (meaning the actual continuous processing time will normalize), the total elimination of the user-space memory copy provides a tangible, measurable throughput increase.*
 
* **Failure Mode:** *Memory mapping is inherently designated as unsafe in Rust. If an external process truncates, deletes, or modifies the mapped file while the Rust program is actively reading from the mapped slice, the program will encounter Undefined Behavior (UB).19 On Windows, this typically results in an uncatchable access violation or segmentation fault (SIGSEGV). Because a workspace scanner operates on live user directories where IDEs or compilers may be modifying files, this presents a significant architectural risk.*

**Verdict on File Reads:** *For small files (under 1 MB), standard std::fs::read is superior, as the system overhead of establishing a memory map, altering page tables, and handling page faults outweighs the simple memory copy cost. ^21^ For files between 1 MB and 50 MB, memmap2 provides excellent zero-copy performance for the hashing pipeline.* **Architectural Recommendation:** *The *MmapOptions* must be wrapped in a robust safety boundary. The Rust port must explicitly accept the risk of a hard crash if the user modifies a massive asset precisely during the 10-millisecond hash window, or implement OS-level file locking (which carries its own performance penalties) prior to mapping.* ^20^

### **2.3 Parallel Hashing and SSD Thrashing Dynamics**

* *Utilizing rayon::par_iter to hash multiple large files concurrently is a double-edged sword. On an NVMe SSD, parallel requests are heavily pipelined via the NVMe queue protocol, resulting in massive throughput gains compared to sequential reads.23 However, if the hardware substrate is a SATA SSD or a mechanical hard drive, or if the thread count drastically exceeds the optimal queue depth, the drive will experience severe I/O thrashing—rapidly seeking between different file sectors—which decimates read speeds.*
  
**Verdict:** *The ideal concurrency sweet spot on modern Gen4 NVMe drives is typically equal to the physical core count of the CPU. The Rust port must dynamically bound the rayon thread pool or utilize a constrained asynchronous I/O queue to prevent issuing 50,000 parallel read requests simultaneously to the OS scheduler, which would result in severe resource starvation.*

## **3. Magic-Byte Detection Canon**

* *The V2.2 scanner hand-rolls approximately 30 magic byte rules to detect mismatches between file extensions and actual file content. As the scanner expands to support diverse game engine assets and machine learning models, hand-rolling these signatures becomes unmaintainable. The Rust ecosystem provides several robust crates, but the requirement to accurately classify ML artifacts (Safetensors, GGUF) and Unity files dictates the selection criteria.*

### **3.1 Evaluation of Canonical Libraries**

| Detection Library | Mechanism | Footprint & Dependencies | Format Coverage |
| :---- | :---- | :---- | :---- |
| **infer** | Pure Rust, no_std compatible | Very small, statically compiled byte-matcher. | ~120 standard formats (images, docs, audio). Limited structural validation.24 |
| **tree_magic_mini** | Pure Rust, MIME subclass tree | Moderate. Loads MIME types into an efficient subclass tree. | Broader coverage, extremely fast (~150ns/file).26 |
| **libmagic-sys** | C FFI bindings | Large. Requires native C library dependencies. | Massive coverage. **Failure mode:** Introduces a cross-compilation and dependency nightmare for a simple CLI tool. |
| **file-format** | Pure Rust, dedicated structural readers | Moderate. Compiles specific format decoders. | ~200 formats. Intelligently employs specific readers for accurate identification. ^28^ |

**file-format** *is the recommended baseline for standard files. Unlike simple prefix byte-matching libraries, file-format intelligently employs specific binary readers when available. For example, it checks the internal central directory structures of ZIP or Compound File Binary (CFB) containers rather than just matching the first two bytes.29 This prevents false positives where a generic header matches, but the internal archive structure is entirely invalid or corrupted.*

### **3.2 Machine Learning Artifact Signatures**

* *No mainstream generic Rust magic-byte crate currently supports the highly specific Machine Learning model formats required by the chthonic-archive scope. These must be handled via custom parsers or specialized crates like hanzo_ai_format or *pmetal-gguf*. ^30^ 

* *The structural signatures for these formats are highly deterministic and can be implemented efficiently:*

* **safetensors**: *The file structure is highly rigid. It begins with an 8-byte, unsigned little-endian 64-bit integer (u64). This integer strictly specifies the byte length (![][image1]) of the subsequent UTF-8 JSON metadata header. ^32^ To detect a .safetensors file without false positives, the Rust scanner must read the first 8 bytes, decode the u64 size, read the next ![][image1] bytes, and attempt a lightweight verification (ensuring it begins with the { character and contains expected keys like __metadata__ or dtype).* ^33^  

* **GGUF**: *The format features a standard 4-byte magic number. The first four bytes of any valid GGUF file are identically the ASCII characters 0x47 0x47 0x55 0x46 (which spells "GGUF"). ^34^

* *This is immediately followed by a 32-bit unsigned integer denoting the version (e.g., version 3). Magic-byte detection here is trivial, instantaneous, and highly accurate.*

**Architectural Recommendation:** *The scanner should implement a custom fast-path match cascade. The system should first execute a hand-rolled check for safetensors, gguf, onnx, and .spv (SPIR-V) specific signatures. If these checks fail, the system should fall back to the robust file-format payload for the long tail of generic binary files, images, and standard archives.*

## **4. Cache Durability: Serialization and Architecture**

* *The transition from a 50,000-row NDJSON cache to a massive 5,000,000-row workspace-wide durable cache necessitates evaluating memory footprints, database locks, and deserialization latency.*

### **4.1 SQLite (rusqlite) Limitations**

* *SQLite is the unquestioned gold standard for embedded relational persistence. However, for a high-throughput, highly parallel file scanner, SQLite introduces a severe architectural bottleneck: the single-writer lock.* ^36^

* *While operating in Write-Ahead Logging (WAL) mode allows concurrent readers, all INSERT or UPDATE operations must be serialized through a single lock byte. If the scanner uses rayon to process 16 files simultaneously across 16 CPU threads, they will all block and queue, waiting for the SQLite lock to write their individual cache entries.*
  
* *While configuration pragmas (e.g., PRAGMA synchronous=NORMAL; PRAGMA journal_mode=WAL;) can optimize throughput somewhat 38, a purely key-value cache mapping absolute file paths to SHA-256 fingerprints does not benefit from relational SQL query execution. SQLite is structural overkill and a severe performance liability for this specific caching pattern.*

### **4.2 Binary Serialization: bincode vs rkyv**

* *Moving away from the high CPU parsing cost of JSON requires a robust binary format.*

* **rkyv**: *Achieves near-instantaneous, zero-copy deserialization by ensuring that the binary layout on the disk exactly matches the memory layout of the Rust structs in RAM. However, rkyv lacks a comprehensive schema evolution system.40 If the scanner upgrades to V2.3 and alters the struct definitions to include MinHash data, invalidating and migrating the old cache without crashing becomes highly problematic.* 

* **bincode**: *Highly compressible, standard in the Rust ecosystem, and exceptionally fast. It often generates binary file sizes up to 30% smaller than equivalent JSON representations. ^15^ While it requires active deserialization CPU cycles, the overhead is negligible compared to the latency of file I/O operations.*

**Verdict on Cache Format:** **bincode** *paired with the standard serde framework is the canonical choice. It provides the necessary high-speed performance and footprint reduction without sacrificing the maintainability and forward-compatibility that absolute zero-copy formats like rkyv forfeit.*

### **4.3 Cache Architecture: Per-Project Sharding**

* *To maximize the parallel capabilities of modern NVMe drives and multi-core CPUs, the cache should strictly be split per-project (e.g., one .spread/file_index.bin generated per workspace root or git repository).*  

* *This distributed architecture completely eliminates write contention. Threads processing Project A write exclusively to Cache A, while threads processing Project B write exclusively to Cache B. Furthermore, this cleanly maps to the highly efficient "content-addressed cache" pattern utilized by build systems like Bazel or sccache. Cache invalidation is perfectly localized to the specific mutated graph, rather than invalidating or forcing locks on a massive monolithic global database.*

## **5. Substrate Planning for Next-Generation Pipelines (V2.3 / V2.4)**

* The V2.2 port is merely the foundation. The architecture must be explicitly configured to absorb near-duplicate detection, deep structural code parsing, and extreme GPU acceleration without requiring a subsequent rewrite.*

### **5.1 MinHash Libraries for Near-Duplicate Detection**

* *MinHash is a probabilistic data structure utilized to rapidly estimate the Jaccard similarity between two sets (e.g., documents represented as mathematical sets of k-shingles).43 By hashing the shingles of a document and retaining only the minimum hash values, near-duplicates can be identified efficiently without engaging in O(N²) byte-for-byte comparisons across the entire workspace.* ^45  ^

**The Rust ecosystem contains several mature implementations, each targeting different scales:**

| MinHash Library | Primary Focus | Distinguishing Features |
| :---- | :---- | :---- |
| **minhash-rs** | General-purpose, memory efficient | Highly parsimonious with RAM; standard implementation.46 |
| **revbucket/minhash-rs** | Distributed .jsonl document deduplication | Specialized pipeline including file mapping, signature computation, edge gathering, and Union-Find clustering.47 |
| **probminhash** | State-of-the-art densification algorithms | Supports *weighted* Jaccard similarities, ProbMinHash3, SuperMinHash, and SetSketch. ^48^ |

***Verdict for V2.3:** **probminhash** *is the canonical choice for advanced, source-code-aware deduplication. Its support for weighted sets provides a massive mathematical edge in source code analysis. In programming languages, the frequency of specific structural tokens (e.g., pub fn, interface, class) carries immense statistical weight that standard unweighted MinHash ignores.48 probminhash captures this nuance.* 

**Implementation Parameters for Source Code:** *To effectively deduplicate source code without surfacing false positives on generic boilerplate, the recommended configuration utilizes a k-shingle size of 5 to 7 tokens. A hash count (permutation size) of 128 to 256 provides a robust balance between collision accuracy and memory utilization. A Jaccard similarity threshold of 0.85 to 0.90 is mathematically optimal for identifying heavily copy-pasted files or cloned repository directories.* ^51^

### **5.2 Symbol Extraction: Tree-sitter vs Ext-Aware Regex**

* *V2.3 aims to extract top-level declarations (classes, functions, interfaces) across 15+ programming languages.*

* **Regex / Heuristics**: *Exceptionally fast to execute, but inherently context-blind. Regular expressions cannot reliably distinguish between a legitimate function declaration, a function call, a function signature written inside a multiline block comment, or a string literal.*  
* **Tree-sitter (tree-sitter-rust)**: *Tree-sitter generates a full Concrete Syntax Tree (CST) by utilizing robust LR parsers.53 It handles syntax errors gracefully and allows for highly precise queries (e.g., extracting exclusively class_declaration or function_item nodes).* ^55^

* **Performance Consideration:** *Tree-sitter parsing is highly optimized for incremental updates. Parsing a standard Rust file from scratch takes approximately 6 milliseconds, but incremental updates after an edit take less than a millisecond.57 The primary bottleneck is the Foreign Function Interface (FFI) boundary. Tree-sitter is written in C, and returning tree nodes requires invoking Rust methods from the C environment, which distributes serialization costs. ^58^  However, the cost of this FFI overhead is entirely dwarfed by the accuracy gains.*
  
* **Verdict for V2.3:** **Tree-sitter** is the only viable substrate for polyglot structural indexing. Relying on regex for 15+ complex languages will inevitably result in an unmaintainable, brittle state machine fraught with edge cases.59

### **5.3 GPU MinHash Acceleration via wgpu**

* *For V2.4, leveraging the user's RTX 4090 to accelerate MinHash computations presents a massive computational opportunity. GPU architectures excel at computing thousands of non-cryptographic hashes simultaneously across massive datasets.* ^60 ^

* *The **wgpu** crate is the undisputed standard for cross-platform GPU compute within the Rust ecosystem, natively compiling down to the Vulkan API on Windows.62 Utilizing Compute Shaders written in WGSL (WebGPU Shading Language), or utilizing rust-gpu to compile Rust code directly to SPIR-V, allows the system to dispatch millions of shingle hashes to the GPU's streaming multiprocessors in parallel.* ^63^

* **Failure Mode:** *The fundamental limitation of GPU compute is the cost of transferring data from system RAM to VRAM over the PCIe bus. If the scanner attempts to send individual 5 KB files to the GPU for hashing one by one, the PCIe bus latency will completely negate the GPU's extreme compute speed. GPU acceleration is only mathematically viable if the CPU batches massive chunks of data (e.g., hundreds of megabytes of extracted token streams) and dispatches them in a single monolithic buffer to the WGSL compute shader, retrieving the computed hash signatures in a similarly batched response.*

### **5.4 Continuous Indexing and IPC Architecture**

* *When the scanner evolves into a persistent background service seamlessly integrated with the VS Code extension dispatch lane, one-shot CLI execution is no longer sufficient.*

* **Filesystem Watching:** *The **notify-rs** crate is the canonical solution. It wraps native OS-level APIs (specifically ReadDirectoryChangesW on Windows) to provide low-latency, cross-platform file modification events.* ^65^ 

* **Instead** *of periodic full workspace re-scans, notify-rs allows the scanner to selectively invalidate the bincode cache and re-parse only the precise files that triggered write events, achieving near-instantaneous index consistency.* ^67^

* **Inter-Process Communication (IPC):** *To communicate seamlessly with the TypeScript-based VS Code extension frontend, the Rust background service must establish a bidirectional IPC channel. Standard implementations utilize local TCP sockets or Named Pipes.68 Named Pipes are highly optimized within the Windows kernel and provide a secure, high-bandwidth channel for transmitting the serialized MinHash duplicate graphs and symbol indices back to the IDE interface without incurring network stack overhead.*

## **Synthesis**

* *The architectural transition from Bun V2.2 to Rust requires carefully navigating the boundaries of hardware constraints, memory mappings, and system call overhead. Bun's performance is already formidable due to its reliance on highly optimized native C/C++ libraries (OpenSSL, libuv) and V8's specialized JSON parsing capabilities. The Rust port will not magically resolve NVMe IOPS ceilings or bypass Windows Defender file-locking interventions.*
  
* *However, by rigorously selecting the correct substrates—leveraging jwalk for highly parallelized file traversal, *memmap2* for zero-copy parsing of large ML artifacts, file-format coupled with custom logic for exact binary signature identification, and a per-project sharded bincode cache—the Rust architecture establishes a robust, memory-safe foundation.*

* *This substrate is mathematically and structurally prepared to absorb the *probminhash* near-duplicate metrics and tree-sitter CST parsing requirements of V2.3. Furthermore, it cleanly opens the pipeline for the wgpu compute shader dispatch architectures of V2.4, unlocking scales of analysis fundamentally out of reach for a standard Node.js runtime environment.*

#### **Referanser**

1. Use the compilation cache when running typescript files through `--experimental-transform-types` · Issue #54741 · nodejs/node - GitHub, brukt mai 29, 2026, [https://github.com/nodejs/node/issues/54741](https://github.com/nodejs/node/issues/54741)  
2. sha2: explore addition of SSE and AVX2 backends for SHA-256 · Issue #327 - GitHub, brukt mai 29, 2026, [https://github.com/RustCrypto/hashes/issues/327](https://github.com/RustCrypto/hashes/issues/327)  
3. Is sha256 hashing in rust slower than go? - code review, brukt mai 29, 2026, [https://users.rust-lang.org/t/is-sha256-hashing-in-rust-slower-than-go/99740](https://users.rust-lang.org/t/is-sha256-hashing-in-rust-slower-than-go/99740)  
4. Assembling HeavyThing into Rust - Blitzy, brukt mai 29, 2026, [https://blitzy.com/blog/assembling-heavything-into-rust](https://blitzy.com/blog/assembling-heavything-into-rust)  
5. Sha2's sha256 is very inefficient when building with opt-level "s" (while ring's implementation is unaffected), brukt mai 29, 2026, [https://users.rust-lang.org/t/sha2s-sha256-is-very-inefficient-when-building-with-opt-level-s-while-rings-implementation-is-unaffected/106618](https://users.rust-lang.org/t/sha2s-sha256-is-very-inefficient-when-building-with-opt-level-s-while-rings-implementation-is-unaffected/106618)  
6. jwalk - Rust - Docs.rs, brukt mai 29, 2026, [https://docs.rs/jwalk/](https://docs.rs/jwalk/)  
7. Rust's recursive directory iterator 5x faster than CPP - Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/vdtnuw/rusts_recursive_directory_iterator_5x_faster_than](https://www.reddit.com/r/rust/comments/vdtnuw/rusts_recursive_directory_iterator_5x_faster_than)  
8. Feedback on crate for parallel recursive directory walk - help - Rust Users Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/feedback-on-crate-for-parallel-recursive-directory-walk/25001](https://users.rust-lang.org/t/feedback-on-crate-for-parallel-recursive-directory-walk/25001)  
9. Reading a lot of files : r/rust - Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/1btxq5s/reading_a_lot_of_files/](https://www.reddit.com/r/rust/comments/1btxq5s/reading_a_lot_of_files/)  
10. [lib] jwalk: Fast recursive directory walk - announcements - The Rust Programming Language Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/lib-jwalk-fast-recursive-directory-walk/25126](https://users.rust-lang.org/t/lib-jwalk-fast-recursive-directory-walk/25126)  
11. Byron/jwalk: Filesystem walk performed in parallel with streamed and sorted results - GitHub, brukt mai 29, 2026, [https://github.com/Byron/jwalk](https://github.com/Byron/jwalk)  
12. What's the fastest way to read a lot of files? - help - The Rust Programming Language Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/whats-the-fastest-way-to-read-a-lot-of-files/39743](https://users.rust-lang.org/t/whats-the-fastest-way-to-read-a-lot-of-files/39743)  
13. NTFS is really horrible handling many small files. When compiling/watching node ... - Hacker News, brukt mai 29, 2026, [https://news.ycombinator.com/item?id=41085855](https://news.ycombinator.com/item?id=41085855)  
14. Configuration Manager site sizing and performance FAQ - Microsoft Learn, brukt mai 29, 2026, [https://learn.microsoft.com/en-us/intune/configmgr/core/understand/site-size-performance-faq](https://learn.microsoft.com/en-us/intune/configmgr/core/understand/site-size-performance-faq)  
15. Best format for high-performance Serde? : r/rust - Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/123ci3h/best_format_for_highperformance_serde/](https://www.reddit.com/r/rust/comments/123ci3h/best_format_for_highperformance_serde/)  
16. How to Create Memory-Mapped Files in Rust - OneUptime, brukt mai 29, 2026, [https://oneuptime.com/blog/post/2026-01-30-how-to-create-memory-mapped-files-in-rust/view](https://oneuptime.com/blog/post/2026-01-30-how-to-create-memory-mapped-files-in-rust/view)  
17. Memory-Mapped I/O for Handling Files Larger Than RAM - DEV Community, brukt mai 29, 2026, [https://dev.to/kherld/memory-mapped-io-for-handling-files-larger-than-ram-4o7k](https://dev.to/kherld/memory-mapped-io-for-handling-files-larger-than-ram-4o7k)  
18. Inconsistent performance of memory mapped files : r/rust - Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/tibtwl/inconsistent_performance_of_memory_mapped_files/](https://www.reddit.com/r/rust/comments/tibtwl/inconsistent_performance_of_memory_mapped_files/)  
19. How to use mmap safely in Rust? - Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/10u4anm/how_to_use_mmap_safely_in_rust/](https://www.reddit.com/r/rust/comments/10u4anm/how_to_use_mmap_safely_in_rust/)  
20. memmap2::Mmap - Rust - Documentation - Piston, brukt mai 29, 2026, [https://docs.piston.rs/piston_window/memmap2/struct.Mmap.html](https://docs.piston.rs/piston_window/memmap2/struct.Mmap.html)  
21. How to Handle File I/O Efficiently in Rust - OneUptime, brukt mai 29, 2026, [https://oneuptime.com/blog/post/2026-01-07-rust-file-io-efficient/view](https://oneuptime.com/blog/post/2026-01-07-rust-file-io-efficient/view)  
22. Fastest way to create a hash of the contents of a file - Rust Users Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/fastest-way-to-create-a-hash-of-the-contents-of-a-file/102429](https://users.rust-lang.org/t/fastest-way-to-create-a-hash-of-the-contents-of-a-file/102429)  
23. how to maximize IOPS? : r/storage - Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/storage/comments/1lxgocl/how_to_maximize_iops/](https://www.reddit.com/r/storage/comments/1lxgocl/how_to_maximize_iops/)  
24. GitHub - bojand/infer: Small crate to infer file and MIME type by checking the magic number signature, brukt mai 29, 2026, [https://github.com/bojand/infer](https://github.com/bojand/infer)  
25. How can I verify the integrity and type of JPG, PDF, and DOCX files in Rust before storing them in MinIO?, brukt mai 29, 2026, [https://users.rust-lang.org/t/how-can-i-verify-the-integrity-and-type-of-jpg-pdf-and-docx-files-in-rust-before-storing-them-in-minio/116446](https://users.rust-lang.org/t/how-can-i-verify-the-integrity-and-type-of-jpg-pdf-and-docx-files-in-rust-before-storing-them-in-minio/116446)  
26. tree_magic_mini - Rust - Docs.rs, brukt mai 29, 2026, [https://docs.rs/tree_magic_mini/latest/tree_magic_mini/](https://docs.rs/tree_magic_mini/latest/tree_magic_mini/)  
27. tree_magic - Rust - Docs.rs, brukt mai 29, 2026, [https://docs.rs/tree_magic/](https://docs.rs/tree_magic/)  
28. theseus-rs/file-type - GitHub, brukt mai 29, 2026, [https://github.com/theseus-rs/file-type](https://github.com/theseus-rs/file-type)  
29. file-format - crates.io: Rust Package Registry, brukt mai 29, 2026, [https://crates.io/crates/file-format](https://crates.io/crates/file-format)  
30. hanzo_ai_format - Rust - Docs.rs, brukt mai 29, 2026, [https://docs.rs/hanzo-ai-format](https://docs.rs/hanzo-ai-format)  
31. pmetal-gguf — ML/AI/statistics in Rust // Lib.rs, brukt mai 29, 2026, [https://lib.rs/crates/pmetal-gguf](https://lib.rs/crates/pmetal-gguf)  
32. GitHub - safetensors/safetensors: Simple, safe way to store and distribute tensors, brukt mai 29, 2026, [https://github.com/safetensors/safetensors](https://github.com/safetensors/safetensors)  
33. reading safetensors in zig, brukt mai 29, 2026, [https://yobibyte.github.io/safetensors.html](https://yobibyte.github.io/safetensors.html)  
34. LLM GGUF Guide: File Format, Structure, and How It Works - ApX Machine Learning, brukt mai 29, 2026, [https://apxml.com/posts/gguf-explained-llm-file-format](https://apxml.com/posts/gguf-explained-llm-file-format)  
35. A Short Guide to the GGUF Format - Gianluca Guida's personal page., brukt mai 29, 2026, [http://tlbflush.org/post/2025_02_17_gguf_weekend/](http://tlbflush.org/post/2025_02_17_gguf_weekend/)  
36. GitHub - Dicklesworthstone/frankensqlite: Independent ground-up Rust reimplementation of SQLite with concurrent writers and information-theoretic durability, brukt mai 29, 2026, [https://github.com/dicklesworthstone/frankensqlite](https://github.com/dicklesworthstone/frankensqlite)  
37. Understanding SQLite - dzx.fr, brukt mai 29, 2026, [https://dzx.fr/blog/understanding-sqlite/](https://dzx.fr/blog/understanding-sqlite/)  
38. Releasing Fjall 3.0, brukt mai 29, 2026, [https://fjall-rs.github.io/post/fjall-3/](https://fjall-rs.github.io/post/fjall-3/)  
39. Towards Inserting One Billion Rows in SQLite Under A Minute - blag - avi.im, brukt mai 29, 2026, [https://avi.im/blag/2021/fast-sqlite-inserts/](https://avi.im/blag/2021/fast-sqlite-inserts/)  
40. Motivation - rkyv, brukt mai 29, 2026, [https://rkyv.org/motivation.html](https://rkyv.org/motivation.html)  
41. Rkyv is faster than {bincode, capnp, cbor, flatbuffers, postcard, prost, } | Hacker News, brukt mai 29, 2026, [https://news.ycombinator.com/item?id=26428812](https://news.ycombinator.com/item?id=26428812)  
42. djkoloski/rust_serialization_benchmark: Benchmarks for rust serialization frameworks - GitHub, brukt mai 29, 2026, [https://github.com/djkoloski/rust_serialization_benchmark](https://github.com/djkoloski/rust_serialization_benchmark)  
43. GitHub - LucaCappelletti94/minhash-rs: A Rust implementation of MinHash trying to be parsimonious with memory., brukt mai 29, 2026, [https://github.com/LucaCappelletti94/minhash-rs](https://github.com/LucaCappelletti94/minhash-rs)  
44. MinHash LSH in Milvus: The Secret Weapon for Fighting Duplicates in LLM Training Data, brukt mai 29, 2026, [https://milvus.io/blog/minhash-lsh-in-milvus-the-secret-weapon-for-fighting-duplicates-in-llm-training-data.md](https://milvus.io/blog/minhash-lsh-in-milvus-the-secret-weapon-for-fighting-duplicates-in-llm-training-data.md)  
45. minhash_rs - Rust - Docs.rs, brukt mai 29, 2026, [https://docs.rs/minhash-rs](https://docs.rs/minhash-rs)  
46. MinHash-rs — Rust implementation // Lib.rs, brukt mai 29, 2026, [https://lib.rs/crates/minhash-rs](https://lib.rs/crates/minhash-rs)  
47. revbucket/minhash-rs: Minhashing done in rust · GitHub - GitHub, brukt mai 29, 2026, [https://github.com/revbucket/minhash-rs](https://github.com/revbucket/minhash-rs)  
48. Rust implementation of probminhash, superminhash and hyperloglog sketching algorithms - GitHub, brukt mai 29, 2026, [https://github.com/jean-pierreBoth/probminhash](https://github.com/jean-pierreBoth/probminhash)  
49. probminhash - Rust - Docs.rs, brukt mai 29, 2026, [https://docs.rs/probminhash](https://docs.rs/probminhash)  
50. Locality-sensitive hashing for the edit distance - PMC - NIH, brukt mai 29, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC6612865/](https://pmc.ncbi.nlm.nih.gov/articles/PMC6612865/)  
51. LSH for Document Search: Improved Algorithm in Python - Mad Devs, brukt mai 29, 2026, [https://maddevs.io/writeups/lsh-for-document-search/](https://maddevs.io/writeups/lsh-for-document-search/)  
52. Large-scale Near-deduplication Behind BigCode - Hugging Face, brukt mai 29, 2026, [https://huggingface.co/blog/dedup](https://huggingface.co/blog/dedup)  
53. A Better R Programming Experience Thanks to Tree-sitter - rOpenSci, brukt mai 29, 2026, [https://ropensci.org/blog/2026/04/02/tree-sitter-overview/](https://ropensci.org/blog/2026/04/02/tree-sitter-overview/)  
54. The Grammar DSL - Tree-sitter, brukt mai 29, 2026, [https://tree-sitter.github.io/tree-sitter/creating-parsers/2-the-grammar-dsl.html](https://tree-sitter.github.io/tree-sitter/creating-parsers/2-the-grammar-dsl.html)  
55. Introducing Rust Sitter - Shadaj Laddad, brukt mai 29, 2026, [https://www.shadaj.me/writing/introducing-rust-sitter](https://www.shadaj.me/writing/introducing-rust-sitter)  
56. Tree-sitter-based Repo Map · Issue #3382 · aaif-goose/goose - GitHub, brukt mai 29, 2026, [https://github.com/aaif-goose/goose/issues/3382](https://github.com/aaif-goose/goose/issues/3382)  
57. Rust grammar for tree-sitter - GitHub, brukt mai 29, 2026, [https://github.com/tree-sitter/tree-sitter-rust](https://github.com/tree-sitter/tree-sitter-rust)  
58. Benchmark TypeScript Parsers: Demystify Rust Tooling Performance - Medium, brukt mai 29, 2026, [https://medium.com/@hchan_nvim/benchmark-typescript-parsers-demystify-rust-tooling-performance-025ebfd391a3](https://medium.com/@hchan_nvim/benchmark-typescript-parsers-demystify-rust-tooling-performance-025ebfd391a3)  
59. 4x speed-up by switching from regex to Nom for parsing : r/rust - Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/1gg3eom/4x_speedup_by_switching_from_regex_to_nom_for](https://www.reddit.com/r/rust/comments/1gg3eom/4x_speedup_by_switching_from_regex_to_nom_for)  
60. (PDF) Fast GPU ray tracing of dynamic meshes using geometry images - ResearchGate, brukt mai 29, 2026, [https://www.researchgate.net/publication/215506037_Fast_GPU_ray_tracing_of_dynamic_meshes_using_geometry_images](https://www.researchgate.net/publication/215506037_Fast_GPU_ray_tracing_of_dynamic_meshes_using_geometry_images)  
61. FED: Fast and Efficient Dataset Deduplication Framework with GPU Acceleration - arXiv, brukt mai 29, 2026, [https://arxiv.org/html/2501.01046v2](https://arxiv.org/html/2501.01046v2)  
62. ShaderStages in wgpu - Rust - Docs.rs, brukt mai 29, 2026, [https://docs.rs/wgpu/latest/wgpu/struct.ShaderStages.html](https://docs.rs/wgpu/latest/wgpu/struct.ShaderStages.html)  
63. RustyBamboo/hash-shader: SHA256 WebGPU Compute Shader (Kernel) Written in Rust, brukt mai 29, 2026, [https://github.com/RustyBamboo/hash-shader](https://github.com/RustyBamboo/hash-shader)  
64. GPU compute shader for SHA256 using Rust! - Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/mykk7x/gpu_compute_shader_for_sha256_using_rust](https://www.reddit.com/r/rust/comments/mykk7x/gpu_compute_shader_for_sha256_using_rust)  
65. amp-rs | MCP Servers · LobeHub, brukt mai 29, 2026, [https://lobehub.com/pl/mcp/mmorris35-amp-rs](https://lobehub.com/pl/mcp/mmorris35-amp-rs)  
66. LebJe/awesome-stars - GitHub, brukt mai 29, 2026, [https://github.com/LebJe/awesome-stars](https://github.com/LebJe/awesome-stars)  
67. Newest 'callback' Questions - Stack Overflow, brukt mai 29, 2026, [https://stackoverflow.com/questions/tagged/callback?tab=Newest](https://stackoverflow.com/questions/tagged/callback?tab=Newest)  
68. How do you do interprocess communication (IPC) in Rust? - Stack Overflow, brukt mai 29, 2026, [https://stackoverflow.com/questions/27683266/how-do-you-do-interprocess-communication-ipc-in-rust](https://stackoverflow.com/questions/27683266/how-do-you-do-interprocess-communication-ipc-in-rust)  
69. How to run a background service singleton in Rust - Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/phe7zl/how_to_run_a_background_service_singleton_in_rust](https://www.reddit.com/r/rust/comments/phe7zl/how_to_run_a_background_service_singleton_in_rust)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAaCAYAAABVX2cEAAABhUlEQVR4AeyTu0oDURCGo4jiXRFsBLFUtFAU0VIQEWy8lAo+hW9iZ2WpeKkE8YKlomIhFnaijYp4xSRFAsn3b3LC7pxtAumS8H8z58xsJmfnTOoTFfxUabEZWvgBuSLH+GZw6mBxAi4vf8C+FRK2ZxcEe2ELMqDio3inPxZzsAL70ALLkASvmGJdmCbYgEZYhToIa4DNIaShJHsyJfoxX7ALj7AI+jIuUAN2CB4gorhiIzyhIq/4HeiDBXDSyXXiFxdwPq7YOMlbkPYwP7AGnSANYtS7b3xEtlg32R54Bkkn1I1OspkGaRhzBZ5sMdevz+KTWfw2SOsYjckE3usXMe82Xb80P8qLS8w1zINOF9svcpFiuv4pgncQ1i+bTVDj5d9Ye/0iFimmhzXhT0oYTtmrfxqJe9axCvdsjCfaIQVW7wQ0Jpo/e3JSBanYLMt/OIcl0CuE54pQII3JDSu9Js6Xip0RbgP1TOivdMTeSjeoS9CP2VywV7FgUQlTK1Z+F6ukZ3kAAAD//11EDSIAAAAGSURBVAMAn3lDNYWGEaYAAAAASUVORK5CYII=>