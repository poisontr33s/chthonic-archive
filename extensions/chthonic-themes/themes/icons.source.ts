#!/usr/bin/env bun

// @SID: THEME_ICON_SOURCE_V1

// Icon source manifest — single-line-per-icon format.
// Build target: extensions/chthonic-archive/themes/chthonic-file-icon-theme.json
// Run: bun run scripts/build-icon-theme.ts
//
// Each entry:
//   id        — internal icon key (becomes "_<id>" in theme)
//   svg       — filename in themes/icons/ (without path)
//   ext       — fileExtensions to map (optional)
//   lang      — VS Code languageId(s) to map (optional)
//   names     — exact filenames (fileNames) to map (optional)
//   folder    — if true, expects svg + svg with "-open" suffix for folderNamesExpanded
//   folderFor — folderNames keys this icon applies to

export interface IconEntry {
  id: string;
  svg: string;
  ext?: string[];
  lang?: string[];
  names?: string[];
}

export interface FolderEntry {
  id: string;
  svg: string;      // closed state (e.g. "folder-src.svg")
  svgOpen: string;  // open state  (e.g. "folder-src-open.svg")
  names: string[];
}

export const FILE_ICONS: IconEntry[] = [
  { id: "ts",         svg: "file-ts.svg",         ext: ["ts"],                         lang: ["typescript"] },
  { id: "tsx",        svg: "file-tsx.svg",         ext: ["tsx"],                        lang: ["typescriptreact"] },
  { id: "js",         svg: "file-js.svg",          ext: ["js","mjs","cjs"],             lang: ["javascript"] },
  { id: "jsx",        svg: "file-jsx.svg",         ext: ["jsx"],                        lang: ["javascriptreact"] },
  { id: "rs",         svg: "file-rs.svg",          ext: ["rs"],                         lang: ["rust"] },
  { id: "py",         svg: "file-py.svg",          ext: ["py","pyi"],                   lang: ["python"],        names: ["pyproject.toml"] },
  { id: "json",       svg: "file-json.svg",        ext: ["json","jsonc"],               lang: ["json","jsonc"] },
  { id: "toml",       svg: "file-toml.svg",        ext: ["toml"],                       lang: ["toml"],          names: ["mise.toml",".mise.toml"] },
  { id: "md",         svg: "file-md.svg",          ext: ["md","mdx"],                   lang: ["markdown"] },
  { id: "yml",        svg: "file-yml.svg",         ext: ["yml","yaml"],                 lang: ["yaml"] },
  { id: "ps1",        svg: "file-ps1.svg",         ext: ["ps1","psm1","psd1"],          lang: ["powershell"] },
  { id: "go",         svg: "file-go.svg",          ext: ["go"],                         lang: ["go"] },
  { id: "rb",         svg: "file-rb.svg",          ext: ["rb"],                         lang: ["ruby"] },
  { id: "lock",       svg: "file-lock.svg",        ext: ["lock"],                       names: ["Cargo.lock","bun.lock","uv.lock","package-lock.json","yarn.lock","Gemfile.lock"] },
  { id: "wasm",       svg: "file-wasm.svg",        ext: ["wasm"] },
  { id: "sh",         svg: "file-sh.svg",          ext: ["sh","bash","zsh"],            lang: ["shellscript"] },
  { id: "svg",        svg: "file-svg.svg",         ext: ["svg"] },
  { id: "img",        svg: "file-img.svg",         ext: ["png","jpg","jpeg","gif","webp","ico"] },
  { id: "git",        svg: "file-git.svg",         names: [".gitignore",".gitattributes",".gitmodules",".gitconfig"] },
  { id: "claude",     svg: "file-claude.svg",      names: ["CLAUDE.md"] },
  { id: "copilot",    svg: "file-copilot.svg",     names: ["copilot-instructions.md"] },
  { id: "env",        svg: "file-env.svg",         ext: ["env"],                        names: [".env",".env.local",".env.development",".env.production"] },
  { id: "css",        svg: "file-css.svg",         ext: ["css","scss","less"],          lang: ["css","scss","less"] },
  { id: "html",       svg: "file-html.svg",        ext: ["html","htm"],                 lang: ["html"] },
  { id: "rust_toml",  svg: "file-rust-toml.svg",   names: ["Cargo.toml"] },
  { id: "txt",        svg: "file-txt.svg",         ext: ["txt","text"],                 lang: ["plaintext"] },
  { id: "c",          svg: "file-c.svg",           ext: ["c"],                          lang: ["c"] },
  { id: "h",          svg: "file-h.svg",           ext: ["h","hpp","hh","hxx"] },
  { id: "cpp",        svg: "file-cpp.svg",         ext: ["cc","cpp","cxx"],             lang: ["cpp"] },
  { id: "log",        svg: "file-log.svg",         ext: ["log"],                        lang: ["log"] },
  { id: "csv",        svg: "file-csv.svg",         ext: ["csv","tsv"] },
  { id: "bat",        svg: "file-bat.svg",         ext: ["bat","cmd"],                  lang: ["bat"] },
  { id: "rst",        svg: "file-rst.svg",         ext: ["rst"],                        lang: ["restructuredtext"] },
  { id: "cmake",      svg: "file-cmake.svg",       ext: ["cmake"],                      lang: ["cmake"],         names: ["CMakeLists.txt",".cmake"] },
  { id: "cfg",        svg: "file-cfg.svg",         ext: ["cfg","ini","conf"],           lang: ["ini","properties"], names: [".editorconfig",".pylintrc",".flake8",".prettierrc"] },
  { id: "xml",        svg: "file-xml.svg",         ext: ["xml","xsl","xslt","xsd","wsdl","plist","csproj","sln"], lang: ["xml"] },
  { id: "sql",        svg: "file-sql.svg",         ext: ["sql"],                        lang: ["sql"] },
  { id: "proto",      svg: "file-proto.svg",       ext: ["proto"],                      lang: ["proto3","proto"] },
  { id: "map",        svg: "file-map.svg",         ext: ["map"] },
  { id: "docker",     svg: "file-docker.svg",      lang: ["dockerfile"],                names: ["Dockerfile","dockerfile",".dockerignore","docker-compose.yml","docker-compose.yaml"] },
  { id: "font",       svg: "file-font.svg",        ext: ["ttf","otf","woff","woff2","eot"] },
  { id: "binary",     svg: "file-binary.svg",      ext: ["exe","dll","so","dylib","bin","o","a","lib","pyd","node"] },
  { id: "audio",      svg: "file-audio.svg",       ext: ["mp3","wav","ogg","flac","aac","m4a"] },
  { id: "code_workspace", svg: "file-code-workspace.svg", ext: ["code-workspace"],     names: ["chthonic-archive.code-workspace"] },
  { id: "js_cfg",     svg: "file-js.svg",          names: ["bunfig.toml","package.json"] },
  { id: "ts_cfg",     svg: "file-ts.svg",          names: ["tsconfig.json"] },
];

