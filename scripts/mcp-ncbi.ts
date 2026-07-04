#!/usr/bin/env bun
// @SID: SCRIPT_MCP_NCBI_V1

/**
 * mcp-ncbi — generalized NCBI E-utilities MCP server.
 *
 * This server wraps the official E-utilities surface documented by NCBI:
 *   - EInfo
 *   - ESearch
 *   - EPost
 *   - ESummary
 *   - EFetch
 *   - ELink
 *   - EGQuery
 *   - ESpell
 *   - ECitMatch
 *
 * It is designed for "all types of content" reachable via Entrez databases,
 * not just PubMed. Any valid Entrez database string can be passed to the
 * generic tools. The NCBI API key, if present in ~/.chthonic/api_pool.json,
 * is sent as `api_key` on each request. A tool name and contact email are also
 * attached when configured, per NCBI usage guidance.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const REPO_ROOT = process.cwd();
const NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils";
const TOOL_NAME = "chthonic-archive-ncbi-mcp";
const DEFAULT_THROTTLE_MS = 334;
const KEYED_THROTTLE_MS = 100;

type JsonLike = Record<string, unknown>;

function getEnv(name: string): string {
  return String(process.env[name] ?? "").trim();
}

function normalize(value: unknown): string {
  let v = String(value ?? "").trim();
  if (v.startsWith("<") && v.endsWith(">") && v.length >= 3) {
    v = v.slice(1, -1).trim();
  }
  if (/^Bearer\s+/i.test(v)) {
    v = v.replace(/^Bearer\s+/i, "").trim();
  }
  return v;
}

const API_KEY = normalize(getEnv("NCBI_API_KEY"));
const CONTACT_EMAIL = normalize(getEnv("NCBI_ADMIN_EMAIL") || getEnv("NCBI_EMAIL"));

let requestQueue = Promise.resolve();
let lastRequestStartedAt = 0;

function queue<T>(task: () => Promise<T>): Promise<T> {
  const run = requestQueue.then(async () => {
    const minDelay = API_KEY ? KEYED_THROTTLE_MS : DEFAULT_THROTTLE_MS;
    const now = Date.now();
    const wait = Math.max(0, lastRequestStartedAt + minDelay - now);
    if (wait > 0) {
      await new Promise((resolve) => setTimeout(resolve, wait));
    }
    lastRequestStartedAt = Date.now();
    return task();
  });
  requestQueue = run.then(() => undefined, () => undefined);
  return run;
}

function encodeParams(params: JsonLike): URLSearchParams {
  const out = new URLSearchParams();
  for (const [key, raw] of Object.entries(params)) {
    if (raw === undefined || raw === null) continue;
    if (Array.isArray(raw)) {
      const joined = raw
        .map((item) => normalize(item))
        .filter((item) => item.length > 0)
        .join(",");
      if (joined) out.set(key, joined);
      continue;
    }
    if (typeof raw === "boolean") {
      out.set(key, raw ? "y" : "n");
      continue;
    }
    const value = normalize(raw);
    if (value.length > 0) out.set(key, value);
  }
  if (API_KEY) out.set("api_key", API_KEY);
  out.set("tool", TOOL_NAME);
  if (CONTACT_EMAIL) out.set("email", CONTACT_EMAIL);
  return out;
}

async function ncbiRequest(
  endpoint: string,
  params: JsonLike,
  method: "GET" | "POST" = "GET",
): Promise<{
  endpoint: string;
  method: string;
  url: string;
  status: number;
  contentType: string;
  parsed?: unknown;
  body?: string;
}> {
  const url = new URL(`${NCBI_BASE}/${endpoint}`);
  const bodyParams = encodeParams(params);
  let response: Response;
  if (method === "GET") {
    url.search = bodyParams.toString();
    response = await fetch(url, {
      headers: {
        Accept: "application/json, text/xml, application/xml, text/plain;q=0.9, */*;q=0.8",
      },
    });
  } else {
    response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Accept: "application/json, text/xml, application/xml, text/plain;q=0.9, */*;q=0.8",
      },
      body: bodyParams.toString(),
    });
  }

  const contentType = response.headers.get("content-type") || "";
  const text = await response.text();
  let parsed: unknown;
  if (/json/i.test(contentType) || /^[{\[]/.test(text.trim())) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = undefined;
    }
  }
  return {
    endpoint,
    method,
    url: response.url || url.toString(),
    status: response.status,
    contentType,
    ...(parsed !== undefined ? { parsed } : { body: text }),
  };
}

