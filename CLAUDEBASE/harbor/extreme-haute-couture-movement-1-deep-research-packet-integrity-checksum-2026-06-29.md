# The Extreme Haute Couture — Movement 1 Deep Research Packet

Subject: VS Code Insiders integrity warning, checksum reconciliation, and substrate ownership.

## Ask

Research whether the "Your Code - Insiders installation appears to be corrupt" warning can be fixed without abandoning Movement 1's local substrate patching architecture.

This packet is scoped to serious reverse engineering and implementation planning, not marketplace reassurance copy.

## Working Conclusion

The warning is fixable in the narrow technical sense.

VS Code computes SHA-256/base64-no-padding checksums for files listed in `product.json -> checksums`. If a listed app resource differs from the expected checksum, the workbench integrity service shows the corrupt-install warning.

For our current Insiders build, the checksum table includes:

```text
vs/code/electron-browser/workbench/workbench.html
```

Our substrate injects a CSS link into that HTML file. That changes the file hash, so the warning is expected unless the checksum table is reconciled.

The serious version of the fix is not "hide warning"; it is an owned integrity reconciler that:

```text
1. verifies Chthonic substrate markers and rejects foreign drift
2. recomputes VS Code-format checksums for only allowlisted patched files
3. updates product.json checksums for only those allowlisted files
4. backs up product.json per VS Code commit
5. runs as part of couture:gate
```

## Local Evidence

Local Insiders:

```text
Version: 1.127.0-insider
Commit: 628f6de50e89b20c7688c66ac2923cce2862c1b0
App root: C:\Users\eldno\AppData\Local\Programs\Microsoft VS Code Insiders\628f6de50e\resources\app
```

Current `product.json -> checksums` includes:

```text
vs/code/electron-browser/workbench/workbench.html = fg2fsFbPwbrb4+QjdKJ8TqaQMi1NaRJFXy7NMSgF9GA
```

Current patched file checksum:

```text
vs/code/electron-browser/workbench/workbench.html = sD6Yz99Z54jj5poug5VGh+0T8fDPdxved0ZT3Co0uD4
```

`out/main.js` is patched by Movement 1 but is not currently listed in this build's checksum map.

## Upstream Source Anchors

VS Code integrity service:

```text
src/vs/workbench/services/integrity/electron-browser/integrityService.ts
```

The service reads `this.productService.checksums`, resolves each app resource, compares actual and expected checksums, and shows the warning message when any listed file differs.

Source:

```text
https://github.com/microsoft/vscode/blob/main/src/vs/workbench/services/integrity/electron-browser/integrityService.ts
```

VS Code checksum service:

```text
src/vs/platform/checksum/node/checksumService.ts
```

The checksum format is:

```text
sha256(file bytes) -> base64 -> remove trailing =
```

Source:

```text
https://github.com/microsoft/vscode/blob/main/src/vs/platform/checksum/node/checksumService.ts
```

Vibrancy Continued acknowledges the warning because it edits checksum-verified HTML, and points users to a separate checksum fixer rather than owning this step itself.

Source:

```text
https://github.com/illixion/vscode-vibrancy-continued
https://github.com/illixion/vscode-vibrancy-continued/blob/main/extension/file-transforms.js
https://github.com/illixion/vscode-vibrancy-continued/blob/main/extension/index.js
```

`vesper-vibrant` is a conventional color theme package. It contributes a theme JSON and does not appear to participate in the checksum/integrity layer.

Source:

```text
https://github.com/iotacb/vesper-vibrant
```

## Proposed Implementation Candidate

Add:

```text
scripts/insiders-integrity-reconcile.ps1
manifest/insiders-integrity-reconcile.json
```

Commands:

```powershell
pwsh -NoProfile -File scripts/insiders-integrity-reconcile.ps1 -Status
pwsh -NoProfile -File scripts/insiders-integrity-reconcile.ps1 -Apply
pwsh -NoProfile -File scripts/insiders-integrity-reconcile.ps1 -Verify
pwsh -NoProfile -File scripts/insiders-integrity-reconcile.ps1 -Restore
```

Allowlist, initial:

```text
vs/code/electron-browser/workbench/workbench.html
vs/code/electron-sandbox/workbench/workbench.html
vs/code/electron-sandbox/workbench/workbench.esm.html
```

Do not touch a checksum entry unless:

```text
file is present in product.json checksums
file path is allowlisted
file contains the Chthonic substrate CSS link
file does not contain Claude Design substrate markers
file does not contain Vibrancy Continued markers
scripts/mica-substrate.ps1 -Verify passes
```

Add to `bun run couture:gate`:

```text
integrity-checksum-owned
integrity-no-foreign-checksum-drift
integrity-product-json-backup-present
```

## Risks

Updating `product.json` checksums can hide unintended app-file drift if done generically. The implementation must refuse broad reconciliation and update only known Chthonic-owned files after marker verification.

VS Code updates will replace the app root and product metadata. Treat reconciliation as commit-scoped and rerun after every Insiders update.

If this is ever shipped as a public extension, marketplace policy and user consent need separate review. For local Movement 1 engineering, it is a deterministic owner step.

## Deep Research Prompt

Investigate VS Code's current integrity-warning mechanism for Stable and Insiders on Windows. Focus on `product.json.checksums`, `IntegrityService`, `ChecksumService`, and how app-resource paths map to files under `resources/app/out`.

Research whether updating `product.json.checksums` after a controlled local workbench HTML injection is sufficient to prevent the "Your Code installation appears to be corrupt" warning in modern VS Code builds, and whether any secondary integrity/signature mechanism also watches `product.json` itself on Windows user installs.

Compare:

```text
illixion/vscode-vibrancy-continued
RimuruChan.vscode-fix-checksums-next
lehni/vscode-fix-checksums
Microsoft VS Code source
```

Return:

```text
1. exact checksum algorithm and path mapping
2. whether product.json checksum reconciliation suppresses the warning on current Stable/Insiders
3. whether VS Code has changed from MD5 to SHA-256 and when that matters
4. safest local implementation design with backup/restore/gate behavior
5. public-extension policy risk versus local private tooling risk
6. test matrix for Windows Stable, Windows Insiders, and update-after-reconcile
```

Current local case to reason from:

```text
VS Code Insiders: 1.127.0-insider
Commit: 628f6de50e89b20c7688c66ac2923cce2862c1b0
Tracked checksum entry: vs/code/electron-browser/workbench/workbench.html
Original product checksum: fg2fsFbPwbrb4+QjdKJ8TqaQMi1NaRJFXy7NMSgF9GA
Current patched checksum: sD6Yz99Z54jj5poug5VGh+0T8fDPdxved0ZT3Co0uD4
```
