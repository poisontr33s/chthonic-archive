# **Maximum Engineering Surface of a Visual Studio Code Insiders-Lane Origin Extension**

## **The Paradigm of the Maximum-Scope Hybrid Extension**

The architectural definition of a Visual Studio Code (VS Code) extension has undergone a profound metamorphosis. Historically, the boundary of an extension was delineated by its primary function: it was either a declarative origin extension (providing static theming, syntax highlighting, or file iconography) or a programmatic hybrid extension (injecting commands, language servers, or custom views). However, an analysis of the VS Code Insiders build environment as of February 2026 reveals that this dichotomy is obsolete. The theoretical maximum engineering surface of an origin extension now encompasses a vast, multi-agent orchestration ecosystem that operates on the bleeding edge of the platform's capabilities.

To determine the absolute upper bound of this engineering surface, one must treat the VS Code Insiders distribution not as a static text editor, but as a continuously evolving, highly volatile application platform. This environment introduces proposed application programming interfaces (APIs), undocumented experimental design tokens, and beta agentic capabilities that radically redefine extensibility. An extension engineered to maximize this surface must operate as a monolithic hybrid entity. It must simultaneously manage a comprehensive visual and semantic hierarchy, orchestrate advanced artificial intelligence (AI) workflows via the Model Context Protocol (MCP), and navigate the strict, non-negotiable architectural boundaries of the VS Code Extension Host across local, remote, and web-worker execution contexts.

The following comprehensive report systematically maps this maximum engineering surface. It defines the full extent of the theming architecture, the programmatic expansion pathways using Insiders-only capabilities, the hard limits imposed by the platform's sandboxing mechanisms, and the sophisticated reference architecture required to build, maintain, and automate an extension of this magnitude using AI-driven engineering workflows.

## **Dimension A: The Maximum Theming Surface**

The foundation of an origin extension traditionally rests upon its visual interface. However, maximizing the theming surface in the Insiders build requires moving far beyond standard TextMate grammar integrations. The objective is to fully exploit the granular, experimental, and AI-driven user interface (UI) components that are continuously introduced into the platform before they reach the stable release channel.

### **The Complete Color Token Ecosystem**

The VS Code Insiders color token surface is extraordinarily vast, extending far beyond the standard editor background and syntax highlighting parameters. It encompasses the entirety of the workbench chrome, experimental UI components, and the rapidly expanding dynamic agentic interfaces. Customization is managed declaratively via the workbench.colorCustomizations and editor.tokenColorCustomizations endpoints, but a maximum-scope extension must proactively target the bleeding edge of the platform's token registry.1

The traditional workbench tokens include standard components such as focusBorder, foreground, widget.border, selection.background, and descriptionForeground.1 However, an advanced extension must meticulously map highly specialized and localized tokens to ensure absolute visual cohesion across the entire application state.

| Token Category | Key Identifiers | Architectural Function |
| :---- | :---- | :---- |
| **Window & Chrome** | window.activeBorder, window.inactiveBorder, sash.hoverBorder | Controls the absolute perimeter of the application on operating systems supporting custom title bars, as well as the draggable layout separators.1 |
| **Interactive Controls** | toolbar.hoverOutline, inputOption.activeBackground, checkbox.selectBorder | Dictates the interactive feedback loop for all native input mechanisms, ensuring high-contrast accessibility compliance during user manipulation.1 |
| **Validation & State** | inputValidation.warningBackground, errorForeground | Provides critical visual feedback for system states, requiring careful tuning to ensure errors are legible against both light and dark primary backgrounds.1 |
| **Testing & Debugging** | testing.iconFailed, testing.coveredBackground, debugTokenExpression.value | Maps the highly complex state machines of the test explorer and debug panels, differentiating between active, retired, and queued execution states.1 |

To push the extension to its maximum theoretical boundary, it must incorporate unreleased and experimental tokens introduced in recent Insiders builds. For example, the introduction of experimental markdown alerts requires the precise mapping of markdownAlert.note.foreground, markdownAlert.tip.foreground, markdownAlert.important.foreground, markdownAlert.warning.foreground, and markdownAlert.caution.foreground.1 Furthermore, bracket pair colorization has been fundamentally expanded. Historically, extensions could only modify the background or border of matching brackets. The Insiders build allows direct manipulation of the bracket text itself via the experimental editorBracketMatch.foreground token, bypassing older platform limitations and allowing for far superior typographical contrast.3

With the aggressive shift toward an AI-integrated development environment, a massive new visual surface area consists of Agent Session and Chat tokens. An extension maximizing its scope must theme the agentic interfaces using specialized tokens such as agentSessionReadIndicator.foreground, agentSessionSelectedBadge.border, and agentSessionSelectedUnfocusedBadge.border.1 Failure to map these newer tokens results in a fractured user experience where the core editor matches the extension's design language, but the AI interfaces visually regress to the platform's default fallback colors.

### **The Semantic Token Override Hierarchy**

