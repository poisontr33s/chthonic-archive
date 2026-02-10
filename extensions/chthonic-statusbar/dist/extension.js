var __create = Object.create;
var __getProtoOf = Object.getPrototypeOf;
var __defProp = Object.defineProperty;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __toESM = (mod, isNodeMode, target) => {
  target = mod != null ? __create(__getProtoOf(mod)) : {};
  const to = isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target;
  for (let key of __getOwnPropNames(mod))
    if (!__hasOwnProp.call(to, key))
      __defProp(to, key, {
        get: () => mod[key],
        enumerable: true
      });
  return to;
};
var __moduleCache = /* @__PURE__ */ new WeakMap;
var __toCommonJS = (from) => {
  var entry = __moduleCache.get(from), desc;
  if (entry)
    return entry;
  entry = __defProp({}, "__esModule", { value: true });
  if (from && typeof from === "object" || typeof from === "function")
    __getOwnPropNames(from).map((key) => !__hasOwnProp.call(entry, key) && __defProp(entry, key, {
      get: () => from[key],
      enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable
    }));
  __moduleCache.set(from, entry);
  return entry;
};
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, {
      get: all[name],
      enumerable: true,
      configurable: true,
      set: (newValue) => all[name] = () => newValue
    });
};

// src/extension.ts
var exports_extension = {};
__export(exports_extension, {
  deactivate: () => deactivate,
  activate: () => activate
});
module.exports = __toCommonJS(exports_extension);
var vscode = __toESM(require("vscode"));
var import_child_process = require("child_process");
var path = __toESM(require("path"));
var fs = __toESM(require("fs"));
var ssotStatusItem;
var lineageStatusItem;
var pythonLaneStatusItem;
var gpuStatusItem;
var metabolicCycleStatusItem;
var refreshTimer;
var workspaceRoot;
function activate(context) {
  process.env.PYTHONIOENCODING = process.env.PYTHONIOENCODING || "utf-8";
  console.log("\uD83D\uDD25 Chthonic Archive Status Bar extension activated");
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (workspaceFolders && workspaceFolders.length > 0) {
    workspaceRoot = workspaceFolders[0].uri.fsPath;
  }
  metabolicCycleStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  metabolicCycleStatusItem.command = "chthonic.runMetabolicCycle";
  metabolicCycleStatusItem.tooltip = "Click to run metabolic cycle";
  context.subscriptions.push(metabolicCycleStatusItem);
  gpuStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 99);
  gpuStatusItem.command = "chthonic.showGPUStats";
  gpuStatusItem.tooltip = "GPU VRAM usage (click for details)";
  context.subscriptions.push(gpuStatusItem);
  pythonLaneStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 98);
  pythonLaneStatusItem.tooltip = "Python lane version (uv managed)";
  context.subscriptions.push(pythonLaneStatusItem);
  lineageStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 97);
  lineageStatusItem.tooltip = "Active lineage (A: Infrastructure, B: Consolidation, C: Heritage)";
  context.subscriptions.push(lineageStatusItem);
  ssotStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 96);
  ssotStatusItem.command = "chthonic.verifySSO_T";
  ssotStatusItem.tooltip = "SSOT integrity status (click to verify)";
  context.subscriptions.push(ssotStatusItem);
  context.subscriptions.push(vscode.commands.registerCommand("chthonic.refreshStatus", refreshAllStatus), vscode.commands.registerCommand("chthonic.verifySSO_T", verifySSO_T), vscode.commands.registerCommand("chthonic.runMetabolicCycle", runMetabolicCycle), vscode.commands.registerCommand("chthonic.showGPUStats", showGPUStats));
  refreshAllStatus();
  const config = vscode.workspace.getConfiguration("chthonic.statusBar");
  const refreshInterval = config.get("refreshInterval", 30000);
  refreshTimer = setInterval(refreshAllStatus, refreshInterval);
  context.subscriptions.push({ dispose: () => clearInterval(refreshTimer) });
  context.subscriptions.push(vscode.workspace.onDidChangeConfiguration((e) => {
    if (e.affectsConfiguration("chthonic.statusBar")) {
      refreshAllStatus();
    }
  }));
}
function deactivate() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
}
async function refreshAllStatus() {
  const config = vscode.workspace.getConfiguration("chthonic.statusBar");
  if (!config.get("enabled", true)) {
    hideAllItems();
    return;
  }
  if (config.get("ssotHashEnabled", true)) {
    await updateSSO_TStatus();
    ssotStatusItem.show();
  } else {
    ssotStatusItem.hide();
  }
  if (config.get("lineageEnabled", true)) {
    await updateLineageStatus();
    lineageStatusItem.show();
  } else {
    lineageStatusItem.hide();
  }
  if (config.get("pythonLaneEnabled", true)) {
    await updatePythonLaneStatus();
    pythonLaneStatusItem.show();
  } else {
    pythonLaneStatusItem.hide();
  }
  if (config.get("gpuEnabled", true)) {
    await updateGPUStatus();
    gpuStatusItem.show();
  } else {
    gpuStatusItem.hide();
  }
  if (config.get("metabolicCycleEnabled", true)) {
    await updateMetabolicCycleStatus();
    metabolicCycleStatusItem.show();
  } else {
    metabolicCycleStatusItem.hide();
  }
}
function hideAllItems() {
  ssotStatusItem.hide();
  lineageStatusItem.hide();
  pythonLaneStatusItem.hide();
  gpuStatusItem.hide();
  metabolicCycleStatusItem.hide();
}
async function updateSSO_TStatus() {
  try {
    if (!workspaceRoot) {
      ssotStatusItem.text = "$(error) SSOT: No workspace";
      return;
    }
    const ssotPath = path.join(workspaceRoot, "ssot_immunity.py");
    if (!fs.existsSync(ssotPath)) {
      ssotStatusItem.text = "$(question) SSOT";
      ssotStatusItem.tooltip = "SSOT verification script not found";
      return;
    }
    const result = import_child_process.execSync("uv run python ssot_immunity.py --quiet", {
      cwd: workspaceRoot,
      encoding: "utf-8",
      timeout: 5000
    }).trim();
    if (result.includes("✅") || result.includes("VALID")) {
      ssotStatusItem.text = "$(pass) SSOT";
      ssotStatusItem.color = "#A8C686";
    } else if (result.includes("⚠️") || result.includes("DRIFT")) {
      ssotStatusItem.text = "$(warning) SSOT";
      ssotStatusItem.color = "#C9A55A";
    } else {
      ssotStatusItem.text = "$(error) SSOT";
      ssotStatusItem.color = "#B35050";
    }
  } catch (error) {
    ssotStatusItem.text = "$(sync~spin) SSOT";
    ssotStatusItem.tooltip = `SSOT check pending: ${error}`;
  }
}
async function updateLineageStatus() {
  try {
    if (!workspaceRoot) {
      lineageStatusItem.text = "$(git-branch) ???";
      return;
    }
    const branch = import_child_process.execSync("git branch --show-current", {
      cwd: workspaceRoot,
      encoding: "utf-8"
    }).trim();
    let lineage = "?";
    let color = "#B8B8CC";
    if (branch.includes("lineage-a") || branch.includes("infrastructure")) {
      lineage = "A";
      color = "#C75D5D";
    } else if (branch.includes("lineage-b") || branch.includes("consolidation")) {
      lineage = "B";
      color = "#6B9E94";
    } else if (branch.includes("lineage-c") || branch.includes("heritage")) {
      lineage = "C";
      color = "#C9A55A";
    } else {
      const lineageAExists = fs.existsSync(path.join(workspaceRoot, "dumpster-dive", "intake", "templates", "lineage-A-template"));
      const lineageBExists = fs.existsSync(path.join(workspaceRoot, "dumpster-dive", "intake", "templates", "lineage-B-template"));
      const lineageCExists = fs.existsSync(path.join(workspaceRoot, "dumpster-dive", "intake", "templates", "lineage-C-template"));
      lineage = "Ø";
      color = "#E8DDD4";
    }
    lineageStatusItem.text = `$(git-branch) ${lineage}`;
    lineageStatusItem.color = color;
  } catch (error) {
    lineageStatusItem.text = "$(git-branch) ?";
  }
}
async function updatePythonLaneStatus() {
  try {
    const result = import_child_process.execSync("uv run python --version", {
      cwd: workspaceRoot,
      encoding: "utf-8",
      timeout: 3000
    }).trim();
    const match = result.match(/Python\s+(\d+\.\d+(?:\.\d+)?)/);
    if (match) {
      const version = match[1];
      pythonLaneStatusItem.text = `$(symbol-method) ${version}`;
      pythonLaneStatusItem.color = "#6B9E94";
    } else {
      pythonLaneStatusItem.text = "$(symbol-method) ???";
    }
  } catch (error) {
    pythonLaneStatusItem.text = "$(symbol-method) err";
    pythonLaneStatusItem.tooltip = `Python lane error: ${error}`;
  }
}
async function updateGPUStatus() {
  try {
    if (!workspaceRoot) {
      gpuStatusItem.text = "$(device-desktop) ???";
      return;
    }
    try {
      const result = import_child_process.execSync("nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits", {
        encoding: "utf-8",
        timeout: 2000
      }).trim();
      const [used, total] = result.split(",").map((s) => parseInt(s.trim()));
      const usedGB = (used / 1024).toFixed(1);
      const totalGB = (total / 1024).toFixed(1);
      const percent = (used / total * 100).toFixed(0);
      gpuStatusItem.text = `$(device-desktop) ${usedGB}/${totalGB}GB`;
      if (parseInt(percent) < 50) {
        gpuStatusItem.color = "#A8C686";
      } else if (parseInt(percent) < 80) {
        gpuStatusItem.color = "#C9A55A";
      } else {
        gpuStatusItem.color = "#B35050";
      }
    } catch {
      gpuStatusItem.text = "$(device-desktop) N/A";
      gpuStatusItem.tooltip = "GPU stats unavailable (nvidia-smi not found)";
    }
  } catch (error) {
    gpuStatusItem.text = "$(device-desktop) err";
  }
}
async function updateMetabolicCycleStatus() {
  try {
    if (!workspaceRoot) {
      metabolicCycleStatusItem.text = "$(pulse) ???";
      return;
    }
    const autonomousCoordinatorPath = path.join(workspaceRoot, "autonomous_coordinator.py");
    if (!fs.existsSync(autonomousCoordinatorPath)) {
      metabolicCycleStatusItem.text = "$(pulse) N/A";
      return;
    }
    const sessionStatusPath = path.join(workspaceRoot, "AUTONOMOUS_SESSION_STATUS.md");
    if (fs.existsSync(sessionStatusPath)) {
      const stats = fs.statSync(sessionStatusPath);
      const lastModified = stats.mtime;
      const ageMs = Date.now() - lastModified.getTime();
      const ageHours = Math.floor(ageMs / (1000 * 60 * 60));
      const ageDays = Math.floor(ageHours / 24);
      let displayAge = "";
      let color = "#A8C686";
      if (ageDays > 0) {
        displayAge = `${ageDays}d`;
        color = ageDays > 7 ? "#B35050" : "#C9A55A";
      } else if (ageHours > 0) {
        displayAge = `${ageHours}h`;
        color = "#A8C686";
      } else {
        displayAge = "now";
        color = "#6B9E94";
      }
      metabolicCycleStatusItem.text = `$(pulse) ${displayAge}`;
      metabolicCycleStatusItem.color = color;
      metabolicCycleStatusItem.tooltip = `Last metabolic cycle: ${lastModified.toLocaleString()}`;
    } else {
      metabolicCycleStatusItem.text = "$(pulse) ???";
      metabolicCycleStatusItem.tooltip = "No metabolic cycle status found";
    }
  } catch (error) {
    metabolicCycleStatusItem.text = "$(pulse) err";
  }
}
async function verifySSO_T() {
  if (!workspaceRoot) {
    vscode.window.showErrorMessage("No workspace folder found");
    return;
  }
  const terminal = vscode.window.createTerminal({
    name: "SSOT Verification",
    cwd: workspaceRoot
  });
  terminal.show();
  terminal.sendText("uv run python ssot_immunity.py");
  setTimeout(() => updateSSO_TStatus(), 2000);
}
async function runMetabolicCycle() {
  if (!workspaceRoot) {
    vscode.window.showErrorMessage("No workspace folder found");
    return;
  }
  const terminal = vscode.window.createTerminal({
    name: "Metabolic Cycle",
    cwd: workspaceRoot
  });
  terminal.show();
  terminal.sendText("uv run python autonomous_coordinator.py");
  vscode.window.showInformationMessage("\uD83D\uDD25 Metabolic cycle initiated by The Decorator \uD83D\uDC51\uD83D\uDC80⚜️");
  setTimeout(() => {
    refreshAllStatus();
    vscode.window.showInformationMessage("✅ Metabolic cycle complete");
  }, 20000);
}
async function showGPUStats() {
  if (!workspaceRoot) {
    vscode.window.showErrorMessage("No workspace folder found");
    return;
  }
  const terminal = vscode.window.createTerminal({
    name: "GPU Statistics",
    cwd: workspaceRoot
  });
  terminal.show();
  terminal.sendText("nvidia-smi");
}
