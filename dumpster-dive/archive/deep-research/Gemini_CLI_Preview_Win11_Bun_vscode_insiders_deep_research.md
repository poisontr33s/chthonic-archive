# **Definitive Guide to Architecting the Gemini CLI on Windows 11 with Bun and MCP**

## **1\. Executive Summary and Architectural Philosophy**

The integration of Large Language Model (LLM) agents into the command-line interface (CLI) represents a fundamental shift in software engineering workflows. Moving beyond the constraints of chat-based web interfaces, the CLI agent offers direct access to the developer's filesystem, build tools, and version control systems, effectively closing the loop between reasoning and execution. This report provides an exhaustive, expert-level analysis and implementation plan for deploying the Google Gemini CLI within a high-performance Windows 11 environment.

The architecture detailed herein is specific and non-trivial: it leverages the **Bun runtime** for superior execution speed, **PowerShell 7.x** for advanced scripting capabilities, and the **Model Context Protocol (MCP)** for standardized interoperability with external systems, specifically GitHub. The target environment—Windows 11 running Visual Studio Code (VS Code) Insiders—presents unique challenges regarding character encoding, terminal emulation, and process management. Addressing these challenges requires a rigorous, "zero redundancy" approach to configuration, ensuring that every setting is defined at the optimal level of the abstraction hierarchy to maximize efficiency and minimize maintenance overhead.

The core philosophy driving this implementation is **latency reduction and context optimization**. By selecting Bun over Node.js, we aim to eliminate the Just-In-Time (JIT) compilation overhead associated with V8, thereby making the agent's startup time imperceptible.1 By utilizing the remote GitHub MCP server via HTTP, we offload the computational cost of local containerization, leveraging GitHub's hosted infrastructure for semantic code search and repository management.3 This report serves as the definitive manual for establishing this sophisticated environment.

## **2\. The Computational Substrate: Bun Runtime on Windows**

To understand the necessity of the specific configurations detailed later in this report, one must first appreciate the underlying mechanics of the chosen runtime environment. The user has correctly identified Bun as the preferred execution engine, a choice that necessitates a deviation from standard Node.js-based instructions.

### **2.1. The Architecture of Bun vs. Node.js**

The Gemini CLI is written in TypeScript/JavaScript, typically targeting the Node.js runtime. Node.js is built on Google's V8 engine, which is optimized for long-running server processes. In a server context, the initial "warm-up" period—where the engine parses JavaScript, generates bytecode, and optimizes frequently executed paths (hot paths)—is a negligible fraction of the application's total uptime.

However, a CLI tool operates on a fundamentally different lifecycle. It is ephemeral. It is invoked, performs a discrete task (processing a prompt, generating a diff), and terminates. In this context, the startup latency of the runtime dominates the user experience. Bun, written in the Zig programming language, utilizes the JavaScriptCore (JSC) engine, originally developed for WebKit (Safari). JSC prioritizes rapid startup and lower memory footprints over the peak throughput optimization of V8. Benchmarks consistently demonstrate that Bun can be 3–6 times faster in real-world web workloads and up to 30 times faster in tooling execution.2

For an AI agent, this difference is palpable. A delay of 300-500 milliseconds (typical for Node.js cold starts) creates friction that discourages frequent use. Bun reduces this to near-instantaneous execution, preserving the developer's "flow state."

### **2.2. The Windows Compatibility Layer**

While Bun has achieved significant stability on macOS and Linux, its Windows implementation relies on a translation layer to map POSIX-style system calls to Windows APIs. This is particularly relevant for the Gemini CLI, which uses "raw mode" in the terminal to render its Text User Interface (TUI)—the interactive spinner, the streaming text, and the diff views.

Older versions of the Gemini CLI had significant compatibility issues with Bun on Windows, particularly regarding signal handling (e.g., Ctrl+C interruption) and TTY context switching.5 However, the "Preview" channel of the Gemini CLI (@google/gemini-cli@preview) has seen aggressive patching to address these runtimes specificities. The commit history for the preview branch indicates cherry-picked fixes specifically for Bun runtime environments.6 Therefore, using the preview tag is not merely a preference for new features; it is a stability requirement for the Bun-on-Windows architecture.

