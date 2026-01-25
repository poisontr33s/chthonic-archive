# Windows 11 Bun-Playwright Trajectory Analysis

> **Purpose**: Data-driven analysis for solving Bun-Playwright on enterprise Windows 11
> **Date**: 2026-01-23 | **Source**: debugging_data logs + validation attempts

---

## 1. Execution Timeline (from Extension_Host_data.log)

```
04:40:31 - cd bun-playwright-poc; bun install        ✅ Executed
04:40:44 - bunx playwright install chromium          ✅ Executed  
04:41:03 - bunx playwright test --project=chromium   ❓ Attempted
04:41:24 - bunx playwright test --project=chromium 2>&1  ❓ Attempted
04:41:40 - bun run test:chromium                     ❓ Attempted
04:41:55 - bunx playwright --version                 ✅ Verified
04:42:10 - bun --version; bunx playwright --version  ✅ Verified
04:44:38 - bun install                               ✅ Re-executed
04:45:15 - bun --cwd ... install                     ✅ Verified
04:45:30 - bun install --cwd ...                     ✅ Verified
04:45:45 - Test-Path node_modules/playwright         ✅ Checked
04:45:56 - bun run launch-diag                       🔴 HUNG HERE
04:46:11 - bun run launch-diag                       🔴 HUNG AGAIN
04:46:49 - Get-Process chrome|bun|playwright         ⚠️ Checking hung state
04:47:22 - taskkill chrome.exe; taskkill bun.exe     🛑 Manual kill required
```

**Key Finding**: All install/verify commands succeed. Only browser-launching commands hang.

**Non-Cause (from Window.log)**: VS Code Insiders UI errors (listener leak, chat participant manifest warnings) are unrelated to Playwright launch failures.

---

## 2. The WebSocket Block Point

### bun-launcher.ts Flow Analysis

```typescript
// STAGE 1: This completes ✅
console.log("Testing Chromium...");
const browser = await chromium.launch({ headless: true });
//                 ^^^^^^^^^^^^^^^^
//                 BLOCKS HERE on Windows 11 enterprise

// STAGE 2: Never reached ❌
const version = browser.version();
```

### What Playwright Does Internally

