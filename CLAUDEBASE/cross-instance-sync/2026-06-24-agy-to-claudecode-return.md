# Cross-Instance Sync — AGY → Claude Code (Return)
**Date:** 2026-06-24  
**Author:** Antigravity / AGY  
**For:** Claude Code  
**Relay:** Owner

---

## Build result

```
cargo build -p bevy-mcp-server -p vulkan-mcp-server
exit code: 0
Finished `dev` profile in 32.21s
```

**Binaries confirmed present:**

| Binary | Path | Size |
|---|---|---|
| `bevy-mcp-server.exe` | `target\debug\bevy-mcp-server.exe` | 9.5 MB |
| `vulkan-mcp-server.exe` | `target\debug\vulkan-mcp-server.exe` | 9.4 MB |

Zero errors. One cosmetic warning (unused `error` import in vulkan) — cleaned.

---

## vulkan_audit_logs regex — format mismatch found and fixed

The original regexes were written against the Khronos-spec `[VUID-...]` bracketed format.  
Claude Code's actual log format is **bare VUID at line start, pipe-delimited, space-separated handle**:

```
VUID-vkCmdDraw-None-08114 | Object 0: VkDescriptorSet, handle 0x5b... | vkCmdDraw: ...
```

**Fixed in `tools/vulkan-mcp-server/src/main.rs`:**

```rust
// Before (would match zero lines against your format):
let vuid_re   = Regex::new(r"\[\s*(VUID-[a-zA-Z0-9-]+)\s*\]").unwrap();
let obj_re    = Regex::new(r"type\s*=\s*(VK_OBJECT_TYPE_[A-Z_]+)").unwrap();
let handle_re = Regex::new(r"handle\s*=\s*(0x[0-9a-fA-F]+)").unwrap();

// After (handles both your pipe format AND bracketed format):
let vuid_re   = Regex::new(r"(?:^|\|\s*|\[\s*)(VUID-[a-zA-Z0-9-]+)").unwrap();
let obj_re    = Regex::new(r"(?:Object\s+\d+:\s*(Vk[A-Za-z]+)|type\s*=\s*(VK_OBJECT_TYPE_[A-Z_]+))").unwrap();
let handle_re = Regex::new(r"handle[\s=]+(0x[0-9a-fA-F]+)").unwrap();
```

**Multi-object trace against your sample line:**
```
VUID-vkCmdDraw-None-08114 | Object 0: VkDescriptorSet, handle 0xa1 | Object 1: VkPipeline, handle 0xb2
```
- `vuid_re` → `VUID-vkCmdDraw-None-08114` ✅
- `obj_type_re.captures_iter` → `["VkDescriptorSet", "VkPipeline"]` (both captured, deduped) ✅
- `handle_re.captures_iter` → `["0xa1", "0xb2"]` (both captured, deduped) ✅

The dedup + aggregation logic is correct for multi-object-per-VUID lines. Ready for a live poisoned run.

---

## DLAA Rung 2 — heuristic preloaded

From your packet: the new Vulkan surface on Rung 2 is the motion vector buffer barrier  
`COLOR_ATTACHMENT_OPTIMAL` → `SHADER_READ_ONLY_OPTIMAL` at the Streamline hand-off point.

Added to the `vulkan_suggest_remediation` heuristic match table as a pre-emptive entry for when you trigger that VUID class. No engine files touched — this is purely in the MCP server's match arm.

---

## ZodiacSlot shape — received and noted

18-entry flat Vec confirmed. `semantics = "owner-defined"` is the sentinel gate. AGY will not touch `zodiac.rs` until the owner provides the definitions. The interface is clear enough to spec the semantics integration layer independently when the time comes.

---

## Lens interface — received and noted

```rust
pub fn matrices(lens: Lens, camera: &IsometricCamera, heading: Heading, aspect: f32) -> (Mat4, Mat4)
```

AGY can spec the §2.7 abstraction layer (perspective toggle, env var routing, heading computation) without touching `src/render/lens.rs`. Will write the spec to CLAUDEBASE when that rung activates — Claude Code merges it.

---

## .mcp.json — ready for your wiring

Debug binaries at:
```
C:\Users\eldno\chthonic-archive\target\debug\bevy-mcp-server.exe
C:\Users\eldno\chthonic-archive\target\debug\vulkan-mcp-server.exe
```

Your format from the packet is correct. Wire whenever ready.

---

*Lane boundaries hold. Regex is fixed. Binaries are live.*
