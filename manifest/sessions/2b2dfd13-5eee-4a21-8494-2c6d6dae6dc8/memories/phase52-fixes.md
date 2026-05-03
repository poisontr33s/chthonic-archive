# Phase 5.2 — District Fix State

## MCP (Restructure-MCP-Orchestration)
- ✅ FIXED + COMMITTED (d4dcfe4)
- tsconfig.json: added `baseUrl: "."` + paths for all @mcp/* packages pointing to src
- Excluded `packages/monitor` (has own tsconfig with jsx: react-jsx)
- Changed `types` in base/shared package.json to `src/index.ts`
- `bunx tsc --noEmit --skipLibCheck` now exits 0 from MCP root
- runner MCP Install Health still uses `bun install` — TODO: change to `bunx pnpm install` or keep bun if it works for symlinks

## Claudine biome.json
- Schema version mismatch: 2.3.5 vs installed 2.4.8
- Unknown keys: `force-include` (now `includes`), `ignore` (inside `files`, now moved)
- Fix: run `bun x biome migrate` in Claudine repo OR manually update the schema URL and key names
- biome.json is at: C:\Users\eldno\Claudine_Supreme-Polyglot-Git-Cli-Lsp-Repo-Clone-Engineering-Bun-Technique\biome.json

## PNK extension.ts
- ✅ Added `iconPath: vscode.ThemeIcon` and `description: string` declarations to PatternItem and PlatformItem
- Runner uses `bunx tsc --noEmit --skipLibCheck` from PNK ROOT (`cwd: "."`)
- PNK root tsconfig: `include: ["**/*.ts"]` — picks up vscode-extension/src/extension.ts
- PNK root tsconfig: `types: ["node", "bun-types"]` — NO vscode types 
- BUT `@types/vscode` may be in PNK root node_modules — check: `ls C:\Users\eldno\PsychoNoir-Kontrapunkt\node_modules\@types\vscode`
- If vscode resolves, PatternItem/PlatformItem fix should work
- Also: `SessionArchiveItem` on line 489 has same iconPath issue — STILL NEEDS FIX
- There may be more SessionArchiveItem-related properties to declare
- Check line 489 area in extension.ts for SessionArchiveItem class definition

## chthonic-archive cargo check
- cmake-0.1.58 build script fails exit code 103
- Pre-existing, likely CMake not found or version mismatch
- Investigate: `cargo check -p <specific-package>` to narrow scope
