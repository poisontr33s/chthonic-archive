# **Architectural Assessment and Port Validation: Upgrading the Chthonic-Archive Spread Scanner to Rust**

* *The transition of the polyglot workspace scanner from Bun (scripts/spread-value.ts V2.2) to a native Rust crate (chthonic-scanner) represents a major architectural shift. This report analyzes the performance bottlenecks, hashing strategies, file walking mechanics, cache paradigms, and future-generation substrates (V2.3 near-duplicate detection and V2.4 GPU compute acceleration) to guide the implementation.*


## **Performance Analysis and Hardware-Bound Bottlenecks**

* *A common misconception in runtime migration is that native compiled languages universally outperform high-level interpreters across all operations. The performance dynamics of SHA256 throughput, file traversal, and serialization reveal a more complex picture.*


### **SHA256 Throughput and Hardware Acceleration**

* *The Bun runtime does not execute cryptographic hashing in native JavaScript; instead, it delegates these tasks to the underlying OpenSSL library.1 On modern x86\_64 and ARM64 platforms, OpenSSL utilizes dedicated hardware instructions (SHA-NI and cryptographic extensions).1 Consequently, the execution gap for hashing large files between Bun and Rust is narrow.* ^3^

```

+-----------------------------------------------------------------------------+
| Bun (OpenSSL)                                                               |
|  --(N-API Context Switch)-->                                                |
+-----------------------------------------------------------------------------+  
                                     vs.  
+-----------------------------------------------------------------------------+  
| Rust (ring / sha2 with asm)                                                 |
|  ---------------->                                                          |
+-----------------------------------------------------------------------------+

```

*When evaluating Rust crates, ring and sha2 (built with the asm or native compiler features) deliver performance parity with OpenSSL.3 The ring crate relies on assembly-backed primitives, meaning it is largely unaffected by compiler optimization levels.3 The sha2 crate uses safe Rust by default, which can be slow unless compiled in release mode with target-cpu optimizations.* ^3^

**Under native optimization and active SHA-NI, both runtimes can saturate hardware-level execution speeds** ^1^ **^:^**

| System Architecture & Core Engine | Runtime Environment | MD5 Throughput | SHA-256 Throughput |
| :---- | :---- | :---- | :---- |
| **Apple M2 (ARM64)** 1 | Bun 1.31 1 | 0.7 GB/s 1 | 2.6 GB/s 1 |
| **Apple M2 (ARM64)** 1 | Node.js 23 1 | 0.6 GB/s 1 | 2.6 GB/s 1 |
| **Intel Ice Lake (x86\_64)** 1 | Bun 1.31 1 | 0.7 GB/s 1 | 1.2 GB/s 1 |
| **Intel Ice Lake (x86\_64)** 1 | Node.js 23 1 | 0.7 GB/s 1 | 1.2 GB/s 1 |

*The true performance win for the Rust scanner lies in the eradication of the N-API/JS context switching overhead, which dominates when hashing tens of thousands of files smaller than 32 KB.* ^1^


### **File Walking and Traversal Overheads on NTFS**

* *Traversing a filesystem directory tree is heavy on system calls, often consuming over 50% of the total wall-clock execution time in the kernel.7 In Bun, filesystem traversal is gated by single-threaded synchronous N-API bounds or asynchronous thread-pool delegation via libuv. Rust bypasses this by utilizing high-performance parallel walkers that issue non-blocking traversal syscalls concurrently.* ^8^

**A performance comparison of walking directories containing up to 100,000 files shows significant variations between sequential and parallel implementations:**

| Walker Implementation | Mode of Operation | 1,000 Files | 10,000 Files | 100,000 Files |
| :---- | :---- | :---- | :---- | :---- |
| **dirwalk** 9 | Parallel 9 | 0.35 ms 9 | 2.45 ms 9 | 24.70 ms 9 |
| **dirwalk** 9 | Sequential 9 | 1.99 ms 9 | 18.80 ms 9 | 206.00 ms 9 |
| **ignore** 9 | Parallel 9 | 5.86 ms 9 | 11.70 ms 9 | 71.10 ms 9 |
| **ignore** 9 | Sequential 9 | 5.50 ms 9 | 50.20 ms 9 | 531.00 ms 9 |
| **walkdir** 9 | Sequential 9 | 2.15 ms 9 | 20.30 ms 9 | 215.00 ms 9 |
| **jwalk** 9 | Parallel 9 | 11.90 ms 9 | 122.00 ms 9 | 1,262.00 ms 9 |

*On Windows NTFS hosts, the sequential performance of Bun is bounded by single-threaded directory-read system calls. Using a native parallel walker like dirwalk or ignore in Rust allows the scanner to run directory reads concurrently across all physical CPU cores, significantly reducing metadata discovery times* ^9^


### **Cache Serialization and Deserialization**

While Bun relies on V8's highly optimized JSON parser, reading and writing large flat-file NDJSON caches scales linearly ![][image1] with string manipulation and allocation overhead. Rust allows for compile-time generation of zero-copy binary deserializers like rkyv, which read serial structured data directly from memory maps.11 This architecture eliminates allocation and parsing logic, cutting warm cache startup times from seconds to microseconds.12

### **Hard Disk I/O Ceilings**

The performance limits of the workspace scanner are heavily dependent on the file-size distribution within the 158 GiB target repository. This physical performance ceiling is governed by three distinct hardware constraints:

* **Small Files (<32 KB):** Traversal is entirely bound by physical random-access latency, directory lock contention, and the kernel system-call ceiling.7 Total throughput rarely exceeds 50 to 100 MB/s, making parallel directory traversal and pipelined metadata queries essential.9  
* **Medium Files (~1 MB):** These files straddle the line between system-call overhead and sequential disk throughput. Parallel reading minimizes I/O bottlenecks by leveraging the deep command queues of modern NVMe drives.14  
* **Large Files (>10 MB):** Hashing is limited strictly by the sequential read throughput of the host NVMe SSD (typically 3.5 to 7.5 GB/s on modern PCIe Gen 4/5 interfaces).16
* 

## **Progressive Hashing and Multi-Stage File Comparison Strategy**

* *Hashing every file in its entirety is highly inefficient, particularly when a significant portion of the repository contains unique assets.* 

* *To prevent unnecessary disk reads and avoid saturating the NVMe controller, the scanner must employ a multi-stage progressive comparison pipeline.*

### **The Canonical Multi-Stage Pipeline**

A robust, progressive verification pipeline eliminates non-duplicate candidates early, postponing resource-intensive full-content hashing to the final validation step 17:

```

+-----------------------------------------------------------------------------+  
| 1. Metadata Ingestion: Query and Group Files strictly by File Size          |
+-----------------------------------------------------------------------------+  
                                     | (Prune Groups with Size < 2)  
                                     v  
+-----------------------------------------------------------------------------+  
| 2. Identity Resolution: Prune Hardlinks sharing the same System Inode ID    |
+-----------------------------------------------------------------------------+  
                                     | (Prune Groups with Size < 2)  
                                     v  
+-----------------------------------------------------------------------------+  
| 3. Prefix Hashing: Hash a small initial block (e.g., 4 KB to 64 KB)         |
+-----------------------------------------------------------------------------+  
                                     | (Prune Groups with Size < 2)  
                                     v  
+-----------------------------------------------------------------------------+  
| 4. Suffix Hashing: Hash a small trailing block (e.g., last 4 KB to 64 KB)   |
+-----------------------------------------------------------------------------+  
                                     | (Prune Groups with Size < 2)  
                                     v  
+-----------------------------------------------------------------------------+  
| 5. Collision Verification: Compute full content cryptographic SHA256        |
+-----------------------------------------------------------------------------+

```

*Applying this progressive filter chain allows the scanner to process large datasets while reading less than 1% of the total disk footprint.* ^19^

* A critical failure mode exists if the system halts at partial hashing (steps 3 or 4\) and assumes identical hashes indicate identical files.20 Many file formats (e.g., video, audio, database files, and structured code assets) append modifications sequentially or modify internal payload segments while preserving identical headers and footers.20 

* *To prevent false positives, full cryptographic validation must always be executed as the final verification step on any colliding subsets.* ^17^


### **Memory-Mapped I/O via memmap2**

* *For medium-to-large files (1 MB to 50 MB), utilizing the memmap2 crate is highly effective.* ^16^

* By memory-mapping a file, the OS maps the file directly into the application's virtual address space as a &[u8] slice.* ^21^ 

* *This bypasses the buffer allocation and memory copies associated with std::fs::read or Read::read_to_end. ^21^
However, memory mapping is highly sensitive to the underlying runtime environment. On Windows 11 host environments accessing virtualized filesystems (such as WSL2 cross-drive partitions /mnt/c/), memory-mapped I/O can be slower than standard buffered reads.* ^16^ 

* *When run on native NTFS, memory-mapped I/O is highly efficient, delivering execution speeds of 8 to 9 GB/s for non-cryptographic hashing.* ^16^


### **Parallel Hashing and Rayon Dispatch**

