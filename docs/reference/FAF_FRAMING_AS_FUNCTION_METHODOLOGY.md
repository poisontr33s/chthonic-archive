# FAF — Framing As Function

**Version:** v0.1  
**Status:** Methodology draft hardened into executable protocol  
**Primary proving challenge:** Ruby 4.0.3 on Windows 11 as a validated foreign-capability host  
**Source:** `The-Savant-Grade-Undercellar_Library_Study/FAF_Framing_As_Function_Methodology_Google_Do.html`  
**Filed:** 2026-04-25

---

## 0. One-Line Definition

**FAF — Framing As Function — is a failure-opening method: every surfaced impossibility is forced to become a gate, and every gate must emit a probe, binding, membrane, or impossible-currently boundary record.**

FAF is not the formatted challenge.  
FAF is the method that makes the challenge become solvable.

---

## 1. Core Law

**Every surfaced impossibility must become a gate.**  
**Every gate must emit exactly one primary artifact:**  
1. probe  
2. binding  
3. membrane  
4. impossible-currently boundary  

A blocker is not permitted to remain abstract.

A failure may stop a build.  
It may not stop the system from learning.

---

## 2. Artifact Ontology

### 2.1 Probe

A **probe** is the smallest executable truth test that turns an unknown into a recorded fact.

A probe answers:

> Can this host discover, load, identify, call, or fail against this boundary?

A probe may be written in Ruby, C, Rust, PowerShell, Python, or CI YAML.

A probe is valid only if it:
- executes reproducibly;
- emits machine-readable output;
- distinguishes absence from failure;
- exits cleanly unless the probe infrastructure itself is broken;
- appends failure evidence to the gate ledger.

---

### 2.2 Binding

A **binding** is a minimal intentional connection across a boundary.

A binding is not a wrapper for convenience.  
A binding exists only after a probe has proven that the boundary is real enough to call.

Examples:
```
Ruby Fiddle call -> native version symbol
Ruby C extension -> native loader call
Rust FFI crate -> stable ABI membrane
PowerShell harness -> external toolchain identity
Python import -> wheel-provided C extension
uv index route -> upstream registry wheel slot
```

A binding must expose:
- the called function or symbol;
- ABI assumptions;
- version assumptions;
- failure behavior;
- minimal call proof.

---

### 2.3 Membrane

A **membrane** is the protective layer between the host language and foreign capability.

It translates foreign failure into host-visible boundary facts.

A membrane must prevent:
- silent crashes where possible;
- PATH-mutation mythology;
- "DLL exists therefore capability exists" claims;
- "wheel resolved therefore capability is usable" claims;
- untyped foreign errors;
- hidden ABI drift;
- false admission of unsupported platforms.

Examples:
```
Fiddle membrane
Ruby C extension membrane
Rust FFI membrane
MSVC bridge membrane
MSYS2 bridge membrane
DirectML provider membrane
CUDA driver membrane
Vulkan loader membrane
uv override-dependencies membrane
PyO3 ABI membrane
```

---

### 2.4 Impossible-Currently Boundary

An **impossible-currently boundary** is not closure.

It is the highest-leverage FAF artifact when the wall is real but not yet open.

A gate may be declared impossible-currently only when the boundary is named, the failure is reproducible, and the condition required to reopen the gate is explicit.

**Schema:**
```json
{
  "artifact_type": "impossible_currently_boundary",
  "gate": "string",
  "claim": "string",
  "observed_failure": "string",
  "proof": "path-or-command",
  "minimum_condition_to_reopen": "string",
  "upstream_dependency": "string",
  "next_probe": "string",
  "status": "blocked_not_closed"
}
```

Category 4 is therefore not:  
> We gave up.

It is:  
> The ceiling is now visible, named, and ready for future pressure.

---

## 3. False Success Ban

A foreign capability is **not** admitted because any of these are true:

```
An installer ran.
A DLL exists.
PATH was extended.
A gem installed.
A compiler exists.
A header exists.
A library linked.
A wheel resolved.
A pyproject.toml has an optional-dependency entry.
A sample project compiled outside the host language.
A README says the platform is supported.
```

Those facts may create candidate gates.  
They do not admit capability.

---

## 4. Capability Admission Rule

A foreign capability is admitted only when the host process can:

1. **discover** it;
2. **identify** it;
3. **load** it;
4. **interrogate** it;
5. **call** at least one minimal function;
6. **survive success and failure**;
7. **emit a reproducible boundary record**.

In compact form:
```
installed   != available
available   != loadable
loadable    != callable
callable    != safe
safe        != admitted
```

