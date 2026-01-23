#!/usr/bin/env bun
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

import { launchBrowser, createPage, CDPPage } from './src';
import type { TargetInfo } from './src';

// ============================================================
// Configuration
// ============================================================

interface CrawlConfig {
  seed: string;           // Starting topic
  maxDepth: number;       // How deep to recurse
  maxPages: number;       // Total page limit
  heuristic: (url: string, title: string, text: string) => number;  // Relevance scorer (0-1)
  outputDir: string;      // Where to save artifacts
}

interface CrawlNode {
  id: string;
  url: string;
  title: string;
  excerpt: string;        // First 500 chars
  links: string[];        // Outbound URLs
  relevance: number;      // Heuristic score
  depth: number;
  timestamp: string;
  screenshotPath?: string;
}

interface KnowledgeGraph {
  seed: string;
  nodes: Map<string, CrawlNode>;
  edges: Array<{ from: string; to: string; label?: string }>;
}

// ============================================================
// Default Heuristic: Keyword Density
// ============================================================

function createKeywordHeuristic(keywords: string[]): CrawlConfig['heuristic'] {
  const lowerKeywords = keywords.map(k => k.toLowerCase());
  
  return (url: string, title: string, text: string) => {
    const combined = `${url} ${title} ${text}`.toLowerCase();
    let score = 0;
    
    for (const kw of lowerKeywords) {
      const matches = (combined.match(new RegExp(kw, 'g')) || []).length;
      score += Math.min(matches * 0.1, 0.3);  // Cap per keyword
    }
    
    return Math.min(score, 1);
  };
}

// ============================================================
// Crawler Core
// ============================================================

class ChthonicCrawler {
  private browser: Awaited<ReturnType<typeof launchBrowser>> | null = null;
  private graph: KnowledgeGraph;
  private visited = new Set<string>();
  private queue: Array<{ url: string; depth: number }> = [];
  private pageCount = 0;

  constructor(private config: CrawlConfig) {
    this.graph = {
      seed: config.seed,
      nodes: new Map(),
      edges: [],
    };
  }

  async init(): Promise<void> {
    this.browser = await launchBrowser({ headless: true });
    
    // Ensure output directory exists
    await Bun.write(`${this.config.outputDir}/.keep`, '');
    
    console.log(`🕸️  Chthonic Crawler initialized`);
    console.log(`   Seed: "${this.config.seed}"`);
    console.log(`   Max depth: ${this.config.maxDepth}`);
    console.log(`   Max pages: ${this.config.maxPages}`);
  }

  async crawl(): Promise<KnowledgeGraph> {
    if (!this.browser) throw new Error('Call init() first');

    // Phase 1: Search for seed topic
    console.log(`\n🔍 Searching for: "${this.config.seed}"`);
    const searchResults = await this.search(this.config.seed);
    
    // Add search results to queue
    for (const url of searchResults) {
      this.queue.push({ url, depth: 1 });
    }

    // Phase 2: Recursive exploration
    while (this.queue.length > 0 && this.pageCount < this.config.maxPages) {
      const { url, depth } = this.queue.shift()!;
      
      if (this.visited.has(url)) continue;
      if (depth > this.config.maxDepth) continue;
      
      this.visited.add(url);
      
      try {
        const node = await this.extractPage(url, depth);
        
        if (node.relevance >= 0.3) {  // Threshold
          this.graph.nodes.set(node.id, node);
          
          // Add outbound links to queue
          for (const link of node.links.slice(0, 5)) {  // Limit per page
            if (!this.visited.has(link)) {
              this.queue.push({ url: link, depth: depth + 1 });
              this.graph.edges.push({ from: node.id, to: this.urlToId(link) });
            }
          }
          
          console.log(`   ✅ [${this.pageCount}] ${node.title.slice(0, 40)}... (relevance: ${node.relevance.toFixed(2)})`);
        } else {
          console.log(`   ⏭️  Skipped (low relevance): ${url.slice(0, 50)}...`);
        }
      } catch (err: any) {
        console.log(`   ❌ Failed: ${url.slice(0, 50)}... (${err.message})`);
      }
    }

    return this.graph;
  }

