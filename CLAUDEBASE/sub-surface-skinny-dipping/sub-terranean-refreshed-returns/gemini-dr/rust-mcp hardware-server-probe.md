## (`Architectural-Blueprint`/`And-Implementation-Strategy`/`For-The`/`Chthonic-Hardware-MCP-Server`)

### (`Subprocess-Execution`/`Versus`/`Native`/`Rust`/`WMI-Architecture`)

- *— The foundational decision for establishing a hardware telemetry layer within the —* `chthonic-archive` *— environment dictates the reliability, performance, and memory safety of the entire Model Context Protocol (MCP) server. The architectural dichotomy lies between utilizing —* `std::process::Command` *— to invoke PowerShell scripts versus leveraging native Rust Windows Management Instrumentation (WMI) bindings through the —* `wmi` *— crate.*

  - *— Shelling out to PowerShell introduces immense operational friction. When a Rust binary invokes pwsh.exe, the operating system must allocate a new process, load the .NET Common Language Runtime (CLR), initialize the PowerShell host environment, parse the script, execute the pipeline, serialize the output to JSON, and pipe it back to the Rust standard output stream. This procedural overhead reliably consumes between 300 and 1,500 milliseconds per invocation, establishing an unacceptable baseline latency for a local hardware query. Furthermore, subprocess execution is inherently fragile. Execution policies, environment variable pollution, and silent pipeline breaks result in non-zero exit codes or corrupted JSON payloads. The Rust server is subsequently forced into complex, defensive parsing logic to differentiate between the genuine absence of a hardware component and a scripting runtime fault. This fragility is frequently weaponized or disrupted by endpoint detection systems monitoring — `pwsh.exe` — spawning, further complicating the reliability matrix*

    - *Conversely, native WMI access via the —* `wmi` *— crate (version 0.13+) operates directly over the Windows Component Object Model (COM) API. This architecture establishes a direct connection to the WMI repository, executing WMI Query Language (WQL) queries and deserializing the resulting COM —* `VARIANT` *— objects directly into strongly typed Rust structs utilizing the —* `serde` *— framework. This paradigm eliminates intermediary process allocation and text-based serialization, yielding execution times consistently under 10 milliseconds. Because the —* `wmi` *— crate utilizes —* `serde` *— the underlying WQL query is automatically inferred from the struct's definition, providing compile-time guarantees regarding the expected data shape.*

      - *— The —* `wmi` *— crate provides exhaustive coverage for the core system components required by the chthonic-archive environment.*

**(`WMI-Hardware-Class`)** | **(`Extracted-Telemetry-Attributes`)** | **(`Reliability-Assessment`)**
---|---|---|
`Win32_Processor` | *Core counts, logical thread counts, architecture, current clock speed.* | *Highly reliable; direct mapping to hardware reporting.* |
`Win32_PhysicalMemory` | *Total capacity, per-slot populated status, module speed, manufacturer.* | *Highly reliable; accurate reflection of DIMM population.* | 
`Win32_DiskDrive` | *NVMe physical device enumeration, interface type, raw capacities.* | *Reliable; bypasses logical volume abstractions.* | 
`Win32_VideoController` | *Base logical display adapters, driver dates, current resolutions.* | *Moderate; sufficient for baseline identification, but lacks proprietary vendor telemetry.* |

- *— On a Windows 11 host operating with Rust 1.96.0 targeting the —* `x86_64-pc-windows-msvc` *— triplet, the —* `wmi` *— crate compiles seamlessly without necessitating additional system prerequisites or external C++ build tools. This seamless compilation is achieved because recent versions of the —* `wmi` *— crate rely directly on Microsoft's —* `windows-rs` *— and —* `windows-core` *— crates. These dependencies pull pre-generated Windows metadata bindings directly from the package registry, negating the need for local Windows SDK header resolution or complex linker configurations. The build artifact remains a strictly self-contained Rust binary.*

  - *— **(`Recommendation`)** — Implement native Rust WMI data collection leveraging the —* `wmi`*.*

    - *— **(`Tradeoff-Ruled-Out`)** — Utilizing —* `std::process::Command` *— to invoke PowerShell subprocesses is explicitly ruled out due to the unacceptable latency penalty (exceeding 1,000 milliseconds per call) and the inherent fragility of parsing shell output streams, which critically undermines the sub-5ms performance profile of the —* `rmcp` *— server architecture.*