### **2.3. Package Resolution and the bunx Imperative**

A critical decision point in the setup is the installation method. The standard npm install \-g places the binary in the global node\_modules folder, managed by Node.js. To utilize Bun, one must bypass this default.

The command bunx is Bun's equivalent of npx. It downloads and executes a package from the registry without permanently installing it into the global Node path, or it executes a locally installed binary using the Bun runtime. To ensure "Zero Redundancy" and guarantee that the Bun runtime is *always* used (even if a Node.js shim exists in the path), the specific invocation bunx \--bun is recommended. The \--bun flag forces the executable to run with bun instead of node, even if the package's bin script specifies \#\!/usr/bin/env node.1

| Feature | Node.js (V8) | Bun (JSC) | Implication for Gemini CLI |
| :---- | :---- | :---- | :---- |
| **Startup Time** | Slow (JIT Warmup) | Instant (AOT/JSC) | Bun provides a "native" feel to the CLI agent. |
| **Package Manager** | npm/yarn | bun | Bun installs dependencies orders of magnitude faster. |
| **Windows TTY** | Mature | Evolving | Requires Gemini CLI @preview for stability. |
| **Global Path** | %APPDATA%\\npm | %USERPROFILE%\\.bun | Separate distinct environments; prevents conflict. |

## **3\. The Terminal Environment: PowerShell 7.x and VS Code Insiders**

The operating system environment, Windows 11, presents specific constraints regarding character encoding that must be aggressively managed to ensure the AI agent functions correctly. The default legacy configurations of Windows are hostile to the rich, multi-lingual, and emoji-laden output generated by modern Large Language Models.

### **3.1. PowerShell 7.x: The Modern Shell**

The user specifies PowerShell 7.x (pwsh), which is built on.NET Core. Unlike the legacy Windows PowerShell (5.1), PowerShell 7 is cross-platform and fully supports UTF-8. However, simply installing it is insufficient. The console host—the window in which the shell runs—defaults to the system's active code page, often CP437 (OEM US) or CP1252 (Windows-1252).

When the Gemini CLI streams a response containing complex Unicode characters (e.g., box-drawing characters for tables, mathematical symbols, or non-Latin scripts), a mismatch between the shell's output encoding and the console's code page results in "Mojibake"—garbled, unreadable text.7

### **3.2. The Profile Hierarchy and "Zero Redundancy"**

To achieve the user's goal of "Zero Redundancy," we must configure the environment such that manual intervention is never required after the initial setup. This is achieved through the PowerShell Profile system.

PowerShell loads profiles in a specific order of precedence:

1. **All Users, All Hosts**  
2. **All Users, Current Host**  
3. **Current User, All Hosts** ($PROFILE.CurrentUserAllHosts)  
4. **Current User, Current Host** ($PROFILE.CurrentUserCurrentHost)

For a developer working across VS Code, Windows Terminal, and potentially standalone windows, the **Current User, All Hosts** profile is the optimal injection point. Configurations placed here apply universally to the user's session, regardless of the host application, eliminating the need to re-configure the shell for different contexts.

### **3.3. Detailed Encoding Configuration Plan**

The following configuration block must be appended to the user's global profile. It does not merely suggest UTF-8; it *enforces* it across the Input, Output, and Error streams. This is critical for the Gemini CLI, which acts as a pipe, reading user input (Input Stream) and streaming AI responses (Output Stream).

**Path Verification:**

To verify the location of this profile file, execute $PROFILE.CurrentUserAllHosts in the PowerShell terminal. Typically, on Windows 11, this resolves to C:\\Users\\\<Username\>\\Documents\\PowerShell\\profile.ps1.

**The Configuration Script:**

PowerShell

\# \=============================================================================  
\# Gemini CLI & Bun Runtime Environment Optimization  
\# \=============================================================================

\# 1\. Universal UTF-8 Enforcement  
\# \-----------------------------------------------------------------------------  
\# Standard Windows consoles default to legacy code pages (e.g., 437).  
\# Gemini CLI generates rich Markdown and Unicode content.  
\# The following lines force the.NET Console class to use UTF-8 No BOM.

\[Console\]::InputEncoding  \=::UTF8  
\[Console\]::OutputEncoding \=::UTF8  
$OutputEncoding           \=::UTF8

