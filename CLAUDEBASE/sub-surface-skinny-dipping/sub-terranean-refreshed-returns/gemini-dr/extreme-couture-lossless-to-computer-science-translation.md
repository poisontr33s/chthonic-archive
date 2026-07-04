# The Extreme Haute Couture — Movement 1: VS Code Insiders Integrity Reconciliation and Substrate Ownership

## Introduction and Architectural Context

The evolution of modern, web-technology-based desktop environments has introduced unprecedented flexibility for developers to manipulate the visual and functional paradigms of their workspaces. Applications built upon the Electron framework, such as Microsoft Visual Studio Code (VS Code), inherently expose their user interfaces through standard web technologies, primarily HTML, CSS, and JavaScript. In the context of the Movement 1 architecture, the introduction of the Chthonic substrate necessitates the precise injection of custom stylesheet links directly into the primary rendering entry points of the VS Code Insiders build. While this patching methodology guarantees deep visual integration and structural ownership, it inevitably collides with the application’s internal self-verification mechanisms.

The immediate consequence of injecting the Chthonic substrate into the VS Code HTML files is the triggering of a persistent warning notification: "Your Code - Insiders installation appears to be corrupt. Please reinstall." For casual users modifying their editors with third-party themes, manually dismissing this warning or relying on brittle, community-maintained extensions to silence it has become standard practice. However, within a strictly controlled, high-assurance engineering environment, superficial suppression strategies introduce unacceptable architectural friction and security ambiguities.

This comprehensive research report conducts an exhaustive reverse-engineering analysis of the VS Code integrity verification mechanism, focusing on both the Stable and Insiders release channels on the Windows operating system. It delineates the cryptographic foundations of the checksum algorithm, the lifecycle of the internal IntegrityService, and the secondary implications of metadata mutation. Furthermore, it evaluates the deficiencies of existing public marketplace solutions, contrasting them with the proposed deterministic, local implementation designed to integrate seamlessly into the couture:gate deployment pipeline. The objective is to establish a mathematically sound, fully owned integrity reconciliation process that verifies expected Chthonic markers, rejects foreign code drift, and safely synchronizes the application's internal metadata without abandoning the core substrate patching architecture.

## The Anatomy of the VS Code Integrity Service

The foundation of the VS Code anti-corruption architecture is entirely self-contained within the application's typescript logic, functioning as a safeguard against accidental file degradation, incomplete updates, or erroneous disk operations rather than a hardened, cryptographically secure anti-tamper mechanism designed to thwart hostile adversaries. Understanding the lifecycle of this service is paramount to engineering a programmatic reconciliation process.

### Service Initialization and Metadata Ingestion

Upon the initialization of the VS Code workbench, the internal dependency injection container instantiates the IntegrityService. Historically, as VS Code evolved, the location and execution context of this service shifted. Originally housed within `src/vs/workbench/services/integrity/electron-browser/integrityService.ts`, the ongoing migration toward stricter context isolation and ES modules has transitioned these responsibilities into `electron-sandbox/integrityService.ts`.

The integrity validation process relies entirely on a static metadata file named `product.json`, located at the root of the extracted application directory (e.g., `%LOCALAPPDATA%\Programs\Microsoft VS Code Insiders\resources\app\product.json`). This JSON object serves as the definitive configuration manifest for a specific build, containing the application's commit hash, telemetry endpoints, gallery URLs, and crucially, a checksums dictionary. During startup, the IntegrityService reads this.productService.checksums. This dictionary maps relative internal file paths, such as `vs/code/electron-browser/workbench/workbench.html`, to their expected cryptographic hashes.

### Resource Resolution and Verification

Once the metadata is ingested, the service resolves the relative paths defined in the `product.json` dictionary into absolute disk paths targeting the `resources/app/out` directory. The application then delegates the actual file hashing to the ChecksumService, a core platform utility located at `src/vs/platform/checksum/node/checksumService.ts`. The ChecksumService calculates the hash of the file currently residing on the disk and returns the value to the IntegrityService for a strict string-equality comparison against the expected value sourced from the `product.json` manifest.