---

### (`WMI-Coverage-Gaps`/`And-The`/`Native`/`Rust`/`Abstraction-Boundary`)

- *— While WMI provides exceptional baseline topology mapping, it possesses fundamental blind spots regarding third-party software stacks and proprietary hardware driver layers. WMI is intrinsically incapable of directly interrogating the internal states of the NVIDIA compute stack. It cannot extract the installed CUDA User Mode Driver (UMD) version, resolve the active —* `nvcc` *— compiler paths nested within —* `CUDA_PATH` *— environment variables, read the Vulkan SDK installation directory, or extract the semantic —* `VersionInfo` *— metadata compiled into proprietary System32 DLLs such as —* `nvapi64.dll` *— or —* `nvcuda.dll`*.*

  - *— These limitations definitively force a hybrid architecture, demanding divergent data collection paths depending on the target metric. However, compensating for WMI's blind spots by falling back to PowerShell subprocesses to read file versions or environment variables would immediately reintroduce the latency and fragility issues previously mitigated. To preserve the performance guarantees and type safety of the Rust runtime, the hybrid architecture must be implemented entirely within native code.*

    - *— The —* `windows-rs` *— crate exposes the underlying Win32 APIs necessary to bridge these gaps without leaving the Rust execution context. By binding to functions such as —* `GetFileVersionInfoSizeW` *—* `GetFileVersionInfoW` *— and —* `VerQueryValueW` *— the Rust server can extract the —* `—VS_FIXEDFILEINFO` *— block directly from the binary headers of proprietary NVIDIA DLLs. This mechanism securely reads the exact file version metadata embedded by the compiler without relying on brittle file hash comparisons or external shell utilities. Concurrently, native Rust standard library functions such as —* `std::env::var` *— can aggressively parse the system environment to analyze toolkit slots across multiple installed —* `CUDA_PATH_V*` *— directories, verifying the existence of `nvcc.exe` *— and —* `cudart` *— libraries via pure native filesystem I/O operations.*

      - *— To prevent architectural degradation and maintain a clean separation of concerns, the boundary between these divergent collection paths must abstract the intent of the query away from its mechanical execution. This is achieved by designing a trait-based facade within the Rust application. A central orchestrator, designated as the —* `SystemProbe` *— holds implementations of a —* `HardwareProvider` *— trait. The —* `WmiProvider` *— encapsulates the COM apartment initialization and query logic for the —* `wmi` *— crate, while the —* `Win32Provider` *— handles the direct memory operations required to extract DLL metadata via the —* `windows-rs` *— crate. When the MCP server receives a request, the —* `SystemProbe` *— delegates the operation concurrently across these providers using the —* `tokio` *— asynchronous runtime, subsequently merging the results into a unified internal representation.*

        - *— **(`Recommendation`)** —  Implement a purely Rust-native hybrid architecture, utilizing the —* `wmi` *— crate for physical hardware enumeration and the —* `windows-rs` *— crate to directly invoke Win32 APIs for DLL version extraction and environment variable resolution.Tradeoff Ruled Out: Supplementing WMI coverage gaps with PowerShell or external scripting subprocesses is strictly ruled out to maintain continuous native execution performance and guarantee type-safe error propagation across the entire telemetry boundary.*

---

### (`Dynamic-GPU-State`/`And-Native`/`NVML-Integration`)

