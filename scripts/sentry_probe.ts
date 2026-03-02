// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: sentry_probe.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * Sentry Probe (Bun)
 *
 * @SID           TOOL_SENTRY_PROBE_V1
 * @Shabti        CLI Script
 * @Heka-Ayni     CONCEPT_SENTRY_OBSERVABILITY
 * @Ankh-Tinku    STATE_SENTRY_PROBE_ACTIVE
 * @Purpose       Validates Sentry token and fetches issue payloads.
 *                Writes deterministic logs to dumpster-dive/intake/.
 *                No auto-fixing, no secrets written to disk.
 */

import { dirname, join, resolve } from "path";
import { mkdir } from "fs/promises";

function nowStamp(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

function parseArgs(argv: string[]) {
  const args = new Map<string, string | boolean>();
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (next && !next.startsWith("--")) {
      args.set(key, next);
      i++;
    } else {
      args.set(key, true);
    }
  }
  return args;
}

async function findRepoRoot(startDir: string): Promise<string> {
  let cur = resolve(startDir);
  for (;;) {
    const gitDir = join(cur, ".git");
    try {
      if (await Bun.file(gitDir).exists()) return cur;
    } catch {
      // ignore
    }
    const parent = dirname(cur);
    if (parent === cur) break;
    cur = parent;
  }
  return resolve(startDir, "..");
}

type ProbeResult = {
  generatedAt: string;
  baseUrl: string;
  ok: boolean;
  tokenPresent: boolean;
  requests: Array<{
    name: string;
    url: string;
    method: string;
    status: number;
    contentType?: string;
    bodyFile?: string;
    error?: string;
  }>;
};

async function writeText(path: string, text: string) {
  await Bun.write(path, text);
  return path.replaceAll("\\", "/");
}

async function fetchAndLog(
  outDir: string,
  name: string,
  url: string,
  init: RequestInit,
): Promise<ProbeResult["requests"][number]> {
  const req: ProbeResult["requests"][number] = {
    name,
    url,
    method: (init.method ?? "GET").toString(),
    status: 0,
  };

  try {
    const res = await fetch(url, init);
    req.status = res.status;
    req.contentType = res.headers.get("content-type") ?? undefined;

    const bodyText = await res.text();
    const bodyFile = join(outDir, `${name}.body.txt`);
    req.bodyFile = await writeText(bodyFile, bodyText);
  } catch (e) {
    req.error = e instanceof Error ? e.message : String(e);
  }

  return req;
}

async function main() {
  const args = parseArgs(Bun.argv.slice(2));
  const issueId = (args.get("issue") as string | undefined) ?? undefined;
  const org = (args.get("org") as string | undefined) ?? undefined;
  const project = (args.get("project") as string | undefined) ?? undefined;
  const query = (args.get("query") as string | undefined) ?? undefined;

  const token = process.env.SENTRY_AUTH_TOKEN ?? "";
  const baseUrl = (process.env.SENTRY_BASE_URL ?? "https://sentry.io").replace(/\/+$/, "");

  if (!token) {
    console.error("error: SENTRY_AUTH_TOKEN is not set in this process environment");
    process.exit(2);
  }

  const scriptDir = dirname(Bun.fileURLToPath(import.meta.url));
  const repoRoot = await findRepoRoot(scriptDir);

  const outBase = join(repoRoot, "dumpster-dive", "intake", "sentry-probe");
  const stamp = nowStamp();
  const outDir = join(outBase, stamp);
  await mkdir(outDir, { recursive: true });
  await Bun.write(join(outDir, ".keep"), "");

  const headers: HeadersInit = {
    Authorization: `Bearer ${token}`,
    Accept: "application/json",
  };

  const result: ProbeResult = {
    generatedAt: new Date().toISOString(),
    baseUrl,
    ok: false,
    tokenPresent: true,
    requests: [],
  };

  // 1) Basic auth sanity: /api/0/ should return version + user/org if authenticated.
  result.requests.push(
    await fetchAndLog(outDir, "api_0_root", `${baseUrl}/api/0/`, { method: "GET", headers }),
  );

  // 2) Optional: issue fetch by numeric ID.
  if (issueId) {
    const safe = encodeURIComponent(issueId);
    result.requests.push(
      await fetchAndLog(outDir, "issue", `${baseUrl}/api/0/issues/${safe}/`, { method: "GET", headers }),
    );
  }

  // 3) Optional: list/search issues within a project.
  if (org && project) {
    const orgSafe = encodeURIComponent(org);
    const projSafe = encodeURIComponent(project);
    const qs = new URLSearchParams();
    qs.set("limit", "10");
    if (query) qs.set("query", query);
    result.requests.push(
      await fetchAndLog(
        outDir,
        "project_issues",
        `${baseUrl}/api/0/projects/${orgSafe}/${projSafe}/issues/?${qs.toString()}`,
        { method: "GET", headers },
      ),
    );
  }

  result.ok = result.requests.every((r) => r.status >= 200 && r.status < 300);

  const jsonPath = join(outDir, "probe.json");
  await Bun.write(jsonPath, JSON.stringify(result, null, 2));

  console.log(`probe: ${jsonPath.replaceAll("\\", "/")}`);
  const first = result.requests[0];
  console.log(`api/0: ${first?.status ?? 0}`);
  if (issueId) {
    const iss = result.requests.find((r) => r.name === "issue");
    console.log(`issue: ${iss?.status ?? 0}`);
  }
  if (org && project) {
    const list = result.requests.find((r) => r.name === "project_issues");
    console.log(`project_issues: ${list?.status ?? 0}`);
  }
}

await main();
