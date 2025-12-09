// ═══════════════════════════════════════════════════════════════════════════════
// 🧬 MAS-MCP Dashboard - /api/metrics
// Returns aggregated metrics for the last 7 days
// ═══════════════════════════════════════════════════════════════════════════════

import type { NextApiRequest, NextApiResponse } from 'next';
import { apiRoutes } from '../../../api/routes';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const response = await apiRoutes.getMetrics();
    const data = await response.json();
    return res.status(response.status).json(data);
  } catch (err) {
    console.error('[API] /api/metrics error:', err);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
