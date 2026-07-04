#!/usr/bin/env bun
// @SID: SCRIPT_VERIFY_LANE_LAUNCH_V1
// Smoke test for mcp-lane: proves the launch plan is well-formed and `claude` is reachable,
// WITHOUT launching a real session -- the dry-run answers the question before it fires.
// (The actual new-window interactive spawn is the conductor's one-time confirm, named below.)

import { buildLaunch } from "./mcp-lane.ts";
import { existsSync } from "fs";

let pass = 0;
let fail = 0;
const check = (cond: boolean, label: string): void => {
  if (cond) {
    pass++;
    console.log(`PASS  ${label}`);
  } else {
    fail++;
    console.log(`FAIL  ${label}`);
  }
};

const repo = process.cwd();
const plan = buildLaunch(repo, {});
const joined = plan.spawnArgs.join(" ");

check(plan.spawnCmd === "pwsh", "spawn uses pwsh");
check(joined.includes("launch-sonnet-lane.ps1"), "spawn targets the launcher script (same method, one level up)");
check(joined.includes("'-Model','sonnet'"), "default model sonnet (plan weekly quota)");
check(joined.includes("'-Effort','max'"), "default effort max (max thinking)");
check(existsSync(plan.script), "launcher script exists on disk");

check(buildLaunch(repo, { effort: "bogus" }).spawnArgs.join(" ").includes("'-Effort','max'"), "invalid effort falls back to max");
check(buildLaunch(repo, { effort: "xhigh" }).spawnArgs.join(" ").includes("'-Effort','xhigh'"), "valid effort xhigh passes through");
check(buildLaunch(repo, { model: "opus" }).spawnArgs.join(" ").includes("'-Model','opus'"), "model override passes through");

// Ground truth for a real launch: claude must be resolvable. No session is spawned.
const claude = Bun.which("claude");
check(!!claude, `claude resolvable on PATH${claude ? ` (${claude})` : ""}`);

console.log("");
console.log(fail === 0 ? `PASS -- all ${pass} checks` : `FAIL -- ${fail} failed, ${pass} passed`);
console.log("(conductor confirm, out of safe-test scope: run launch_lane non-dry-run once -> a new window opens a Sonnet lane on its brief.)");
process.exit(fail === 0 ? 0 : 1);