If a discrepancy is detected—as is the deterministic outcome when the Chthonic substrate injects a CSS link into `workbench.html`—the service executes a private `_prompt()` method. The detection mechanism operates on a fail-fast boolean logic; a single mismatched byte in any monitored file invalidates the entire installation state, triggering the notification payload.

### State Persistence and the Ephemeral Prompt

The manifestation of the warning prompt is conditionally governed by the user's localized state preferences. Within the `_prompt()` execution block, the service accesses the application's local storage to query the existence of a `dontShowPrompt` flag. VS Code categorizes its internal state storage into several distinct scopes, primarily `StorageScope.Application`, `StorageScope.Profile`, and `StorageScope.Workspace`.

The decision to suppress the integrity warning is stored within the `StorageScope.Application` context. This architectural choice means that once a user clicks "Don't Show Again," the prompt is silenced globally across all local profiles, remote windows, and independent workspaces associated with that installation. However, there is a critical programmatic condition attached to this suppression: the boolean flag is strictly bound to the specific commit hash of the current build, evaluated as `storedData.commit === this.productService.commit`.

Because the VS Code Insiders channel experiences highly frequent, often daily, updates, the underlying commit hash changes constantly. Every background update invalidates the stored `dontShowPrompt` state, causing the warning to resurface immediately upon the subsequent launch. For a persistent, highly tailored environment like Movement 1, relying on human intervention to perpetually dismiss this notification is procedurally unacceptable, necessitating a permanent, programmatic reconciliation of the underlying `product.json` checksums.

## Cryptographic Foundations and the Checksum Algorithm

To construct an authoritative reconciler capable of silencing the integrity warning directly at the source, the script must perfectly replicate the cryptographic operations executed by the internal ChecksumService. Any deviation in the hashing algorithm, string encoding, or padding configuration will result in a continued mismatch, perpetuating the error state.

### The Evolution from MD5 to SHA-256

Throughout the history of digital file distribution, algorithms such as MD5 and SHA-1 were ubiquitous standards for verifying file integrity. However, as computational power increased and the mathematical vulnerabilities of these older algorithms were exposed, the industry broadly transitioned toward the SHA-2 family to mitigate the risk of collision attacks. A collision occurs when two distinct inputs mathematically result in the identical hash output. While an accidental collision in an HTML file using MD5 is statistically negligible, the adoption of SHA-256 ensures cryptographic guarantees against intentional, malicious tampering.

VS Code modernized its internal ChecksumService to utilize the SHA-256 algorithm. This transition is highly relevant to the implementation of a local reconciler. If a generic tool blindly recalculates a SHA-256 hash without simultaneously verifying the underlying semantic content of the file, it effectively weaponizes the strength of the algorithm against the user, providing a false cryptographic seal of approval over potentially compromised or drifted code. The mathematical rigorousness of SHA-256 dictates that even a single altered bit, such as the insertion of a carriage return or a modified CSS class, will radically alter the resulting output.

### The Exact Hashing Pipeline

The precise cryptographic pipeline employed by VS Code to generate the `product.json` checksums involves hashing the raw binary bytes of the target file, encoding the digest, and manipulating the resulting string.

The mathematical and encoding sequence is defined as:
`H_final = StripPadding(Base64(SHA-256(F_bytes)))`

In practical terms, the ChecksumService reads the file stream, processes it through a standard SHA-256 cryptographic function, and outputs the result as a Base64-encoded string. Base64 encoding inherently utilizes padding characters (specifically, the equals sign `=`) at the end of the string to ensure the final output length is a multiple of four bytes. The VS Code implementation deliberately strips this trailing padding.

This specific formatting can be programmatically reproduced in local engineering environments utilizing standard cryptographic tools. For example, within a Bash or PowerShell environment leveraging OpenSSL, the identical checksum can be generated using the following command pipeline:
`openssl dgst -binary -sha256 workbench.html | base64 -w0 | sed 's/=$//'`

### Local Case Analysis and Hash Verification

Applying this understanding to the current local VS Code Insiders build (Version 1.127.0-insider, Commit 628f6de50e89b20c7688c66ac2923cce2862c1b0) allows for a direct verification of the theory. The `product.json` manifest for this specific commit dictates that the `vs/code/electron-browser/workbench/workbench.html` file must possess the checksum `fg2fsFbPwbrb4+QjdKJ8TqaQMi1NaRJFXy7NMSgF9GA6`.

