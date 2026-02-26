# Patch Strategy — Chthonic Golden

## Approach: Shallow Patch (VSCodium-style)

We maintain a set of discrete `.patch` files applied to a fresh upstream VS Code checkout.
This is the same strategy used by VSCodium and avoids the maintenance burden of a deep fork.

### Patch Application Order

1. **001-product-json.patch** — Replace `product.json` with Chthonic Golden identity
2. **002-telemetry-strip.patch** — Remove/redirect Microsoft telemetry endpoints
3. **003-gpu-defaults.patch** — Bake GPU acceleration into default Electron configuration

### How Patches Are Generated

```powershell
# After making changes to an upstream checkout:
cd upstream-vscode
git diff > ..\chthonic-golden\patches\001-product-json.patch
```

### How Patches Are Applied

```powershell
cd upstream-vscode
git apply ..\chthonic-golden\patches\001-product-json.patch
git apply ..\chthonic-golden\patches\002-telemetry-strip.patch
git apply ..\chthonic-golden\patches\003-gpu-defaults.patch
```

### Upstream Sync Protocol

When pulling a new upstream VS Code release:

1. `git fetch upstream && git checkout <tag>`
2. Apply patches in order
3. If any patch fails: manually resolve, regenerate patch file
4. Run build pipeline
5. Run stability matrix (`scripts/vscode_insiders_matrix.ps1` adapted)
6. If stable: commit updated patches

### Patch Naming Convention

```
NNN-description.patch
```

- `NNN` = 3-digit sequence number
- Patches apply in numeric order
- Each patch is self-contained and addresses one concern

### ANKH Alignment

> @ankh: heritage-continuity — Patches preserve the fork's identity across upstream updates.
> The upstream VS Code is the substrate; patches are the Interface Vessel translation.
> When patches conflict with upstream, the ANKH invariant (our intent) takes precedence,
> not the upstream change. Resolve toward lineage, not convenience.