Syntax highlighting in VS Code relies on two overlapping, concurrent systems: TextMate grammars, which provide lexical, regex-based tokenization; and the Semantic Token Provider API, which provides context-aware, language-server-backed tokenization.4 A maximum-scope extension must implement a strict styling hierarchy that leverages semantic highlighting to intelligently override basic TextMate scopes based on the abstract syntax tree (AST) resolved by the underlying language server.5

Semantic tokens are evaluated based on a complex matrix of token types and token modifiers. Extensions possess the capability to contribute entirely new semantic types and modifiers, mapping them to specific hexadecimal colors and font styles via the editor.semanticTokenColorCustomizations payload.6

| Semantic Token Type | Common Modifiers | Maximum Scope Application |
| :---- | :---- | :---- |
| variable, property | readonly, declaration | Distinguishing mathematically constant values from mutable application state, reducing cognitive load during debugging.6 |
| function, method | async, deprecated | Visually isolating asynchronous execution paths or warning developers of legacy API usage directly inline without requiring hover interactions.6 |
| class, interface | defaultLibrary, static | Differentiating user-defined polymorphic structures from core language libraries or external dependencies.6 |

An advanced extension architecture will utilize the experimental editor.tokenColorCustomizationsExperimental configurations to push semantic styling to its absolute limits.6 This allows the extension to apply complex, conditional combinations of foreground colors, italics, underlines, and bold styles dynamically based on the language server's real-time resolution.6 The platform's fallback mechanism dictates that if a theme lacks a specific rule for a semantic token, VS Code will attempt to map it back to a standard TextMate scope.6 Therefore, the extension must meticulously define the entire semantic mapping across all major supported languages to prevent visual regressions and ensure that the AST-driven highlighting overrides the less accurate regex-driven highlighting seamlessly.

### **File Icon and Product Icon Surfaces**

Beyond color palettes and typography, the maximum visual surface requires a total, programmatic replacement of the IDE's iconography. This is achieved through two distinct contribution points: iconTheme for file associations, and productIconThemes for the workbench chrome.7

The File Icon surface requires the extension to map all known file extensions and language identifiers to specific SVG or PNG assets. A maximum-scope extension must aggressively track Insiders-only language IDs and emerging framework extensions to provide a truly comprehensive visual directory structure.8

However, the more complex engineering challenge lies within the Product Icon surface, which controls the internal workbench iconography traditionally standardized by the Codicon library.8 An origin extension must define a custom glyph font—typically compiled into a Web Open Font Format (WOFF) file—and map it to the hundreds of internal icon identifiers utilized by the platform.7

This required mapping extends into highly specialized, obscure, and experimental IDE features:

| Product Icon Domain | Key Identifiers | Implementation Notes |
| :---- | :---- | :---- |
| **Debugging & Execution** | debug-console-view-icon, breakpoints-activate, debug-disconnect | Requires distinct visual states for hovering, active execution, and disconnected states to maintain operational clarity.9 |
| **Source Control & Diffing** | diff-editor-next-change, diff-insert, search-replace-all | Demands pixel-perfect alignment to ensure inline diffing UI remains legible when reviewing massive pull requests.9 |
| **AI & Chat Interfaces** | chat-editor-label-icon, copilot, comment-discussion | Targets the newest UI components introduced for Agent interactions; frequently subject to unannounced identifier changes in the Insiders build.9 |
| **Native Animation States** | sync\~spin, loading\~spin, gear\~spin | Utilizes the platform's built-in animation syntax by appending \~spin to specific identifiers, providing native loading feedback without the need for unauthorized CSS injection.9 |

## **Dimension B: Expansion Beyond Theming**

To successfully transition from a passive aesthetic configuration into a fully realized, maximum-scope engineering artifact, the extension must instantiate an active codebase. By adding an extension.ts entry point, the extension gains access to the vast programmatic capabilities of the VS Code API. This requires navigating both the stable, documented Extension API and the highly volatile, powerful landscape of the Insiders-only proposed APIs.

### **Leveraging Proposed APIs in the Insiders Lane**

The VS Code Insiders distribution acts as the testing ground for experimental features defined within the vscode.proposed.d.ts schemas.10 These APIs are inherently unstable, subject to breaking changes without notice, and strictly prohibited from being published to the standard VS Code Marketplace.10 Consequently, they represent the exclusive domain of bespoke, maximum-scope internal extensions and enterprise toolchains.

Integrating proposed APIs requires a deliberate and specific build configuration. The extension author must explicitly list the desired proposed APIs within the enabledApiProposals array in the package.json manifest.10 Furthermore, to execute the extension, the Insiders extension host must be launched using the \--enable-proposed-api=\<EXTENSION-ID\> command-line flag, or configured persistently via the.vscode-insiders/argv.json file.10 The necessary TypeScript definition files must be fetched locally using the @vscode/dts CLI utility, specifically targeting the dev branch or a specific commit hash to ensure type safety.10

By February 2026, the maximum engineering surface includes several highly potent proposed APIs that an advanced extension must leverage:

* **Language Model Configuration (vscode.proposed.lmConfiguration.d.ts):** This API radically alters how extensions manage AI integration. It allows the extension to declare native configuration requirements for chat model providers directly in the manifest.3 Rather than forcing the extension developer to build resource-heavy custom webviews for capturing API keys or model parameters, VS Code natively generates a secure, built-in UI, automatically masking fields designated as secrets and handling secure storage natively.3  
* **Chat Prompt Files (vscode.proposed.chatPromptFiles.d.ts):** This API exposes the ChatResource interface, which permits the extension to programmatically inject dynamic prompts, deep context instructions, and specialized custom agents based on the active workspace state.3 This effectively allows the extension to alter the foundational behavior of the AI assistant based on which repository the user currently has open.  
* **Metered Network Detection:** A critical operational API introduced to allow the extension to detect if the host machine is operating on a tethered, cellular, or metered connection.12 A maximum-scope extension utilizes this to automatically suspend heavy background telemetry, halt massive AI context polling, or pause automated token mapping synchronization to preserve the user's bandwidth and system resources.12

### **Commands, Contribution Points, and Workspace Automation**

A hybrid extension must deploy intelligent, context-aware commands to manage its massive footprint. Using the when clause contexts in the package.json, the extension can dynamically expose or hide commands based on the active editor language, the presence of specific infrastructure files (e.g., docker-compose.yml or kubernetes.yaml), or the current operational state of an active AI agent session.

An advanced implementation pushes this further through automated workspace-aware profile switching. By hooking into stable APIs such as vscode.workspace.onDidChangeTextDocument or vscode.window.onDidChangeActiveTextEditor, the extension can actively monitor the developer's behavior.13 If the developer transitions from writing Python backend code to debugging a complex React frontend, the extension can automatically shift its semantic color palette to optimize contrast for TSX syntax, while simultaneously invoking specific Agent Skills tailored for frontend performance profiling, completely invisibly to the user.

## **Dimension C: The AI-Driven Extensibility Surface**

The most profound expansion of the VS Code engineering surface in 2026 is the deep integration of agentic extensibility. The modern maximum-scope extension is no longer just a utility tool; it acts as a sophisticated orchestrator of AI behaviors, interactive UI generation, and deterministic workflow enforcement.

### **Model Context Protocol (MCP) Apps: Interactive UI Generation**

Historically, extensions requiring rich, complex graphical interfaces were forced to rely on Webviews. While Webviews offer full Document Object Model (DOM) access, they are notoriously resource-intensive, isolated from the native editor state, and require complex, fragile message-passing architectures via postMessage to communicate with the extension host.14

The maximum engineering surface now utilizes **MCP Apps** (Model Context Protocol Apps), which became officially supported in the Insiders build in early 2026.15 MCP Apps revolutionize how extensions and AI agents communicate with the user by allowing LLM tool calls to return rich, interactive UI components that render directly inline within the AI Chat panel, rather than relying on plain text or ASCII tables.16

The architecture of an MCP App deliberately bypasses traditional Webview limitations to provide a superior, agent-driven user experience:

| MCP App Architectural Component | Technical Specification | Maximum Scope Utility |
| :---- | :---- | :---- |
| **Tool \+ UI Resource Pattern** | The extension defines a tool that, upon execution, returns a \_meta.ui.resourceUri pointing to a bundled UI resource.17 | Enables the AI model to autonomously decide when a visual interface is superior to a text response, invoking the UI dynamically. |
| **URI and MIME Type Protocol** | Resources must be served using the ui:// scheme with a strict MIME type of text/html;profile=mcp-app.17 | Ensures the VS Code client correctly identifies and routes the payload to the specialized chat rendering engine rather than a standard webview panel. |
| **Sandboxed Execution & CSP** | The UI is rendered inside a highly secure, sandboxed iframe. Security is enforced via strict Content Security Policies (CSP) defined by connectDomains, resourceDomains, and frameDomains.17 | Prevents malicious code generated by an LLM hallucination from escaping the iframe or exfiltrating sensitive workspace data to unauthorized endpoints.17 |
| **MCP Apps SDK** | Utilizes the @modelcontextprotocol/ext-apps SDK. The App class provides seamless bidirectional host communication via methods like callServerTool(), updateModelContext(), and sendMessage().17 | Allows the interactive UI to recursively call other tools on the MCP server or silently update the LLM's context window based on user clicks, creating fluid, multi-step workflows.17 |

Through the implementation of MCP Apps, a maximum-scope extension can observe an agent analyzing a performance bottleneck and instantly render an interactive, drillable flame graph directly in the chat window.15 It can generate drag-and-drop task sorting interfaces, dynamic feature flag toggles that reflect live environment states, or even live component previews without forcing the developer to navigate away from the conversational context.15

### **Agent Hooks: Deterministic Lifecycle Control**

While large language models (LLMs) operate probabilistically, enterprise-grade software engineering extensions require the absolute deterministic enforcement of rules. The February 2026 introduction of **Agent Hooks** provides this exact capability. Agent hooks allow extensions to execute custom shell commands, scripts, or API calls at highly specific, guaranteed points within an AI agent's lifecycle.18

