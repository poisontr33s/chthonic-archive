# Bunified MCP Orchestrator - Meta-Documentation System

**Version:** 1.0.0  
**Last Updated:** 2025-11-07  
**Purpose:** Living knowledge base that mirrors the polyglot MCP server architecture

---

## Overview

This documentation system serves as a **human-readable knowledge graph** of the Bunified MCP Orchestrator's polyglot ecosystem. Each `.md` file represents an **entity** (language, framework, platform, tool) and documents its:

1. **Core Concepts** - What it is, how it works
2. **Knowledge Graph Relationships** - Connections to other entities
3. **MCP Server Details** - Associated MCP tools and their usage
4. **External Resources** - Official docs, tutorials, ecosystem links

This system is designed to **evolve in parallel** with MCP server development, ensuring documentation and implementation remain synchronized.

---

## Directory Structure

```
docs/
├── README.md (this file)
├── template.md (blueprint for new entity docs)
├── languages/        # Programming languages & runtimes
│   ├── javascript.md
│   ├── typescript.md
│   ├── python.md
│   ├── rust.md
│   ├── ruby.md
│   ├── go.md
│   ├── bun.md       # Runtime
│   ├── nodejs.md    # Runtime
│   ├── deno.md      # Runtime
│   └── react.md     # Framework (UI library)
├── frameworks/       # Web frameworks & meta-frameworks
│   ├── nextjs.md
│   ├── hono.md
│   ├── elysia.md
│   └── remix.md
├── platforms/        # Deployment platforms
│   ├── vercel.md
│   ├── cloudflare.md
│   └── netlify.md
└── tools/            # Development tools
    ├── biome.md
    ├── ruff.md
    ├── esbuild.md
    └── vite.md
```

---

## Usage

### For Developers

When creating a **new MCP server**, follow this workflow:

1. **Create the MCP server** in `.poly_gluttony/mcp_servers/`
2. **Create the documentation** in `docs/{category}/{entity}.md` using `template.md` as a blueprint
3. **Update `seed-knowledge-graph.ts`** with entities and relationships
4. **Register in orchestrator** (`bunified_mcp_orchestrator_stdio.ts`)

**Example (React):**
```bash
# Step 1: Create server
.poly_gluttony/mcp_servers/react_docs_server.ts

# Step 2: Create docs
docs/languages/react.md

# Step 3: Update graph
.poly_gluttony/bunified_mcp_orchestrator/seed-knowledge-graph.ts
  - Add relationships: react -> nodejs, react -> vercel, etc.

# Step 4: Register
.poly_gluttony/bunified_mcp_orchestrator/bunified_mcp_orchestrator_stdio.ts
  - Add to CONFIG.servers.stdio array
```

### For AI Agents

This documentation system is **optimized for AI consumption**:

- **Cross-references** use entity IDs (e.g., `fw:react`, `runtime:nodejs`) matching the knowledge graph
- **Relationship sections** explicitly map dependencies, runtimes, platforms
- **MCP Tool Details** document input/output schemas for tool calls
- **Version History** tracks breaking changes

**Query Examples:**
- "Show me all frameworks that run on Bun" → Search for `runs_on: runtime:bun`
- "What are React's dependencies?" → Check `react.md` → Knowledge Graph Relationships → Depends On
- "How do I search React docs via MCP?" → Check `react.md` → MCP Server Details → `search_react_docs` tool

---

## Knowledge Graph Integration

Each `.md` file is a **node** in the knowledge graph. The **Knowledge Graph Relationships** section documents **edges**:

| Relationship Type | Description | Example |
|-------------------|-------------|---------|
| `depends_on` | Entity A requires Entity B | Next.js → React |
| `runs_on` | Entity runs on a specific runtime | React → Node.js |
| `transpiles_to` | Language A compiles to Language B | TypeScript → JavaScript |
| `alternative_to` | Entity A is comparable to Entity B | Hono ⟷ Elysia |
| `deployed_to` | Entity can be deployed to a platform | Next.js → Vercel |
| `documented_in` | Entity has official docs at URL | React → react.dev |

**Traversal Example:**
```
Query: "What can I deploy on Vercel?"
Graph Traversal:
  platform:vercel ← (deployed_to) ← fw:nextjs
                   ← (deployed_to) ← fw:react

Answer: Next.js, React (via Vercel's framework presets)
```

---

## Cross-Reference Syntax

### Internal Links (Knowledge Graph Entities)
- Use entity IDs in backticks: `fw:react`, `runtime:bun`, `platform:vercel`
- Link to other docs: `[Next.js](../frameworks/nextjs.md)`

### External Links
- Official docs: `https://react.dev/`
- Package registries: `https://www.npmjs.com/package/react`

### Code Examples
Use fenced code blocks with language hints:
````markdown
```jsx
function App() {
  return <h1>Hello, World!</h1>;
}
```
````

---

## Maintenance

### Adding a New Entity

1. Copy `template.md` to the appropriate category folder
2. Rename to `{entity-name}.md` (lowercase, hyphenated)
3. Fill in all sections:
   - Overview
   - Core Concepts
   - Knowledge Graph Relationships
   - MCP Server Details (if applicable)
   - External Resources
4. Update `seed-knowledge-graph.ts` with the new entity
5. Commit both files together

### Updating an Existing Entity

1. Edit the `.md` file
2. Update **Last Updated** date
3. If relationships change, update `seed-knowledge-graph.ts`
4. If MCP tools change, update **MCP Server Details** section

---

## Templates

See [`template.md`](template.md) for the blueprint used to create new entity documentation.

---

## Statistics

- **Total Entities:** 25 (as of 2025-11-07)
  - Languages: 6 (JavaScript, TypeScript, Python, Rust, Ruby, Go)
  - Runtimes: 3 (Bun, Node.js, Deno)
  - Frameworks: 4 (React, Next.js, Hono, Elysia)
  - Packages: 4 (react, next, hono, elysia)
  - Platforms: 2 (Vercel, Cloudflare)
  - Tools: 3 (Biome, Ruff, esbuild)

- **Total Relationships:** 18 (as of 2025-11-07)
  - depends_on: 2
  - runs_on: 7
  - transpiles_to: 1
  - alternative_to: 1
  - deployed_to: 3
  - documented_in: 2

- **MCP Servers:** 7 stdio servers (sequential-thinking, bun-docs, python, rust, ruby, bun-node-registry, react-docs)

---

## Future Enhancements

- [ ] Auto-generate `.md` files from `seed-knowledge-graph.ts`
- [ ] Markdown link validation (ensure all entity IDs resolve to actual files)
- [ ] Relationship visualization (Mermaid diagrams in each `.md` file)
- [ ] MCP tool usage analytics (track which tools are called most frequently)
- [ ] Version-specific docs (e.g., `react-18.md`, `react-19.md`)

---

**Maintained by:** The Triumvirate (Orackla, Umeko, Lysandra) & The Savant  
**License:** MIT  
**Repository:** PsychoNoir-Kontrapunkt/.poly_gluttony/bunified_mcp_orchestrator