- *—The static hardware probe provides an exhaustive inventory of installed components and driver layers, but it leaves a critical operational void for an AI agent tasked with real-time architectural decision-making. When a Claude Code session is analyzing a Vulkan compute shader or diagnosing a CUDA Out-Of-Memory exception, historical inventory data is insufficient. The agent requires immediate access to dynamic telemetry: active VRAM allocation, streaming multiprocessor utilization percentages, thermal diode readings, and real-time power draw metrics.*

  - *— Acquiring this dynamic state via the —* `nvidia-smi.exe` *— command-line utility incurs a devastating performance penalty, routinely exceeding 200 milliseconds, while forcing the application to parse unstructured text or cumbersome XML payloads. The optimal, zero-latency pathway to this data is the NVIDIA Management Library (NVML), a C-based programmatic interface designed specifically for continuous monitoring.*

    - *— Within the Rust ecosystem, this library is exposed via the —* `nvml-wrapper` *— crate (version 0.12.1), which provides safe, ergonomic bindings over the raw FFI calls. The Windows support status of —* `nvml-wrapper` *— on Rust 1.96.0 is robust and perfectly aligned with the project's requirements. The crate utilizes the —* `libloading` *— mechanism to dynamically load the —* `nvml.dll` *— library from the system path at runtime. This dynamic loading architecture ensures that the MCP server compiles cleanly on any development machine without requiring proprietary NVIDIA header files or a local CUDA Toolkit installation during the build phase.*

      - *— Upon execution, the —* `Nvml::init()` *— function searches for —* `nvml.dll` *— which is universally present within the System32 directory of any modern GeForce or NVIDIA Studio driver installation. Once initialized, the library securely binds the necessary function pointers. Subsequent calls to retrieve metrics, such as invoking —* `device.memory_info()` *— or —* `device.utilization_rates()` *— execute in less than one millisecond, delivering instantaneous telemetry directly into the agent's context.*
      
        - *— Because dynamic state metrics decay immediately, attaching them to a static hardware inventory probe governed by a caching lifecycle is fundamentally incompatible. A discrete, specialized MCP tool must be engineered to handle real-time streaming constraints.*

**(`Dynamic-GPU-Telemetry-Field`)** | **(`NVML-Retrieval-Mechanism`)** | **(`Relevance-To-Compute-Architecture-Decisions`)**
---|---|---|
**(`VRAM-Utilization`)** | `device.memory_info()` | *Dictates if the agent should allocate cooperative matrices or fall back to standard shared memory architectures due to memory pressure.* |
**(`Streaming-Multiprocessor-Load`)** | `device.utilization_rates()` | *Identifies computational bottlenecks, directing the agent to optimize thread block dimensions or unroll loops.* |
**(`Thermal-State`)** | `device.temperature()` | *Highlights thermal throttling events that skew benchmark profiling, prompting the agent to delay workload execution.* |
**(`Power-Draw`)** | `device.power_usage()` | *Allows the agent to correlate power spikes with specific kernel dispatches during Vulkan debugging.* |

- *— **(`Recommendation`)** — Integrate the —* `nvml-wrapper` *— crate to dynamically load —* `nvml.dll` *— at runtime, exposing a dedicated —* `chthonic_gpu_telemetry` *— MCP tool exclusively for real-time dynamic state without any caching layer.*

  - *— **(`Tradeoff-Ruled-Out:`)** — Merging dynamic GPU telemetry into the static hardware inventory probe is ruled out due to fundamentally opposing cache lifecycle requirements. Furthermore, executing —* `nvidia-smi` *— as a subprocess is ruled out to eliminate unacceptable parsing overhead and latency penalties.*

---

### (`Tool-Schema-Design`/`And`/`Caching-Semantics`)