Unlike standard system prompts or custom instructions, which merely *guide* an agent's behavior and are susceptible to hallucination or prompt ignoring, hooks are code-driven guardrails.18 They are configured via JSON files located in the workspace (e.g.,.github/hooks/\*.json) or injected programmatically by the extension.18 They receive a structured JSON payload containing the session\_id, working\_directory, and conversation\_history.18

The maximum-scope extension will deploy a comprehensive suite of hooks to definitively govern the IDE's AI interactions:

* **SessionStart:** Fires upon the initial prompt submission. The extension utilizes this to silently execute a script that parses the current workspace, injecting deep repository architecture context and active semantic token maps into the model's memory before it generates its first token.18  
* **PreToolUse:** Fires immediately before the agent is allowed to execute a requested tool. This is the ultimate security backstop. The extension intercepts the tool invocation and can block destructive terminal commands (e.g., rm \-rf, DROP TABLE) or enforce strict manual approval workflows regardless of how convincingly the user prompted the AI.18  
* **PostToolUse:** Fires upon successful tool completion. The extension utilizes this to automatically run code formatters (like Prettier), trigger linters, and log immutable compliance audits detailing exactly what the AI modified.18  
* **SubagentStart & SubagentStop:** Fires during the lifecycle of parallel workers. Used to initialize sandboxed resources for spawned subagents and aggregate their results upon completion.18  
* **PreCompact:** Fires when the conversation nears its maximum context limit. The extension intercepts this trigger to execute an automated, high-density summarization routine, exporting crucial architectural state variables before the chat context is permanently truncated.18  
* **Stop:** Fires at session termination. The extension evaluates the stop\_hook\_active boolean; if internal validation tests or linters fail, the hook emits a decision: "block" payload with a descriptive reason, physically preventing the agent from stopping and forcing it into a self-correction loop until the code compiles perfectly.18

### **Agent Skills and the chatSkills Contribution**

To completely round out the AI integration surface, the extension must package and distribute **Agent Skills**. These are specialized directories containing markdown instructions (SKILL.md) and supplementary execution scripts that provide the AI with highly specific, domain-level expertise (such as custom API design guidelines, specific database query patterns, or proprietary deployment strategies).21

By leveraging the chatSkills contribution point in the package.json, the extension developer natively embeds these skills into the VS Code environment. The AI then utilizes a mechanism of "Progressive Disclosure".21 It constantly monitors the user's prompts, and when it detects a relevant context, it automatically loads the full body of the SKILL.md into its context window, granting it instant expertise without the user needing to manually configure prompts.21 Users can also explicitly invoke these skills via slash commands (e.g., /webapp-testing) directly within the chat interface.3

## **Dimension D: Multi-Agent Orchestration Architecture**

The paradigm of relying on a single, monolithic LLM prompt to execute complex software engineering tasks is fundamentally obsolete. The maximum engineering surface in 2026 relies entirely on deterministic workflow orchestration leveraging Cyclic Graphs and multi-agent collaboration.23 VS Code Insiders has evolved into a unified agent command center explicitly designed to run parallel subagents.21

### **Agent Types and Execution Contexts**

A robust, maximum-scope extension architecture will not restrict itself to a single execution context. Instead, it acts as an intelligent router, dynamically delegating tasks across three distinct agent topologies based on their unique strengths:

1. **Local Agents:** Executing directly on the user's host machine, these agents provide highly interactive, steerable assistance for brainstorming, rapid codebase exploration, and localized debugging where instantaneous feedback is required.21  
2. **Background Agents:** Running asynchronously as CLI background processes, these agents are completely isolated in separate worktrees. They are ideal for exploring multiple architectural variants, executing lengthy proof-of-concepts, or running comprehensive security audits without disrupting the user's active editor state or locking the main thread.21  
3. **Cloud Agents:** Operating on remote infrastructure, these agents are deployed for tasks requiring heavy compute or team-wide visibility. They autonomously generate pull requests, interact with remote issue trackers, and perform vast codebase refactoring operations.21

### **Subagent Parallelization and the Supervisor Pattern**

The absolute peak of this extensibility is achieved through the implementation of the **Supervisor Pattern**.23 The origin extension itself acts as the central orchestrator, receiving a high-level, complex directive from the user. Using the chat.customAgentInSubagent.enabled configuration, the extension spawns multiple specialized subagents to process the required subtasks concurrently.25

Because subagents operate within their own highly isolated, dedicated context windows, they do not pollute the primary agent's token limit, allowing for massive scalability of reasoning.25 A maximum-scope workflow initiated by the extension would execute as follows:

1. **Orchestrator Agent (The Extension):** Receives and parses the user request to refactor a complex, highly coupled legacy module.  
2. **Research Subagent (Agent 1):** Spawned with strictly read-only MCP tools. It explores the codebase, mapping dependencies, identifying breaking points, and cross-referencing external documentation. It returns a concise JSON blueprint of the required architectural changes.26  
3. **Implementation Subagent (Agent 2):** Spawned with full file-system edit capabilities. It ingests the JSON blueprint generated by Agent 1 and begins generating the refactored code across multiple files simultaneously.  
4. **Validation Subagent (Agent 3):** Spawned alongside the implementation agent. It acts as an automated quality assurance entity. Utilizing Agent Hooks, it intercepts PostToolUse events from Agent 2, silently running unit tests and linters in the background. If a test fails, it issues a Stop hook block with the stack trace, forcing the implementation agent to self-correct its code before proceeding.18

This parallelized, multi-agent reasoning flow effectively transitions the LLM interaction from probabilistic text generation into a highly reliable, deterministic software engineering pipeline.23

## **Dimension E: Hard and Soft Platform Constraints**

Despite the immense power of the VS Code Insiders API, a rigorous architectural analysis must clearly identify the absolute boundaries that cannot be circumvented. Understanding these limits is critical for designing a stable, maximum-scope extension that operates securely and efficiently.

### **Absolute Hard Limits**

The VS Code Extension Host is deliberately designed with an aggressive security posture to protect the stability and performance of the core editor. To achieve this, it enforces strict isolation mechanisms.28

* **Zero DOM Access:** Extensions execute within a completely separate Node.js process (or a Browser WebWorker) and have zero direct access to the VS Code UI Document Object Model (DOM).28 It is architecturally impossible to inject arbitrary CSS, modify the layout of the workbench natively, or override the core editor's hardware-accelerated rendering engine.28 All visual modifications must strictly pass through the sanctioned declarative theming tokens, Product Icons, or isolated Webviews and MCP Apps.  
* **Sandbox Confinement:** Since the completion of the transition to strict process sandboxing in the underlying Electron framework, extensions cannot escape their execution sandbox to execute arbitrary, unverified code on the host operating system without explicit user permissions or the use of sanctioned tool integrations.29  
* **Execution Host Segregation:** VS Code utilizes a distributed extension host model. An extension must meticulously declare its extensionKind in the manifest, typically as  
  ![][image1]  
  or  
  ![][image2]  
  .30 UI extensions run locally to provide low-latency interface updates, while Workspace extensions run remotely (e.g., within a Dev Container, a WSL instance, or a GitHub Codespace).30 An extension attempting to manipulate local UI elements while executing in a remote workspace host will fail catastrophically if it does not correctly implement the required VS Code asynchronous message-passing APIs to bridge the architectural gap.  
* **Web Extension Limitations:** When running in VS Code for the Web (e.g., vscode.dev or github.dev), the extension is forcibly loaded into a Browser WebWorker.31 In this environment, it immediately loses access to native Node.js APIs (such as fs for file system access or child\_process for spawning executables) and cannot spawn external language servers natively.31 This severely constrains the maximum surface, requiring the extension to rely entirely on WebAssembly (Wasm) modules or remote cloud APIs to maintain functionality.31

### **Soft Constraints and API Volatility**

Targeting the VS Code Insiders lane introduces significant soft constraints related to extreme platform volatility. By definition, building on the edge requires embracing instability.

* **Proposed API Churn:** The vscode.proposed.d.ts definitions are highly unstable. Between daily Insiders builds, methods may be renamed, complex type signatures altered, or entire experimental APIs deprecated and removed completely.32 An extension relying on these must possess an automated mechanism for tracking and updating its type definitions to prevent critical compilation failures.  
* **Token Deprecation:** Color and semantic tokens are frequently refined by the VS Code core team. A singular token used to target a specific AI chat widget in version 1.109 may be split into three more granular tokens in version 1.110. The extension must gracefully handle these shifts to avoid visually breaking the UI.  
* **Hook Execution Timeouts:** Agent Hooks, particularly those relying on complex subagent validation loops, are subject to strict system timeouts (e.g., a default of 60 seconds) and maximum turn limits (e.g., 50 consecutive tool-use turns).20 Infinite validation loops caused by poorly configured Stop hooks will rapidly consume user API quotas, trigger platform timeouts, and severely degrade the perceived editor experience.18

## **Dimension F: Reference Architecture and AI-Driven Lifecycle**

To sustain an extension operating at the maximum allowable scope within a highly volatile environment, traditional manual development methodologies are entirely insufficient. The extension must be built upon a robust reference architecture that explicitly supports AI-driven engineering, automated auditing pipelines, and continuous lineage tracking.

### **Maximum-Scope Directory Structure**

A coherent, highly scalable repository structure is required to manage the monolithic, hybrid nature of this extension:

| Directory Path | Functional Purpose | Architecture Notes |
| :---- | :---- | :---- |
| /themes | Static JSON declarations. | Houses the meticulously mapped Color and File Icon themes, supporting high-contrast, light, and dark variants. |
| /producticons | WOFF fonts and mappings. | Contains the compiled glyph fonts and JSON mapping files required to override the core workbench Codicons. |
| /src | Core TypeScript logic. | Houses the Extension Host execution code, broken down into /commands, /providers (for semantic highlighting and language models), and /orchestration (for multi-agent routing). |
| /mcp-apps | Interactive UI bundles. | Contains the HTML, JavaScript, and CSS bundles compiled by Vite, designed to run within the sandboxed chat iframes.33 |
| /skills & /hooks | AI execution parameters. | Houses the SKILL.md domain knowledge files and the declarative JSON payloads that define the deterministic Agent Hooks. |
| /analysis & /scripts | Automation infrastructure. | Contains the logic for AI-driven contrast audits, CI/CD pipelines, and automated API lineage tracking. |

