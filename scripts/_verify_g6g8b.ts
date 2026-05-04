#!/usr/bin/env bun
import { Database } from "bun:sqlite";
const db = new Database("manifest/corpus.sqlite", { readonly: true });
const counts = db.prepare("SELECT kind, COUNT(*) as n FROM entities GROUP BY kind ORDER BY n DESC").all();
console.log("entities by kind:", JSON.stringify(counts));
const occ = db.prepare("SELECT COUNT(*) as n FROM entity_occurrences").get() as { n: number };
console.log("entity_occurrences:", occ.n);
const sr = db.prepare("SELECT sessionId, ROUND(recencyScore,4) as rs, ROUND(signalScore,4) as ss FROM session_ranked LIMIT 3").all();
console.log("session_ranked sample:", JSON.stringify(sr));
db.close();