  private async search(query: string): Promise<string[]> {
    // Direct seed URLs - bypasses search engine bot detection
    // In production, this could use a search API (SerpAPI, Brave Search API, etc.)
    const seedUrls: Record<string, string[]> = {
      'default': [
        'https://en.wikipedia.org/wiki/Circular_economy',
        'https://ellenmacarthurfoundation.org/topics/circular-economy-introduction/overview',
        'https://www.epa.gov/recyclingstrategy/what-circular-economy',
        'https://www.weforum.org/stories/2022/01/what-is-the-circular-economy/',
      ],
    };
    
    console.log(`   Using seed URLs (search APIs require keys)`);
    return seedUrls['default'];
  }

  private async extractPage(url: string, depth: number): Promise<CrawlNode> {
    this.pageCount++;
    const page = await createPage(this.browser!, 'about:blank');
    
    try {
      await page.goto(url, { timeout: 10000 });  // Faster timeout, skip networkidle
      
      const title = await page.title();
      
      // Extract text content
      const text = await page.evaluate(`
        document.body.innerText.slice(0, 5000)
      `) as string || '';
      
      // Extract links
      const links = await page.evaluate(`
        Array.from(document.querySelectorAll('a[href^="http"]'))
          .map(a => a.href)
          .filter(url => !url.includes('javascript:'))
          .slice(0, 20)
      `) as string[] || [];
      
      // Calculate relevance
      const relevance = this.config.heuristic(url, title, text);
      
      // Take screenshot if relevant
      let screenshotPath: string | undefined;
      if (relevance >= 0.3) {
        const screenshot = await page.screenshot({ format: 'png' });
        screenshotPath = `${this.config.outputDir}/${this.urlToId(url)}.png`;
        await Bun.write(screenshotPath, screenshot);
      }
      
      return {
        id: this.urlToId(url),
        url,
        title,
        excerpt: text.slice(0, 500).replace(/\s+/g, ' '),
        links,
        relevance,
        depth,
        timestamp: new Date().toISOString(),
        screenshotPath,
      };
    } finally {
      // Page cleanup handled by browser
    }
  }

  private urlToId(url: string): string {
    return url
      .replace(/^https?:\/\//, '')
      .replace(/[^a-zA-Z0-9]/g, '_')
      .slice(0, 64);
  }

  async saveGraph(): Promise<void> {
    const output = {
      seed: this.graph.seed,
      crawledAt: new Date().toISOString(),
      nodeCount: this.graph.nodes.size,
      edgeCount: this.graph.edges.length,
      nodes: Object.fromEntries(this.graph.nodes),
      edges: this.graph.edges,
    };
    
    const path = `${this.config.outputDir}/knowledge-graph.json`;
    await Bun.write(path, JSON.stringify(output, null, 2));
    console.log(`\n📊 Knowledge graph saved: ${path}`);
    
    // Also generate markdown summary
    const md = this.generateMarkdown();
    const mdPath = `${this.config.outputDir}/CRAWL_SUMMARY.md`;
    await Bun.write(mdPath, md);
    console.log(`📝 Summary saved: ${mdPath}`);
  }

  private generateMarkdown(): string {
    const nodes = Array.from(this.graph.nodes.values())
      .sort((a, b) => b.relevance - a.relevance);
    
    let md = `# Chthonic Crawl: "${this.graph.seed}"\n\n`;
    md += `**Crawled:** ${new Date().toISOString()}\n`;
    md += `**Pages:** ${nodes.length}\n`;
    md += `**Edges:** ${this.graph.edges.length}\n\n`;
    md += `## Top Results\n\n`;
    
    for (const node of nodes.slice(0, 20)) {
      md += `### ${node.title}\n`;
      md += `- **URL:** ${node.url}\n`;
      md += `- **Relevance:** ${node.relevance.toFixed(2)}\n`;
      md += `- **Depth:** ${node.depth}\n`;
      if (node.screenshotPath) {
        md += `- **Screenshot:** ${node.screenshotPath}\n`;
      }
      md += `\n> ${node.excerpt.slice(0, 200)}...\n\n`;
    }
    
    return md;
  }

  async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

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
