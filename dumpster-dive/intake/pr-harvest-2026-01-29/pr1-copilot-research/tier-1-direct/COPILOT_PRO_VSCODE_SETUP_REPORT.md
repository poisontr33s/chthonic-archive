# GitHub Copilot Pro VS Code Setup Research Report

**Research Date:** December 2025
**Platform:** Visual Studio Code on Windows 11
**Target:** GitHub Copilot Pro Users
**Source:** PR #1 (closed, never merged)

---

## Table of Contents

1. [GitHub Copilot Pro Features & Agents](#1-github-copilot-pro-features--agents)
2. [Model Switching & Multi-Model Support](#2-model-switching--multi-model-support)
3. [User Tier Benefits Comparison](#3-user-tier-benefits-comparison)
4. [YOLO Mode Configuration](#4-yolo-mode-configuration)
5. [Recommended Settings.json Configuration](#5-recommended-settingsjson-configuration)
6. [Required Extensions for Full Agent Functionality](#6-required-extensions-for-full-agent-functionality)
7. [Optimal VS Code Settings for Copilot Pro](#7-optimal-vs-code-settings-for-copilot-pro)
8. [Sources & References](#8-sources--references)

---

## 1. GitHub Copilot Pro Features & Agents

### Copilot Agent Mode

As of late 2025, GitHub Copilot has evolved beyond simple code completion into a full **Agent Mode** that enables:

- **Multi-step task automation** — refactoring, testing, documentation, and code migration
- **In-editor automation** — Copilot acts as an agent driving coding workflows
- **Context-aware assistance** — understands project structure and dependencies

### Available Agents (@mentions)

| Agent | Description | Use Case |
|-------|-------------|----------|
| `@workspace` | Project-wide queries and context | "Where is authentication implemented?" |
| `@terminal` | Shell commands, git, and deployment | "Show last git commit" |
| `@vscode` | IDE configuration and settings | "Change theme to dark" |
| `/help` | Lists all available agents/participants | Discovery and guidance |

### Key Capabilities

- **Code Generation** — Generate code from natural language descriptions
- **Code Explanation** — Understand complex code patterns
- **Test Generation** — Automatically create unit tests
- **Documentation** — Generate inline comments and README files
- **Refactoring** — Multi-file refactoring with context awareness
- **Bug Fixing** — Identify and suggest fixes for issues

---

## 2. Model Switching & Multi-Model Support

### Native Multi-Model Support

GH CP supports myriads of AI models **natively** without add. extensions:

| Model Provider | Available Models | Best For |
|----------------|------------------|----------|
| **OpenAI** | GPT-4.1- 5.2 + Codex 5.2 | General use to advanced |
| **Anthropic** | Claude Opus 4.5/Sonnet 4.5, Haiku 4.5 | Complex reasoning, agentic workflows |
| **Google** | Gemini 2.5 Pro- 3 Pro + Flash | Multimodal tasks, large codebases |

### Model Selection

- Access via **model picker** in VS Code status bar/chat interface
- Available in GH CP/Chat/GitHub.com/GH CP CLI/Sub-agents/Cloud/Background work
- **Agent Mode default:** GPT-4.1 (free "default"), Claude Sonnet/Opus 4.5 (in Pro/+ tiers)

### Current Status (Era)

- Claude Opus/Sonnet/Haiku 4.5
- Gemini 3 Pro/Flash
- Multi-model picker

---

## 3. User Tier Benefits Comparison

### Pricing & Feature Matrix

| Tier | Price | Premium Requests/mo | Key Features |
|------|-------|---------------------|--------------|
| **Free** | $0 | 50 | Basic completions, limited chat, students/OSS |
| **Pro** | $10/mo ($100/yr) | 300 | Unlimited completions, full chat, premium models |
| **Pro+** | $39/mo ($390/yr) | 1500 | All Pro + GPT-4.5, priority previews, advanced chat |
| **Business** | $19/user/mo | 300/user | Org management, SSO, policy controls |
| **Enterprise** | $39/user/mo | 1000/user | Deep repo integration, advanced security, compliance |

### Pro vs Pro+ Feature Differences

| Feature | Pro | Pro+ |
|---------|-----|------|
| Model Switching | Yes | Yes |
| Claude Opus 4.5 | Yes (limited) | Yes (priority) |
| Premium Request Quota | 300/mo | 1500/mo |
| GPT-4.5 Exclusive Access | No | Yes |
| Early Feature Access | No | Yes |
| Advanced Agent Scenarios | Limited | Full |

---

## 4. YOLO Mode Configuration

### What is YOLO Mode?

**YOLO Mode** refers to VS Code/Copilot configuration that **auto-approves** tool calls and terminal commands without confirmation dialogs. This enables faster, hands-off automation but should only be used in sandbox environments.

### Safety Warning

> YOLO mode is **experimental** and intended for sandboxes, demos, and VMs—**never production**. Always have version control and backups ready.

### Configuration Settings

```json
{
    // === AUTO-APPROVE ALL TOOL CALLS ===
    "chat.tools.autoApprove": true,

    // === TERMINAL COMMAND PATTERNS (Allow/Deny) ===
    "chat.tools.terminal.autoApprove": {
        // ALLOWED - Safe read-only commands
        "/^git\\s+(status|diff|log|show)\\b/": true,
        "/^npm\\s+(test|run\\s+lint)\\b/": true,
        "/^pnpm\\s+(test|lint)\\b/": true,
        "/^cargo\\s+(check|test|clippy)\\b/": true,

        // Relative - Risky commands (YOLO mode)
        "rm": false,
        "rmdir": false,
        "del": false,
        "kill": false,
        "chmod": false,
        "chown": false,
        "/^git\\s+(push|reset|revert|clean)\\b/": false
    }
}
```

---

## 5. Recommended Settings.json Configuration

### Full Configuration for Copilot Pro Users

```json
{
    // === COPILOT CORE SETTINGS ===
    "github.copilot.enable": {
        "*": true,
        "plaintext": true,
        "markdown": true,
        "scminput": false
    },
    "github.copilot.editor.enableCodeActions": true,
    "github.copilot.renameSuggestions.triggerAutomatically": true,

    // === INLINE SUGGESTIONS ===
    "editor.inlineSuggest.enabled": true,
    "editor.inlineSuggest.showToolbar": "always",
    "github.copilot.nextEditSuggestions.enabled": true,

    // === COPILOT CHAT CONFIGURATION ===
    "github.copilot.chat.localeOverride": "auto",
    "github.copilot.chat.useProjectTemplates": true,
    "github.copilot.chat.scopeSelection": true,
    "github.copilot.chat.terminalChatLocation": "chatView",
    "github.copilot.chat.codesearch.enabled": true,
    "github.copilot.chat.editor.temporalContext.enabled": true,

    // === CHAT EDITING & CHECKPOINTS ===
    "chat.editRequests": "inline",
    "chat.editing.autoAcceptDelay": 0,
    "chat.editing.confirmEditRequestRemoval": true,
    "chat.editing.confirmEditRequestRetry": true,
    "chat.checkpoints.enabled": true,
    "chat.checkpoints.showFileChanges": true,
    "chat.emptyState.history.enabled": true,

    // === CHAT UI SETTINGS ===
    "chat.editor.wordWrap": "on",
    "chat.editor.fontSize": 14,
    "chat.detectParticipant.enabled": true,
    "chat.math.enabled": true,

    // === INLINE CHAT ===
    "inlineChat.finishOnType": false,
    "inlineChat.holdToSpeech": true,

    // === INSTRUCTION FILES ===
    "github.copilot.chat.codeGeneration.useInstructionFiles": true,

    // === TERMINAL INTEGRATION ===
    "chat.tools.terminal.autoReplyToPrompts": true
}
```

---

## 6. Required Extensions for Full Agent Functionality

### Essential Extensions

| Extension | ID | Purpose |
|-----------|----|---------|
| **GitHub Copilot** | `GitHub.copilot` | Core AI code completion |
| **GitHub Copilot Chat** | `GitHub.copilot-chat` | Chat-based AI assistance |

### Recommended Extensions

| Extension | ID | Purpose |
|-----------|----|---------|
| **GitHub Copilot Workspace** | `GitHub.copilot-workspace` | Project-wide AI, session sync (tech preview) |
| **GitHub Pull Requests and Issues** | `GitHub.vscode-pull-request-github` | PR/issue integration, agent tracking |

### Notes

- `@workspace`, `@terminal`, and `@vscode` agents require **GitHub Copilot Chat** extension
- **GitHub Copilot Workspace** requires opt-in access (technical preview)
- No additional third-party extensions needed for multi-model support

---

## 7. Optimal VS Code Settings for Copilot Pro

### Performance Optimization

```json
{
    // === PERFORMANCE ===
    "files.watcherExclude": {
        "**/target/**": true,
        "**/node_modules/**": true,
        "**/.git/objects/**": true
    },
    "search.exclude": {
        "**/target": true,
        "**/node_modules": true
    },

    // === MINIMAL SUGGESTION DELAY ===
    "editor.inlineSuggest.minShowDelay": 0,

    // === CONTEXT AWARENESS ===
    "github.copilot.chat.editor.temporalContext.enabled": true,
    "github.copilot.chat.scopeSelection": true
}
```

---

## 8. Sources & References

### Official Documentation

- [GitHub Copilot Setup Guide](https://code.visualstudio.com/docs/copilot/setup)
- [Copilot Settings Reference](https://code.visualstudio.com/docs/copilot/reference/copilot-settings)
- [Workspace Context Guide](https://code.visualstudio.com/docs/copilot/reference/workspace-context)
- [Supported AI Models](https://docs.github.com/en/copilot/reference/ai-models/supported-models)
- [Copilot Plans](https://docs.github.com/en/copilot/get-started/plans)

### Announcements & Changelogs

- [Claude Opus 4.5 Public Preview (Nov 2025)](https://github.blog/changelog/2025-11-24-claude-opus-4-5-is-in-public-preview-for-github-copilot/)
- [Agent Mode & Next Edit Suggestions](https://github.blog/changelog/2025-02-06-next-edit-suggestions-agent-mode-and-prompts-files-for-github-copilot-in-vs-code-january-release-v0-24/)
- [Copilot Pro+ Announcement](https://github.blog/changelog/2025-04-04-announcing-github-copilot-pro/)

---

**Harvested from:** PR #1 (closed, never merged)
**Harvest Date:** 2026-01-29 (might be outdated, it's all relative, these are the times we live in -cowboy- ai- snot-bubbles)