function toolInput(properties: JsonLike, required: string[] = []) {
  return {
    type: "object",
    properties,
    required,
  };
}

const CONTENT_FAMILIES = {
  literature: ["pubmed", "pmc", "books", "nlmcatalog", "mesh"],
  sequence: ["nucleotide", "protein", "genome", "assembly", "biosample", "bioproject", "sra"],
  variation: ["snp", "clinvar", "dbvar", "omim"],
  chemistry: ["pubchem", "pccompound", "pcsubstance", "pcassay"],
  expression: ["gene", "gds", "geo", "gtr", "medgen"],
  structure: ["structure", "cdd", "proteinclusters", "proteinfamilies"],
  taxonomy: ["taxonomy"],
  collections: ["biocollections", "gap"],
} as const;

const server = new Server(
  { name: "ncbi", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "ncbi_request",
      description:
        "Low-level NCBI E-utilities request helper. Call any official E-utility endpoint directly (einfo, esearch, epost, esummary, efetch, elink, egquery, espell, ecitmatch) by name, with arbitrary parameters. This is the escape hatch for any Entrez-supported content type or edge-case parameter combination. Use when a convenience wrapper is missing or when you need exact control over request method, rettype/retmode, history keys, or link parameters.",
      inputSchema: toolInput(
        {
          endpoint: {
            type: "string",
            enum: [
              "einfo.fcgi",
              "esearch.fcgi",
              "epost.fcgi",
              "esummary.fcgi",
              "efetch.fcgi",
              "elink.fcgi",
              "egquery.fcgi",
              "espell.fcgi",
              "ecitmatch.cgi",
            ],
          },
          method: { type: "string", enum: ["GET", "POST"], default: "GET" },
          params: {
            type: "object",
            additionalProperties: true,
            description: "Endpoint parameters as key/value pairs.",
          },
        },
        ["endpoint"],
      ),
    },
    {
      name: "ncbi_database_info",
      description:
        "Get database metadata and field/link definitions from EInfo. With no db specified, returns the global Entrez database list. With db specified, returns that database's index fields, link names, and update metadata. Use this to discover what content types and links are available before searching or fetching.",
      inputSchema: toolInput({
        db: {
          type: "string",
          description: "Optional Entrez database name, e.g. pubmed, pmc, nucleotide, protein, gene, taxonomy, structure.",
        },
      }),
    },
    {
      name: "ncbi_search",
      description:
        "Search any Entrez database with ESearch. Works across literature, sequence, variation, chemistry, expression, taxonomy, and structure databases as long as the db name is valid. Supports history server mode for large workflows. Returns ids plus query translation metadata.",
      inputSchema: toolInput(
        {
          db: { type: "string", description: "Entrez database name." },
          term: { type: "string", description: "Entrez query string." },
          retmax: { type: "number", default: 20 },
          retstart: { type: "number", default: 0 },
          sort: { type: "string" },
          usehistory: { type: "boolean", default: false },
          idtype: { type: "string", enum: ["acc", "gi"] },
          datetype: { type: "string" },
          mindate: { type: "string" },
          maxdate: { type: "string" },
          reldate: { type: "number" },
        },
        ["db", "term"],
      ),
    },
    {
      name: "ncbi_summary",
      description:
        "Get ESummary records for any Entrez database. Accepts a comma-separated ids list, or a history server pair (webenv + query_key). Use version 2.0 JSON for structured summaries when available. Good for document metadata, article summaries, sequence summaries, and similar record overviews.",
      inputSchema: toolInput(
        {
          db: { type: "string" },
          ids: { type: "array", items: { type: "string" } },
          webenv: { type: "string" },
          query_key: { type: "string" },
          retstart: { type: "number", default: 0 },
          retmax: { type: "number", default: 20 },
        },
        ["db"],
      ),
    },
    {
      name: "ncbi_fetch",
      description:
        "Fetch full records with EFetch from any Entrez database. Accepts ids or history server keys, plus rettype and retmode. This is the generic record retrieval tool for full text, FASTA, GenBank, XML, ASN.1, and other database-specific formats supported by NCBI.",
      inputSchema: toolInput(
        {
          db: { type: "string" },
          ids: { type: "array", items: { type: "string" } },
          webenv: { type: "string" },
          query_key: { type: "string" },
          rettype: { type: "string" },
          retmode: { type: "string" },
          retstart: { type: "number", default: 0 },
          retmax: { type: "number", default: 20 },
          strand: { type: "number" },
          seq_start: { type: "number" },
          seq_stop: { type: "number" },
        },
        ["db"],
      ),
    },
    {
      name: "ncbi_link",
      description:
        "Run ELink to discover cross-database relationships, same-db neighbors, and link-outs. Useful for moving between PubMed, PMC, Gene, Protein, Nucleotide, Structure, and other Entrez databases without guessing the linkage path.",
      inputSchema: toolInput(
        {
          dbfrom: { type: "string" },
          db: { type: "string" },
          ids: { type: "array", items: { type: "string" } },
          linkname: { type: "string" },
          cmd: { type: "string" },
          webenv: { type: "string" },
          query_key: { type: "string" },
        },
        ["dbfrom"],
      ),
    },
    {
      name: "ncbi_post",
      description:
        "Upload a UID set to the E-utilities history server with EPost. Use when you want to batch subsequent ESummary, EFetch, or ELink calls against a stable query_key/WebEnv pair rather than sending large id lists repeatedly.",
      inputSchema: toolInput(
        {
          db: { type: "string" },
          ids: { type: "array", items: { type: "string" } },
        },
        ["db", "ids"],
      ),
    },
    {
      name: "ncbi_global_query",
      description:
        "Run EGQuery to see how a search term distributes across the Entrez database family. This is useful when you want to know which NCBI content types are actually surfacing matches before narrowing to one database.",
      inputSchema: toolInput({
        term: { type: "string" },
      }, ["term"]),
    },
    {
      name: "ncbi_spell",
      description:
        "Run ESpell to get spelling suggestions for a query in a database-aware way. Helpful when biological terms, gene symbols, or publication titles are misspelled.",
      inputSchema: toolInput(
        {
          db: { type: "string" },
          term: { type: "string" },
        },
        ["db", "term"],
      ),
    },
    {
      name: "ncbi_citmatch",
      description:
        "Run ECitMatch for batch citation matching against PubMed. Provide one or more citations and the server resolves them to PMIDs when possible. This is the bibliographic matching tool for reference repair and citation normalization.",
      inputSchema: toolInput(
        {
          citations: {
            type: "array",
            items: {
              type: "object",
              additionalProperties: true,
              properties: {
                journal: { type: "string" },
                year: { type: "string" },
                volume: { type: "string" },
                first_page: { type: "string" },
                author: { type: "string" },
                title: { type: "string" },
                key: {
                  type: "string",
                  description: "Optional local citation identifier echoed back by ECitMatch.",
                },
              },
            },
            description: "Citation objects. At minimum provide the fields that identify your reference.",
          },
        },
        ["citations"],
      ),
    },
    {
      name: "ncbi_content_map",
      description:
        "Return a curated starter map of common Entrez content families and example database names. Use this when you need to pick the right db for literature, sequence, variation, chemistry, structure, taxonomy, or expression content. Any valid Entrez database string can still be used directly in the generic tools.",
      inputSchema: toolInput({}),
    },
  ],
}));