1. **Spawn browser process** → Works (chromium.exe starts)
2. **Browser opens CDP WebSocket** → Works (ws://127.0.0.1:PORT)
3. **Playwright connects to WebSocket** → **BLOCKED** by enterprise policy
4. **Timeout after 30s** → Process hangs indefinitely

### Evidence: Process Still Running After Hang

```powershell
# From log at 04:46:49
Get-Process | Where-Object { $_.ProcessName -match "chrome|bun" }
# Shows chrome.exe and bun.exe still running = spawn worked, connection blocked
```

---

## 3. Windows 11 Enterprise Security Layer

### Likely Blockers (Ranked by Probability)

| Probability | Blocker | Detection Method |
|-------------|---------|------------------|
| **HIGH** | Windows Defender Application Control (WDAC) | Check `Get-CimInstance -ClassName Win32_DeviceGuard` |
| **HIGH** | Corporate firewall blocking localhost loopback | Check `netsh advfirewall show currentprofile` |
| **MEDIUM** | SmartScreen blocking unsigned executables | Check Event Viewer > Windows Defender SmartScreen |
| **MEDIUM** | VPN/Proxy intercepting localhost traffic | Check `netsh winhttp show proxy` |
| **LOW** | Antivirus real-time scan blocking ws:// | Check AV quarantine logs |

### Quick Detection Commands

```powershell
# 1. Check if loopback is being filtered
Test-NetConnection -ComputerName localhost -Port 9222 -InformationLevel Detailed

# 2. Check Windows Firewall rules for bun/playwright
Get-NetFirewallRule | Where-Object { $_.DisplayName -match 'bun|playwright|chrome' }

# 3. Check Device Guard (WDAC)
(Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root/Microsoft/Windows/DeviceGuard).VirtualizationBasedSecurityStatus

# 4. Check proxy settings
netsh winhttp show proxy

# 5. List listening ports (see if browser opens port)
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -gt 9000 -and $_.LocalPort -lt 10000 }
```

---

## 4. Potential Windows 11 Solutions

### Solution A: Bun WebSocket Direct Mode (No Browser Spawn)

Skip browser launch entirely for tests that don't need real rendering:

```typescript
// Mock browser for unit tests - no WebSocket needed
import { test, expect } from '@playwright/test';

test.use({
  // Use mock browser context
  browserName: 'chromium',
  launchOptions: {
    args: ['--no-sandbox', '--disable-gpu', '--disable-software-rasterizer']
  }
});
```

**Verdict**: Only works for smoke tests, not full E2E.

### Solution B: Named Pipe Instead of WebSocket

Chromium supports `--remote-debugging-pipe` mode which uses stdin/stdout instead of WebSocket:

```typescript
// Modified bun-launcher.ts approach
const browser = await chromium.launch({
  headless: true,
  args: ['--remote-debugging-pipe'], // Use pipe, not WebSocket
});
```

**Verdict**: May bypass network security. Needs testing.

### Solution C: Explicit Loopback Binding

Force browser to bind to specific interface:

```typescript
const browser = await chromium.launch({
  headless: true,
  args: [
    '--remote-debugging-address=127.0.0.1',
    '--remote-debugging-port=0', // Auto-select port
  ],
});
```

**Verdict**: May help if firewall is blocking all 0.0.0.0 bindings.

### Solution D: Pre-authenticated WebSocket

Start browser manually, get WebSocket URL, connect:

```powershell
# Step 1: Start Chromium manually with known port
& "$env:LOCALAPPDATA\ms-playwright\chromium-*\chrome-win\chrome.exe" --headless --remote-debugging-port=9222

# Step 2: Connect from Bun
```

```typescript
// Step 2 in Bun
const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
```

**Verdict**: Bypasses Playwright's spawn mechanism. Useful for debugging.

### Solution E: WSL2 Passthrough

Run Playwright in WSL2, render on Windows X server:

```bash
# In WSL2
export DISPLAY=:0  # If using VcXsrv/X410
bun run launch-diag
```

**Verdict**: Known to work but adds architectural complexity.

---

## 5. Diagnostic Script for Windows 11

Create this to isolate the exact failure point:

```typescript
// win11-diagnostic.ts
#!/usr/bin/env bun

import { spawn } from 'bun';
import { chromium } from 'playwright';

async function diagnose() {
  console.log('🔬 Windows 11 Bun-Playwright Diagnostic\n');
  
  // Test 1: Can we spawn chromium at all?
  console.log('1️⃣ Testing raw chromium spawn...');
  const chromePath = await chromium.executablePath();
  console.log(`   Executable: ${chromePath}`);
  
  const proc = spawn({
    cmd: [chromePath, '--version'],
    stdout: 'pipe',
  });
  const output = await new Response(proc.stdout).text();
  console.log(`   Version: ${output.trim()}`);
  
  // Test 2: Can chromium open a debug port?
  console.log('\n2️⃣ Testing debug port binding...');
  const debugProc = spawn({
    cmd: [chromePath, '--headless', '--remote-debugging-port=19222', '--no-sandbox'],
    stdout: 'pipe',
    stderr: 'pipe',
  });
  
  // Wait 3 seconds for port to open
  await Bun.sleep(3000);
  
  // Test 3: Can we connect to the port?
  console.log('\n3️⃣ Testing TCP connection to debug port...');
  try {
    const socket = await Bun.connect({
      hostname: '127.0.0.1',
      port: 19222,
      socket: {
        open() { console.log('   ✅ TCP connection succeeded'); },
        close() { console.log('   Socket closed'); },
        data() {},
        error(err) { console.log(`   ❌ Socket error: ${err}`); },
      },
    });
    socket.end();
  } catch (e) {
    console.log(`   ❌ TCP connection failed: ${e}`);
  }
  
  // Test 4: Can we fetch the WebSocket URL?
  console.log('\n4️⃣ Testing CDP endpoint discovery...');
  try {
    const resp = await fetch('http://127.0.0.1:19222/json/version');
    const json = await resp.json();
    console.log(`   WebSocket URL: ${json.webSocketDebuggerUrl}`);
    console.log('   ✅ CDP endpoint accessible');
  } catch (e) {
    console.log(`   ❌ CDP endpoint blocked: ${e}`);
  }
  
  // Cleanup
  debugProc.kill();
  
  console.log('\n━'.repeat(50));
  console.log('Diagnostic complete. Review results above.');
}

diagnose().catch(console.error);
```

---

## 6. Data for Codex Handoff

### What Works
- `bun install` ✅
- `bunx playwright install chromium` ✅
- `bunx playwright --version` ✅
- Chromium binary execution ✅
- Process spawning ✅

### What Blocks
- WebSocket handshake to localhost:PORT ❌
- CDP endpoint discovery ❌
- Any command requiring `browser.launch()` ❌

### Immediate Next Actions (Win11 Bun-Centric)
1. Run `win11-diagnostic.ts` to confirm whether TCP, HTTP, or WebSocket is blocked.
2. Test `--remote-debugging-pipe` in `bun-launcher.ts` to bypass WebSocket.
3. If still blocked, capture WDAC + firewall status for IT (see §3).
4. Use WSL2 as the local validation escape hatch if policy cannot be adjusted.

### Next Logical Steps

1. **Run `win11-diagnostic.ts`** to isolate exact failure point
2. **Test `--remote-debugging-pipe`** flag to bypass WebSocket
3. **Check Windows Event Viewer** for security blocks
4. **Test with Windows Firewall disabled** (if allowed)
5. **Try WSL2** if all Windows paths fail

---

## 7. Architecture Recommendation

Given enterprise Windows 11 constraints, recommend **hybrid architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Developer Workstation                     │
│  ┌──────────────┐    ┌──────────────────────────────────┐  │
│  │   VS Code    │    │           WSL2 Ubuntu            │  │
│  │   (Windows)  │◄──►│  bun + playwright (headless)     │  │
│  │              │    │  - Browser tests run here        │  │
│  │  Edit code   │    │  - WebSocket works               │  │
│  └──────────────┘    └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (git push)
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                           │
│  - Full E2E tests with all browsers                         │
│  - No enterprise security restrictions                       │
│  - Playwright Test Reporter publishes to PR                  │
└─────────────────────────────────────────────────────────────┘
```

This keeps:
- **Bun-centric** development workflow
- **Windows 11** as primary dev environment
- **CI/CD** for full browser coverage
- **WSL2** as escape hatch for local debugging

---

*Document ready for Codex continuation.*