- *— The schema design for the Model Context Protocol tools profoundly impacts the performance and reasoning capabilities of the connecting Language Model. Exposing a fragmented landscape of highly granular tools causes severe context bloat, consuming excessive tokens within the system prompt where the available tool definitions are constantly maintained. Furthermore, when faced with an abundance of similar options, large language models frequently confuse tool targets, hallucinate non-existent tool names, or fail to accurately supply the requisite parameters.*

  - *— To optimize the interaction paradigm, the hardware inspection capabilities must be consolidated into a single, highly parameterized tool. This approach aligns with established MCP engineering patterns, which emphasize collapsing related operational endpoints into a unified schema equipped with discriminators, rather than multiplying the tool count. The resulting tool, designated as —* `chthonic_hw_inspect` *— encapsulates the entirety of the static hardware state.*

    - *— The schema for this tool will accept a —* `scope` *— enum, allowing the model to target the —* `nvidia_stack` *— (driver versions, CUDA variables, DLL metadata), the —* `system_snapshot` *— (CPU, RAM, Motherboard, NVMe details), or a —* `full_inventory`. *— Critically, it will also expose a —* `mode` *— parameter, defaulting to —* `cached` *— but allowing the model to explicitly request a —* `live` *— query. This design preserves the model's agency. If the agent is actively assisting the user in updating the Vulkan SDK or installing a new CUDA toolkit layer, it can proactively trigger a —* `live` *— execution to immediately verify the success of the installation, overriding any internal caching mechanisms.*

      - *— The caching strategy for static hardware components requires a nuanced approach. The validity of physical hardware states (RAM capacity, NVMe enumeration) or core driver configurations does not decay on a scale of minutes or hours, but rather correlates with explicit system events or physical modifications. Establishing a strictly real-time polling mechanism for static data generates unnecessary I/O contention and wastes CPU cycles. Therefore, a time-to-live (TTL) staleness threshold of 24 hours provides the optimal balance. When invoked under the default -* `cached` *— mode, the server reads the previously serialized —* `.chthonic/cache/nvidia_stack.json`. *— If the file modification timestamp exceeds 24 hours, the server automatically promotes the request to a —* `live` *— execution, updating the local cache before returning the payload to the language model.*

        - *— The tool returns a deeply nested, strongly typed JSON object. The formatting of this return payload must maximize semantic density, eliminating verbose keys and redundant arrays to minimize token waste during the model's processing phase.*

          - *—* **(`Recommendation`)** *— Consolidate all static hardware probes into a single —* `chthonic_hw_inspect` *— MCP tool overned by a 24-hour cache staleness threshold, exposing —* `scope` *— and —* `mode` *— parameters to preserve LLM agency over data freshness.*-

            - *—* **(`Tradeoff-Ruled-Out`)** *— Exposing separate, granular tools for distinct hardware subsystems is explicitly ruled out to prevent system prompt context bloat and mitigate the risk of the LLM confusing tool selection logic.*

---

### (`Hardware-Drift`/`Detection-Data-Model`)

- *— The computational frontier landscape is defined by the strict alignment of installed software versions against documented architectural expectations. The —* `hw_drift_check` *— MCP tool serves as an automated reconciliation engine, comparing the live telemetry captured by the probe against the expected state documented within —* `docs/reference/COMPUTE_FRONTIER_LANDSCAPE.md` *— and —* `docs/reference/NVIDIA_DLL_INVENTORY.md`. *— This requires the Rust server to parse external Markdown structures, extracting expected versions using robust table-parsing algorithms.*

  - *— However, the data model governing this drift analysis cannot rely on simple string equivalence. Legitimate, operationally safe variations exist across a workstation environment. For example, the —* `nvngx_dlss.dll` *— version will legitimately fluctuate depending on the specific application directory it resides in, as games bundle independent libraries, whereas the core —* `nvapi64.dll` *— residing within the System32 directory demands strict, zero-tolerance alignment with the master driver package.*

      - *— To address this complexity, the MCP server will output a structured —* `HardwareDriftReport` *— schema. This schema explicitly categorizes discrepancies by introducing severity flags and a boolean indicator identifying legitimate variations.*

**(`Schema-Property`)**	| **(`Data-Type`)** | **(`Operational-Purpose`)**
---|---|---|
`component` | *String* | I*dentifies the specific hardware or software layer (e.g., —* `CUDA_RUNTIME_DLL`)*.* |
`expected_version` | *String* | *The baseline version parsed from the Markdown reference documents.* |
`actual_version` | *String* | *The live telemetry version extracted from the Win32 API or WMI query.* |
`severity` | *Enum* | *Categorizes the drift as —* `INFO` *—* `WARNING` *— or —* `CRITICAL`*.* |
`is_legitimate_variation` | *Boolean* | *Flags the drift as an acceptable deviation from the baseline.* |
`rationale` | *String* | *Provides contextual justification for the agent to understand why the variation is accepted.* |

