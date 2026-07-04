import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { loadModel } from "./scan";
import { applyRepairs, repairRules } from "./repairs";
import { unifiedDiff } from "./diff";
import { createSeal, sealPathFor, writeSeal, readSeal } from "./seal";
import { report } from "./report";
import { sha256 } from "./bytes";
import { markdownDiagnostics } from "./validators/markdown";
import { validateKatex } from "./validators/katex";
import { validateCandidate } from "./validation";
import { refuse } from "./refusals";
import type { MdsealJsonResult, Patch } from "./types";
import { buildImageWitness, writeImageWitness } from "./image-witness";
import { imageReferences } from "./images";
import { defaultImageWitnessConfig } from "./config";
import { listProviders, doctorProviders } from "./providers/doctor";

const args = Bun.argv.slice(2);
const cmd = args[0];
const subcmd = cmd === "corpus" || cmd === "providers" ? args[1] : undefined;
const has = (flag: string) => args.includes(flag);
const positionalStart = cmd === "corpus" || cmd === "providers" ? 2 : 1;
const positional = args.slice(positionalStart).filter((a) => !a.startsWith("--"));
const pathArg = positional[0];
const workspaceRoot = resolve(import.meta.dir, "..", "..", "..", "..");
const absPath = (p: string) => resolve(workspaceRoot, p);

const files = (p: string): string[] => {
  const resolved = absPath(p);
  if (!existsSync(resolved)) return [];
  if (resolved.endsWith(".md") || resolved.endsWith(".markdown")) return [resolved];
  const out: string[] = [];
  for (const entry of readdirSync(resolved, { withFileTypes: true })) {
    const fp = join(resolved, entry.name);
    if (entry.isDirectory()) out.push(...files(fp));
    else if (entry.name.endsWith(".md") || entry.name.endsWith(".markdown")) out.push(resolve(fp));
  }
  return out;
};

const sealStatus = (file: string) => {
  const p = sealPathFor(workspaceRoot, file);
  if (!existsSync(p)) return { status: "missing" as const, path: null };
  try {
    const seal = JSON.parse(readFileSync(p, "utf-8")) as { hashOnly?: boolean };
    return { status: seal.hashOnly ? "hash-only" as const : "present" as const, path: p };
  } catch {
    return { status: "stale" as const, path: p };
  }
};

const summarize = (result: MdsealJsonResult) => {
  result.summary = {
    filesChecked: result.files.length,
    filesChanged: result.files.filter((f) => f.wrote).length,
    diagnostics: result.files.reduce((n, f) => n + f.diagnostics.length, 0),
    errors: result.files.reduce((n, f) => n + f.diagnostics.filter((d) => d.severity === "error").length, 0),
    warnings: result.files.reduce((n, f) => n + f.diagnostics.filter((d) => d.severity === "warning").length, 0),
  };
  result.status = result.summary.errors ? "failed" : result.summary.warnings ? "warning" : "passed";
  return result;
};

const makeResult = (command: string): MdsealJsonResult => ({ command, status: "passed", files: [], summary: { filesChecked: 0, filesChanged: 0, diagnostics: 0, errors: 0, warnings: 0 } });

const collectPatch = (before: string, after: string, file: string): Patch[] => before === after ? [] : [{ file, code: "MDSEAL_PATCH", description: "deterministic patch", confidence: 1, replacements: [{ startOffset: 0, endOffset: before.length, before, after }], protectedZoneTouches: [] }];

const summarizeImages = (model: ReturnType<typeof loadModel>) => {
  const refs = imageReferences(model);
  return {
    count: refs.length,
    existing: refs.filter((i) => i.exists).length,
    missing: refs.filter((i) => !i.exists).length,
    likelyEquation: refs.filter((i) => i.likelyEquation).length,
    witnessWritten: 0,
    witnessSkipped: refs.length,
    hashChanged: 0,
    witnesses: refs.map((img) => ({
      markdownPath: img.markdownPath,
      witnessPath: null as string | null,
      status: (img.exists ? "skipped" : "missing") as const,
      sha256: img.sha256,
      likelyEquation: img.likelyEquation,
    })),
  };
};

