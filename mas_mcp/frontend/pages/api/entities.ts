// @SID: MAS_ENTITIES_V1
// ═══════════════════════════════════════════════════════════════════════════════
// 🧬 MAS-MCP Dashboard - /api/entities
// Returns entity registry data
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
    const response = await apiRoutes.getEntities();
    const data = await response.json();
    return res.status(response.status).json(data);
  } catch (err) {
    console.error('[API] /api/entities error:', err);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