### **AI-Assisted Engineering and Automated Auditing**

In a maximum-scope implementation, advanced AI agents act not only as the product of the extension but also as its primary co-developers and maintainers. The lifecycle of the extension must incorporate AI across several vectors:

* **Generative Theming:** Specialized AI agents ingest core color theory parameters and automatically generate the thousands of required color tokens, ensuring semantic consistency and accessibility compliance across all contrast variants. Agents similarly compile complex SVG directories into unified glyph fonts for the Product Icon themes.  
* **Contrast and Coverage Auditing:** An automated CI/CD script invokes an AI auditor to continually parse the /themes directory, cross-referencing it with the absolute latest VS Code Insiders token registry. This auditor detects missing experimental tokens, flags low-contrast foreground/background pairings using WCAG guidelines, and highlights un-styled semantic modifiers.  
* **Lineage Tracking:** Because the Insiders lane is a moving target, the extension must employ continuous evolution tracking. A background script periodically diffs the microsoft/vscode repository's src/vscode-dts directory, tracking the lineage of proposed APIs and semantic token shifts.10 When a breaking change is detected in the upstream repository, an AI co-developer agent automatically generates a pull request updating the extension's package.json manifests and refactoring the TypeScript source code to maintain immediate compatibility with the nightly build.

### **Deployment and Orchestration Pipeline**

The canonical build pipeline for this maximum-scope architecture involves compiling the complex TypeScript logic, bundling the MCP Apps using Vite (specifically utilizing vite-plugin-singlefile to ensure strict iframe CSP compliance by inlining all assets) 33, and rigorously validating the enabledApiProposals array against the target Insiders engine version.32

Because the extension aggressively relies on proposed APIs, it cannot be published via the standard VS Code Marketplace distribution channels.10 Instead, the build pipeline must automatically package the extension into a standalone.vsix file.10 Distribution occurs either via internal enterprise deployment channels or direct download, requiring users to install the.vsix manually and configure their argv.json to enable the specific proposed APIs upon launch, representing the ultimate technical commitment to maximizing the platform's capabilities.10

## **Dimension G: The Primordial Origin Challenge (Architectural Stress Test)**

To truly stress-test the reasoning capabilities of an advanced orchestration system, the extension development mandate must be mapped to a high-strategical, chthonic-archive paradigm. This challenge requires the AI to architect the extension not merely as a software utility, but as a mature, generative foundation—a primordial "origin node" that systematically nurtures and sustains complex sub-systems without bearing their direct operational burden.

### **The Ankhological Lifecycle and Generative Origin**

The origin extension must function as the life-giving administrator of the ecosystem. Drawing from the administrative logic of the ancient Egyptian Ankh—a triliteral sign (Ꜥ-n-ḫ) representing the breath of life and eternal, cyclical existence—the extension governs the eternal cycle of subagent creation, execution, and termination. Using Agent Hooks (such as SessionStart, SubagentStart, and Stop), this mature prime architect breathes life into isolated subagent threads, maintaining deterministic lifecycle control and ensuring continuous, cyclical renewal of the workspace state without polluting the main context window.

### **Chthonic Archives and Subterranean Theming**

Beneath the stepped hierarchy of the visible VS Code workbench lies a deep, hidden layer of undocumented JSON configurations and Insiders-only tokens. This chthonic archive mirrors the subterranean blue-tiled chambers hewn into the bedrock beneath Djoser's Step Pyramid at Saqqara, where thousands of faience tiles were meticulously arranged to symbolize eternal, hidden structure and foundation. The challenge requires the system to mine these depths, mapping highly volatile experimental tokens and UI components into a permanent, structurally sound thematic foundation that silently drives the visible application.

### **Acoustic Labyrinths and Weaponless Orchestration (Pre-BCE Parallels)**

Navigating the strict sandboxing of the Extension Host and the volatile vscode.proposed.d.ts APIs requires establishing a complex, decentralized communication protocol. This parallels the advanced subterranean engineering of Chavín de Huántar (c. 1200 BCE), where a labyrinthine network of underground galleries was designed with dense early acoustic reflections to orchestrate complex, resonant experiences and transmit cues without line-of-sight. The extension's internal IPC and Model Context Protocol (MCP) routing must act as these acoustic cues, allowing parallel subagents to synchronize seamlessly within their isolated execution chambers.