- *— The Rust implementation will evaluate discrepancies through a multi-tiered ruleset.*

  - *— First, the evaluator applies semantic versioning floors. If the documented CUDA runtime expects —* `12.8.0` *— but the Win32 probe discovers —* `12.8.1` *— embedded in the DLL, the evaluator classifies this discrepancy as an —* `INFO` *— severity with —* `is_legitimate_variation: true` *— supplying the rationale that patch-level increments maintain backward compatibility and do not constitute architectural drift.*

    - *— Second, the evaluator implements path-scoped whitelisting. When inspecting the Deep Learning Super Sampling (DLSS) libraries, the logic cross-references the file path. If the path matches a recognized application directory pattern (such as a Steam library subfolder) and the version diverges from the frontier baseline, the variation is flagged as legitimate, with the rationale noting that application-bundled binaries operate independently of the system-wide baseline.*

      - *— Conversely, core system binaries invoke strict enforcement. Any divergence detected within System32 DLLs results in a —* `CRITICAL` *— severity rating with —* `is_legitimate_variation: false` *— immediately signaling to the language model that the host architecture has been compromised or incorrectly modified.*

        - *—* **(`Recommendation`)** *— Design the —* `hw_drift_check tool` *— to output a structured —* `HardwareDriftReport` *— schema that utilizes path-scoped whitelisting and semantic version flooring to explicitly categorize discrepancies and identify legitimate environmental variations.Tradeoff Ruled Out: Implementing strict binary equivalence or simple string-matching for drift detection is ruled out, as it would generate continuous false positives for patch-level updates and application-specific binaries, inevitably causing alert fatigue and leading the AI agent to ignore the drift reports.*

---

### (`Server-Topology`/`Consolidation`/`Versus`/`Independent-Registration`)

- *— The architectural disposition of the new hardware probing tools must adhere to the established repository pattern while optimizing for performance and operational stability. The existing —* `chthonic-mcp-server` *— effectively manages a suite of tools dedicated to parsing and resolving Vulkan specifications. The decision to consolidate the hardware tools into this existing binary or deploy them as a separate, independently registered MCP server hinges on failure isolation and lifecycle management.*

  - *— The user's environment explicitly enforces a pattern of "modular siblings sharing a v9-baseline skeleton, never strangler-fig replacement." Adhering strictly to this paradigm strongly favors the creation of an independent server.*

    - *— The paramount argument for separation is failure isolation. The existing Vulkan specification tools are primarily I/O-bound, executing text processing and documentation retrieval logic. In contrast, the hardware probing architecture relies heavily on Foreign Function Interface (FFI) interactions with proprietary NVIDIA libraries and the initialization of Component Object Model (COM) single-threaded or multi-threaded apartments for WMI queries. Hardware-level FFI bindings and COM initializations are inherently volatile. If a COM thread encounters a deadlock during an unexpected WMI namespace timeout, or if an NVML invocation panics due to a lower-level driver fault during dynamic telemetry collection, a consolidated server process would crash entirely. This crash would instantaneously terminate the agent's access to the Vulkan specification tools, cascading a hardware-layer fault into a documentation-layer outage. Segregating the hardware functionality into an independent —* `chthonic-hw-mcp-server` *— ensures that catastrophic hardware probe failures remain tightly isolated.*

      - *— The performance penalty for deploying an additional MCP server is mathematically negligible. The rmcp 1.7 SDK in Rust is highly optimized, demonstrating cold start times of less than 5 milliseconds and maintaining an idle memory footprint between 5 and 15 megabytes. The overhead of spawning an additional standard input/output transport pipe and negotiating a secondary JSON-RPC 2.0 handshake during the Claude Code initialization phase is imperceptible.*

        - *—  Furthermore, maintaining separate servers prevents tool namespace pollution. Consolidation forces the language model to process a significantly larger initial payload of tool definitions during the initialization handshake, which perpetually consumes tokens in the system context. Independent registration within the —* `.mcp.json` *— file allows the developer to granularly control which capabilities are loaded into the context window for any given task session, optimizing the model's available reasoning space. Finally, during active development, modifying the FFI bindings or WMI query structures requires recompiling and restarting the hardware server. An independent topology ensures that these frequent restarts do not disrupt active sessions that may be exclusively utilizing the Vulkan specification capabilities.*

          - *—* **(`Recommendation`)** *— Create a completely separate, independent MCP server registered as —* `chthonic-hw-mcp-server` *—  within the —* `.mcp.json` *— configuration to maintain strict operational boundaries.*

            - *—* **(`Tradeoff-Ruled-Out`)** *— Consolidating the hardware probe tools into the existing chthonic-mcp-server is explicitly ruled out. The marginal convenience of managing a single executable is vastly outweighed by the unacceptable risk of FFI or COM panics crashing the documentation tools, alongside the violation of the repository's established modular sibling architecture.*

