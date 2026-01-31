# **Resolution Pattern: OpenAI Codex CLI/IDE Authentication Failure on Windows 11 Due to Credential Manager Character Limit**

## **Executive Summary**

This document captures a debugging pattern discovered while configuring the OpenAI Codex CLI and VS Code extension on Windows 11. The core issue manifests as a persistent authentication failure with the error:

```
Unable to persist auth file: failed to write OAuth tokens to keyring:
Attribute 'password encoded as UTF-16' is longer than platform limit of 2560 chars
```

### **Core Findings**

1. **Root Cause:** Windows Credential Manager enforces a **2560 character limit** on stored password attributes. OAuth tokens from ChatGPT authentication exceed this limit when encoded as UTF-16.

2. **Configuration Ignored:** The documented setting `cli_auth_credentials_store = "file"` in `~/.codex/config.toml` was **not honored** by Codex when existing cached state was present in the config directory.

3. **Solution Pattern:** Creating a **fresh `CODEX_HOME` directory** with a minimal config forced Codex to respect the file-based storage setting. The resulting `auth.json` could then be migrated to the standard location.

---

## **1. Technical Context: Windows Credential Manager Limitations**

### **1.1 The UTF-16 Encoding Problem**

Windows Credential Manager stores credentials using the `CredWrite` API. Password attributes are stored as `CREDENTIAL_BLOB` structures with a platform-imposed limit:

| Platform | Limit | Encoding |
|----------|-------|----------|
| Windows 10/11 | 2560 chars | UTF-16LE |
| macOS Keychain | ~64KB | UTF-8 |
| Linux libsecret | Variable | UTF-8 |

OAuth tokens from OpenAI's ChatGPT authentication flow contain:
- Access token (~1500 chars)
- Refresh token (~1500 chars)
- ID token with claims (~2000 chars)
- Metadata fields

**Combined UTF-16 encoded length exceeds 2560 characters.**

### **1.2 Codex Credential Storage Options**

Per OpenAI documentation, `cli_auth_credentials_store` accepts:

| Value | Behavior |
|-------|----------|
| `file` | Store in `$CODEX_HOME/auth.json` |
| `keyring` | Use OS credential store |
| `auto` | Prefer keyring, fallback to file |

**Expected behavior:** Setting `file` should bypass keyring entirely.
**Actual behavior:** Setting was ignored when `~/.codex` contained prior state.

---

## **2. Debugging Attempts (Failed)**

### **2.1 Configuration File Approach**

```toml
# ~/.codex/config.toml
cli_auth_credentials_store = "file"
forced_login_method = "chatgpt"
```

**Result:** Keyring error persisted. Config setting ignored.

### **2.2 CLI Flag Override**

```powershell
codex login -c cli_auth_credentials_store='"file"'
```

**Result:** Same keyring error. Flag ignored.

### **2.3 Logout and Re-authenticate**

```powershell
codex logout
codex login
```

**Result:** Fresh login attempt still triggered keyring write.

### **2.4 Device Authorization Flow**

```powershell
codex login --device-auth
```

**Result:** Alternative OAuth flow, same keyring write failure.

### **2.5 Windows Credential Manager Inspection**

```powershell
cmdkey /list | Select-String 'codex|openai'
```

**Result:** No existing entries. Issue was write failure, not stale data.

---

## **3. Resolution Pattern (Successful)**

### **3.1 Isolation via CODEX_HOME**

The breakthrough: **environment variable isolation** forces Codex to initialize fresh state.

```powershell
# Step 1: Create isolated config directory
New-Item -ItemType Directory "$HOME\.codex-fresh" -Force
Set-Content "$HOME\.codex-fresh\config.toml" 'cli_auth_credentials_store = "file"'

# Step 2: Set CODEX_HOME and authenticate
$env:CODEX_HOME = "$HOME\.codex-fresh"
codex login

# Step 3: Verify auth.json created (not keyring)
Get-ChildItem "$HOME\.codex-fresh"
# Output: auth.json (4298 bytes), config.toml

# Step 4: Migrate to standard location
Copy-Item "$HOME\.codex-fresh\auth.json" "$HOME\.codex\auth.json" -Force

# Step 5: Verify authentication persists
codex login status
# Output: Logged in using ChatGPT
```