\# 2\. File Encoding Standardization  
\# \-----------------------------------------------------------------------------  
\# When the agent generates files (e.g., using \`run\_shell\_command\` or file tools),  
\# we ensure those files are written in UTF-8 to maintain diff integrity.

$PSDefaultParameterValues\['Out-File:Encoding'\]    \= 'utf8'  
$PSDefaultParameterValues \= 'utf8'  
$PSDefaultParameterValues\['Add-Content:Encoding'\] \= 'utf8'

\# 3\. Bun & Gemini Aliases (Zero Redundancy)  
\# \-----------------------------------------------------------------------------  
\# Instead of typing 'bunx \--bun @google/gemini-cli@preview' every time,  
\# we create a robust function 'g' that encapsulates the runtime logic.

function g {  
    \<\#  
   .SYNOPSIS  
    Launches Gemini CLI using Bun runtime with Preview features.  
   .DESCRIPTION  
    Wraps the bunx command to ensure the Bun runtime is used (--bun)  
    and targets the @preview tag for maximum compatibility on Windows.  
    \#\>  
    param(  
         
        $Args  
    )  
    \# The '--bun' flag is critical: it forces the script to run with Bun's  
    \# internal interpreter, bypassing Node.js entirely for speed.  
    bunx \-\-bun @google/gemini\-cli@preview $Args  
}

\# 4\. Context-Aware Launcher  
\# \-----------------------------------------------------------------------------  
\# Rapidly launches the agent with the current directory as the context.  
function gc {  
    bunx \-\-bun @google/gemini\-cli@preview \-\-context. $Args  
}

The inclusion of $PSDefaultParameterValues is a subtle but vital optimization. It ensures that if the user manually pipes Gemini output to a file (e.g., g "Draft a readme" | Out-File README.md), the file is created with the correct encoding, preventing corruption of the generated documentation.9

### **3.4. VS Code Insiders Terminal Optimization**

The Visual Studio Code "Insiders" build often features an updated rendering engine for the integrated terminal (xterm.js). To fully leverage this, specific settings in VS Code's settings.json are required to support the TUI elements used by Gemini.

**GPU Acceleration:**

The Gemini CLI spinner and streaming output can be graphically intensive for a terminal. Enabling GPU acceleration ensures smooth rendering without flickering.

**Font Ligatures:**

Modern coding fonts (Cascadia Code, Fira Code) support ligatures, which the Gemini CLI may utilize for cleaner code block rendering.

**Configuration for VS Code settings.json:**

JSON

{  
    "terminal.integrated.defaultProfile.windows": "PowerShell",  
    "terminal.integrated.profiles.windows": {  
        "PowerShell": {  
            "path": "C:\\\\Program Files\\\\PowerShell\\\\7\\\\pwsh.exe",  
            "args": \["-NoLogo"\]  
        }  
    },  
    "terminal.integrated.gpuAcceleration": "on",  
    "terminal.integrated.fontFamily": "'Cascadia Code', 'Fira Code', Consolas",  
    "terminal.integrated.detectLocale": "off",  
    "terminal.integrated.localEchoEnabled": "auto"  
}

Setting terminal.integrated.detectLocale to "off" is a crucial redundancy elimination step. It prevents VS Code from attempting to auto-configure the shell environment variables based on the OS language, which can occasionally conflict with the manual UTF-8 enforcement defined in the PowerShell profile.10

## **4\. The Model Context Protocol (MCP) Integration Strategy**

The Model Context Protocol (MCP) is the defining feature that transforms the Gemini CLI from a text generator into a capable agent. It provides a standardized interface for the LLM to discover tools, read resources, and execute prompts provided by external servers.11

### **4.1. Architecture of the Remote GitHub MCP Server**

The user's requirement involves the GitHub MCP Server. Standard documentation often points to running this server locally via Docker (docker run ghcr.io/github/github-mcp-server). However, this approach introduces significant redundancy: it requires a running Docker daemon, consumes local system resources (RAM/CPU), and requires manual updates of the Docker image.

The optimized path, leveraging the user's GitHub Copilot Pro subscription, is to utilize the **Remote GitHub MCP Server** hosted by GitHub itself. This server is accessible via an HTTP transport layer at https://api.githubcopilot.com/mcp/.3