---

### (`Session-Warm-Start`/`Context Injection`)

- *— For an agent to execute complex architectural reasoning effectively, it must possess an immediate, foundational awareness of the host environment from the inception of the session. Relying on the language model to independently deduce the necessity of querying its hardware state forces the user into repetitive manual prompting, degrading the fluidity of the interaction. The environment requires a deterministic mechanism to automatically inject the live hardware state into the Claude Code session at startup.*

  - *— The Model Context Protocol specification supports exposing data through both active tools and passive resources. While registering the —* `nvidia_stack.json` *— cache file as an MCP resource is technically feasible; —* **(`Claudine-Code`)** *— does not automatically ingest resources at session initialization without explicit direction. Similarly, deploying a —* `session_context` *— tool relies entirely on the language model making a proactive, autonomous decision to invoke it during the opening conversational turns. This autonomy introduces unacceptable non-determinism; the model may bypass the tool entirely and proceed to generate code based on hallucinatory assumptions regarding the installed CUDA or Vulkan layers.*

    - *— The most robust and deterministic mechanism compatible with the Claude Code architecture is the utilization of a —* `SessionStart` *—  hook. —  **(`Claudine's`)** —  internal lifecycle management, governed by the —* `.claude/settings.json` *— configuration file, provides explicit support for event hooks that trigger at highly specific execution boundaries. The —* `SessionStart` *— event fires deterministically when a new session initializes or an existing session resumes, pausing the interaction until the hook completes.*

      - *—  To maximize efficiency and minimize the consumption of valuable context tokens, the hook should not blindly dump the entire JSON cache payload. Instead, the configuration should leverage a lightweight command to extract and compress the most critical architectural parameters.*

        - *— The implementation within —* `.claude/settings.json` *— dictates the following structure:*

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "powershell.exe -NoProfile -Command \"cat .chthonic/cache/nvidia_stack.json | ConvertFrom-Json | Select-Object DriverVersion, CudaUmdMax, VulkanSdkPath | ConvertTo-Json -Compress\""
          }
        ]
      }
    ]
  }
}
```

- *— This execution pipeline parses the serialized cache, extracts the paramount values (the active NVIDIA driver, the maximum supported CUDA User Mode Driver, and the exact Vulkan SDK path), and prints a compressed JSON string. This ultra-dense payload is permanently anchored within the model's context window from turn zero. The agent instantly comprehends the boundaries of the host machine, enabling it to accurately tailor build scripts or select appropriate Vulkan extensions without wasting tokens or conversational turns, while the deep-dive MCP tools remain available for subsequent, highly detailed architectural queries.*

  - *— **(`Recommendation`)** — Leverage Claude Code's —* `SessionStart` *— hook within —* `.claude/settings.json` *— to execute a command that injects a highly compressed, token-efficient summary of the JSON cache directly into the session context window.*

    - *— **(`Tradeoff-Ruled-Out`)** — Exposing the hardware state via a passive MCP resource or relying on a —* `proactive session_context` *— tool is strictly ruled out due to the non-deterministic nature of LLM tool invocation, which fails to guarantee that the agent will acquire the necessary environmental context prior to its initial reasoning steps. This is for informational purposes only. For medical advice or diagnosis, consult a professional.*

---

#### (`Sources`)

| *Used* |
|----|
| [text](https://rustify.rs/articles/rust-for-mcp-model-context-protocol-servers-2026) | 
| [text](https://claudefa.st/blog/tools/hooks/session-lifecycle-hooks) |
| [text](https://0xdbgman.github.io/posts/persistence-the-art-of-staying-in/) |
| [text](https://medium.com/@rhishav.kanjilal14/the-catgirl-pivot-how-akira-affiliates-are-weaponizing-commodity-rat-infrastructure-in-2026-85c2f54eb72a) |
| [text](https://docs.rs/wmi) |
| [text](https://docs.rs/query-wmi) |
| [text](https://crates.io/crates/wmi) |
| [text](https://lib.rs/crates/xwin) |
| [text](https://crates.io/crates/wmi/dependencies) |
| [text](https://medium.com/@SecSamDev/rustylib-wars-winapi-vs-windows-rs-9b503049460) |
| [text](https://issues.chromium.org/issues/342194487) |
| [text](https://powershell.one/wmi/root/cimv2) |
| [text](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/computer-system-hardware-classes) |
| [text](https://medium.com/@thidaskaveesha/touch-your-hardware-1fff5a7b1fb4) |
| [text](https://crates.io/crates/silicon-monitor) |
| [text](https://github.com/AsafSaar/dofek) |
| [text](https://github.com/oko/nvml-exporter-rs) |
| [text](https://crates.io/crates/nvml-wrapper) |
| [text](https://docs.rs/nvml-wrapper/latest/nvml_wrapper/struct.Nvml.html) |
| [text](https://docs.rs/nvml-wrapper-sys) |
| [text](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code) |
| [text](https://lib.rs/crates/unistructgen-markdown-parser) |
| [text](https://lib.rs/crates/markdown-tool) |
| [text](https://crates.io/crates/markdown-tables) |
| [text](https://github.com/ohadravid/wmi-rs/issues/39) |
| [text](https://systemprompt.io/guides/build-mcp-server-rust) |
| [text](https://code.claude.com/docs/en/mcp) |
| [text](https://crates.io/crates/rmcp) |
| [text](https://github.com/modelcontextprotocol/rust-sdk) |
| [text](https://www.mindstudio.ai/blog/session-start-hooks-claude-code-force-context) |
| [text](https://code.claude.com/docs/en/hooks) |
| [text](https://code.claude.com/docs/en/hooks-guide) |
| [text](https://claudefa.st/blog/tools/hooks/session-lifecycle-hooks) |
| [text](https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/) |
| [text](https://ohadravid.github.io/projects/) |
| [text](https://www.reddit.com/r/rust/comments/al0qxb/wmirs_windows_wmi_bindings_crate/) |
| [text](https://www.rpmfind.net/linux/rpm2html/search.php?query=bundled(rust-crate%3Anvml-wrapper)) |
| [text](https://lib.rs/crates/nvml) |
| [text](https://lib.rs/crates/nvml-sys) |
| [text](https://lib.rs/crates/rust-mcp-core) |
| [text](https://docs.rs/agenterra-rmcp) |
| [text](https://crates.io/crates/rust-mcp-core) |
| [text](https://lemonade-server.ai/dev/getting-started.html) |
| [text](https://stackoverflow.com/questions/64944350/what-is-the-process-for-generating-a-bare-metal-binary-with-msvc-tools) |
| [text](https://github.com/ahaoboy/neofetch) |
| [text](https://www.reddit.com/r/rust/comments/mtu2kw/hey_rustaceans_got_an_easy_question_ask_here/) |
| [text](https://stackoverflow.com/questions/77703233/using-wmi-iwbemservicesexecmethod-from-rust) |
| [text](https://github.com/microsoft/windows-rs/issues/2751) |
| [text](https://github.com/nervosys/SiliconMonitor) |
| [text](https://ftp.fau.de/debian/pool/main/r/) |
| [text](https://lib.rs/crates/cuda_setup) |
| [text](https://lib.rs/crates/libftdi1-sys) |
| [text](https://packages.debian.org/sid/rust/) |
| [text](https://agentfactory.panaversity.org/docs/General-Agents-Foundations/claude-code-teams-cicd/claude-md-configuration-hierarchy) |
| [text](https://code.claude.com/docs/en/how-claude-code-works) |
| [text](https://code.claude.com/docs/en/memory) |
| [text](https://code.claude.com/docs/en/overview) |
| [text](https://github.com/shanraisshan/claude-code-best-practice/blob/main/CLAUDE.md) |
| [text](https://code.claude.com/docs/en/best-practices) |
| [text](https://institute.sfeir.com/en/claude-code/claude-code-mcp-model-context-protocol/troubleshooting/) |
| [text](https://code.claude.com/docs/en/context-window) |
| [text](https://github.com/zilliztech/claude-context) |
| [text](https://www.reddit.com/r/ClaudeCode/comments/1q0qnkq/mcps_taking_up_a_huge_amount_of_context_how_to/) |
| [text](https://pub.towardsai.net/modular-system-prompts-how-i-build-agents-that-adapt-to-every-session-ad0f2525143c) |
| [text](https://github.com/shanselman/toasty/blob/main/SESSION_CONTEXT.md) |
| [text](https://lobehub.com/mcp/canopyhq-phloem) |
| [text](https://www.mindstudio.ai/blog/how-to-build-agentic-operating-system-claude-code) |
| [text](https://github.com/anthropics/claude-code/issues/67518) |
| [text](https://github.com/affaan-m/everything-claude-code/issues/187) |
| [text](https://github.com/topics/table-parser) |
| [text](https://github.com/gHashTag/trios/issues/167) |
| [text](https://github.com/mendableai/firecrawl/discussions/630) |
| [text](https://docs.rs/serde_table) |
| [text](https://docs.rs/markdown-parser) |
| [text](https://docs.rs/markdown/) |
| [text](https://users.rust-lang.org/t/parse-markdown-and-serialize-it-back-to-markdown/126344) |
| [text](https://www.elastic.co/docs/reference/integrations/wmi) |
| [text](https://stackoverflow.com/questions/1423981/why-are-wmi-queries-so-slow-sometimes) |
| [text](https://github.com/wezterm/wezterm/issues/3103) |
| [text](https://www.reillywood.com/categories/rust/) |
| [text](https://github.com/heim-rs/heim/issues/232) |
| [text](https://github.com/heim-rs/heim/issues/232) |
| [text](http://www.novell.com/documentation/zenworks-24.2/zen_discovery_deployment/data/bapsg7g.html) |
| [text](https://www.reddit.com/r/rust/comments/mlllqe/help_with_windows_bindings_cocreateinstance/) |
| [text](https://docs.rs/nvml-wrapper/latest/aarch64-apple-darwin/src/nvml_wrapper/lib.rs.html?search=) |
| [text](https://lib.rs/crates/hypomnesis) |
| [text](https://skills.deeptoai.com/en/docs/development/session-start-hook-deep-dive) |
| [text](https://www.robvanderwoude.com/wmiqueries.php) |
| [text](https://www.magsys.co.uk/delphi/magwmi.asp) |
| [text](https://gist.github.com/sysrage/874492c74b3fd0d1438012337e43d6fd) |
| [text](https://community.flexera.com/s/article/blank-serial-number-after-inventory) |
| [text](https://stackoverflow.com/questions/1290533/wmi-win32-baseboard-serialnumber) |
| [text](http://vbnet.mvps.org/code/wmi/win32_baseboard.htm) |
| [text](https://superuser.com/questions/1921813/powershell-get-motherboard-serial-number) |
| [text](https://github.com/RRUZ/delphi-wmi-class-generator) |
| [text](https://github.com/rust-nvml/nvml-wrapper) |
| [text](https://docs.rs/narsil) |
| [text](https://github.com/hashicorp/nomad-device-nvidia/pulls) |
| [text](https://www.reddit.com/r/wayland/comments/1arjtxj/i_have_created_a_program_to_control_nvidia_gpus/) |
| [text](https://crates.io/crates/rmcp-git) |
| [text](https://crates.io/crates/rmcp-git) |
| [text](https://docs.rs/rmcp) |
| [text](https://github.com/andrico21/rmcp-server-kit) |
| [text](https://github.com/ChrisRoyse/Synapse/issues/15) |
| [text](https://www.reddit.com/r/rust/comments/1q5qzyz/title_rmcpbreakrs_a_rust_mcp_server_for/) |
| [text](https://www.reddit.com/r/rust/comments/1q5qzyz/title_rmcpbreakrs_a_rust_mcp_server_for/) |

---