### **3.2 Why This Works**

| Factor | Standard ~/.codex | Fresh CODEX_HOME |
|--------|-------------------|------------------|
| Cached state | Present (corrupted/stale) | None |
| Config precedence | Overridden by cache | Config is authoritative |
| Keyring fallback | Triggered | Bypassed |
| auth.json creation | Blocked | Successful |

**Hypothesis:** Codex maintains internal state beyond `config.toml` that influences credential storage decisions. A pristine directory eliminates interference.

---

## **4. Secondary Issues Encountered**

### **4.1 Wrong Account Authentication**

**Symptom:** After successful auth, API returned:
```json
{"error":{"type":"usage_not_included","message":"Usage not included in your plan","plan_type":"free"}}
```

**Cause:** Browser cached credentials for wrong OpenAI account (Apple relay email vs. ChatGPT Plus account).

**Resolution:**
1. Clear browser cookies for `openai.com`, `auth.openai.com`
2. Disconnect Codex at ChatGPT Settings > Connected Apps
3. Re-authenticate with correct account

### **4.2 Model Configuration Mismatch**

**Symptom:**
```json
{"error":{"message":"Unsupported value: 'concise' is not supported with the 'gpt-5.2-codex' model. Supported values are: 'detailed'."}}
```

**Resolution:**
```toml
# ~/.codex/config.toml
model_reasoning_summary = "detailed"  # NOT "concise"
```

---

## **5. Final Working Configuration**

```toml
# ~/.codex/config.toml
cli_auth_credentials_store = "file"
forced_login_method = "chatgpt"
model = "gpt-5.2-codex"
model_provider = "openai"
file_opener = "vscode-insiders"

sandbox_mode = "workspace-write"
network_access = true
write_permissions = true

model_reasoning_effort = "medium"
model_reasoning_summary = "detailed"
hide_agent_reasoning = false
show_raw_agent_reasoning = true

[features]
apply_patch_freeform = true
view_image_tool = true
unified_exec = true
web_search_request = true
```

**Files required:**
- `~/.codex/config.toml` (above)
- `~/.codex/auth.json` (generated via fresh CODEX_HOME method)

---

## **6. Pattern Generalization**

This debugging pattern applies broadly to CLI tools with:

1. **Config files that can be overridden** by cached/internal state
2. **OS-specific storage backends** with undocumented limitations
3. **Environment variable isolation** support (`*_HOME` patterns)

### **Resolution Template**

```powershell
# Generic pattern for config-respecting CLI tools
$toolName = "codex"  # Replace with tool name
$homeVar = "CODEX_HOME"  # Replace with tool's HOME variable

# Isolate
$freshHome = "$HOME\.$toolName-fresh"
New-Item -ItemType Directory $freshHome -Force
# Copy minimal config...

# Authenticate in isolation
Set-Item "Env:$homeVar" $freshHome
& $toolName login  # or init, auth, etc.

# Migrate artifacts
Copy-Item "$freshHome\auth*" "$HOME\.$toolName\" -Force
```

---

## **References**

- [OpenAI Codex Configuration Reference](https://developers.openai.com/codex/config-reference/)
- [OpenAI Codex Authentication](https://developers.openai.com/codex/auth/)
- [Windows Credential Manager Limits](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credwritew)
- [OpenAI Codex GitHub Issues](https://github.com/openai/codex/issues)

---

**Document Metadata**
- Created: 2026-01-31
- Platform: Windows 11 (MSYS_NT-10.0-26200)
- Codex Version: 0.92.0
- Resolution Method: CODEX_HOME isolation pattern
