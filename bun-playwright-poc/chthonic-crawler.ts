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
  const seed = process.argv[2] || 'Circular Economy';
  const keywords = seed.split(' ');
  
  const crawler = new ChthonicCrawler({
    seed,
    maxDepth: 1,      // Reduced for demo
    maxPages: 5,      // Reduced for demo
    heuristic: createKeywordHeuristic(keywords),
    outputDir: './crawl-output',
  });

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