export const FOLDER_ICONS: FolderEntry[] = [
  { id: "folder_src",       svg: "folder-src.svg",              svgOpen: "folder-src-open.svg",              names: ["src","lib","dev","native"] },
  { id: "folder_github",    svg: "folder-github.svg",           svgOpen: "folder-github-open.svg",           names: [".github"] },
  { id: "folder_scripts",   svg: "folder-scripts.svg",          svgOpen: "folder-scripts-open.svg",          names: ["scripts"] },
  { id: "folder_game",      svg: "folder-game.svg",             svgOpen: "folder-game-open.svg",             names: ["game"] },
  { id: "folder_temple",    svg: "folder-temple.svg",           svgOpen: "folder-temple-open.svg",           names: [".temple","ankh_atlas",".chthonic","lore","chthonic-golden"] },
  { id: "folder_nodemod",   svg: "folder-node-modules.svg",     svgOpen: "folder-node-modules-open.svg",     names: ["node_modules"] },
  { id: "folder_docs",      svg: "folder-docs.svg",             svgOpen: "folder-docs-open.svg",             names: ["docs","doc","documentation"] },
  { id: "folder_assets",    svg: "folder-assets.svg",           svgOpen: "folder-assets-open.svg",           names: ["assets","static","public","media","images","icons","fonts","resources","wasm"] },
  { id: "folder_claude",    svg: "folder-claude.svg",           svgOpen: "folder-claude-open.svg",           names: ["claude",".claude",".claude-plugin","claude-codex-gemini","gemini",".gemini"] },
  { id: "folder_codex",     svg: "folder-codex.svg",            svgOpen: "folder-codex-open.svg",            names: ["codex",".codex"] },
  { id: "folder_ext",       svg: "folder-extensions.svg",       svgOpen: "folder-extensions-open.svg",       names: ["extensions","apps","chthonic-vscode-extension","bun-playwright-poc","mas_mcp","plugins","addons"] },
  { id: "folder_artifacts", svg: "folder-artifacts.svg",        svgOpen: "folder-artifacts-open.svg",        names: ["artifacts","dumpster-dive","logs","pr2_review","WET_PAPER_TO_GOLD_WIP"] },
  { id: "folder_data",      svg: "folder-data.svg",             svgOpen: "folder-data-open.svg",             names: ["data","debugging_data","datasets","models"] },
  { id: "folder_test",      svg: "folder-test.svg",             svgOpen: "folder-test-open.svg",             names: ["test","tests","__tests__","spec","specs"] },
  { id: "folder_build",     svg: "folder-build.svg",            svgOpen: "folder-build-open.svg",            names: ["build","target","dist","out","output",".cache",".cargo",".ruff_cache",".venv","__pycache__",".vscode-test"] },
  { id: "folder_session_archives", svg: "folder-session-archives.svg", svgOpen: "folder-session-archives-open.svg", names: ["session-archives"] },
  { id: "folder_checkpoints", svg: "folder-checkpoints.svg",   svgOpen: "folder-checkpoints-open.svg",      names: ["checkpoints"] },
  { id: "folder_reports",   svg: "folder-reports.svg",          svgOpen: "folder-reports-open.svg",          names: ["reports","reference"] },
  { id: "folder_prompts",   svg: "folder-prompts.svg",          svgOpen: "folder-prompts-open.svg",          names: ["prompts"] },
  { id: "folder_protocols", svg: "folder-protocols.svg",        svgOpen: "folder-protocols-open.svg",        names: ["protocols","ops"] },
  { id: "folder_skills",    svg: "folder-skills.svg",           svgOpen: "folder-skills-open.svg",           names: ["skills"] },
  { id: "folder_governance",svg: "folder-governance.svg",       svgOpen: "folder-governance-open.svg",       names: ["anti-patterns","governance",".vscode","evidence","ledger","standards"] },
  { id: "folder_architecture", svg: "folder-architecture.svg", svgOpen: "folder-architecture-open.svg",     names: ["architecture","design","frameworks","meta-ide",".meta","themes","syntaxes"] },
  { id: "folder_methodology", svg: "folder-methodology.svg",   svgOpen: "folder-methodology-open.svg",      names: ["error-classifier","mcp-apps","methodology"] },
  { id: "folder_handoffs",  svg: "folder-handoffs.svg",         svgOpen: "folder-handoffs-open.svg",         names: ["handoffs"] },
];