* *For cryptographic hashing (SHA256), individual file processing cannot be parallelized natively due to the sequential state-chaining design of the algorithm.* ^14^ 

* *However, processing thousands of independent files is highly parallelizable.14 Using Rayon's par\_iter allows the scanner to distribute file hashing tasks across all available CPU threads.* ^23^ 

* *On modern NVMe storage, parallel reads are highly effective because the SSD controller can process multiple concurrent read requests.14 Conversely, on legacy spinning disks (HDDs), parallel random reads degrade performance due to mechanical head thrashing.* ^14^ 

* *For these storage devices, the scanner must route I/O operations through a single-threaded sequential queue to preserve throughput.* ^14^


## **Magic-Byte and Machine Learning Artifact Detection**

* *The existing Bun scanner relies on \~30 hand-rolled magic-byte validation rules.*

* *Porting this logic to a production-grade Rust library requires a robust framework to match standard file signatures, combined with specialized parsers for large machine learning artifacts.*

### **Pure-Rust File Identification Library Analysis**

**Several pure-Rust crates are available to replace the hand-rolled magic-byte detection engine:**

* **infer:** A lightweight, dependency-free crate with approximately 120 formats. ^25^

*  *It is highly optimized but lacks native definitions for specialized ML/GPU artifacts.*
 
* **tree_magic_mini:*** A pure-Rust implementation of the shared MIME-database specification.25 It offers broad format coverage but carries a larger memory and binary footprint.*

* **file-format:** *The most comprehensive pure-Rust format identification crate. It supports over 200 formats, including compilation assets, ZIP-based archives, and binary outputs, with no external C bindings.*

### **Format Coverage Matrix**

**The table below outlines how each library matches the target workspace's file formats, highlighting where standard libraries fall short and require custom parsing:**

| Format Class | File Extension | infer Coverage | file-format Coverage | Custom Signature Parsing Required |
| :---- | :---- | :---- | :---- | :---- |
| **Deep Learning Weights** | .safetensors 26 | No | No | **Yes:** Must parse the 8-byte header size prefix followed by JSON validation.27 |
| **Quantized Models** | .gguf 29 | No | No | **Yes:** Must match the magic-byte array 0x46554747 ("GGUF" in ASCII).29 |
| **Interoperable ML Graphs** | .onnx 26 | No | Yes | **No:** file-format detects the protobuf signature.26 |
| **PyTorch Artifacts** | .pt / .pth 30 | No | No | **Yes:** Must identify PyTorch's underlying ZIP or Pickle archive wrapper.27 |
| **GPU Shaders** | .spv (SPIR-V) | No | Yes | **No:** Detected natively by file-format. |
| **Unity Configuration** | .meta / .asmdef | No | Yes | **No:** Recognized as structured YAML/JSON text configurations. |


### **Specialized Parsing for GGUF and SafeTensors**

Because general-purpose file identification libraries lack support for deep learning weights, the Rust scanner must implement custom parsers to identify these formats.


#### **GGUF Layout Analysis**

A GGUF file is a binary format designed for local inference.27 It starts with a 4-byte magic signature 29:  
![][image2]  
This signature is followed by a 32-bit version integer, a 64-bit tensor count, and a 64-bit metadata key-value count.29 Parsing these initial header fields allows the scanner to validate the format and extract model metadata without scanning the entire multi-gigabyte file.27

```

+-----------------------------------------------------------------------------+  
| GGUF Binary Structure                                                       |  
|  -> ->                                                                      |  
+-----------------------------------------------------------------------------+

```


#### **SafeTensors Layout Analysis**