function asText(value: unknown): string {
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function citationToBdata(c: JsonLike): string {
  const parts = [
    normalize(c.journal),
    `year|${normalize(c.year)}`,
    `volume|${normalize(c.volume)}`,
    `first_page|${normalize(c.first_page)}`,
    normalize(c.author),
    normalize(c.key || c.title),
  ];
  return `${parts.map((p) => p.replace(/\|/g, " ")).join("|")}|`;
}

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;
  const a = (args ?? {}) as Record<string, unknown>;

  try {
    if (name === "ncbi_request") {
      const endpoint = String(a.endpoint ?? "").trim();
      if (!endpoint) throw new Error("ncbi_request requires endpoint.");
      const method = String(a.method ?? "GET").toUpperCase() === "POST" ? "POST" : "GET";
      const params = (a.params && typeof a.params === "object" ? a.params : {}) as JsonLike;
      const result = await queue(() => ncbiRequest(endpoint, params, method));
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "ncbi_database_info") {
      const db = String(a.db ?? "").trim();
      const params: JsonLike = db ? { db, retmode: "json" } : { retmode: "json" };
      const result = await queue(() => ncbiRequest("einfo.fcgi", params, "GET"));
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "ncbi_search") {
      const result = await queue(() =>
        ncbiRequest("esearch.fcgi", {
          db: a.db,
          term: a.term,
          retmax: a.retmax ?? 20,
          retstart: a.retstart ?? 0,
          sort: a.sort,
          usehistory: a.usehistory ?? false,
          idtype: a.idtype,
          datetype: a.datetype,
          mindate: a.mindate,
          maxdate: a.maxdate,
          reldate: a.reldate,
          retmode: "json",
        }),
      );
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "ncbi_summary") {
      const ids = Array.isArray(a.ids) ? a.ids : [];
      const params: JsonLike = {
        db: a.db,
        id: ids.length > 0 ? ids : undefined,
        webenv: a.webenv,
        query_key: a.query_key,
        retstart: a.retstart ?? 0,
        retmax: a.retmax ?? 20,
        version: "2.0",
        retmode: "json",
      };
      const result = await queue(() => ncbiRequest("esummary.fcgi", params, "GET"));
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "ncbi_fetch") {
      const ids = Array.isArray(a.ids) ? a.ids : [];
      const params: JsonLike = {
        db: a.db,
        id: ids.length > 0 ? ids : undefined,
        webenv: a.webenv,
        query_key: a.query_key,
        rettype: a.rettype,
        retmode: a.retmode,
        retstart: a.retstart ?? 0,
        retmax: a.retmax ?? 20,
        strand: a.strand,
        seq_start: a.seq_start,
        seq_stop: a.seq_stop,
      };
      const method = ids.length > 50 ? "POST" : "GET";
      const result = await queue(() => ncbiRequest("efetch.fcgi", params, method));
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "ncbi_link") {
      const ids = Array.isArray(a.ids) ? a.ids : [];
      const params: JsonLike = {
        dbfrom: a.dbfrom,
        db: a.db,
        id: ids.length > 0 ? ids : undefined,
        linkname: a.linkname,
        cmd: a.cmd,
        webenv: a.webenv,
        query_key: a.query_key,
        retmode: "json",
      };
      const result = await queue(() => ncbiRequest("elink.fcgi", params, "GET"));
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "ncbi_post") {
      const ids = Array.isArray(a.ids) ? a.ids : [];
      const result = await queue(() =>
        ncbiRequest(
          "epost.fcgi",
          {
            db: a.db,
            id: ids,
          },
          ids.length > 50 ? "POST" : "GET",
        ),
      );
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "ncbi_global_query") {
      const result = await queue(() =>
        ncbiRequest("egquery.fcgi", { term: a.term, retmode: "json" }, "GET"),
      );
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "ncbi_spell") {
      const result = await queue(() =>
        ncbiRequest("espell.fcgi", { db: a.db, term: a.term, retmode: "json" }, "GET"),
      );
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "ncbi_citmatch") {
      const citations = Array.isArray(a.citations) ? (a.citations as JsonLike[]) : [];
      if (citations.length === 0) throw new Error("ncbi_citmatch requires citations.");
      const bdata = citations.map(citationToBdata).join("\r");
      const result = await queue(() =>
        ncbiRequest(
          "ecitmatch.cgi",
          {
            db: "pubmed",
            retmode: "xml",
            bdata,
          },
          "POST",
        ),
      );
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }

    if (name === "ncbi_content_map") {
      const payload = {
        note:
          "Curated starter map only. Any valid Entrez database name can still be passed to ncbi_request/ncbi_search/ncbi_summary/ncbi_fetch/ncbi_link.",
        families: CONTENT_FAMILIES,
        common_databases: [
          "pubmed",
          "pmc",
          "books",
          "nlmcatalog",
          "mesh",
          "nucleotide",
          "protein",
          "gene",
          "genome",
          "assembly",
          "biosample",
          "bioproject",
          "sra",
          "structure",
          "taxonomy",
          "clinvar",
          "snp",
          "dbvar",
          "omim",
          "pubchem",
          "gds",
          "geo",
          "gtr",
        ],
      };
      return { content: [{ type: "text", text: JSON.stringify(payload, null, 2) }] };
    }
  } catch (error) {
    return {
      content: [{ type: "text", text: `${name} error: ${String(error)}` }],
      isError: true,
    };
  }

  return {
    content: [{ type: "text", text: `Unknown tool: ${name}` }],
    isError: true,
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