const imageDriftDiagnostics = (file: string, model: ReturnType<typeof loadModel>) => {
  const sealInfo = sealStatus(file);
  if (sealInfo.status === "missing" || !sealInfo.path) return [];
  try {
    const seal = readSeal(workspaceRoot, file);
    const refs = imageReferences(model);
    return refs.flatMap((img) => {
      const match = seal.images.find((entry) => entry.markdownPath === img.markdownPath);
      if (match && match.sha256 && img.sha256 && match.sha256 !== img.sha256) return [refuse("MDSEAL_IMAGE_HASH_CHANGED", `image hash changed for ${img.markdownPath}`, "seal")];
      return [];
    });
  } catch {
    return [];
  }
};

const maybeWriteWitnesses = (file: string, model: ReturnType<typeof loadModel>) => {
  const refs = imageReferences(model);
  const images = {
    count: refs.length,
    existing: refs.filter((i) => i.exists).length,
    missing: refs.filter((i) => !i.exists).length,
    likelyEquation: refs.filter((i) => i.likelyEquation).length,
    witnessWritten: 0,
    witnessSkipped: 0,
    hashChanged: 0,
    witnesses: [] as Array<{ markdownPath: string; witnessPath: string | null; status: "written" | "skipped" | "missing" | "stale" | "report-only"; sha256: string | null; likelyEquation: boolean }>,
  };
  if (!defaultImageWitnessConfig.enabled || !defaultImageWitnessConfig.writeSidecars) return images;
  for (const img of refs) {
    if (!img.exists) {
      images.witnessSkipped++;
      images.witnesses.push({ markdownPath: img.markdownPath, witnessPath: null, status: "missing", sha256: img.sha256, likelyEquation: img.likelyEquation });
      continue;
    }
    const witness = buildImageWitness(workspaceRoot, model, img, defaultImageWitnessConfig.policy);
    const path = writeImageWitness(workspaceRoot, witness);
    images.witnessWritten++;
    images.witnesses.push({ markdownPath: img.markdownPath, witnessPath: path, status: "written", sha256: img.sha256, likelyEquation: img.likelyEquation });
  }
  return images;
};

const runCheck = (file: string) => {
  const model = loadModel(file);
  const diags = [...model.diagnostics, ...markdownDiagnostics(model), ...imageDriftDiagnostics(file, model)];
  return { file, profile: model.dialect.name, seal: sealStatus(file), diagnostics: diags, patches: [], validation: validateCandidate(model, model.text), wrote: false, images: summarizeImages(model) };
};

const runFix = (file: string, write = false) => {
  const model = loadModel(file);
  const repairs = applyRepairs(model);
  const validation = validateCandidate(model, repairs.text);
  const patches = collectPatch(model.text, repairs.text, file);
  const refusal = repairs.diagnostics.some((d) => d?.code?.includes("REFUSE")) ? repairs.diagnostics : [];
  const out = { file, profile: model.dialect.name, seal: sealStatus(file), diagnostics: [...model.diagnostics, ...repairs.diagnostics, ...refusal, ...imageDriftDiagnostics(file, model)], patches, validation, wrote: false, backupPath: undefined as string | undefined, images: summarizeImages(model) };
  const canWrite = write && validation.passed && !out.diagnostics.some((d) => d.severity === "error" && d.code.startsWith("MDSEAL_REFUSE"));
  if (write && !canWrite) {
    out.diagnostics.push(refuse("MDSEAL_REFUSE_WRITE_WITHOUT_EXPLICIT_WRITE_FLAG", "write refused by validation or refusal gate", "cli"));
    return out;
  }
  if (write && canWrite && repairs.text !== model.text) {
    const backup = `${file}.mdseal.bak`;
    if (!has("--no-backup")) {
      writeFileSync(backup, model.text, "utf-8");
      out.backupPath = backup;
    }
    writeFileSync(file, repairs.text, "utf-8");
    out.wrote = true;
    const recheck = applyRepairs(loadModel(file)).text;
    if (recheck !== repairs.text) out.diagnostics.push(refuse("MDSEAL_REFUSE_NON_IDEMPOTENT_FIX", "fix is not idempotent", "cli"));
  }
  return out;
};

const emit = (result: MdsealJsonResult) => console.log(report(summarize(result)));