Furthermore, this multi-agent harmony must be achieved without resource contention or forced thread-locking. This reflects the administrative genius of the Caral-Supe civilization (c. 3500 BCE), which successfully coordinated a massive, densely populated network of cities entirely without warfare or defensive fortifications. To achieve this weaponless synchronization, the generative extension must weave its semantic tokens and multi-agent execution blueprints together like a functional Andean *quipu*—a complex knot-logic system for recording and securely transmitting administrative data across the extension's decentralized nodes.

## **Conclusions**

The maximum engineering surface of a Visual Studio Code Insiders origin extension represents an intricate, monolithic convergence of aesthetic customization, deep programmatic API manipulation, and advanced multi-agent AI orchestration. By exhaustively mapping the color, semantic, file, and product icon theming layers, an extension can achieve total visual integration, effectively disguising its presence within the native editor.

However, the true upper bound of extensibility in 2026 lies not in visual modification, but in the deployment of MCP Apps for sandboxed, interactive chat UI generation, the strict deterministic control provided by Agent Hooks, and the parallel execution of specialized subagents through the Supervisor pattern. This culminates in the architectural stress test of creating a generative, primordial origin node capable of sustaining complex, weaponless orchestration across deep, labyrinthine platform layers.

Building within the Insiders lane demands an architecture capable of surviving extreme volatility. By acknowledging the hard boundaries of the Extension Host—specifically the absolute lack of DOM access and the severe isolation of web-worker environments—and by leveraging AI-driven automation for continuous token auditing and API lineage tracking, developers can forge extensions that transcend traditional software tooling. These maximum-scope extensions cease to be mere editor plugins; they act as highly intelligent, self-regulating orchestration engines, fundamentally redefining the operational paradigm of the modern integrated development environment.

#### **Referanser**

