# Dependency Freshness — 2026-02-11T02-19-33

# Dependency Analysis

## Package.json (Root)
| Dependency | Version | Outdated? | Security-Sensitive | Notes |
|---|---|---|---|---|
| @modelcontextprotocol/sdk | ^1.26.0 | No | Auth/Network | MCP core—recent |
| @sentry/bun | ^10.38.0 | No | Auth/Network | Error telemetry—current |
| minimatch | ^10.1.2 | No | — | Pattern matching—current |
| @playwright/mcp | ^0.0.64 | ⚠️ | — | Pre-release (0.0.x)—unstable |

## Extensions (Archive, Mandala, StatusBar)
| Dependency | Version | Outdated? | Notes |
|---|---|---|---|
| @types/node | ^20.x | No | **CONSISTENT across all 3 extensions** |
| @types/vscode | ^1.90.0 | No | **CONSISTENT across all 3 extensions** |
| typescript | ^5.x | No | **CONSISTENT across all 3 extensions** |

## Cargo.toml (Rust)
| Dependency | Version | Outdated? | Security-Sensitive | Notes |
|---|---|---|---|---|
| winit | 0.29 | No | — | Window library—stable |
| ash | 0.38 | No | — | Vulkan bindings—recent |
| ash-window | 0.13 | No | — | Vulkan/window—aligned |
| gpu-allocator | 0.22 | No | — | GPU memory—current |
| bevy_ecs | 0.14 | ⚠️ | — | ECS—potentially trailing 0.15+ |
| serde | 1.0 | No | — | Serialization—stable |
| glam | 0.24 | No | — | Math library—current |
| **sha2** | 0.10 | No | ✅ **Crypto** | Hash function—current |
| tokio | 1.0 | No | — | Async runtime—stable |
| rand | 0.8 | No | — | RNG—current |

## Pyproject.toml (Python)
| Dependency | Version | Outdated? | Security-Sensitive | Notes |
|---|---|---|---|---|
| networkx | >=3.6,<4 | No | — | Graph library—current |
| fastmcp | >=2.14,<3 | No | Auth/Network | MCP client—recent |
| **huggingface-hub** | >=1.4.1,<2 | No | ✅ **Auth/Network** | Model downloads—requires API tokens |
| **idna** | >=3.11 | No | ✅ **Network** | Domain name encoding—security-critical |
| **requests** | >=2.32,<3 | No | ✅ **Network** | HTTP client—active maintenance required |
| radon | >=6.0.1,<7 | No | — | Code metrics—optional |
| mcp | >=1.26.0,<2 | No | Auth/Network | **Overlaps with JS root** (same SDK) |
| pydantic-settings | >=2.12.0,<3 | No | — | Config validation—current |

## Cross-Manifest Conflicts
| Issue | Details |
|---|---|
| **MCP Naming Mismatch** | `@modelcontextprotocol/sdk` (JS) vs `mcp` (Python) are the **same package**, version-aligned at 1.26.x ✅ |
| **Pre-release Extension** | `@playwright/mcp@0.0.64` is unstable; flag for upgrade when stable (1.0+) |
| **Bevy ECS Lag** | Rust: `bevy_ecs@0.14` may be behind latest (check if 0.15+ needed) |
| **No Version Pinning** | Python uses ranges (`>=X,<Y`); JS uses carets/tildes—appropriate for their contexts |

## Security Summary
🔴 **Critical Network Deps:**
- `requests` (2.32+) — Keep updated for SSL/proxy vulnerabilities
- `huggingface-hub` — Ensure token management is sandboxed
- `idna` (3.11+) — Active library; monitor for unicode attack vectors

🟢 **Crypto:** 
- `sha2@0.10` is current; suitable for archive fingerprinting