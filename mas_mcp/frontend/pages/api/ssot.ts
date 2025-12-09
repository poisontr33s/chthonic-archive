// ═══════════════════════════════════════════════════════════════════════════════
// 🧬 MAS-MCP Dashboard - /api/ssot
// Returns current SSOT hash and metadata
// Implements Section XIV.3 of the Codex Brahmanica Perfectus
// ═══════════════════════════════════════════════════════════════════════════════

import type { NextApiRequest, NextApiResponse } from 'next';
import { getSSOTMetadata, verifyBookend } from '../../lib/ssot';

export interface SSOTResponse {
  path: string;
  size: number;
  hash: string;
  hashShort: string;
  timestamp: string;
}

export interface SSOTVerifyRequest {
  hashStart: string;
}

export interface SSOTVerifyResponse {
  isConsistent: boolean;
  hashStart: string;
  hashEnd: string;
  timestamp: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<SSOTResponse | SSOTVerifyResponse | { error: string }>
) {
  try {
    if (req.method === 'GET') {
      // GET /api/ssot - Return current SSOT metadata and hash
      const metadata = await getSSOTMetadata();
      return res.status(200).json(metadata);
    }
    
    if (req.method === 'POST') {
      // POST /api/ssot - Verify bookend (compare against provided hash)
      const body = req.body as SSOTVerifyRequest;
      
      if (!body?.hashStart || typeof body.hashStart !== 'string') {
        return res.status(400).json({ 
          error: 'Request body must include hashStart: string' 
        });
      }
      
      if (!/^[a-f0-9]{64}$/i.test(body.hashStart)) {
        return res.status(400).json({ 
          error: 'hashStart must be a valid SHA-256 hex digest (64 characters)' 
        });
      }
      
      const result = await verifyBookend(body.hashStart);
      
      return res.status(200).json({
        isConsistent: result.isConsistent,
        hashStart: body.hashStart,
        hashEnd: result.hashEnd,
        timestamp: new Date().toISOString(),
      });
    }
    
    return res.status(405).json({ error: 'Method not allowed' });
    
  } catch (err) {
    console.error('[API] /api/ssot error:', err);
    return res.status(500).json({ 
      error: err instanceof Error ? err.message : 'Internal server error' 
    });
  }
}
