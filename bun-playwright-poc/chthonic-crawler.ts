// @SID: SCRIPT_CHTHONIC_CRAWLER_V1
// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: chthonic-crawler.ts                           ║
// ║  TypeScript module: frontend utility                                        ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency: ORANGE                                                 ║
// ║  Architectural Role: 🔭 THE OBSERVATORY                                      ║
// ║  Purpose: * Chthonic Crawler - Agentic Web Explorer                        ║
// ║           * Uses bun-cdp to autonomously explore the web                   ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Cross-References (Bidirectional):                                      ║
// ║    (Standalone file - no detected dependencies)                          ║
// ╚════════════════════════════════════════════════════════════════════════════╝

/**
 * Chthonic Crawler - Agentic Web Explorer
 * 
 * Uses bun-cdp to autonomously explore the web from a seed topic,
 * building a local knowledge graph with screenshots.
 * 
 * Architecture:
 * ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
 * │   SEED      │────▶│   SEARCH    │────▶│   EXTRACT   │
 * │  (topic)    │     │  (DuckDuckGo)│     │  (text/links)│
 * └─────────────┘     └─────────────┘     └──────┬──────┘
 *                                                │
 *       ┌────────────────────────────────────────┘
 *       ▼
 * ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
 * │   FILTER    │────▶│   RECURSE   │────▶│   OUTPUT    │
 * │ (heuristic) │     │  (depth N)  │     │ (JSON/MD)   │
 * └─────────────┘     └─────────────┘     └─────────────┘
 * 
 * @module chthonic-crawler
 */

import { ChthonicCrawler, createKeywordHeuristic } from './src';

// ============================================================
// Main Entry Point
// ============================================================

async function main() {
  const args = process.argv.slice(2);
  const localLlmEnabled = args.includes('--local-llm') || process.env.CHTHONIC_LOCAL_LLM === '1';
  const seed = args.find((arg) => !arg.startsWith('--')) || 'Circular Economy';
  const llmEndpointArg = args.find((arg) => arg.startsWith('--llm-endpoint='));
  const llmModelArg = args.find((arg) => arg.startsWith('--llm-model='));
  const llmEndpoint = llmEndpointArg?.slice('--llm-endpoint='.length) || process.env.CHTHONIC_LOCAL_LLM_ENDPOINT;
  const llmModel = llmModelArg?.slice('--llm-model='.length) || process.env.CHTHONIC_LOCAL_LLM_MODEL;
  const keywords = seed.split(' ');
  
  const crawler = new ChthonicCrawler({
    seed,
    maxDepth: 1,      // Reduced for demo
    maxPages: 5,      // Reduced for demo
    heuristic: createKeywordHeuristic(keywords),
    outputDir: './crawl-output',
    localLLM: {
      enabled: localLlmEnabled,
      endpoint: llmEndpoint,
      model: llmModel,
      apiKeyEnvVar: 'LOCAL_LLM_API_KEY',
    },
  });

  if (localLlmEnabled) {
    console.log('🧠 Local LLM reranker: ENABLED');
    if (llmEndpoint) {
      console.log(`   Endpoint: ${llmEndpoint}`);
    }
    if (llmModel) {
      console.log(`   Model: ${llmModel}`);
    }
  }

  try {
    await crawler.init();
    await crawler.crawl();
    await crawler.saveGraph();
  } finally {
    await crawler.close();
  }
  
  console.log('\n🏁 Crawl complete.');
}

await main().catch(err => {
  console.error('❌ Crawler error:', err.message);
  process.exit(1);
});