When the Movement 1 architecture initiates the `couture:gate` sequence, the substrate injection scripts append the necessary Chthonic CSS link references into the \`\<head\>`of the`workbench.html`document. This targeted mutation alters the raw bytes of the file. Processing the patched file through the verified SHA-256 Base64-unpadded pipeline yields a new checksum:`sD6Yz99Z54jj5poug5VGh+0T8fDPdxved0ZT3Co0uD4` . As long as the  `product.json`file retains the original hash, the IntegrityService will flag the installation. Updating the`product.json`dictionary to reflect the new`sD6Yz99Z54jj5poug5VGh+0T8fDPdxved0ZT3Co0uD4\` hash fully pacifies the application logic.

## Path Mapping and Architectural Drift in Stable vs. Insiders

A robust integrity reconciliation script cannot rely on static, hardcoded file paths due to the ongoing architectural restructuring within the VS Code codebase. The mapping of application resources under the `resources/app/out` directory differs noticeably between older Stable builds, modern Stable builds, and cutting-edge Insiders releases.

Historically, the primary visual entry point for the editor was located strictly at `vs/code/electron-browser/workbench/workbench.html`. The `product.json` checksums dictionary explicitly tracked this path. However, as Microsoft initiated a broad engineering effort to enhance the security posture of the editor through strict Electron sandboxing, the directory structure began to branch. The execution context for the renderer process was gradually isolated, leading to the introduction of parallel entry points such as `vs/code/electron-sandbox/workbench/workbench.html`.

Furthermore, the transition towards ECMAScript Modules (ESM) to improve loading performance and optimize the dependency graph has introduced entirely new files, such as `vs/code/electron-sandbox/workbench/workbench.esm.html`. A comprehensive reconciliation strategy must proactively account for these variants.

Additionally, the analysis of the local Insiders build reveals that while the Movement 1 patching architecture currently modifies `out/main.js` to facilitate deep substrate hooks, this specific JavaScript file is not universally tracked within the current build's `product.json` checksum dictionary. The IntegrityService only verifies files that are explicitly listed in the manifest. Therefore, while mutating `main.js` carries significant functional implications, it does not currently trigger the corrupt installation warning in this specific build iteration. Nevertheless, a forward-looking implementation must dynamically parse the existing `product.json` keys rather than blindly attempting to update paths that may not be tracked.

## Comparative Analysis of Third-Party Marketplace Reconcilers

The friction generated by the VS Code integrity warning is not a novel problem; the broader developer community has historically relied on UI-altering extensions, custom CSS loaders, and advanced themes to personalize their workspaces. Evaluating the methodologies adopted by these public tools provides critical insights into the limitations of generic solutions and reinforces the necessity for a bespoke, owned implementation.

### The lehni/vscode-fix-checksums Lineage and its Flaws

The most widely recognized utility for addressing the integrity warning is the `lehni/vscode-fix-checksums` extension. Introduced during the peak popularity of deep-customization themes like SynthWave '84, this extension contributes two primary commands to the VS Code command palette: *Fix Checksums: Apply* and *Fix Checksums: Restore*.

The extension operates by executing a Node.js script within the VS Code Extension Host process. When triggered, it reads the modified core files, recalculates their hashes, and overwrites the `product.json` file with the updated values. As VS Code evolved and the internal file paths shifted from `electron-browser` to `electron-sandbox`, the original extension ceased to function correctly on newer builds, leading to a proliferation of derivative forks such as `RimuruChan.vscode-fix-checksums-next` and `iewnfod.vscode-fix-checksums-next-next`. These forks largely maintained the original architecture but updated the target paths to accommodate modern VS Code and alternative distributions like Cursor.

Despite their popularity, these extensions exhibit severe architectural flaws that render them unsuitable for the Movement 1 environment:

1.  **Blind Cryptographic Endorsement:** The most critical failing of these extensions is their total lack of content verification. The scripts do not inspect the syntax, abstract syntax tree (AST), or specific markers within the modified files. They simply read whatever bytes reside on the disk, calculate the hash, and update the manifest. If an unintended process, an errant script, or a malicious actor were to inject a keylogger into `main.js` or `extensionHostProcess.js`, executing the *Fix Checksums: Apply* command would mathematically validate the compromise, permanently blinding the internal security mechanisms.
2.  **Runtime Privilege Escalation Limitations:** Because the logic executes within the context of the VS Code Extension Host, it is subject to the permission model of the operating system governing the application's launch state. On Windows, where the application is typically installed in `%LOCALAPPDATA%` for the current user, this is less problematic. However, on macOS and Linux systems where VS Code is installed globally (e.g., `/Applications/` or `/usr/share/`), the Extension Host lacks the write permissions necessary to alter `product.json`. This results in standard `EACCES: permission denied` errors, forcing users to execute VS Code as a superuser (sudo)—a catastrophic violation of basic security hygiene.
3.  **Lack of Deterministic Automation:** The interactive nature of a Command Palette-driven extension precludes its seamless integration into a headless, automated deployment pipeline. It demands manual human intervention after every software update, destroying the concept of a self-healing engineering substrate.

### The Vibrancy Continued Approach: Acknowledged Drift

An alternative approach is demonstrated by complex visual modifications like the `illixion/vscode-vibrancy-continued` extension. This tool enables hardware-accelerated acrylic and mica materials by injecting custom CSS and JavaScript directly into the `workbench.html` file.

Unlike the checksum-fixing extensions, the authors of Vibrancy Continued explicitly acknowledge the resulting "corrupt installation" warning in their documentation but decline to resolve it programmatically. Instead, the extension provides instructions on how to manually dismiss the prompt using the "Don't Show Again" gear icon, or alternatively, directs users to install a third-party reconciler like `vscode-fix-checksums-next`.

This deferred responsibility is a pragmatic and highly defensible choice for a public marketplace extension. Attempting to programmatically rewrite application manifests across highly fragmented user environments—accounting for arbitrary permission denied errors, locked files, and conflicting modifications from other extensions—is a support nightmare. By opting out of the reconciliation process, Vibrancy Continued maintains a narrower, more stable scope. However, for the Movement 1 architecture, relying on manual user acknowledgment or secondary, blind-patching extensions is incompatible with the objective of a deterministic, zero-friction local substrate.

### Standard Theming Packages

It is crucial to contrast these deep-patching methodologies with conventional color themes, such as `iotacb/vesper-vibrant`. Standard themes operate entirely within the officially supported VS Code Extension API. They contribute declarative JSON configurations to the `workbench.colorCustomizations` and `editor.tokenColorCustomizations` registries. Because they do not mutate the core HTML, CSS, or JavaScript files comprising the application runtime, they never trigger the IntegrityService and exist completely outside the checksum reconciliation domain.

### Table 1: Checksum Reconciliation Methodologies Compared

| Methodology                                   | Content Verification Capability                 | OS Privilege Requirements                             | Automation & CI/CD Compatibility                        | Architectural Substrate Ownership |
| :-------------------------------------------- | :---------------------------------------------- | :---------------------------------------------------- | :------------------------------------------------------ | :-------------------------------- |
| **Integrity Ignore (Manual UI)**              | None                                            | Standard User                                         | None (Manual intervention required per update)          | None                              |
| **lehni/vscode-fix-checksums (and variants)** | None (Blind hash computation and update)        | Often requires elevated/root privileges (macOS/Linux) | Low (Dependent on interactive Extension Host execution) | Reactive / Fragile                |
| **Movement 1 Dedicated Reconciler**           | Strict (AST/Regex marker verification enforced) | Standard User (Local AppData scope on Windows)        | High (Native integration into couture:gate pipeline)    | Authoritative / Deterministic     |

## Windows Authenticode and Secondary Integrity Mechanisms

Before implementing a mechanism that aggressively mutates `product.json`, it is necessary to determine if secondary, OS-level security mechanisms monitor the integrity of the VS Code installation. If a secondary mechanism exists, altering the manifest might trigger a larger failure cascade, such as an OS quarantine or process termination by antivirus software.

### OS-Level Execution Signatures

On the Windows operating system, application binaries (such as `.exe` and `.dll` files) are protected by Authenticode digital signatures. Security features like Windows SmartScreen and AppLocker rely on these cryptographic signatures to verify the publisher's identity and ensure the integrity of the binary payload prior to execution.

However, VS Code is constructed on the Electron framework. The primary executable, `Code - Insiders.exe`, is indeed digitally signed by Microsoft. Yet, the vast majority of the application's actual business logic, UI rendering code, and configuration metadata resides in loosely extracted JavaScript, HTML, and JSON files within the `%LOCALAPPDATA%\Programs\Microsoft VS Code Insiders\resources\app` directory.

Unlike the macOS environment, which employs a rigid application bundle signature (codesign) that recursively hashes all resources and assets contained within the `.app` directory, Windows Authenticode generally does not enforce strict, recursive runtime hashing of loosely extracted asset directories for standard user-mode applications. Modifying `product.json` or `workbench.html` strictly breaks the VS Code *internal* integrity check engineered by the application developers, but it does not invalidate the OS-level digital signature of the `Code - Insiders.exe` binary in a manner that prevents the Windows kernel from executing it. Consequently, there is no secondary, OS-level blocking mechanism to overcome on Windows for this specific patching vector.

### The Ephemeral Nature of product.json

The `product.json` file is intimately coupled to the specific commit hash of the build it accompanies. Every time the VS Code Insiders application performs a background update, the patching engine downloads the differential delta, extracts the new assets, and completely overwrites the `resources/app` directory.

This update process wipes out any local modifications made to `workbench.html`, `main.js`, and `product.json`. This ephemeral nature is, paradoxically, highly advantageous for the Movement 1 architecture. It prevents the possibility of long-term, compounding corruption or the accumulation of obsolete checksums. Each Insiders update acts as a destructive reset, providing a clean slate that forces the deterministic reconciler to execute anew, re-apply the substrate patches, and re-establish the owned integrity state from a verified baseline.

## The Movement 1 Implementation Candidate: Deterministic Reconciliation

To resolve the integrity warning definitively without compromising the security or stability of the local environment, the solution must transition from a reactive workaround to an authoritative, mathematically rigorous build step. The proposed implementation utilizes an external PowerShell script (`scripts/insiders-integrity-reconcile.ps1`) governed by a strict configuration manifest (`manifest/insiders-integrity-reconcile.json`).

### The Strict Allowlist and Verification Logic

The core operational philosophy of the Movement 1 reconciler is that no checksum entry within `product.json` should ever be modified unless the file drift is exclusively, verifiably, and intentionally caused by the Movement 1 architecture. The implementation must adhere to a rigid execution sequence to guarantee this assertion.

1.  **State Initialization and Target Resolution:** The script locates the current Insiders build via the standard Windows local installation path. It reads the active `product.json` payload into memory and parses the checksums dictionary. The script then filters its operational scope against a strictly defined allowlist of potential target files:
    
      * `vs/code/electron-browser/workbench/workbench.html`
      * `vs/code/electron-sandbox/workbench/workbench.html`
      * `vs/code/electron-sandbox/workbench/workbench.esm.html`
        If a modified file is detected that falls outside this allowlist (e.g., `out/main.js` or `extensionHostProcess.js`), the script must explicitly ignore it, preserving the integrity warning for that specific violation.

2.  **Pre-Flight Content Verification (-Verify):** Before any cryptographic recomputation occurs, the script executes a mandatory verification phase. It reads the raw text of the target HTML file and performs a rigid textual or AST-based inspection. It asserts that the specific Chthonic substrate CSS link is present. Crucially, it simultaneously asserts that foreign markers—such as those injected by the Claude Design substrate or Vibrancy Continued—are strictly absent. If a secondary script, such as `scripts/mica-substrate.ps1 -Verify`, reports a failure or detects unauthorized code drift, the reconciler must abort immediately.

3.  **Cryptographic Recomputation and Targeted Mutation (-Apply):** If, and only if, the verification phase yields a perfect pass, the script reads the bytes of the newly patched file and processes them through the SHA-256 Base64-unpadded hashing algorithm. The `product.json` object held in memory is then mutated, altering solely the specific dictionary key that matches the allowlisted path.

4.  **Transactional Commit (-Restore Capability):** Before writing the mutated JSON back to disk, the script generates a backup of the pristine `product.json` (e.g., `product.json.chthonic.bak`). This transactional approach guarantees that the -Restore command can instantly revert the application metadata to its mathematically pure, pre-patch state, enabling rapid debugging and clean updates.

### Integration with the couture:gate Pipeline

By isolating this reconciliation logic into a standalone, headless PowerShell script rather than burying it inside a VS Code Extension Host process, the operation transcends the limitations of the editor's runtime environment. The reconciliation becomes a standard, deterministic CI/CD-style gate.

The execution commands—`integrity-checksum-owned`, `integrity-no-foreign-checksum-drift`, and `integrity-product-json-backup-present`—can be appended directly to the `bun run couture:gate` lifecycle. This pipeline guarantees that if VS Code seamlessly updates in the background overnight, the next initialization of the local development environment will instantly detect the missing substrate, halt execution, re-patch the necessary HTML entry points, execute the strict verifications, and quietly reconcile the checksums before the IDE is fully initialized. This produces a zero-friction, self-healing substrate.

## Risk Modeling: Local Tooling vs. Public Extensions

Implementing an automated integrity reconciler carries distinct technical and policy risks that must be carefully modeled and managed. The architectural viability of this solution hinges heavily on the distinction between private, localized engineering environments and mass-distributed public extensions.

### The Danger of Generic Metadata Drift

The primary technical risk involves the unintentional masking of severe application corruption. If a reconciler were designed with generic parameters—similar to the public `vscode-fix-checksums` utilities—it would silently calculate a new hash for any file that experienced drift. In a scenario where a legitimate software update fails halfway through extracting files, or worse, a malicious background process injects arbitrary code into the VS Code runtime, a generic reconciler would blindly validate the corrupted state. This neutralizes the exact early-warning system that the IntegrityService is designed to provide.

The Movement 1 implementation mitigates this critical risk by explicitly refusing broad reconciliation. By enforcing a highly restrictive allowlist and mandating exact cryptographic marker verification prior to generating a hash, the script guarantees that the internal integrity service continues to function exactly as designed for the remaining 99.9% of the application's core files.

### Marketplace Policy and User Consent

Microsoft maintains stringent policies regarding the behavior of extensions published to the VS Code Marketplace. The official documentation explicitly warns that extensions designed to directly modify or patch the core product files in a semi-permanent manner are unsupported, as they can induce hard-to-reproduce bugs, rendering anomalies, and general application instability. While the marketplace ecosystem has historically tolerated the presence of visual hacking tools like Custom CSS loaders and transparency enablers, extensions that actively suppress security warnings or silently mutate integrity manifests walk an extremely precarious policy line.

For the Movement 1 architecture, this policy distinction defines the operational boundaries of the project. If this patching and reconciliation architecture were ever to be packaged and distributed as a public extension, it would necessitate extensive, explicit user consent dialogs, potential policy waivers, and an exhaustively engineered permission model capable of handling the severe file access restrictions across macOS and Linux environments.

However, because this specific implementation is scoped entirely to local, private engineering tooling, the marketplace policy risk is functionally zero. The execution of the `insiders-integrity-reconcile.ps1` script is a deliberate, deterministic, and highly privileged action executed by the explicit owner of the local development substrate.

## Comprehensive Implementation Test Matrix

To guarantee the robustness and failsafe nature of the `insiders-integrity-reconcile.ps1` implementation, an exhaustive test matrix must be executed across various environmental states. The matrix must empirically validate both the successful reconciliation of authorized modifications and the deliberate, graceful failure (resulting in the preservation of the integrity warning) for unauthorized or malicious modifications.

### Table 2: Deterministic Reconciler Test Matrix

| Test Scenario Context                  | Substrate Configuration State                                      | Expected Reconciler Action (-Apply)                                                                                                | Expected VS Code Startup State                               |
| :------------------------------------- | :----------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------- |
| **Baseline Verification**              | Clean VS Code Insiders install; no HTML modifications.             | \-Verify fails (absence of Chthonic markers). Script exits gracefully without mutating `product.json`.                             | Normal execution; no warning.                                |
| **Authorized Substrate Injection**     | Chthonic CSS properly injected into `workbench.html`.              | \-Verify passes. Script computes SHA-256 hash and targets the allowlisted key. `product.json` is updated.                          | Normal execution; warning successfully suppressed.           |
| **Foreign Drift Detection (Vibrancy)** | Vibrancy Continued CSS injected alongside or instead of Chthonic.  | \-Verify fails (foreign marketplace markers detected). Script halts execution immediately.                                         | **Warning Triggered:** "Installation appears to be corrupt." |
| **Malicious or Unintended Drift**      | Arbitrary modification to `out/main.js` or standard core UI files. | Script ignores modification (target path is not present in the strict allowlist).                                                  | **Warning Triggered:** "Installation appears to be corrupt." |
| **Application Background Update**      | VS Code automatically updates to a new commit hash.                | Substrate and `product.json` wiped. Next `couture:gate` run detects missing substrate and forces a full re-patch and re-reconcile. | Normal execution; clean state re-established.                |
| **Architectural State Reversion**      | The -Restore command is executed manually via PowerShell.          | The `.bak` file replaces the modified `product.json`. HTML patches are stripped.                                                   | Normal execution; pristine state restored.                   |

This test matrix underscores the critical operational importance of testing against continuous application update cycles. Because the Insiders channel is highly volatile, the success of the architecture depends entirely on the `couture:gate` pipeline's ability to seamlessly transition from the "Application Background Update" state back to the "Authorized Substrate Injection" state without requiring manual developer intervention.

## Architectural Recommendations and Conclusion

The deep investigation into the mechanics of VS Code's internal integrity architecture confirms that the "Your Code installation appears to be corrupt" warning is fundamentally a deterministic checksum comparison algorithm relying on a static, localized JSON manifest, rather than an immutable, OS-kernel-enforced digital signature (specifically within the Windows user-mode environment).

The initial working conclusion is validated: abandoning the local substrate patching architecture to appease an internal integrity check is entirely unnecessary and architecturally regressive. The optimal path forward is the immediate deployment of the `insiders-integrity-reconcile.ps1` infrastructure.

To operationalize this conclusion, the engineering focus must center on deploying the deterministic reconciler utilizing the precise SHA-256 Base64-unpadded hashing algorithm required by the ChecksumService. The pre-flight -Verify logic must be engineered to act as an unyielding gatekeeper, utilizing advanced AST parsing or strict regex bounding to guarantee that the HTML modification is exclusively the authorized Chthonic substrate. Any detection of overlapping extensions, such as Vibrancy Continued, or unknown structural elements must instantly halt the reconciliation process.

By aggressively binding this reconciliation script to the `couture:gate` deployment lifecycle, the ephemeral nature of `product.json` during rapid Insiders updates is neutralized. This approach successfully isolates the patching infrastructure from the severe constraints, permission errors, and security vulnerabilities associated with public marketplace extensions. By adopting this heavily guarded, mathematically sound approach to integrity reconciliation, Movement 1 successfully elevates its patching architecture from a fragile visual modification into a stable, highly resilient, native-feeling development environment.

### Referanser

1.  Extensions are not loading · Issue \#206522 · microsoft/vscode - GitHub, <https://github.com/microsoft/vscode/issues/206522>
2.  Hide Claude Opus 4.7 in Model Picker (Unavailable Featured, <https://github.com/microsoft/vscode/issues/312960>
3.  The Ports panel is opening by itself. · Issue \#194694 · microsoft/vscode - GitHub, <https://github.com/microsoft/vscode/issues/194694>
4.  corruption notification doesn't have a "Don't show again button" · Issue \#326 - GitHub, <https://github.com/VSCodium/vscodium/issues/326>
5.  Solution to Pylance not working with VSCodium \#1641 - GitHub, <https://github.com/VSCodium/vscodium/discussions/1641>
6.  VS code(version -1.99) automatically closes after launching · Issue \#245704 · microsoft/vscode - GitHub, <https://github.com/microsoft/vscode/issues/245704>
7.  vscode crashes when delete file with explorer · Issue \#233967 - GitHub, <https://github.com/microsoft/vscode/issues/233967>
8.  lib/vscode/src/vs/platform/checksum/common · v3.11.1 · coder / code-server - GitLab, <https://gitlab.b-data.ch/coder/code-server/-/tree/v3.11.1/lib/vscode/src/vs/platform/checksum/common>
9.  Review new `StorageScope` for application and profile scope · Issue \#152679 · microsoft/vscode - GitHub, <https://github.com/microsoft/vscode/issues/152679>
10. Checksums - Support Documentation, <https://docs.nesi.org.nz/Data_Transfer/Checksums/>
11. When a file is corrupt even a single bit, does the sha256 go partially or completely wrong?, <https://www.reddit.com/r/linuxquestions/comments/1roynef/when_a_file_is_corrupt_even_a_single_bit_does_the/>
12. Does compression change the hash value? - Stack Overflow, <https://stackoverflow.com/questions/40527788/does-compression-change-the-hash-value>
13. how to for vscode terminal padding at bottom - Reddit, <https://www.reddit.com/r/vscode/comments/1r1oxie/how_to_for_vscode_terminal_padding_at_bottom/>
14. lehni/vscode-fix-checksums: A VSCode extension to adjust checksums after changes to core files - GitHub, <https://github.com/lehni/vscode-fix-checksums>
15. Fix VSCode Checksums - Visual Studio Marketplace, <https://marketplace.visualstudio.com/items?itemName=lehni.vscode-fix-checksums>
16. Fix VSCode Checksums Next - Visual Studio Marketplace, <https://marketplace.visualstudio.com/items?itemName=RimuruChan.vscode-fix-checksums-next>
17. Fix VSCode Checksums Next Next - Visual Studio Marketplace, <https://marketplace.visualstudio.com/items?itemName=iewnfod.vscode-fix-checksums-next-next>
18. AI chat panel background uses editor color instead of sidebar color (workaround included), <https://forum.cursor.com/t/ai-chat-panel-background-uses-editor-color-instead-of-sidebar-color-workaround-included/157025>
19. \[Feature\]: Cursor.com compatibillity · Issue \#176 · illixion/vscode-vibrancy-continued, <https://github.com/illixion/vscode-vibrancy-continued/issues/176>
20. Error "An error occurred during execution. Make sure you have write access rights to the VSCode files, see README" \#2 - GitHub, <https://github.com/lehni/vscode-fix-checksums/issues/2>
21. \[Bug\]: EACCES: permission denied · Issue \#39 · illixion/vscode-vibrancy-continued - GitHub, <https://github.com/illixion/vscode-vibrancy-continued/issues/39>
22. GitHub - illixion/vscode-vibrancy-continued: Enable Acrylic/Glass effect for your VS Code., <https://github.com/illixion/vscode-vibrancy-continued>
23. Vibrancy Continued - Visual Studio Marketplace, <https://marketplace.visualstudio.com/items?itemName=illixion.vscode-vibrancy-continued>
24. \[Bug\] Cannot minimize or maximize VSCode on Windows · Issue \#140 - GitHub, <https://github.com/illixion/vscode-vibrancy-continued/issues/140>
25. dnsactivity package - [github.com/synqly/go-sdk/client/engine/ocsf/v100/dnsactivity](https://github.com/synqly/go-sdk/client/engine/ocsf/v100/dnsactivity) - Go Packages, <https://pkg.go.dev/github.com/synqly/go-sdk/client/engine/ocsf/v100/dnsactivity>
26. GR5xx Firmware Encryption Application Note - Goodix, <https://www.goodix.com/en/docview/GR5xx%20Firmware%20Encryption%20Application%20Note?objectId=203&objectType=document&version=372>
27. vscode/build/lib/electron.ts at main - GitHub, <https://github.com/microsoft/vscode/blob/main/build/lib/electron.ts>
28. Podman Desktop 1.25 Release, <https://podman-desktop.io/blog/podman-desktop-release-1.25>
29. How to use python with the Cursor AI IDE - Gist - GitHub, <https://gist.github.com/joeblackwaslike/752b26ce92e3699084e1ecfc790f74b2?permalink_comment_id=5529604>
30. Installation appears to be corrupt \[Unsupported\] - Visual Studio Code - Stack Overflow, <https://stackoverflow.com/questions/61028032/installation-appears-to-be-corrupt-unsupported-visual-studio-code/>