---

## 5. Capability Ladder

Every capability passes through levels.

| Level | Name | Meaning |
|-------|------|---------|
| L0 | Discoverable | Host can find a candidate path, DLL, tool, or provider name. |
| L1 | Loadable | Host can load the library or invoke the tool without crashing. |
| L2 | Interrogable | Host can call version, identity, provider, or device-query functions. |
| L3 | Survivable | Host can fail cleanly and emit a structured boundary record. |
| L4 | Useful | Host can perform one minimal real operation through the capability. |

**No gate may skip levels silently.**

---

## 6. Primary Proving Challenge

### 6.1 Challenge Statement

> Ruby 4.0.3 on Windows 11 must be forced into a verified foreign-capability host.

The candidate system begins as:
```
CRuby source
RubyInstaller / DevKit / ridk / MSYS2
Rust
Prism
ZJIT
YJIT reality-probing
rv as optional distribution shell
foreign middleware candidates:
  CUDA
  cuDNN
  TensorRT
  Vulkan SDK
  DirectML
  ONNX Runtime
  NVIDIA driver stack
  future native libraries
```

The challenge is **not**:
```
Install DLLs.
Make Ruby use GPU.
Stuff CUDA into Ruby.
Replace the task with WSL.
Replace the task with Rails.
Replace the task with Bundler.
Replace the task with a generic RubyInstaller walkthrough.
```

The actual challenge is:
> Make Ruby 4.0.3 on Windows 11 become a validated foreign-capability host  
> without lying about what Ruby, Windows, YJIT, ZJIT, MSYS2, CUDA, Vulkan,  
> TensorRT, ONNX Runtime, DirectML, NVIDIA drivers, or rv can actually do.

---

## 7. Current Factual Ground (Ruby proving challenge)

| Topic | Ground |
|-------|--------|
| Ruby 4.0.3 | Released 21 April 2026; narrowly security/update-focused around ERB/CVE handling. |
| Ruby 4.0.0 | Introduced Ruby Box and ZJIT. |
| ZJIT | Experimental method-based JIT; enabled with `--zjit` or `RubyVM::ZJIT.enable`; build requires Rust 1.85.0 or later; faster than interpreter but not yet as fast as YJIT as of Ruby 4.0.0 release notes. |
| YJIT | Native CRuby JIT; documented support is macOS, Linux, and BSD on x86-64 and arm64/aarch64. Native Windows support must be treated as a platform gate, not assumed. |
| RubyInstaller | Uses MSYS2 as the DevKit/toolchain layer for building Ruby and native gems on Windows; `ridk install` is the native access point. |
| rv | Relevant as a Ruby gem/project/version/tool environment manager; not the revolution itself. |
| CUDA on Windows | Requires Windows + compatible compiler + CUDA-capable NVIDIA GPU/driver/toolkit coherence. |
| TensorRT | Requires explicit CUDA/driver/platform compatibility checks. |
| Vulkan SDK | The SDK is not proof of driver/runtime capability; loader, driver, and layer stack must be tested. |
| ONNX Runtime | Uses execution providers; CPU, CUDA, DirectML, and other providers must be distinguished through runtime interrogation. |

---

## 8. First Gate

The first gate is not CUDA.

The first gate is:

> Can Ruby 4.0.3 be built or assembled on Windows 11 in a reproducible native  
> environment where every native capability probe is executable, logged, and  
> replayable?

Without this gate, GPU ambition is decoration.

---

## 9. First Executable Proof

The first proof is deliberately smaller than the ambition.

**Target:** `probes/ruby/ruby_host_probe.rb`

**Required emissions:**
```
manifest/host.json
manifest/toolchain.json
manifest/capabilities.json
manifest/failures.jsonl
```

**Required behavior:**
```
Missing capability candidate -> record blocked gate.
Missing DLL -> record loader gate.
Absent JIT module -> record platform/build gate.
Probe infrastructure failure -> nonzero exit.
Capability absence -> zero exit plus boundary record.
```

---

## 10. Initial Ruby Host Probe