* **SafeTensors** *is a secure, zero-copy format designed to replace unsafe Python Pickle serialization.* ^28^ 
* Its layout consists of three distinct segments.* ^27^**^:^**

  * 1. **Header Size:** An 8-byte little-endian unsigned 64-bit integer, ![][image3], defining the length of the metadata header.27  

  * 2. **Metadata Header:** ![][image3] bytes containing a UTF-8 JSON string.27 This string must begin with a curly brace ({ or 0x7B).27  

  * 3. **Payload Buffer:** The remaining bytes of the file, containing the raw tensor data.27

 * *To identify a SafeTensors file, the scanner reads the first 8 bytes to get the header length ![][image3], and then checks if the byte at index 8 matches 0x7B.* ^27^ 

**This simple check confirms the file's format without reading the rest of the payload.**

```

+-----------------------------------------------------------------------------+  
| SafeTensors Layout                                                          |  
|  -> ->                                                                      |  
+-----------------------------------------------------------------------------+

```

## **Cache Architecture and Durability Paradigms**

The V2.2 Bun implementation uses an append-only NDJSON cache. While simple and robust, parsing flat files becomes a bottleneck as the dataset grows.31 For a workspace containing millions of records, the scanner needs a more scalable cache architecture.


### **Storage Engine Analysis**

Several cache storage options are available, each with distinct trade-offs for indexing speeds and payload sizes 32:

| Storage Engine & Format | Key-Value Performance | Query capabilities | Read Complexity | Write Overhead | Rust Ecosystem Fit |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **NDJSON** 31 | Slow ![][image1] 31 | None 31 | High (re-parse) | Low (append-only) | High (serde\_json) |
| **SQLite (rusqlite)** 33 | Fast ![][image4] | SQL Indexes 31 | Low (point query) | Medium (ACID write) | High (bundled feature) 34 |
| **Binary (bitcode)** 12 | Fast (in-memory) | None | Medium (deserialization) 12 | Low 12 | High (Apache-2.0) 12 |
| **Zero-Copy (rkyv)** 11 | Extremely Fast | None | Zero-Copy Read 11 | High (construction) 12 | High (pure Rust) |


#### **SQLite (rusqlite)**

SQLite is highly reliable and extensively tested.34 In the Rust ecosystem, rusqlite serves as the standard synchronous interface.33  
Using the bundled feature compiles SQLite directly into the Rust binary, simplifying cross-platform compilation on Windows and eliminating external C dependencies.34 For key-by-path lookups, SQLite's B+ Tree index outperforms sequential file scanning.31 Additionally, SQLite can write database updates faster than raw filesystem writes for small blobs, as it minimizes file handle opening overhead.34

#### **Flat-File Binary Formats (bitcode & rkyv)**

* *If the cache only requires simple key-value lookups, serialization libraries like bitcode or rkyv offer a high-performance alternative to structured databases.* ^12^**^:^**

 * **bitcode:** A highly optimized binary serializer that produces payloads 20% smaller and 7x faster than MessagePack or Protobuf, making it ideal for disk-space efficiency.12  

* **rkyv:** A zero-copy binary format.11 It allows the scanner to query cached metadata directly from a memory-mapped file without loading and deserializing the entire payload into heap memory, offering near-instantaneous read times.11

### **The Recommended Hybrid Cache Architecture**

For a large-scale workspace containing over 500,000 files, a hybrid cache design is recommended:

```

+-----------------------------------------------------------------------------+
| Hybrid Cache Engine                                                         |
|                                                                             |
|                      +------------------------+                             |
|                      | Point Query / Update   |                             |
|                      +------------------------+                             |
|                                   |                                         |
|                                   v                                         |
|                      +------------------------+                             |
|                      |  SQLite Engine (WAL)   |                             |
|                      +------------------------+                             |
|                        |                    |                               |
|       (Path Metadata)  v                    v  (Serialized Payloads)        |
|     +--------------------+                +--------------------+            |
|     | B+ Tree Indexing   |                |  bitcode payloads  |            |
|     +--------------------+                +--------------------+            |
+-----------------------------------------------------------------------------+

```

*Integrating SQLite with the bitcode binary serializer provides the optimal balance of query flexibility and performance.12 SQLite manages directory hierarchies and indexed path metadata, while file inventory datasets are stored in compressed bitcode payloads.* ^12^

* *Activating SQLite's Write-Ahead Logging (WAL) and memory-mapped I/O further optimizes read and write performance on Windows environments.*


### **Split-Cache Strategy**

Using a single, global cache file introduces lock contention and write-block bottlenecks. To avoid this, the scanner should implement a split-cache strategy that segments the cache by project root:

```

workspace/
├── project_a/
│   └──.spread/cache.db  <-- Isolated SQLite database for project_a
├── project_b/
│   └──.spread/cache.db  <-- Isolated SQLite database for project_b
└──.spread/global.db     <-- Global index mapping project roots

```

**This split-cache design offers several key advantages:**

* **Concurreny:** *Parallel walks can read and write to their respective project caches simultaneously without database lock contention.*  

* **Portability:** *Moving or deleting a project subdirectory automatically preserves its local cache, preventing corruption of the global index.* 

* **Performance:** *Loading and query times scale with the size of individual projects rather than the entire workspace.*


## **High-Scale Directory Traversal and Walker Optimization**

* *At scale, directory traversal is a primary bottleneck.*

* *The scanner must select a walking strategy that minimizes system-call overhead and scales efficiently across hundreds of thousands of files on NTFS.*

### **Walk Engine Comparison**

**Rust offers several directory traversal libraries, each designed for different concurrency models:**

* **walkdir:** A single-threaded, depth-first recursive walker.10 It is stable and highly compatible but slow at scale.10  

* **ignore:** A multi-threaded parallel walker used in ripgrep. ^8^
  * *It natively parses ignore files (e.g., .gitignore).38 However, to meet the requirement of scanning all files, this ignore logic must be explicitly disabled, which adds configuration complexity.*

* **jwalk:** *A parallel directory walker built on Rayon that streams sorted results.8 It improves latency for sorted directory lists but introduces synchronization overhead.*^10^

* **dirwalk:** *A highly optimized parallel traversal library.9 It uses a work-stealing scheduling architecture that outperforms other walking engines in raw scale benchmarks.* ^9^

### **NTFS Traversal Optimization**

* *On Windows NTFS filesystems, standard recursive traversal is heavily bound by system-call latency.7 While a native parallel walker like dirwalk or ignore minimizes this by parallelizing traversal tasks, the ultimate optimization for Windows environments is raw Master File Table (MFT) parsing.* ^41^

* *By reading the NTFS volumes directly and parsing the binary MFT blocks, a scanner can bypass the Windows filesystem subsystem and catalog over a million files in less than 25 milliseconds.* ^41^ 

* *However, this raw approach requires administrative privileges to access physical disk volumes, which limits its usability for standard users.* 

* *For a non-administrative workspace scanner, the recommended approach is a multi-threaded parallel walk using dirwalk.9 This maximizes I/O queue depth and concurrent system-call execution without requiring elevated privileges.* ^9^

## **Next-Generation Substrates for Near-Duplicate and Symbol Extraction**

* *The roadmap for V2.3 and V2.4 introduces MinHash near-duplicate detection, multi-language symbol extraction, and optional GPU compute acceleration. Designing the core architecture with these features in mind prevents downstream refactoring.*


### **High-Performance MinHash Crates**

* *MinHash is a locality-sensitive hashing algorithm used to estimate the Jaccard similarity coefficient between two sets.* ^43^ **^:^**
![][image5]

* *By mapping sets to a fixed-size signature of minimum hash values, the scanner can approximate similarity without storing or comparing large datasets. ^43^ **^:^**
![][image6]

* *In the Rust ecosystem, two primary crates implement this algorithm:*

* **probabilistic-collections:** *A standard library providing key-value collections and a baseline MinHash implementation.43 However, it relies on standard cryptographic hash builders, which introduces significant CPU overhead in high-throughput pipelines.* ^43^

* **rensa:** *A high-performance MinHash library designed specifically for large-scale deduplication.46 It is up to 12 times faster than other native implementations.* ^46^

* *rensa achieves its speed through two key optimizations.* ^46^ **^:^**
  * 1. **Multiply-Shift Hashing (R-MinHash):** It replaces expensive modular reduction operations with a fast multiply-shift hash family. ^46^ **^:^** 

![][image7]

* *This allows signatures to be stored as 32-bit integers, halving memory usage compared to standard 64-bit implementations.* ^46^

  * 2. **Vectorized Pipeline:** It avoids generic trait dispatch in hot code paths and hashes input tokens in vectorized blocks of 32\.46

  * *For source-code deduplication, the recommended configuration is a token-based  ![][image8]-shingle generator with ![][image9] or ![][image10], combined with a signature size of 128 or 256 permutations to optimize accuracy and memory footprint.*

```

+-----------------------------------------------------------------------------+
| Tokenization Pipeline                                                       |
|  -> ->                                                                      |
+-----------------------------------------------------------------------------+

```


### **Symbol Extraction Across Languages**

* *Extracting language-level symbols (such as function declarations, classes, and structs) can be implemented using either regular expressions or incremental parsers.* 

*While regular expression extractors are simple and fast, they lack the contextual accuracy required for complex codebases.47 Regex-based extraction struggles to resolve scopes, nested classes, template parameters, multi-line definitions, and docstrings, leading to high false-positive rates.* ^47^

* *The canonical solution is Tree-sitter.47 Tree-sitter compiles language grammars into fast, incremental concrete syntax tree parsers.* ^48^

* *Using its declarative query interface, developers can extract specific AST nodes using Lisp-like S-expression queries.* ^47^ 

* *This ensures the parser understands nested syntax scopes and ignores non-code structures like comments and string literals.* ^47^

```

; Tree-sitter Query to extract Rust function definitions  
(function\_item  
  name: (identifier) @function.name)

```

*By using Tree-sitter queries with language-specific grammars (e.g., tree-sitter-rust, tree-sitter-typescript), the scanner can extract precise syntax patterns across multiple languages in a single pipeline.* ^47^

### **GPU MinHash via wgpu**

* *For large repositories containing millions of files, calculating MinHash signatures on the CPU can become a performance bottleneck. The V2.4 roadmap addresses this by leveraging the host's NVIDIA RTX 4090 GPU for hardware acceleration.*  

* *The standard cross-platform GPU compute engine in the Rust ecosystem is wgpu.50 It provides a safe, portable abstraction layer over native backends (Vulkan, DirectX 12, and Metal).* ^51^

```

+-----------------------------------------------------------------------------+
| GPU Acceleration Substrate                                                  |
|  -> -> [Vulkan API] ->                                              |
+-----------------------------------------------------------------------------+

```

* *To run MinHash computations on the GPU, the scanner must implement custom WGSL (WebGPU Shading Language) compute shaders.* ^52^ 

* *The tokenized shingle inputs are packed into contiguous GPU storage buffers, allowing the shader to calculate thousands of hash permutations in parallel across the GPU's execution units.*

### **Continuous Indexing and Event-Driven Invalidation**

Running full periodic directory scans across hundreds of thousands of files degrades disk and CPU performance. To achieve near-instantaneous indexing in a persistent service, the Rust scanner must adopt an event-driven continuous indexing model:

```

+------------------------------------------------------------------------------+
| File Modification Event                                                      |
|                                                                              |
|                      +------------------------+                              |
|                      |  notify-rs Watch Loop  |                              |
|                      +------------------------+                              |
|                                   |                                          |
|                                   v                                          |
|                      +------------------------+                              |
|                      | Progressive Re-Hashing |                              |
|                      +------------------------+                              |
|                                   |                                          |
|                                   v                                          |
|                      +-------------------------+                             |
|                      | SQLite WAL Invalidation |                             |
|                      +-------------------------+                             |
+------------------------------------------------------------------------------+

```

* Using the notify (or notify-rs) crate, the scanner hooks directly into the host OS filesystem APIs (such as FSEvents on macOS or ReadDirectoryChangesW on Windows) to monitor files and directories.* 

* *When a file modification event occurs, the scanner isolates the changed file path, executes the progressive hashing pipeline, and updates the local SQLite database cache.* 

* *This event-driven architecture keeps the workspace index updated in real time, eliminating the overhead of full periodic directory sweeps.*

## **Architectural Verdict and Implementation Path**

* *Based on the architectural analysis, porting the scanner to Rust is highly recommended and provides clear performance advantages for large workspaces.*

* *While Bun delivers comparable SHA256 hashing throughput for large, contiguous files due to its direct delegation to OpenSSL 1, the Rust implementation significantly outperforms the Bun runtime across several critical areas:*

* **Concurrency:** *Rust's work-stealing parallel filesystem traversal using dirwalk overcomes the system-call bottlenecks that limit Bun's single-threaded event loop.* ^7^

* **Startup Overhead:** *Eliminating the N-API/JS context-switching wrapper drastically reduces latency when scanning datasets dominated by small files.* ^1^

* **Cache Efficiency:** Replacing flat NDJSON with an indexed, split SQLite database wrapper compiled natively prevents write locking and scales efficiently to millions of records.31

* *Furthermore, compiling directly to native machine code provides a robust foundation for integrating Tree-sitter parsers 48, rensa MinHash signatures 46, and wgpu compute shaders 52 for GPU-accelerated near-duplicate detection in the V2.3 and V2.4 releases.*

#### **Referanser**

1. JavaScript hashing speed comparison: MD5 versus SHA-256 ..., brukt mai 29, 2026, [https://lemire.me/blog/2025/01/11/javascript-hashing-speed-comparison-md5-versus-sha-256/](https://lemire.me/blog/2025/01/11/javascript-hashing-speed-comparison-md5-versus-sha-256/)  
2. Hardware Optimised SHA256 Hashing in Golang | by Paulo Gomes \- Medium, brukt mai 29, 2026, [https://medium.com/@pjbgf/hardware-optimised-sha256-hashing-in-golang-a71ed24517c0](https://medium.com/@pjbgf/hardware-optimised-sha256-hashing-in-golang-a71ed24517c0)  
3. Sha2's sha256 is very inefficient when building with opt-level "s" (while ring's implementation is unaffected), brukt mai 29, 2026, [https://users.rust-lang.org/t/sha2s-sha256-is-very-inefficient-when-building-with-opt-level-s-while-rings-implementation-is-unaffected/106618](https://users.rust-lang.org/t/sha2s-sha256-is-very-inefficient-when-building-with-opt-level-s-while-rings-implementation-is-unaffected/106618)  
4. Is sha256 hashing in rust slower than go? \- code review, brukt mai 29, 2026, [https://users.rust-lang.org/t/is-sha256-hashing-in-rust-slower-than-go/99740](https://users.rust-lang.org/t/is-sha256-hashing-in-rust-slower-than-go/99740)  
5. sha2: explore addition of SSE and AVX2 backends for SHA-256 · Issue \#327 \- GitHub, brukt mai 29, 2026, [https://github.com/RustCrypto/hashes/issues/327](https://github.com/RustCrypto/hashes/issues/327)  
6. Optimizing hashing performance · Issue \#136 · nodejs/performance \- GitHub, brukt mai 29, 2026, [https://github.com/nodejs/performance/issues/136](https://github.com/nodejs/performance/issues/136)  
7. Blazing-Fast Directory Tree Traversal: Haskell Streamly Beats Rust \- Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/1iekv4t/blazingfast\_directory\_tree\_traversal\_haskell/](https://www.reddit.com/r/rust/comments/1iekv4t/blazingfast_directory_tree_traversal_haskell/)  
8. Reading a lot of files : r/rust \- Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/1btxq5s/reading\_a\_lot\_of\_files/](https://www.reddit.com/r/rust/comments/1btxq5s/reading_a_lot_of_files/)  
9. dirwalk \- crates.io: Rust Package Registry, brukt mai 29, 2026, [https://crates.io/crates/dirwalk](https://crates.io/crates/dirwalk)  
10. Feedback on crate for parallel recursive directory walk \- help \- Rust Users Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/feedback-on-crate-for-parallel-recursive-directory-walk/25001](https://users.rust-lang.org/t/feedback-on-crate-for-parallel-recursive-directory-walk/25001)  
11. SQLite JSON at full index speed using generated columns \- Hacker News, brukt mai 29, 2026, [https://news.ycombinator.com/item?id=46243904](https://news.ycombinator.com/item?id=46243904)  
12. bitcode: smallest and fastest binary serializer : r/rust \- Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/1bfxqvh/bitcode\_smallest\_and\_fastest\_binary\_serializer/](https://www.reddit.com/r/rust/comments/1bfxqvh/bitcode_smallest_and_fastest_binary_serializer/)  
13. Performance Impact of Parallel Disk Access | Piotr Kołaczkowski, brukt mai 29, 2026, [https://pkolaczk.github.io/disk-parallelism/](https://pkolaczk.github.io/disk-parallelism/)  
14. Hashing a bunch of files in aparallel \- code review \- Rust Users Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/hashing-a-bunch-of-files-in-aparallel/123496](https://users.rust-lang.org/t/hashing-a-bunch-of-files-in-aparallel/123496)  
15. Eggstrain \- CMU 15-721, brukt mai 29, 2026, [https://15721.courses.cs.cmu.edu/spring2024/files/final/execution1.pdf](https://15721.courses.cs.cmu.edu/spring2024/files/final/execution1.pdf)  
16. Fastest way to create a hash of the contents of a file \- Rust Users Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/fastest-way-to-create-a-hash-of-the-contents-of-a-file/102429](https://users.rust-lang.org/t/fastest-way-to-create-a-hash-of-the-contents-of-a-file/102429)  
17. pkolaczk/fclones: Efficient Duplicate File Finder \- GitHub, brukt mai 29, 2026, [https://github.com/pkolaczk/fclones](https://github.com/pkolaczk/fclones)  
18. Disk Full of Duplicates? fclones: Fast Find, Safe Cleanup | via X-CMD, brukt mai 29, 2026, [https://www.x-cmd.com/install/fclones/](https://www.x-cmd.com/install/fclones/)  
19. I built a duplicate file finder that actually handles 8 TB+ NAS drives without choking – desktop \+ Docker web UI (open source) : r/DataHoarder \- Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/DataHoarder/comments/1rxhd5h/i\_built\_a\_duplicate\_file\_finder\_that\_actually/](https://www.reddit.com/r/DataHoarder/comments/1rxhd5h/i_built_a_duplicate_file_finder_that_actually/)  
20. Do NOT use the option "Partially hash files bigger than" · Issue \#1360 · arsenetar/dupeguru, brukt mai 29, 2026, [https://github.com/arsenetar/dupeguru/issues/1360](https://github.com/arsenetar/dupeguru/issues/1360)  
21. memmap2 \- Rust \- Docs.rs, brukt mai 29, 2026, [https://docs.rs/memmap2](https://docs.rs/memmap2)  
22. Fastest way to create a hash of the contents of a file \- \#3 by drewtato \- Rust Users Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/fastest-way-to-create-a-hash-of-the-contents-of-a-file/102429/3](https://users.rust-lang.org/t/fastest-way-to-create-a-hash-of-the-contents-of-a-file/102429/3)  
23. rayon-rs/rayon \- A data parallelism library for Rust \- GitHub, brukt mai 29, 2026, [https://github.com/rayon-rs/rayon](https://github.com/rayon-rs/rayon)  
24. How to Process Millions of Records with Parallel Jobs in Rust \- OneUptime, brukt mai 29, 2026, [https://oneuptime.com/blog/post/2026-01-25-process-millions-records-parallel-jobs-rust/view](https://oneuptime.com/blog/post/2026-01-25-process-millions-records-parallel-jobs-rust/view)  
25. PO files — Packages not i18n-ed \- Debian, brukt mai 29, 2026, [https://www.debian.org/international//l10n//po/todo](https://www.debian.org/international//l10n//po/todo)  
26. Blog Article: "Safetensors, CKPT, ONNX, GGUF, and Other Key AI Model Formats \[2026\]" · Issue \#7744 \- GitHub, brukt mai 29, 2026, [https://github.com/onnx/onnx/issues/7744](https://github.com/onnx/onnx/issues/7744)  
27. GGUF, the long way around \- Vicki Boykis, brukt mai 29, 2026, [https://vickiboykis.com/2024/02/28/gguf-the-long-way-around/](https://vickiboykis.com/2024/02/28/gguf-the-long-way-around/)  
28. GitHub \- safetensors/safetensors: Simple, safe way to store and distribute tensors, brukt mai 29, 2026, [https://github.com/safetensors/safetensors](https://github.com/safetensors/safetensors)  
29. On-Device Inference Engine from Scratch using Rust — Layer 1: The GGUF Loader | by Karthikeyan Sukumaran | Medium, brukt mai 29, 2026, [https://medium.com/@karthikworks/layer-1-the-gguf-loader-e81e6ce4170a](https://medium.com/@karthikworks/layer-1-the-gguf-loader-e81e6ce4170a)  
30. mlmf \- crates.io: Rust Package Registry, brukt mai 29, 2026, [https://crates.io/crates/mlmf](https://crates.io/crates/mlmf)  
31. json vs sqlite for 300000 photos database \- Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/Database/comments/1rhq5tm/json\_vs\_sqlite\_for\_300000\_photos\_database/](https://www.reddit.com/r/Database/comments/1rhq5tm/json_vs_sqlite_for_300000_photos_database/)  
32. Binary Serialization Formats. A Technical Benchmark & Decision Guide | by Shekhar Manna, brukt mai 29, 2026, [https://medium.com/@shekhar.manna83/binary-serialization-formats-e2703f053010](https://medium.com/@shekhar.manna83/binary-serialization-formats-e2703f053010)  
33. Rust ORMs in 2026: Diesel vs SQLx vs SeaORM vs Rusqlite — Which One Should You Actually Use? \- Aarambh Dev Hub, brukt mai 29, 2026, [https://aarambhdevhub.medium.com/rust-orms-in-2026-diesel-vs-sqlx-vs-seaorm-vs-rusqlite-which-one-should-you-actually-use-706d0fe912f3](https://aarambhdevhub.medium.com/rust-orms-in-2026-diesel-vs-sqlx-vs-seaorm-vs-rusqlite-which-one-should-you-actually-use-706d0fe912f3)  
34. Recommendation for cache-type database \- help \- The Rust Programming Language Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/recommendation-for-cache-type-database/125781](https://users.rust-lang.org/t/recommendation-for-cache-type-database/125781)  
35. Recommendations for cache-type database \- help \- Rust Users Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/recommendations-for-cache-type-database/90336](https://users.rust-lang.org/t/recommendations-for-cache-type-database/90336)  
36. Rust and sqlite, which one to use? \- help \- The Rust Programming Language Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/rust-and-sqlite-which-one-to-use/90780](https://users.rust-lang.org/t/rust-and-sqlite-which-one-to-use/90780)  
37. Deep dive into Turso, the "SQLite rewrite in Rust" \- Sylvain Kerkour, brukt mai 29, 2026, [https://kerkour.com/turso-sqlite](https://kerkour.com/turso-sqlite)  
38. \[lib\] jwalk: Fast recursive directory walk \- announcements \- The Rust Programming Language Forum, brukt mai 29, 2026, [https://users.rust-lang.org/t/lib-jwalk-fast-recursive-directory-walk/25126](https://users.rust-lang.org/t/lib-jwalk-fast-recursive-directory-walk/25126)  
39. Directory Traversal \- Rust Cookbook, brukt mai 29, 2026, [https://rust-lang-nursery.github.io/rust-cookbook/file/dir.html](https://rust-lang-nursery.github.io/rust-cookbook/file/dir.html)  
40. ignore::Walk \- Rust, brukt mai 29, 2026, [https://rust-corpus.github.io/qrates/doc/ignore/struct.Walk.html](https://rust-corpus.github.io/qrates/doc/ignore/struct.Walk.html)  
41. Flash Find: A high-performance, open-source file search engine for Windows (Rust \+ Iced \+ Rayon) \- Reddit, brukt mai 29, 2026, [https://www.reddit.com/r/rust/comments/1qfccak/flash\_find\_a\_highperformance\_opensource\_file/](https://www.reddit.com/r/rust/comments/1qfccak/flash_find_a_highperformance_opensource_file/)  
42. christhomas/rust-fs-ntfs: Pure-Rust NTFS filesystem driver with a C ABI (fs\_ntfs\_\*) for FFI from Swift, C, Go, etc. \- GitHub, brukt mai 29, 2026, [https://github.com/christhomas/rust-fs-ntfs](https://github.com/christhomas/rust-fs-ntfs)  
43. MinHash in probabilistic\_collections::similarity \- Rust \- Docs.rs, brukt mai 29, 2026, [https://docs.rs/probabilistic-collections/latest/probabilistic\_collections/similarity/struct.MinHash.html](https://docs.rs/probabilistic-collections/latest/probabilistic_collections/similarity/struct.MinHash.html)  
44. Approximating Jaccard similarity with MinHash \- Can Güney Aksakalli, brukt mai 29, 2026, [https://aksakalli.github.io/2016/03/01/jaccard-similarity-with-minhash.html](https://aksakalli.github.io/2016/03/01/jaccard-similarity-with-minhash.html)  
45. probabilistic\_collections::similarity \- Rust \- Docs.rs, brukt mai 29, 2026, [https://docs.rs/probabilistic-collections/latest/probabilistic\_collections/similarity/index.html](https://docs.rs/probabilistic-collections/latest/probabilistic_collections/similarity/index.html)  
46. beowolx/rensa: High-performance MinHash ... \- GitHub, brukt mai 29, 2026, [https://github.com/beowolx/rensa](https://github.com/beowolx/rensa)  
47. Unraveling Tree-Sitter Queries: Your Guide to Code Analysis Magic \- DEV Community, brukt mai 29, 2026, [https://dev.to/shrsv/unraveling-tree-sitter-queries-your-guide-to-code-analysis-magic-41il](https://dev.to/shrsv/unraveling-tree-sitter-queries-your-guide-to-code-analysis-magic-41il)  
48. Incremental Parsing Using Tree-sitter \- Strumenta \- Federico Tomassetti, brukt mai 29, 2026, [https://tomassetti.me/incremental-parsing-using-tree-sitter/](https://tomassetti.me/incremental-parsing-using-tree-sitter/)  
49. Tree-sitter and its queries \- Topiary, brukt mai 29, 2026, [https://topiary.tweag.io/book/getting-started/on-tree-sitter.html](https://topiary.tweag.io/book/getting-started/on-tree-sitter.html)  
50. Wgpu \- A cross-platform, safe, pure-Rust graphics API. \- GitHub, brukt mai 29, 2026, [https://github.com/gfx-rs/wgpu](https://github.com/gfx-rs/wgpu)  
51. wgpu \- Rust \- Docs.rs, brukt mai 29, 2026, [https://docs.rs/wgpu/](https://docs.rs/wgpu/)  
52. Rust GPU Programming with wgpu: The 2026 Guide \- Rustify, brukt mai 29, 2026, [https://rustify.rs/articles/rust-gpu-computing-wgpu-2026](https://rustify.rs/articles/rust-gpu-computing-wgpu-2026)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC4AAAAXCAYAAAB0zH1SAAAEEUlEQVR4AeyXWehNWxzHjzvf697rXnfqmmWeMouSMoSIzBFFPCDyYkhRypsnibzwYExkTDInJXMeEB7Ms8wyZf58trNO+2xnnyPOi/Lv+92/31rrt9f5rfX7rd/a/28yX+jfV8djgfsW/U9YAZYLlZjoe5hDsR3/C6sWUPhSG5R+sBZMc0q72Yx3hm9hudCAiZZAF4DIZAo57o5NYnQ3VJ+IfAiPwA3wAlwIdRKRB9/7mR7tEHlwMbfpcUFyG7q2iAi/89wBHQtcT7siPAy3wjkw+t2k4xq5srYYdIHDoLtcDaltT+QDOBZ2hXE0oTEUzof+MCIPe2j9CxfBl9CFhIjSzDzi0R0OhOvgL3AAfAKFfVVR+sCMziilK5mL8j90l4cgdWQc8h7Ume3IebACHAQDbI+ncQhehGn4g4Ef4VT4AxwOfReRg6loxJ7let4rtleiToGV4o6PoaMX1NHKyJlwMTwL49hF4xV0gT8hRRUe7tZGpAtEFEQNet2ENcgz0GjqKGqE73g2gidhIZgyRq1ZcLw6VpOhKzqHbA/NcSOAmgdX/oIepQtAzfhjngedsZ3GpgxocwO5Ghr63sgAI2IkLoeOhLxF24h2Co670658MwPu2CrkSOihRBTEdXqD463Rr0DzH5EK7Y5mR9citR+BDNWiIbq5fh9ZCOb7NQaa6Lg51olGWA1qUdRk1IOzHxnQGOUOfA7TYG23xF7KGrjzVpZ2tDtA4QE/qFKEpxirquNWEkP2mg6JSIWLtNr4o1aJuKG7ESIQ7w96yO+72Q5tl2Z1o2tp9K5Iy++saSQq6nik8TC3fBk1FXUY8UB5aI0QzY9GyG9TMbx0AMUDZ5l11/UhLb8xzaGyjjuRq/+P7vowDZbLaQy62zqO+tEwUh74Y4k3PEML6PNQKm+ip+U3Qzlc0XFDvI8uJ49qJHoSVgzHvDBGMegPInK4ima6mXaoH0DHvBm9dZODO+lwM6xMx9FLwXle6biGK3hYorwNl6HXhsLF1EWxdDVHGlKdRM2D4bWup6VaS6x/g09hEqac81vfkxFJ2uqP1e9UcNxLxuvdGt4X6/PQFHqDtEQuR3rLOTnqB7DEmZ//JEa60X4MvRP6I02DeN2mK4Kl0W8hUyXqSHkYuXqM7QqOo2f28jBcfqcMRu8B/4b2bUIWqzgu3GrRCrs4vGV/pcOdkl73W2gnYSUxmi4sORZvW+eN3Im44xr48ePuuQN+qemM/aVoznu4jEpaupSao9S4C/ei1LeLScdLvVxs3O8UU6tjMaPPGLMUWzKtaG/L6bi5PAHH/LL0dkUtGyzFM5jN/wOim7ecjjNvxkmno4yGHlZEWWAJtvL4j0U0Ybrj0fAnPU7z1izoFySiLPCfD79rcpO9AwAA//8JNfiHAAAABklEQVQDAJjPxC9QIlxLAAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAxCAYAAABnGvUlAAAQAElEQVR4AezdA5hsu7YF4PVs27Z1n23dZ9u2bdu2bePatm3bHH99nfrWrlPdXb13195VXeN8mZ2srHAkK3NkJrXPi079rwgUgSJQBIpAESgCRWCnEShh2+nhaeOKQBEoAvuCQNtZBIrANhEoYdsmui27CBSBIlAEikARKALngEAJ2zmA2CL2A4G2sggUgSJQBIrAviJQwravI9d2F4EiUASKQBEoAtcCgWtSZwnbNYG9lRaBIlAEikARKAJFYHMEStg2x6opi0ARKAL7gUBbWQSKwIVDoITtwg1pO1QEikARKAJFoAhcNARK2C7aiO5Hf9rKIlAEikARKAJF4AwIlLCdAawmLQJFoAgUgSJQBHYJgcNpSwnb4Yx1e1oEikARKAJFoAjsKQIlbHs6cG12EdhhBF5mh9t21ZvWCncOAXpv3Rx9hbT01SLex9vYvVJSvnKkrghsFYGzTsytNqaFXxgE3j09+bLI50VeKjJ3r5KHL494f734LxI5i3vFJH6XSN3uIfDiadKXRozP68T/7MjLRb4o8taRuaPgviAR3xQxT8yFT03Y/Ii3cC+Rvx8dkear439kRDlvFZ/C/cz4Yy59QMLcB+aPuC+J/yaRL4x4XpV3S/wbRLRBPZ+W8NtHVp0+vX8iXz6yiXuxJPqEyKhP3/Q1UQtnzX3vhF4zsol76ST6/Ih2akuCp7oPSopR/6qPXOT1qU47Py6pvi4y8rzHLJzgubjXTSk/Flntm/qNvXH59Lw3rtImuHDG7GMT+uaIOfcx8c2h94z/WRH9tsZ8fMIfFREWZ06aO5+SOPMo3tIp6yPy9JJHor/vmvC8bcb3HRPnnXjttN59ReLqisBWETDZtlpBC991BLbSvtun1GdHfjZiEY23dBbeX8mTxe428V8QOYuz+P5JMlh0410V91qp5T8jvxPZtF5K+nZJ/72RuaP8/jUR/x8ZCujDE/7NmVAyeZzeLn/m8d+ZZ4oq3sK9Uf7eK/I5Ee5b80c753kotUQvHHL8hwnBD/7IkXb8duJGHmMmPlFndm+eHAj6zeNrG7zeIeHviVCW8RaOFeO2CVl/fin+n0UowT+Ij+DFm7T1uxOgjH8jvvY9KP5NIm8ReUbkHyJI3tvEv1mEu2n+vGnkjpEHRv4pov77xf+9I9E/REq6X0/cG0cQwu+KTyHHWzrE6m/yZN7GO9U9Lyn+JfLOEaTgr+M/MTKc8f/zPHxuhDOe108AFvEW7p3y980i3DPz598i0kub4KnuxknxspEPiYw+/3PCXxOBVbxT3fOTwjgaN3jlcfqj/PnkyHk6BOvbUiByHW/pPiMh8/9v4/975CcivsN4kzEyZxGzX0vE70fuE4H768WHub4j+P+V5/+OmIfa/lcJPy0irbFnVcvjwj0qf+V9TvyfjPhGvjK+9Uw6z+YhsqYt5guc/i9p7hypKwJbRWC+SGy1ohZ+UAhYxAhF/CPpOSUeb+EQmUcm5P1ZyVqyTRQwQkNhe962aO8fpxJK9v7xB9lJ8ESHaNwzKYayS3CiQJC4v88DBfP98TkWFLt6CpI8TGSEZQfhvVXC4u8Wf44ZgkaZvGriuefmz30j0j4kPjLz9PgcAqRNLFSvnwjfvrKelPAoH2lCupST6DM7pOKGR7luGd/zg+OzuGlnggtl+1MJIEHIo3lAKMo7JX44lhUWNJYRpEUaeCLASJF0fPEUrfCIe0AC+qV/+jJEGkoXAUR+4IQsPznpkSv1Ky+PS2euflie/ieyqVOGOh+fDPx4S4e8sQb97lEMxf+JCRuPeJNxYllCFD0T/UcihDeRUb+6R5+FWR3N503KkEadRJiwHP6FwDmJvprfMLYRG8UaG5ZRhNsYPjUvEDZ9SHCCF5LNqvWsaZr0FyH3beZx0ucnJPDoiPZ777swHt4lejLm/5EAi1q8SxxCxkrpe7dpYC225mgrMg0Dmy7pbB4uyXzQD+38VhEYi8RWK2nhB4vADdLz94ogAfEmu9+nCMwEUbFofkPiPjQyLCziHTVYnC2UjsVYi+yUPVO8ST6xRDgushPexuKJdNwhFSFtdt0UhDa8beIs6nzHa8KIUKKnt8wfRMAOfCgZVgEEy5EMRYF46FOSLtwt8heRQwwHuUnUhPD8XQIIDavAKM8RIGXP0kAhJcn0i9M0fW2EQkG+fjrhQaBePWFK8PviU2LxJuThk6ZpYoVBVhAD1rrVMUqSUx3LkaO+QTb1l5XnEcnJsgHDBCeWFETyH/NAGcdbOEp59E9eJFYexGuR4OgPCxvFe/S48AYmi4cT/ljvfiDv4cVygxiYM49L3PtFWKHmbUrUYs6ylhlb1lVkivJm/dGvN5ToGNGn1fKQa1Yu9drIIATmsPFixYHPF6c87wlSk8el82zOsQheP7GuCMRb66T1nUivrQg/Muso2Dibt8bM0ec48pVef5Ez5B5GCkcgkRVt8qydyjBO0sFW+33D5r4+It0jvTyrYj0wF815ecZ7pEpbvyURyL50N0rYJscRMUuzec1SluiFM6Y2czBfROSP+TzHn9U/0QsnnuUSBouI2R9EkYXWvLIxtOmBM9xgqn2Sw2ZTy6v0lSJwRQj4yK6ogGYuAicgQHkjGwiZhY6lYk5GZEVuECFWDwrh5xJJYVPqFBfrz9cnDnGxi7bQ2llbLCkD6R0DIiQICoWT5Ev37Qlpwzph5RiKKsmu47RDmx3feanueyTwwRHEktLUTnWwhiEoxLGJoxrKKEkXjmKnCL1zDOkYhVJbvMwfSohVypEe5Z2ohVOu4z5CQYukPJUPN20SNxeEEj6/nEjv9cM9IUdAlFGiL3H64lgJ4ZsrwUsSnfJAqaqTkpTUeCNAwgjq3QUiFL13q/VQuI5jWcusS6waj0167Y+3dPC/9fJps4B2/eg0TcgegiqXzQSFrI1871jwvJuLdplvxkr4enlpngkjto7bEJVEb+TUhQwh+HB4eHKJgwciQBBpRGFgmSRL5wgR0beBMOfNf+O7TDALqMOxMUs3cqhMR+jqYLkkrEj65NhYe2x+bJJgbP7CTpHCsGNV8mzzYR46cnTFwXcME/PcXBNm1TJPpV8nviPHnSytSOWwRsv7w8mA7LNIE3UkarIxcPdslch759v5X4ENxfo06pxnYfGz9iDy2oWsKZfVGg5wkl5eRF64UgS2joCFceuVtIKDRYBicJTBKuEohvKlkOeA3DUPLhU7EqEckBrWNVYHRxoWbYqRUqJQKX6Kx6L5jclLKShTPe69UH6JXjrK1XHXOnFEON+RLzMdBdShTfyjqKXn/p07QQidnTslde+8RU4pHGTDhWX31BAwfWKdoxApfwrpF5KeIlWWdtrts5ghYnk1UabuDb1vHpBW75BUljIWMW1TFhJEYWonnKT9y+QZCp/1Ar5wQoqNBVInfZJNLttrH6uF58sR9eqfMZffOBg3Y24c+eJHWHrPxJjDhZWUxUJaChk23hOWKWOIJLPseBZPKPHRF/5ri5wJJcuiaaxsAMYr4+bozPPwhecCs2HR0z+bBtYf1h7vEFVWn3me48LGSr8eepTA+MDDHFQuSw4SYX5LgyDA4ij5ZDNic6AdLHzmGBxYtZAsYi6M9Egpa6CjZRiIN0+0W14kdYQRLXOARZmF1nc32iQffMQJk+/IHxsZ80m7zHOk8y6JZxlFDLX/uA0R3YN8OtpEiswHbU32hTOPWAWRQlZhaa0jMIKZub9IOPtjXq+O/ez1dYLqOIlsm1fuySG+1hlWN3fV3H80F1m49fk6BTeiCGwDAR/NNsptmZeDwMXMQ7k5SmIdmivL0VsLMeuO+0QIz4i382bZcGSEpLCijXd8c9fldcrNs8WXAhaei0XXIr5OKAPlzNPPw0gHMoXcjHi7e9YHz5SHBZ/CGorVIo5s/mkSsKZRoj+TsIUdAUNQ8zjpr7SsJJSV4xyKGNFipWP1QlhYUty30Q5KUNn64giPYv3BFMYaQJErByYI2tyS+RpJwyF8rGiOmbSJghZvDBy5qsfzNgXp1o85puYIyx8Sy5JqLJENRG60kdWJZdIleGPuWTuNEayEh8zfjzi+eL8ENG6eL1cQrDHem5ZhniHux6U31n6oMX+P4Pl2Rhwyaj7DCGFn3XMk6dqB7wvh8UOKkX745pxjb/kdgY54/RhhPhJkPg9yJ+44YQ1lmWP5RULn6TbBV38RO8fgrHTmueN85NeYI9h8xNKPV1hIbWhsAmxiXJeY1ynM+ufYUnhT8V2uS6sdP58XNlXmp7HTL5s0R7jWJ+OA9CZZXRHYPgIWke3X0hoOEQGkw6JHsTn+c+HZ8c8cC/OPwnEUaGG2Q0Z+3GdjCXCHhZK2kFss53kp9d9KBPIhj7IoLeFELx1lTsmtE0cd8i0Trwmow9ENKxdLIJLliIZlwDGS9xZu5BKR8szKwbrGauSuFMsRywnroB8aOEb5qtSFtLGy6B+rkfyOuxzF6C8FLL067egpY4QH6VA/Re2eHGLobhbyAkPEjUUkVSycy9gsKJSOtmi/+hFECRw/ihO+XEGgYE0Rn1SGOrWfULDSIgjyaTfSbc44vmX9QUbFs1pKy2KjDM/6i2giduaa946pzI3RfyTFnDAfvWctk1f4csR8IafllQYBUr/2u89lzFbzIZHah2gbT33XL2RFHgRq5IGTo0FkFwawYl378SSAk2/Mt5bHSb1EWH+FkV3livNMhIdoi1+YDlJnPOGt/SMN3xxDnmwAtNWmw+bHXThlEumOE+9tZPzqF2EiyKd+DdKKkLFsjTJ8q2PD55jVnLV2wFka4+u7YwHzjOj6nkbb4Uu8G6J/vr/xPHxzkVUP3qxpfjjFkqpOmzVzTJ/dB7zS72bUee5+C7x4CIzJfvF61h5dSwQQLRYfViaWIFYjd4UsgO7TWOQdZ1LadrAWf78ctJBTtJSRIyHHnNK7A2UhdgxkZ+uSs3zurLi8bodOeVhAlT3vO5LIorNOHHOspp/nFXYMxIqlL0iR40aKzSLuCJYSpqz80wRIkDwEyWMZ8OMAShahkN/RpHYjmjBAzsT5MQLi+j7J7G4RxY0QUtgUFRILS5aoJFk4JE8a7UDcKCcYOsqizBeJZn/U6Z/RYHFz92l8/xSmY6ZZ0jMHkStjRsGflplVBpl1xw42cEBOHQWP8YCL4zn4GX9hbZZ23laWGXegjI93rC/ikDaKlQVHmfqNTCNHp7Vv/t4RrCM7R4BIuDmL0IhXprawNo08xtk/HeEXwcYLKTf3kCp9MtbINyJgU+LXhsaMdZG1RrvNZYThMSlU26Vh2WUlgwVS5cK8O5jr5ry85ikC6Mcs8LZZ8E2aG0i7o0ybAaTQM2uZNmmHuWhcfij1I+Lul5prxki5iJCNCNx9o3CFvbnK+iSdI36/BLbZQMZsmFLcwvmeWMxcI0DEYMaS7lv1PavLPEcAWbl8a9aIYWVHur3za1ubEZulX03J8iJqftHr7qc+mQ/ap0zj+K7F9gAABRdJREFU6C6a9if5ZD2ZW/XFEXU5RmapRoJt1NxrY91jbdM/Ywwra5o8lSKwdQTGgr31ilrBQSFAsTq6c5SJnLAKUWp2sy4ue+e4RxzSZGGkZByNugOGjFlgpZHWr0wtkBQlIiSOkrFYUlqUoEXb/ZltAM1qoS8sVPqiDspNO/xYwD8MK4yQeUdc9hZHKBckD6nRB4raoj+OIN2HYm0SLy2FpAwKGx7iETkWCfFD4KR8wkpH2SMH7oFRLiPd8BECaYl6WF68Qyau1FKAIPphByWozFNkMlYIDaVH8SMCCBvFOPLCh+L0ww5K2BgjYKwcIw2f0jYeyD3LDdzEI/+w0F8Yyo8AebepIJXGHnF0zMya5xmhGXMR+RzlmeMItDTmreNmvjaYq0iHDYdykAVtNBaIAcKiHHPdnGY5NRdGPYiUzYyNgB8uIPZwlGcuCI761Wm+sQ6PNrBYs1B5RkCRKkRGeuOAoPk1NmLqG5MX+YQt0qjdvgEbLPe7/PgA/upxRK8c9SKHo93m8PzY1HciDWyMMczUKc43rx3ms00K0ugY331T3/vop3zqd0SJPHrv+4KX9URZ+ojoG3dhce4xmmOsnzCHxyhz+Ei2tHNxfOsIWR71IYSuOIw89YvA1hEoYds6xK1gAwQQBwpfUpYlPnJhQR7/AKbjCErbu1WxkCMrq/Hn+UzRn1cd+jr6Odo4MFiN9yy99yPtab62npZm/l7Z6pnHXU4YGUGQHJltkh+eyBWScFL9lDNlbJyPK9cRsrKUeVyaXY2H/2q7jeFJmMBiNc959k/56h/+urLn81LadWkuJ05ZNjh8RI9lUni1LHHmjvcwXH1/0rMf2iDgyOdJ6VbfwWNf59lqX/q8ZwiUsB0zYI2+5gg4WnE/yeVqR4X+FzmrFqZr3sg24BIEKFfHhH7Nd8mLPhSBHULAsakjYVZSpG80jQXRkalf3o6403xH7Kyw7tOdlrbvi8AVIVDCdkXwNfMWEbCQOtaze3bMYWe7xepa9DkhYLwcjZ1TcS2mCJw7Aqx3jl1X1xQ/+HGMa73ZtFKWUMf5TgOOy9P4InAuCJSwnQuMLaQIFIEiUASKQBEoAttDoIRte9i25CKwHwi0lUWgCBSBIrDzCJSw7fwQtYFFoAgUgSJQBIrAoSOwD4Tt0Meo/S8CRaAIFIEiUAQOHIEStgOfAO1+ESgCReBwEGhPi8D+IlDCtr9j15YXgSJQBIpAESgCB4JACduBDHS7uR8ItJVFoAgUgSJQBNYhUMK2DpXGFYEiUASKQBEoAkVghxA4I2HboZa3KUWgCBSBIlAEikAROBAEStgOZKDbzSJQBIrATiHQxhSBInAmBErYzgRXExeBIlAEikARKAJF4OojUMJ29TFvjfuBQFtZBIpAESgCRWBnEChh25mhaEOKQBEoAkWgCBSBi4fA+fSohO18cGwpRaAIFIEiUASKQBHYGgIlbFuDtgUXgSJQBPYDgbayCBSB3UeghG33x6gtLAJFoAgUgSJQBA4cgRK2A58A+9H9trIIFIEiUASKwGEjUMJ22OPf3heBIlAEikAROBwE9rinJWx7PHhtehEoAkWgCBSBInAYCJSwHcY4t5dFoAjsBwJtZREoAkVgLQIlbGthaWQRKAJFoAgUgSJQBHYHgRK23RmL/WhJW1kEikARKAJFoAhcdQRK2K465K2wCBSBIlAEikARKAJnQ6CE7Wx4NXURKAJFoAgUgSJQBK46Ai8EAAD//4n17y0AAAAGSURBVAMAlBTokPnH/JEAAAAASUVORK5CYII=>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAaCAYAAABVX2cEAAABhUlEQVR4AeyTu0oDURCGo4jiXRFsBLFUtFAU0VIQEWy8lAo+hW9iZ2WpeKkE8YKlomIhFnaijYp4xSRFAsn3b3LC7pxtAumS8H8z58xsJmfnTOoTFfxUabEZWvgBuSLH+GZw6mBxAi4vf8C+FRK2ZxcEe2ELMqDio3inPxZzsAL70ALLkASvmGJdmCbYgEZYhToIa4DNIaShJHsyJfoxX7ALj7AI+jIuUAN2CB4gorhiIzyhIq/4HeiDBXDSyXXiFxdwPq7YOMlbkPYwP7AGnSANYtS7b3xEtlg32R54Bkkn1I1OspkGaRhzBZ5sMdevz+KTWfw2SOsYjckE3usXMe82Xb80P8qLS8w1zINOF9svcpFiuv4pgncQ1i+bTVDj5d9Ye/0iFimmhzXhT0oYTtmrfxqJe9axCvdsjCfaIQVW7wQ0Jpo/e3JSBanYLMt/OIcl0CuE54pQII3JDSu9Js6Xip0RbgP1TOivdMTeSjeoS9CP2VywV7FgUQlTK1Z+F6ukZ3kAAAD//11EDSIAAAAGSURBVAMAn3lDNYWGEaYAAAAASUVORK5CYII=>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAAAXCAYAAACoNQllAAAFzUlEQVR4AeyYB4heRRDH36kRNYq9t9i7nhUbATVYsXdFbNgLolEEG4oNUcSSHkJ6CElIQhJID4GQThoJ6b33Xkj//T7Y430v77275O5LcpBj/m9mdufbMjs7u3tHRUf+cj1wxEG57omiUjjoaPo8FZSB2khF489z0OnMrhxIdfjcBp4C9UDW5LX7ifr7wB4gaWtbJ6rUAuxmjG+Bz0BZmoP04KdUDgLKH8PXgzGgO5gLGgOdASsif3c8JdrBoo/42OEquDLsoNAJ9NIR7AIulGN4GDlOT6KEem22ozcAyv/CbwbPJB1Ul8LW4HZwP3gZGDUXwLW1k3XI74EHQJyuQ3kJ/AfsBBY14nMlWAkOJm2hs1fAHWAZkF7ncwwI1BPhFNAXOJdj4QOBtIPPH6Chk4YXyIj4G+lcYNS8AHfC78PXACfdD/4PcNs8Bw+k/gHKKDAPxGkTylZwKOhqOnW8o+EurjpiBRlpG9DGgyRNo2Be3EFvU/Ao0CGnwb8FLcEsECe9vJMCHXkcXDqPz4OgB9CRsMOCbmUUA0B7YLTEF5Wi6Ao+K8BakCTn2Ds46EJqvwAdwGxwJzAHGVGIRWQ0uF/lNmLlNXzMV3odscpkv4b+5/zCrWgkIhbRyWg6/3G4yd6F+Q75HWDUw1LJk1T7+dT2AYvBi+BsEMi0MDIoKXxycJCR4+nUCyMjoBPcgZucEVNpCaXBQa7UQnTzE6xScmJGaBssJwD7/RHeCpgHYQV6jO8UcAPQMW7hbshui2/gZ4AsuogKU8NquNve6HaLecJSFJmPPJknq2RghQ5y1epjsBzYECyXLqbWvTscHuhaBE+qbfCqkNvZrfwuxhPBTGDec0V/QXZMrvSfyDrxL3hzoAMvg7ttdNpS5Cy6ngoj2gUX7g4j/w3KPWndcibmBehZtFEHuWLnY+GRJxAzyYF7utnxkITVZvQQUYiZ5Kp/Qq2OWQQP5EpPRXEbXAL35DQKjBbUAjm+s5BcpI3wPDKqx8YMjFTHbAR5vzOabDst/1T8TAcFRW/q2aCncVfPY9/kbcSl2VRW5mKYe7Ii7hwauAq4Zb1zOREXhqLIPGcucYHUsxDPP8HGnOkVxnm+SqERlpd/MIkKTw3Dz5U3pE2UhYqUj3njK8odnA5CPCAyzL1nGLnmgWQjjsXo8HRpQaUL8jP8e/Ah8A6m4xAz6VJqjGijErGC3JpeeHXQm5SOA7lkBNnQMKzKQEPgqQErIlfOuvIoitzDyeTtVjEynHRUyZ/J3ZzjgsQjVmf5e68V1vs0uYW2zDXeZXTW5eieSLBcMurcwi5+3FCHtaXA/OPcwyWSolSqo5E13hNMeN4obcAcYLlOc1CdUW4CXrZ0BmIRmeg8ZeITLjKIKTr3V3RDvBweyFPU64XOcPs6Ods0aj1E7sHQ/t3mLhhqKjkGrwRu0TQDHew2HUFlbv6hvm5wkKvms8I70BNUzAEO0DeMR3A7dMPSYxNxHzIZurfPTNR4UhkNJtvfqXNQJlnbfBbdZ0kXuCeVV37vYs3QJZ8LTsbTTRvhG8+xGh0mau0CjD5t/J2J3t/aj5EYbOSe1B75XhnU81AvOEijoXy88PkOex75IeCJY5nvFk8QilLJQRu+bom4QVMUB2gkirvQzS06fzCyD0Kd+CWyidlItQ41Mgp8VZsX/a1wvEayss7ULsBU4bitC7ANnzrBRm77Ot1jXz0PDewwbmDyNBq6UtgfOGlYpeS2+R8ro8wQR6wSOVj70GnJBTCSPZp1fmhM+0koTs67l1GDWhLyFl4/6aDq9GTYuiXvrU4jsd96MTT3PE1ZyDlGhvcwD4omlBs1sJLQI7Q6oyYdZCj7Px/DN5kf6Gu/yRf43fxKh3sc++I297xGmVvHJwdiSciDyd3wW006yJH6MPwawdxh0kasFnmymmvMO+arG2nN+8t0eKnoJBq2Dx/D82vaQbQd+Vz4AcELIazWkZdUH8KF68xeAAAA//9JweihAAAABklEQVQDAGWlJj5nlm1bAAAAAElFTkSuQmCC>

[image5]: <data:image/png;base64,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>

[image6]: <data:image/png;base64,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>

[image7]: <data:image/png;base64,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>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAbCAYAAACqenW9AAABT0lEQVR4AeySuy5FQRSGD0FcEhEhLo1CFG5REAqtREMlQiGeAS+hVvAEKi0VJSLunUI0RBRE4ZYIgu+bk7MzMg2N6pysb681a/37zJo1uzT3h9//iUvoqg5qIbG4jQWqp7AHE5BYLF6jugodcAOJxeJrqm5/h7+AxGJxFdV+OIdbSCwWN1HthgN4AQ/biu+DCsjF4k4SzXAICj3kOPEMjMIP8QCJZ7CNMfwHNMIkeOhMXE1iEO5hCL5gB2zpGL8LmbiBRRfUwDT48hP+CBbhBDJxGwsPuI7fBreewj+CL7zjM7EjeyOxAktQD7NQCe3QA0FcTmC/XoQXY99X5JyUjBC3QBB7a45tn8QDaJc8ymAYHKffTBA7U/vaoPAJmvEZQS/4YblbEBvMk9yCgjmyORbLsAmOMogNvIzCv1IL9srTa8flzQPko188i+J4SN8AAAD//1NNVc0AAAAGSURBVAMAexE8N9z2WUQAAAAASUVORK5CYII=>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADEAAAAaCAYAAAAe97TpAAACjklEQVR4AeyWW4hNURjHXYtcIhKFB0kuJeTuhSKFeKEoEVKUFA+UJ6+UlGsePHiQklviRSkpkZAXKSn3RMTcZ2puv9+e2WfWnjNzzn6Zfc5MZ/r/9rfX+r4za33ruocMGgB/lSTKZRK7z8RgOjYBxkG/UZjEKXrdBH9gL5Ra2+jAShgNDu4k7E5YAAmFSRzHsx2a4SWUUsNo3CSeYWugFX7BFvgECYVJ6FjN4wfkBVKXpRzIahp8B9/gNmwCB7kKm1CYxBg8C8Ef/sWWWg10YDdMh63wEFogT2ESU/HOhafQCK7DWdh1MBLKVmESi+jleHgNw+Ek7IdDcBCyloPoRn5Dw9/hObhSMEmFSSzD9RXcDyewd+EnbIZCmonzFfjbtOwgvphGEfAbloCr5CL2MSyFhOIknIEVeGrhGNyEt/AAjsIV6E0fcSwG125abhBfTIcJOA3xPnjCez0cAU8vTIfiJCZTnAF2Yj3WU2As9gOchTrIWh6tcQK27bs4E17I1kXEScyhZKc3YNeC030NOwKKaSgBXkRTsGnxAiO8V+3B491wANtdzkLc78gXF8L7weXhJnIdeiptJNKjDtOjTNR1uwpvWqYRW0gOihs7jHGwxD3rLOV8JuGozKfGzemtyGukLzw9atdgPXYxPcql5hl+C29a3hNbSLbnRr4aBDlAEymfB/cupkMm4fryPnDjeFPquc9jOVyHz51gMtMLWnLEH2H3wTm4BB4yd7AJmYTH4jxqL0Msr/nZFPwQvIBtgyxle2docBf49eAp6cFjIvqo7pJJWPmPKnc+Jien7H+uVJoXv5vu0bQzkvfNRH0kk4he+vOjnJNIPa6VJFIPVR8HVmaijwc49b8fEDPRDgAA///lSu51AAAABklEQVQDAN+ZhDUzy9iyAAAAAElFTkSuQmCC>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADEAAAAaCAYAAAAe97TpAAACnklEQVR4AeyWWahNYRTHjzFkTBkyRTKniJAXylCEogzJkJKUB3mglPLigRclEi+SpAwpQ56UqUiUBxIpQxkzhiLE7+eefe53zj53330eznBv5/T/7bXPt76991rfsPZum2kFv3oStTKJhTPRhsB6Q09oMQqT2E3UP+E9rINa0EiC2AOHYQm0g5jCJLbhXQ6/4TZUU66ItQRwPssu7GI4Ap0hT2ESOmZweAlPoZqayMMPwD64Ds9hB8yCRZCnMIlueCbAA/gA1dQaHt4FDB7zX+84PoZV0AlyCpMYSOsYuAY/wCkdgZ0NsSmkrZzqkXDzcfh6QU5hEk6hzrt4O8BOWA+bYCPUioyxTxhMmMQUHC/A/bAdexZew0JI0nCcd8Br07KC/km6lHU6mNnTjIFbraxQ7aNGbZSE2U2j4RtshZNwDy7AFjgETekJjkkwuARO0DdJJnGZDgvARFzaSznvCzFFSfTDMwwMZC7WUtsd60bai/0OldQXHmbQHbHP4BHYdgPre+wVNqcoidG0GPQ8rGXM6T7KeV4V4H8xOb1OdX+caelK3+b0kQ4rYQBYYE5h/Zq4j/0EOUVJhO8Hl8dNelitrErzObfkYYrKRCfjmV4Cg+ibJJ99lQ6bwaWEyQzh4HXHsFZPTINMwlEZz18351tsJGu0nWfSYNnFFJVL7SKe0yXwkL5Jcu27zyw2zrT7YgMX3AL3KaZRJuEUOV1XaPaTA5M5x2EqHAfXpHBaMbkHHLivPHEZOEhDsavB4oNplElYFsfSdBAineFkFPghuB/7FyopA7W0++HnR6nvqjkE8AZiMgkDdKP8KfB6o88FbZX8+4uHucRdplZJ46QpLpOIt7awllpOIvVQ1pNIPVRl7lifiTIPcOrbt4qZ+AcAAP//O+q7ugAAAAZJREFUAwC2438128u1ywAAAAB