**Advantages of Remote HTTP Transport:**

1. **Zero Maintenance**: GitHub maintains the server version; the user always accesses the latest tools.  
2. **Resource Efficiency**: No local processes or containers are required.  
3. **Contextual Awareness**: The remote server is integrated with GitHub's semantic search infrastructure, potentially offering superior code search capabilities compared to a local clone-and-grep approach.

### **4.2. Authentication: The Security Topology**

Connecting to api.githubcopilot.com requires rigorous authentication. The connection uses the standard HTTP Authorization header with a Bearer token.

**The Credential: Personal Access Token (PAT)**

While the VS Code Extension for Copilot handles authentication opaquely, the CLI requires an explicit token. This token acts as the bridge between the local Bun process and the remote GitHub API.

**Scope Requirements:**

To ensure the agent has sufficient privileges without granting excessive administrative power, the PAT must be generated with the following specific scopes:

* repo: Full control of private repositories (Required for reading code, creating issues, opening PRs).  
* read:org: Read organization data (Required for listing team repositories).  
* user: Read user profile data (Required for identity verification).  
* copilot: (If listed) Essential for interacting with Copilot-specific features.13

**Secure Injection via Environment Variables:** Hardcoding this PAT into a configuration file is a security violation. The "Zero Redundancy" plan dictates the use of persistent Environment Variables. The Gemini CLI's configuration parser natively supports variable expansion (e.g., $GITHUB\_TOKEN).15

**Implementation:**

Add the following line to the previously edited PowerShell profile ($PROFILE.CurrentUserAllHosts). This ensures the token is available in every session without manual export.

PowerShell

\# Security: GitHub Personal Access Token for MCP  
\# This variable is referenced in \~/.gemini/settings.json  
$env:GITHUB\_MCP\_PAT \= "ghp\_YourGeneratedTokenHere..."

## **5\. Hierarchical Configuration: The settings.json Master Plan**

The Gemini CLI employs a cascading configuration system. Understanding this hierarchy is the key to managing complexity and ensuring consistent behavior across different projects.

### **5.1. The Hierarchy of Precedence**

1. **System Settings** (/etc/gemini-cli/settings.json): rarely used on Windows, applies to all users.  
2. **User Global Settings** (\~/.gemini/settings.json): The default baseline for the user.  
3. **Workspace Settings** (./.gemini/settings.json): Project-specific overrides.  
4. **Command Line Flags**: Ephemeral overrides for a single execution.

To achieve "Zero Redundancy," we must populate the **User Global Settings** with all universal configurations (Auth, MCP servers, UI preferences). We reserve **Workspace Settings** strictly for project-specific context (e.g., specific linter rules or architecture guidelines).

### **5.2. The Definitive settings.json Artifact**

The following configuration JSON is designed for the Windows 11 / Bun / VS Code Insiders stack. It must be placed at:

C:\\Users\\\<YourUsername\>\\.gemini\\settings.json

JSON

{  
  "general": {  
    "previewFeatures": true,  
    "enableAutoUpdate": true,  
    "enablePromptCompletion": true,  
    "debugKeystrokeLogging": false,  
    "sessionRetention": {  
      "enabled": true  
    },  
    "sandbox": "local"   
  },  
  "ui": {  
    "useAlternateBuffer": true,  
    "incrementalRendering": true,  
    "showSpinner": true,  
    "theme": "dark"  
  },  
  "model": {  
    "model": "gemini-2.0-flash-exp",  
    "maxSessionTurns": 100,  
    "compressionThreshold": 0.5,  
    "safetySettings":  
  },  
  "mcpServers": {  
    "github": {  
      "httpUrl": "https://api.githubcopilot.com/mcp/",  
      "headers": {  
        "Authorization": "Bearer $GITHUB\_MCP\_PAT",  
        "User-Agent": "Gemini-CLI-Bun-Preview/1.0"  
      },  
      "timeout": 15000,  
      "enabled": true,  
      "toolsets": \[  
          "issues",  
          "pull\_requests",  
          "repos",  
          "user"  
      \]  
    }  
  }  
}

### **5.3. Deep Dive into Configuration Decisions**

