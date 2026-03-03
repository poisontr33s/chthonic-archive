// @SID: FORGE_TEST_FIXTURES_V1
// Purpose: Recovered test fixture index from corpse-vault test fragments.
// Source-Files: dumpster-dive/forge/extension-archaeology/diagnostics-tests/source-code.test.ts, dumpster-dive/forge/extension-archaeology/diagnostics-tests/source-code.test.ts, dumpster-dive/forge/extension-archaeology/diagnostics-tests/package-config.test.ts
// Pathway: test fragments -> fixture metadata extraction -> reusable registry
// Kept: Fixture names, source provenance, and recovered labels.
// Discarded: Broken module imports and deleted execution context.
export interface RecoveredFixture {
  sourceFile: string;
  name: string;
  hash: string;
}

export const recoveredFixtures: RecoveredFixture[] = [
  { sourceFile: 'dumpster-dive/forge/extension-archaeology/diagnostics-tests/source-code.test.ts', name: 'statusbar extension has UTF-8 enforcement', hash: '32dcc7d8e66b26d7' },
  { sourceFile: 'dumpster-dive/forge/extension-archaeology/diagnostics-tests/source-code.test.ts', name: 'python regex is correctly escaped', hash: '8fbbac79fdacb40f' },
  { sourceFile: 'dumpster-dive/forge/extension-archaeology/diagnostics-tests/package-config.test.ts', name: 'mandala has theme contribution', hash: 'c537c5c89c6495c2' },
];

export function findRecoveredFixtures(keyword: string): RecoveredFixture[] {
  const lowered = keyword.toLowerCase();
  return recoveredFixtures.filter((fixture) => fixture.sourceFile.toLowerCase().includes(lowered) || fixture.name.toLowerCase().includes(lowered));
}
