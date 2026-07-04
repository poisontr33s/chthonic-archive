import { expect, test } from "bun:test";
import { mkdtempSync, readFileSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const run = async (...args: string[]) => {
  const proc = Bun.spawn(["bun", "run", "src/cli.ts", ...args], { cwd: import.meta.dir + "/.." });
  const out = await new Response(proc.stdout).text();
  await proc.exited;
  return out.trim();
};

const withTemp = async (fn: (root: string) => Promise<void>) => {
  const root = mkdtempSync(join(tmpdir(), "mdseal-"));
  try { await fn(root); } finally { rmSync(root, { recursive: true, force: true }); }
};

test("dry-run never writes", async () => {
  await withTemp(async (root) => {
    const file = join(root, "a.md");
    writeFileSync(file, "Math $5 − 3$.");
    const before = readFileSync(file, "utf-8");
    await run("fix", file, "--dry-run");
    expect(readFileSync(file, "utf-8")).toBe(before);
  });
});

test("write creates backup", async () => {
  await withTemp(async (root) => {
    const file = join(root, "a.md");
    writeFileSync(file, "Math $5 − 3$.");
    await run("fix", file, "--write");
    expect(existsSync(`${file}.mdseal.bak`)).toBe(true);
  });
});

test("seal refuses overwrite without force", async () => {
  await withTemp(async (root) => {
    const file = join(root, "a.md");
    writeFileSync(file, "x");
    await run("seal", file);
    const second = await run("seal", file);
    expect(second).toContain("MDSEAL_REFUSE_EXISTING_SEAL_WITHOUT_FORCE");
  });
});

test("restore refuses hash-only raw restore", async () => {
  await withTemp(async (root) => {
    const file = join(root, "a.md");
    writeFileSync(file, "x");
    await run("seal", file, "--hash-only");
    const out = await run("restore", file, "--dry-run");
    expect(out).toContain("MDSEAL_REFUSE_SEAL_HASH_ONLY_RESTORE");
  });
});

test("restore refuses context mismatch", async () => {
  await withTemp(async (root) => {
    const file = join(root, "a.md");
    writeFileSync(file, "x");
    await run("seal", file);
    writeFileSync(file, "changed");
    const out = await run("restore", file, "--dry-run");
    expect(out).toContain("MDSEAL_REFUSE_SEAL_CONTEXT_MISMATCH");
  });
});

test("json output has stable shape", async () => {
  const out = await run("check", "CLAUDEBASE/usables/mdseal/examples/sealed-research.md");
  const parsed = JSON.parse(out);
  expect(parsed.command).toBe("check");
  expect(Array.isArray(parsed.files)).toBe(true);
  expect(parsed.summary).toHaveProperty("filesChecked");
});