* **general.previewFeatures**: Setting this to true is non-negotiable. The preview capabilities often include improvements to the agent's reasoning capabilities that are essential for complex tasks.16  
* **general.sandbox**: Explicitly setting this to "local" ensures the agent executes shell commands directly on the host machine (your Windows environment) rather than attempting to spin up a Docker container for isolation. While Docker is safer, the "local" setting is required for the agent to modify files in your actual working directory, which is the primary use case for a developer tool.  
* **model.model**: We explicitly request gemini-2.0-flash-exp. The "Flash" series of models are optimized for low latency and high throughput, making them ideal for the iterative, conversational nature of a CLI tool. The "exp" (experimental) tag ensures access to the latest reasoning improvements.17  
* **model.safetySettings**: By default, AI models can be overly cautious, refusing to generate code that includes terms like "kill" (process) or "attack" (security simulation). Setting thresholds to BLOCK\_ONLY\_HIGH prevents the agent from refusing legitimate software engineering requests.18  
* **mcpServers.github**:  
  * **httpUrl**: Points to the managed Copilot infrastructure.  
  * **headers**: Uses variable expansion for the PAT. The User-Agent string is added to assist with server-side debugging if GitHub ever reviews traffic logs.  
  * **toolsets**: Explicitly enabling all available toolsets ensures the agent has full visibility into the GitHub ecosystem.20

## **6\. The Skills System: Extending Capability without Bloat**

The final layer of the "Zero Redundancy" plan is the **Skills** system. Skills are modular, reusable context packages that the agent can load dynamically. This solves the problem of "Context Window Pollution," where loading a massive GEMINI.md file consumes tokens and distracts the model from the immediate task.

### **6.1. Skill Structure and Discovery**

Skills reside in directories containing a SKILL.md file. The CLI scans specific paths to discover these skills.

* **User Skills**: \~/.gemini/skills/ (Available globally).  
* **Workspace Skills**: ./.gemini/skills/ (Available only in the project).

The agent sees the *description* of the skill in its system prompt. It effectively says, "I know how to do X, Y, and Z." It only loads the *content* of the skill (the detailed instructions) when it decides to activate that skill to solve a user request.21

### **6.2. Creating a "Core Engineering" Skill**

To improve the out-of-the-box experience, we will create a global skill that enforces engineering rigor. This ensures that every time the agent writes code, it follows a strict set of standards, without you having to repeat "Please use TypeScript and add comments" in every prompt.

**Step 1: Create the Directory**

Execute in PowerShell:

PowerShell

New-Item \-Path "$HOME\\.gemini\\skills\\engineering-standards" \-ItemType Directory \-Force

**Step 2: Create the SKILL.md File**

Create $HOME\\.gemini\\skills\\engineering-standards\\SKILL.md with the following content:

## ---

**name: engineering-standards description: Enforces strict software engineering standards, including type safety, error handling, and documentation. Activate this skill when writing, refactoring, or reviewing code.**

# **Global Engineering Standards**

You are a Senior Principal Engineer. All code you generate must adhere to the following strictures.

## **1\. Type Safety**

* **TypeScript**: Always prefer TypeScript over JavaScript. Use strict typing (noImplicitAny). Avoid any unless absolutely necessary; use unknown or generic constraints instead.  
* **Python**: Always use Type Hints (PEP 484\) for function arguments and return values.

## **2\. Error Handling**

* **No Silent Failures**: Never use empty catch blocks.  
* **Granularity**: Catch specific exceptions rather than global Exception or Error.  
* **Propagation**: If an error cannot be handled locally, propagate it or wrap it with context.

## **3\. Documentation**

* **Public Interfaces**: All exported functions, classes, and types must have JSDoc (TS) or DocString (Python) comments explaining parameters, return values, and potential exceptions.  
* **Inline Comments**: Use inline comments to explain *why* complex logic exists, not *what* it does.

## **4\. Bun Specifics**

* **Runtime APIs**: When operating in a JavaScript context, prioritize Bun-native APIs (e.g., Bun.file(), Bun.write()) over Node.js fs module for performance, unless Node.js compatibility is strictly requested.

### **6.3. The Impact of Skills**

With this skill in place, the workflow transforms.