```ruby
# probes/ruby/ruby_host_probe.rb

require "json"
require "fileutils"
require "fiddle"
require "rbconfig"

ROOT     = File.expand_path("../../..", __dir__)
MANIFEST = File.join(ROOT, "manifest")
FileUtils.mkdir_p(MANIFEST)

host = {
  ruby_description: RUBY_DESCRIPTION,
  ruby_version:     RUBY_VERSION,
  ruby_platform:    RUBY_PLATFORM,
  ruby_engine:      RUBY_ENGINE,
  host_cpu:         RbConfig::CONFIG["host_cpu"],
  host_os:          RbConfig::CONFIG["host_os"],
  arch:             RbConfig::CONFIG["arch"],
  configure_args:   RbConfig::CONFIG["configure_args"]
}

toolchain = {
  cc:    RbConfig::CONFIG["CC"],
  cxx:   RbConfig::CONFIG["CXX"],
  make:  RbConfig::CONFIG["MAKE"],
  rustc: nil,
  cargo: nil
}

def command_version(command)
  output = nil
  IO.popen("#{command} --version 2>&1") { |io| output = io.read.strip }
  status = $?.exitstatus
  { command: command, exitstatus: status, output: output }
rescue => e
  { command: command, error: e.class.name, message: e.message }
end

toolchain[:rustc] = command_version("rustc")
toolchain[:cargo] = command_version("cargo")

capabilities = {
  jit: {
    zjit_present: defined?(RubyVM::ZJIT) ? true : false,
    yjit_present: defined?(RubyVM::YJIT) ? true : false
  },
  native_libraries: {}
}

failures_path = File.join(MANIFEST, "failures.jsonl")

def append_failure(path, record)
  File.open(path, "a", encoding: "utf-8") do |f|
    f.puts(JSON.generate(record.merge(recorded_at_utc: Time.now.utc.iso8601)))
  end
end

candidates = {
  "vulkan_loader"    => "vulkan-1.dll",
  "cuda_driver"      => "nvcuda.dll",
  "onnxruntime"      => "onnxruntime.dll",
  "tensorrt_runtime" => "nvinfer.dll"
}

candidates.each do |name, dll|
  begin
    handle = Fiddle.dlopen(dll)
    capabilities[:native_libraries][name] = {
      candidate: dll,
      level:     "L1_loadable",
      loadable:  true
    }
  rescue Fiddle::DLError => e
    capabilities[:native_libraries][name] = {
      candidate: dll,
      level:     "L0_or_L1_blocked",
      loadable:  false,
      error:     e.message
    }
    append_failure(failures_path, {
      artifact_type:  "probe",
      gate:           "loader_truth/#{name}",
      candidate:      dll,
      failure_class:  "dll_not_loadable",
      observed_failure: e.message,
      next_artifact:  "search_path_manifest_or_installation_probe"
    })
  end
end

unless capabilities[:jit][:zjit_present]
  append_failure(failures_path, {
    artifact_type:    "probe",
    gate:             "jit_reality/zjit",
    failure_class:    "zjit_absent",
    observed_failure: "RubyVM::ZJIT is not defined",
    next_artifact:    "rust_toolchain_and_build_flag_gate"
  })
end

unless capabilities[:jit][:yjit_present]
  append_failure(failures_path, {
    artifact_type:    "probe",
    gate:             "jit_reality/yjit",
    failure_class:    "yjit_absent",
    observed_failure: "RubyVM::YJIT is not defined",
    next_artifact:    "platform_gate_declaration"
  })
end

File.write(File.join(MANIFEST, "host.json"),         JSON.pretty_generate(host))
File.write(File.join(MANIFEST, "toolchain.json"),    JSON.pretty_generate(toolchain))
File.write(File.join(MANIFEST, "capabilities.json"), JSON.pretty_generate(capabilities))

puts JSON.pretty_generate({
  status: "probe_complete",
  emitted: [
    "manifest/host.json",
    "manifest/toolchain.json",
    "manifest/capabilities.json",
    "manifest/failures.jsonl"
  ]
})
```

> Note: this first probe proves only **identity**, **JIT presence**, and **L1 native-loader truth**.  
> It does not admit CUDA, Vulkan, ONNX Runtime, or TensorRT as useful capabilities.

---

## 11. Failure-to-Artifact Compiler

Every failure must compile into an artifact.

| Failure | FAF Artifact |
|---------|-------------|
| Missing compiler | Toolchain probe |
| Missing header | Include-path probe + package manifest requirement |
| Missing DLL | Loader probe + search-path manifest + no-PATH-mutation rule |
| DLL loads but symbol missing | ABI version probe |
| Library version mismatch | Compatibility matrix entry |
| Ruby crashes | Minimal repro + crash bucket + blocked boundary |
| YJIT absent on Windows | Platform-gate declaration |
| ZJIT missing | Rust/toolchain/build-flag gate |
| CUDA installed but unusable | Driver/runtime/compiler compatibility probe |
| TensorRT present but incompatible | CUDA/TensorRT/cuDNN version-triple gate |
| Vulkan SDK present but loader broken | Loader/layer/environment-variable probe |
| ONNX Runtime present but provider absent | Provider enumeration probe |
| rv cannot represent the build | rv integration deferred; Ruby host remains primary |