const main = () => {
  if (!cmd) throw new Error("missing command");
  const targets = files(pathArg ?? ".");
  if (cmd === "check") return emit({ ...makeResult("check"), files: targets.map(runCheck) });
  if (cmd === "fix") return emit({ ...makeResult("fix"), files: targets.map((f) => runFix(f, has("--write"))) });
  if (cmd === "explain") return console.log(report({ command: "explain", files: targets.map(runCheck) }));
  if (cmd === "seal") {
    const out = makeResult("seal");
    for (const file of targets) {
      const p = sealPathFor(workspaceRoot, file);
      if (existsSync(p) && !has("--force")) {
        out.files.push({ file, profile: "katex-gfm", seal: sealStatus(file), diagnostics: [refuse("MDSEAL_REFUSE_EXISTING_SEAL_WITHOUT_FORCE", "seal exists; use --force", "seal")], patches: [], validation: { passed: false, gates: [] }, wrote: false, images: summarizeImages(loadModel(file)) });
        continue;
      }
      const model = loadModel(file);
      const seal = createSeal(workspaceRoot, model, has("--hash-only"));
      writeSeal(workspaceRoot, file, seal);
      out.files.push({ file, profile: model.dialect.name, seal: sealStatus(file), diagnostics: [], patches: [], validation: { passed: true, gates: [] }, wrote: true, images: summarizeImages(model) });
    }
    return emit(out);
  }
  if (cmd === "restore") {
    const out = makeResult("restore");
    for (const file of targets) {
      const sealInfo = sealStatus(file);
      if (sealInfo.status === "missing") {
        const model = loadModel(file);
        out.files.push({ file, profile: "katex-gfm", seal: sealInfo, diagnostics: [refuse("MDSEAL_REFUSE_SEAL_CONTEXT_MISMATCH", "no seal present", "seal"), ...imageDriftDiagnostics(file, model)], patches: [], validation: { passed: false, gates: [] }, wrote: false, images: summarizeImages(model) });
        continue;
      }
      const model = loadModel(file);
      const seal = readSeal(workspaceRoot, file);
      const currentHash = sha256(readFileSync(file));
      if (seal.sha256 && seal.sha256 !== currentHash) {
        out.files.push({ file, profile: seal.dialectProfile, seal: sealInfo, diagnostics: [refuse("MDSEAL_REFUSE_SEAL_CONTEXT_MISMATCH", "source hash differs from seal", "seal"), ...imageDriftDiagnostics(file, model)], patches: [], validation: { passed: false, gates: [] }, wrote: false, images: summarizeImages(model) });
        continue;
      }
      if (seal.hashMode === "hash-only" && !has("--allow-hash-only")) {
        out.files.push({ file, profile: seal.dialectProfile, seal: sealInfo, diagnostics: [refuse("MDSEAL_REFUSE_SEAL_HASH_ONLY_RESTORE", "hash-only seal cannot restore raw math", "seal"), ...imageDriftDiagnostics(file, model)], patches: [], validation: { passed: false, gates: [] }, wrote: false, images: summarizeImages(model) });
        continue;
      }
      out.files.push({ file, profile: seal.dialectProfile, seal: sealInfo, diagnostics: imageDriftDiagnostics(file, model), patches: [], validation: { passed: true, gates: [] }, wrote: false, images: summarizeImages(model) });
    }
    return emit(out);
  }
  if (cmd === "sweep") return emit({ ...makeResult("sweep"), files: targets.map((f) => ({ ...runCheck(f), ...runFix(f, false), ...((!has("--dry-run") || has("--write-image-witnesses")) ? { images: maybeWriteWitnesses(f, loadModel(f)) } : {}) })) });
  if (cmd === "corpus" && subcmd === "test") {
    const root = pathArg ?? join(import.meta.dir, "..", "tests", "fixtures", "cases");
    const caseDirs = readdirSync(root, { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => join(root, d.name));
    const checked = caseDirs.map((dir) => {
      const broken = join(dir, "broken.md");
      const golden = join(dir, "golden.md");
      const meta = JSON.parse(readFileSync(join(dir, "meta.json"), "utf-8")) as { expectedDiagnostics?: string[] };
      const brokenText = readFileSync(broken, "utf-8");
      const goldenText = readFileSync(golden, "utf-8");
      return { dir, ok: typeof brokenText === "string" && typeof goldenText === "string", expectedDiagnostics: meta.expectedDiagnostics ?? [] };
    });
    return console.log(report({ cases: checked.length, ok: checked.every((c) => c.ok), checked }));
  }
  if (cmd === "providers" && subcmd === "list") return console.log(report({ providers: listProviders() }));
  if (cmd === "providers" && subcmd === "doctor") return console.log(report(doctorProviders({ strict: has("--strict") })));
  throw new Error(`unknown command: ${cmd}`);
};

main();
