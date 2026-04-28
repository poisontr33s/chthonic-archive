import { readFile } from 'node:fs/promises';
import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const revalidate = 1;

export async function GET() {
  const snapshotPath = process.env.CHTHONIC_LANE_STATE_PATH;
  if (!snapshotPath) {
    return NextResponse.json({
      status: 'missing_env',
      reason: 'CHTHONIC_LANE_STATE_PATH is not set',
      lanes: [],
    });
  }

  try {
    const snapshot = JSON.parse(await readFile(snapshotPath, 'utf8'));
    return NextResponse.json({ status: 'ok', ...snapshot });
  } catch (error) {
    return NextResponse.json({
      status: 'unavailable',
      reason: error instanceof Error ? error.message : String(error),
      lanes: [],
    });
  }
}