The failure no longer stops the system.  
It is compiled into the system.

---

## 12. Native-Library Truth Test

A native library is not admitted at `dlopen`.

`Fiddle.dlopen("nvcuda.dll")` proves only:

> Ruby can ask the Windows loader to load nvcuda.dll.

It does not prove:
```
CUDA works.
A GPU exists.
The driver is compatible.
The runtime is compatible.
TensorRT can use it.
Ruby has useful GPU capability.
```

A native capability must pass: L0 → L1 → L2 → L3 → L4.

---

## 13. Ruby/JIT Truth Test

### ZJIT

ZJIT is admitted only when:
```
Rust >= 1.85.0 is proven.
Ruby was built with ZJIT support.
RubyVM::ZJIT exists.
ruby --zjit -e "p RubyVM::ZJIT.enabled?" succeeds or fails cleanly.
The result is emitted to manifest/capabilities.json.
```

If ZJIT is absent:
```
artifact = Rust/toolchain/build-flag gate
```

### YJIT

YJIT is not assumed on native Windows.

The system must probe:
```ruby
defined?(RubyVM::YJIT)
```

If absent: `artifact = platform-gate declaration`  
If present: `artifact = YJIT runtime introspection probe`

No FAF-valid output may imply native Windows YJIT support merely because YJIT exists elsewhere.

---

## 14. Windows ABI Truth Test

Windows native capability requires ABI coherence.

The system must record:
```
Ruby build toolchain
MSYS2 environment
MSVC environment, if used
Rust target triple
C extension compiler
linked runtime libraries
DLL architecture
process architecture
PATH/search-path source
```

A Windows ABI gate is open only when:
```
Ruby process architecture matches target DLL architecture.
Compiler runtime expectations are explicit.
Native extension build chain is reproducible.
Loader search order is recorded.
The boundary survives missing-DLL and wrong-architecture cases cleanly.
```

---

## 15. GPU Middleware Truth Tests

### CUDA Driver Gate

Admitted only when Ruby can:
```
load nvcuda.dll
call driver-version query
call device-count query
report GPU identity
```

`nvcuda.dll` loadable ≠ CUDA driver usable.  
Device count = 0 must be recorded as a boundary, not a success.

### Vulkan Gate

Admitted only when:
```
vulkan-1.dll loads
vkEnumerateInstanceVersion is callable
vkEnumeratePhysicalDevices returns > 0
device properties are emitted to manifest
```

Vulkan SDK installed ≠ Vulkan loader present ≠ GPU Vulkan-capable.

### ONNX Runtime Gate

Admitted only when:
```
onnxruntime.dll loads
OrtGetApiBase is callable
provider list is interrogated
at least one provider (CPU minimum) is admitted
target provider (CUDA/DirectML) is explicitly admitted or declared impossible-currently
```

### TensorRT Gate

Admitted only when:
```
nvinfer.dll loads
CUDA driver gate is already open (dependency)
TensorRT/CUDA/cuDNN version triple is recorded
a minimal INetworkDefinition can be constructed
```

---

## 16. Gate Ledger Contract

Every gate that runs must append to the gate ledger (`manifest/failures.jsonl` or equivalent). The ledger is append-only. Each entry is one JSON line.

Minimum entry fields:
```json
{
  "artifact_type": "probe|binding|membrane|impossible_currently_boundary",
  "gate": "short/slash/path identifier",
  "observed_failure": "exact error or 'none'",
  "level_reached": "L0|L1|L2|L3|L4",
  "status": "open|blocked_not_closed|admitted",
  "recorded_at_utc": "ISO8601"
}
```

The ledger is not a log of failures. It is a ledger of gate states.  
A gate with `status: "admitted"` belongs in the ledger as much as a gate with `status: "blocked_not_closed"`.

---

## Summary

FAF operates on one axiom:

> A system that names its boundaries is structurally stronger than a system that denies them.

The methodology produces not a passing test suite but a **boundary ledger** — a reproducible record of what the host can and cannot do, at what level, under what conditions, with what minimum condition to reopen each closed gate.

The ledger is the artifact. The probe is the tool. The membrane is the guard. The impossible-currently boundary is the honest ceiling.

No false success. No decoration. No mythology.