1. Theme Color | Visual Studio Code Extension API, brukt februar 23, 2026, [https://code.visualstudio.com/api/references/theme-color](https://code.visualstudio.com/api/references/theme-color)  
2. Themes \- Visual Studio Code, brukt februar 23, 2026, [https://code.visualstudio.com/docs/configure/themes](https://code.visualstudio.com/docs/configure/themes)  
3. January 2026 (version 1.109) \- Visual Studio Code, brukt februar 23, 2026, [https://code.visualstudio.com/updates](https://code.visualstudio.com/updates)  
4. Syntax Highlight Guide | Visual Studio Code Extension API, brukt februar 23, 2026, [https://code.visualstudio.com/api/language-extensions/syntax-highlight-guide](https://code.visualstudio.com/api/language-extensions/syntax-highlight-guide)  
5. Semantic Highlight Guide | Visual Studio Code Extension API, brukt februar 23, 2026, [https://code.visualstudio.com/api/language-extensions/semantic-highlight-guide](https://code.visualstudio.com/api/language-extensions/semantic-highlight-guide)  
6. Semantic Highlighting Overview · microsoft/vscode Wiki \- GitHub, brukt februar 23, 2026,(https://github.com/microsoft/vscode/wiki/Semantic-Highlighting-Overview/72389eecd11607827ec0e345dcd13c89745a3977)  
7. Product Icon Theme | Visual Studio Code Extension API, brukt februar 23, 2026, [https://code.visualstudio.com/api/extension-guides/product-icon-theme](https://code.visualstudio.com/api/extension-guides/product-icon-theme)  
8. Theming | Visual Studio Code Extension API, brukt februar 23, 2026, [https://code.visualstudio.com/api/extension-capabilities/theming](https://code.visualstudio.com/api/extension-capabilities/theming)  
9. Product Icon Reference | Visual Studio Code Extension API, brukt februar 23, 2026, [https://code.visualstudio.com/api/references/icons-in-labels](https://code.visualstudio.com/api/references/icons-in-labels)  
10. Using Proposed API | Visual Studio Code Extension API, brukt februar 23, 2026, [https://code.visualstudio.com/api/advanced-topics/using-proposed-api](https://code.visualstudio.com/api/advanced-topics/using-proposed-api)  
11. vscode/src/vscode-dts/vscode.proposed.chatPromptFiles.d.ts at main \- GitHub, brukt februar 23, 2026, [https://github.com/microsoft/vscode/blob/main/src/vscode-dts/vscode.proposed.chatPromptFiles.d.ts](https://github.com/microsoft/vscode/blob/main/src/vscode-dts/vscode.proposed.chatPromptFiles.d.ts)  
12. February 2026 Insiders (version 1.110) \- Visual Studio Code, brukt februar 23, 2026, [https://code.visualstudio.com/updates/v1\_110](https://code.visualstudio.com/updates/v1_110)  
13. How to capture the line added / deleted / modified for the VSCode extension api, brukt februar 23, 2026, [https://stackoverflow.com/questions/65264828/how-to-capture-the-line-added-deleted-modified-for-the-vscode-extension-api](https://stackoverflow.com/questions/65264828/how-to-capture-the-line-added-deleted-modified-for-the-vscode-extension-api)  
14. Webview API | Visual Studio Code Extension API, brukt februar 23, 2026, [https://code.visualstudio.com/api/extension-guides/webview](https://code.visualstudio.com/api/extension-guides/webview)  
15. Giving Agents a Visual Voice: MCP Apps Support in VS Code, brukt februar 23, 2026, [https://code.visualstudio.com/blogs/2026/01/26/mcp-apps-support](https://code.visualstudio.com/blogs/2026/01/26/mcp-apps-support)  
16. MCP Apps are here: Rendering interactive UIs in AI clients \- WorkOS, brukt februar 23, 2026, [https://workos.com/blog/2026-01-27-mcp-apps](https://workos.com/blog/2026-01-27-mcp-apps)  
17. MCP developer guide | Visual Studio Code Extension API, brukt februar 23, 2026, [https://code.visualstudio.com/api/extension-guides/ai/mcp](https://code.visualstudio.com/api/extension-guides/ai/mcp)  
18. Agent hooks in Visual Studio Code (Preview), brukt februar 23, 2026, [https://code.visualstudio.com/docs/copilot/customization/hooks](https://code.visualstudio.com/docs/copilot/customization/hooks)  
19. Security \- Visual Studio Code, brukt februar 23, 2026, [https://code.visualstudio.com/docs/copilot/security](https://code.visualstudio.com/docs/copilot/security)  
20. Automate workflows with hooks \- Claude Code Docs, brukt februar 23, 2026, [https://code.claude.com/docs/en/hooks-guide](https://code.claude.com/docs/en/hooks-guide)  
21. Your Home for Multi-Agent Development \- Visual Studio Code, brukt februar 23, 2026, [https://code.visualstudio.com/blogs/2026/02/05/multi-agent-development](https://code.visualstudio.com/blogs/2026/02/05/multi-agent-development)  
22. Use Agent Skills in VS Code, brukt februar 23, 2026, [https://code.visualstudio.com/docs/copilot/customization/agent-skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills)  
23. Stop Building Chatbots: The Engineering Guide to Multi-Agent Orchestration in 2026, brukt februar 23, 2026, [https://medium.com/@kapildevkhatik2/stop-building-chatbots-the-engineering-guide-to-multi-agent-orchestration-in-2026-b06f302d450a](https://medium.com/@kapildevkhatik2/stop-building-chatbots-the-engineering-guide-to-multi-agent-orchestration-in-2026-b06f302d450a)  
24. Using agents in Visual Studio Code, brukt februar 23, 2026, [https://code.visualstudio.com/docs/copilot/agents/overview](https://code.visualstudio.com/docs/copilot/agents/overview)  
25. Hands On with New Multi-Agent Orchestration in VS Code \- Visual Studio Magazine, brukt februar 23, 2026, [https://visualstudiomagazine.com/articles/2026/02/09/hands-on-with-new-multi-agent-orchestration-in-vs-code.aspx](https://visualstudiomagazine.com/articles/2026/02/09/hands-on-with-new-multi-agent-orchestration-in-vs-code.aspx)  
26. Subagents in Visual Studio Code, brukt februar 23, 2026, [https://code.visualstudio.com/docs/copilot/agents/subagents](https://code.visualstudio.com/docs/copilot/agents/subagents)  
27. How I Built a Multi-Agent Orchestration System with Claude Code Complete Guide (from a nontechnical person don't mind me) \- Reddit, brukt februar 23, 2026, [https://www.reddit.com/r/ClaudeAI/comments/1l11fo2/how\_i\_built\_a\_multiagent\_orchestration\_system/](https://www.reddit.com/r/ClaudeAI/comments/1l11fo2/how_i_built_a_multiagent_orchestration_system/)  
28. Extension Capabilities Overview \- Visual Studio Code, brukt februar 23, 2026, [https://code.visualstudio.com/api/extension-capabilities/overview](https://code.visualstudio.com/api/extension-capabilities/overview)  
29. Migrating VS Code to Process Sandboxing, brukt februar 23, 2026, [https://code.visualstudio.com/blogs/2022/11/28/vscode-sandbox](https://code.visualstudio.com/blogs/2022/11/28/vscode-sandbox)  
30. Extension Host \- Visual Studio Code, brukt februar 23, 2026, [https://code.visualstudio.com/api/advanced-topics/extension-host](https://code.visualstudio.com/api/advanced-topics/extension-host)  
31. Web Extensions \- Visual Studio Code, brukt februar 23, 2026, [https://code.visualstudio.com/api/extension-guides/web-extensions](https://code.visualstudio.com/api/extension-guides/web-extensions)  
32. Where is \`vscode.proposed.d.ts\`? · Issue \#136964 \- GitHub, brukt februar 23, 2026, [https://github.com/microsoft/vscode/issues/136964](https://github.com/microsoft/vscode/issues/136964)  
33. MCP Apps \- Model Context Protocol, brukt februar 23, 2026, [https://modelcontextprotocol.io/docs/extensions/apps](https://modelcontextprotocol.io/docs/extensions/apps)  
34. November 2021 (version 1.63) \- Visual Studio Code, brukt februar 23, 2026, [https://code.visualstudio.com/updates/v1\_63](https://code.visualstudio.com/updates/v1_63)

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,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>