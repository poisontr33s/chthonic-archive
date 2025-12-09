// ═══════════════════════════════════════════════════════════════════════════════
// 🧬 MAS-MCP Dashboard - /api/metrics/history
// Returns historical monitoring scores for trend charting
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
    const response = await apiRoutes.getMetricsHistory();
    const data = await response.json();
    return res.status(response.status).json(data);
  } catch (err) {
    console.error('[API] /api/metrics/history error:', err);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