* **Without Skill**: User: "Write a script to parse this CSV." \-\> Agent writes a basic Node.js script with minimal error handling.  
* **With Skill**: User: "Write a script to parse this CSV." \-\> Agent recognizes the coding task \-\> Activates engineering-standards \-\> Writes a robust TypeScript script using Bun.file(), with full JSDoc and try/catch blocks.

This creates a "Zero Redundancy" interaction model: the user states the *intent*, and the system automatically supplies the *rigor*.

## **7\. Operational Workflow and Maintenance**

### **7.1. Verification of the Setup**

To confirm the entire architecture is functioning as designed, perform the following verification sequence:

1. **Launch**: Open VS Code Insiders. Open the Integrated Terminal (PowerShell).  
2. **Verify Profile**: Run $env:GITHUB\_MCP\_PAT. It should output your token.  
3. **Verify Runtime**: Run Get-Command g. It should show the function definition calling bunx \--bun.  
4. **Execute**: Type g. The Gemini CLI interface should launch instantly (thanks to Bun).  
5. **Test MCP**: Enter the prompt: @github list the last 3 issues in my repo.  
   * The agent should show a permission prompt (first time only).  
   * It should successfully connect to api.githubcopilot.com and retrieve the data.  
6. **Test Skill**: Enter the prompt: Write a hello world function in TS.  
   * The agent should produce a TypeScript function with JSDoc comments, adhering to the engineering-standards skill.

### **7.2. Updates and Maintenance**

Because we are using bunx @google/gemini-cli@preview, updates are handled automatically by the package registry.

* **Cache Clearing**: If you suspect you are on a stale version despite the @preview tag (a known issue with package manager caching), run:  
  PowerShell  
  bun pm cache rm

  This forces Bun to re-fetch the latest metadata from the registry on the next run.

### **7.3. Troubleshooting Common Windows Errors**

| Symptom | Probable Cause | Resolution |
| :---- | :---- | :---- |
| **Garbled Text / Question Marks** | Encoding Mismatch | Verify $PROFILE has \[Console\]::OutputEncoding \= UTF8. Check VS Code font supports ligatures. |
| **"Unauthorized" from GitHub** | Invalid PAT / Scope | Regenerate PAT with repo and read:org. Restart VS Code to reload env vars. |
| **"Streamable HTTP not working"** | Firewall / Proxy | Ensure corporate firewalls allow traffic to api.githubcopilot.com. |
| **Process Hangs on Output** | TTY Buffer Lock | Press Enter. Sometimes Windows Console streams pause if user selects text (QuickEdit Mode). |
| **Bun "Command Not Found"** | Path Issue | Ensure C:\\Users\\\<User\>\\.bun\\bin is in the System PATH. |

## **8\. Conclusion**

This report delineates a sophisticated, enterprise-grade architecture for the Gemini CLI on Windows 11\. By synthesizing the raw speed of the **Bun runtime**, the universality of **PowerShell 7.x**, the intelligence of the **Model Context Protocol**, and a rigorous **hierarchical configuration strategy**, we have eliminated the friction typically associated with local AI agents. The result is a system that is not only "set up" but architected for sustained, high-velocity engineering workflows, adhering strictly to the principle of "Zero Redundancy." The developer is now free to focus on reasoning and logic, trusting the environment to handle the execution and context management with precision.

#### **Referanser**

