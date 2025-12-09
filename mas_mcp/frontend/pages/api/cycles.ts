// ═══════════════════════════════════════════════════════════════════════════════
// 🧬 MAS-MCP Dashboard - /api/cycles
// Returns cycle reports with optional date filter and pagination
// ═══════════════════════════════════════════════════════════════════════════════

import type { NextApiRequest, NextApiResponse } from 'next';
import { apiRoutes } from '../../api/routes';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Create a mock Request object for the route handler
    const url = new URL(`http://localhost/api/cycles?${new URLSearchParams(req.query as Record<string, string>).toString()}`);
    const mockReq = new Request(url.toString());
    
    const response = await apiRoutes.getCycles(mockReq);
    const data = await response.json();
    return res.status(response.status).json(data);
  } catch (err) {
    console.error('[API] /api/cycles error:', err);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