1. The Fastest Way to Run the Gemini CLI: A Deep Dive into Package Managers \- Medium, brukt februar 1, 2026, [https://medium.com/google-cloud/the-fastest-way-to-run-the-gemini-cli-a-deep-dive-into-package-managers-8ee8318c5ffa](https://medium.com/google-cloud/the-fastest-way-to-run-the-gemini-cli-a-deep-dive-into-package-managers-8ee8318c5ffa)  
2. Officially support Bun as a runtime · Issue \#12731 · google-gemini/gemini-cli \- GitHub, brukt februar 1, 2026, [https://github.com/google-gemini/gemini-cli/issues/12731](https://github.com/google-gemini/gemini-cli/issues/12731)  
3. A practical guide on how to use the GitHub MCP server, brukt februar 1, 2026, [https://github.blog/ai-and-ml/generative-ai/a-practical-guide-on-how-to-use-the-github-mcp-server/](https://github.blog/ai-and-ml/generative-ai/a-practical-guide-on-how-to-use-the-github-mcp-server/)  
4. github-mcp-server/docs/installation-guides/install-gemini-cli.md at main, brukt februar 1, 2026, [https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-gemini-cli.md](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-gemini-cli.md)  
5. UI lag and ctrl+c / esc not working in versions greater than 0.1.5 · Issue \#2312 \- GitHub, brukt februar 1, 2026, [https://github.com/google-gemini/gemini-cli/issues/2312](https://github.com/google-gemini/gemini-cli/issues/2312)  
6. Releases · google-gemini/gemini-cli \- GitHub, brukt februar 1, 2026, [https://github.com/google-gemini/gemini-cli/releases](https://github.com/google-gemini/gemini-cli/releases)  
7. The Ultimate Guide to orzcls's Gemini CLI MCP Server: Your Windows AI Engineering Co-pilot \- Skywork.ai, brukt februar 1, 2026, [https://skywork.ai/skypage/en/gemini-cli-mcp-server/1977571983261896704](https://skywork.ai/skypage/en/gemini-cli-mcp-server/1977571983261896704)  
8. Japanese characters are garbled in shell command output on Windows in Gemini CLI · Issue \#15389 \- GitHub, brukt februar 1, 2026, [https://github.com/google-gemini/gemini-cli/issues/15389](https://github.com/google-gemini/gemini-cli/issues/15389)  
9. \[BUG\] Claude code bash command execution, output Chinese characters appear as garbled text \#7332 \- GitHub, brukt februar 1, 2026, [https://github.com/anthropics/claude-code/issues/7332](https://github.com/anthropics/claude-code/issues/7332)  
10. Agent unable to run commands on Windows 11 \- Bug Reports \- Cursor \- Community Forum, brukt februar 1, 2026, [https://forum.cursor.com/t/agent-unable-to-run-commands-on-windows-11/143405](https://forum.cursor.com/t/agent-unable-to-run-commands-on-windows-11/143405)  
11. MCP servers with the Gemini CLI, brukt februar 1, 2026, [https://geminicli.com/docs/tools/mcp-server/](https://geminicli.com/docs/tools/mcp-server/)  
12. How to Build an MCP Server with Gemini CLI and Go | Google Codelabs, brukt februar 1, 2026, [https://codelabs.developers.google.com/cloud-gemini-cli-mcp-go](https://codelabs.developers.google.com/cloud-gemini-cli-mcp-go)  
13. Setting up the GitHub MCP Server, brukt februar 1, 2026, [https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/set-up-the-github-mcp-server](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/set-up-the-github-mcp-server)  
14. Using the GitHub MCP Server, brukt februar 1, 2026, [https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/use-the-github-mcp-server](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/use-the-github-mcp-server)  
15. Gemini CLI configuration, brukt februar 1, 2026, [https://geminicli.com/docs/get-started/configuration/](https://geminicli.com/docs/get-started/configuration/)  
16. Gemini CLI settings (\`/settings\` command), brukt februar 1, 2026, [https://geminicli.com/docs/cli/settings/](https://geminicli.com/docs/cli/settings/)  
17. google-gemini/gemini-cli: An open-source AI agent that brings the power of Gemini directly into your terminal. \- GitHub, brukt februar 1, 2026, [https://github.com/google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli)  
18. Understand and use safety settings | Firebase AI Logic \- Google, brukt februar 1, 2026, [https://firebase.google.com/docs/ai-logic/safety-settings](https://firebase.google.com/docs/ai-logic/safety-settings)  
19. Template format, syntax, and examples | Firebase AI Logic \- Google, brukt februar 1, 2026, [https://firebase.google.com/docs/ai-logic/server-prompt-templates/syntax-and-examples](https://firebase.google.com/docs/ai-logic/server-prompt-templates/syntax-and-examples)  
20. GitHub's official MCP Server, brukt februar 1, 2026, [https://github.com/github/github-mcp-server](https://github.com/github/github-mcp-server)  
21. Agent Skills | Gemini CLI, brukt februar 1, 2026, [https://geminicli.com/docs/cli/skills/](https://geminicli.com/docs/cli/skills/)