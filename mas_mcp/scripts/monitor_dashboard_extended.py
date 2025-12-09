#!/usr/bin/env python3
"""
MAS-MCP Genesis Dashboard — Extended Monitor with CSV Logging
Usage: python monitor_dashboard_extended.py [BASE_URL] [--csv PATH] [--summary]

Features:
- All health checks from base monitor
- CSV logging for historical drift analysis
- Daily summary generation
- Trend detection (improving/degrading/stable)

Cron examples:
  # Every 15 minutes: log to CSV
  */15 * * * * python3 /path/to/monitor_dashboard_extended.py https://your-app.vercel.app --csv /var/log/mas_mcp_metrics.csv

  # Daily at midnight: generate summary
  0 0 * * * python3 /path/to/monitor_dashboard_extended.py https://your-app.vercel.app --csv /var/log/mas_mcp_metrics.csv --summary
"""

import sys
import os
import json
import csv
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path

# SLO Thresholds
SLO_EXCELLENT = 90
SLO_ACCEPTABLE = 70
SLO_CRITICAL = 35

# Trend detection window (hours)
TREND_WINDOW_HOURS = 24

@dataclass
class MetricsSnapshot:
    timestamp: str
    quality_score: float
    latency_p95: float
    acceptance_rate: float
    entity_count: int
    history_count: int
    status: str
    endpoints_ok: int
    endpoints_total: int

@dataclass
class DailySummary:
    date: str
    samples: int
    avg_quality: float
    min_quality: float
    max_quality: float
    avg_latency: float
    max_latency: float
    avg_acceptance: float
    degraded_count: int
    trend: str  # "improving", "degrading", "stable"

def fetch_json(url: str, timeout: int = 10) -> tuple[bool, Optional[dict], Optional[str]]:
    """Fetch JSON from endpoint. Returns (success, data, error)."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            return True, data, None
    except urllib.error.URLError as e:
        return False, None, str(e)
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {e}"

def evaluate_slo(quality_score: float) -> str:
    """Evaluate SLO and return status label."""
    if quality_score >= SLO_EXCELLENT:
        return "EXCELLENT"
    elif quality_score >= SLO_ACCEPTABLE:
        return "ACCEPTABLE"
    elif quality_score >= SLO_CRITICAL:
        return "DEGRADED"
    else:
        return "CRITICAL"

def collect_metrics(base_url: str) -> Optional[MetricsSnapshot]:
    """Collect all metrics from dashboard endpoints."""
    timestamp = datetime.now().isoformat()
    endpoints_ok = 0
    endpoints_total = 4
    
    # Fetch /api/metrics
    success, metrics, _ = fetch_json(f"{base_url}/api/metrics")
    if not success:
        return None
    
    endpoints_ok += 1
    quality_score = metrics.get('qualityScore', 0)
    latency_p95 = metrics.get('latencyP95', 0)
    acceptance_rate = metrics.get('acceptanceRate', 0)
    
    # Fetch /api/metrics/history
    success, history, _ = fetch_json(f"{base_url}/api/metrics/history")
    history_count = len(history) if success and isinstance(history, list) else 0
    if success:
        endpoints_ok += 1
    
    # Fetch /api/monitoring
    success, _, _ = fetch_json(f"{base_url}/api/monitoring")
    if success:
        endpoints_ok += 1
    
    # Fetch /api/entities
    success, entities, _ = fetch_json(f"{base_url}/api/entities")
    entity_count = 0
    if success:
        endpoints_ok += 1
        entity_list = entities.get('entities', [])
        entity_count = len(entity_list) if isinstance(entity_list, list) else 0
    
    status = evaluate_slo(quality_score)
    
    return MetricsSnapshot(
        timestamp=timestamp,
        quality_score=quality_score,
        latency_p95=latency_p95,
        acceptance_rate=acceptance_rate,
        entity_count=entity_count,
        history_count=history_count,
        status=status,
        endpoints_ok=endpoints_ok,
        endpoints_total=endpoints_total
    )

def append_to_csv(snapshot: MetricsSnapshot, csv_path: Path):
    """Append metrics snapshot to CSV file."""
    file_exists = csv_path.exists()
    
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(snapshot).keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(asdict(snapshot))

def read_csv_history(csv_path: Path, hours: int = 24) -> list[MetricsSnapshot]:
    """Read CSV and return snapshots from the last N hours."""
    if not csv_path.exists():
        return []
    
    cutoff = datetime.now() - timedelta(hours=hours)
    snapshots = []
    
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts = datetime.fromisoformat(row['timestamp'])
                if ts >= cutoff:
                    snapshots.append(MetricsSnapshot(
                        timestamp=row['timestamp'],
                        quality_score=float(row['quality_score']),
                        latency_p95=float(row['latency_p95']),
                        acceptance_rate=float(row['acceptance_rate']),
                        entity_count=int(row['entity_count']),
                        history_count=int(row['history_count']),
                        status=row['status'],
                        endpoints_ok=int(row['endpoints_ok']),
                        endpoints_total=int(row['endpoints_total'])
                    ))
            except (ValueError, KeyError):
                continue
    
    return snapshots

def detect_trend(snapshots: list[MetricsSnapshot]) -> str:
    """Detect quality score trend from snapshots."""
    if len(snapshots) < 4:
        return "insufficient_data"
    
    scores = [s.quality_score for s in snapshots]
    
    # Compare first quarter average to last quarter average
    quarter = len(scores) // 4
    first_avg = sum(scores[:quarter]) / quarter
    last_avg = sum(scores[-quarter:]) / quarter
    
    diff = last_avg - first_avg
    
    if diff > 5:
        return "improving"
    elif diff < -5:
        return "degrading"
    else:
        return "stable"

def generate_daily_summary(csv_path: Path, date: Optional[str] = None) -> Optional[DailySummary]:
    """Generate summary for a specific date (default: today)."""
    if not csv_path.exists():
        return None
    
    target_date = date or datetime.now().strftime('%Y-%m-%d')
    snapshots = []
    
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts = datetime.fromisoformat(row['timestamp'])
                if ts.strftime('%Y-%m-%d') == target_date:
                    snapshots.append(MetricsSnapshot(
                        timestamp=row['timestamp'],
                        quality_score=float(row['quality_score']),
                        latency_p95=float(row['latency_p95']),
                        acceptance_rate=float(row['acceptance_rate']),
                        entity_count=int(row['entity_count']),
                        history_count=int(row['history_count']),
                        status=row['status'],
                        endpoints_ok=int(row['endpoints_ok']),
                        endpoints_total=int(row['endpoints_total'])
                    ))
            except (ValueError, KeyError):
                continue
    
    if not snapshots:
        return None
    
    qualities = [s.quality_score for s in snapshots]
    latencies = [s.latency_p95 for s in snapshots]
    acceptances = [s.acceptance_rate for s in snapshots]
    degraded = sum(1 for s in snapshots if s.status in ("DEGRADED", "CRITICAL"))
    
    return DailySummary(
        date=target_date,
        samples=len(snapshots),
        avg_quality=round(sum(qualities) / len(qualities), 2),
        min_quality=min(qualities),
        max_quality=max(qualities),
        avg_latency=round(sum(latencies) / len(latencies), 3),
        max_latency=max(latencies),
        avg_acceptance=round(sum(acceptances) / len(acceptances), 2),
        degraded_count=degraded,
        trend=detect_trend(snapshots)
    )

def print_summary(summary: DailySummary):
    """Print formatted daily summary."""
    trend_emoji = {"improving": "📈", "degrading": "📉", "stable": "➡️", "insufficient_data": "❓"}
    status_emoji = "🟢" if summary.avg_quality >= SLO_EXCELLENT else "🟡" if summary.avg_quality >= SLO_ACCEPTABLE else "🔴"
    
    print(f"\n{'='*60}")
    print(f"📊 MAS-MCP Daily Summary — {summary.date}")
    print(f"{'='*60}")
    print(f"Samples collected:     {summary.samples}")
    print(f"")
    print(f"Quality Score:")
    print(f"  {status_emoji} Average:           {summary.avg_quality}%")
    print(f"     Min:               {summary.min_quality}%")
    print(f"     Max:               {summary.max_quality}%")
    print(f"  {trend_emoji.get(summary.trend, '❓')} Trend:             {summary.trend}")
    print(f"")
    print(f"Latency P95:")
    print(f"     Average:           {summary.avg_latency}ms")
    print(f"     Max:               {summary.max_latency}ms")
    print(f"")
    print(f"Acceptance Rate:")
    print(f"     Average:           {summary.avg_acceptance}%")
    print(f"")
    print(f"Governance:")
    print(f"  {'🔴' if summary.degraded_count > 0 else '✅'} Degraded samples:   {summary.degraded_count}")
    print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(description='MAS-MCP Dashboard Extended Monitor')
    parser.add_argument('base_url', nargs='?', default='http://localhost:3000', help='Dashboard base URL')
    parser.add_argument('--csv', type=str, help='Path to CSV log file')
    parser.add_argument('--summary', action='store_true', help='Generate daily summary instead of collecting metrics')
    parser.add_argument('--date', type=str, help='Date for summary (YYYY-MM-DD, default: today)')
    args = parser.parse_args()
    
    timestamp = datetime.now().isoformat()
    csv_path = Path(args.csv) if args.csv else None
    
    # Summary mode
    if args.summary:
        if not csv_path:
            print("Error: --csv required for summary mode")
            sys.exit(1)
        
        summary = generate_daily_summary(csv_path, args.date)
        if summary:
            print_summary(summary)
            # Also output as JSON for programmatic consumption
            print(f"JSON: {json.dumps(asdict(summary))}")
        else:
            print(f"No data found for {args.date or 'today'}")
            sys.exit(1)
        return
    
    # Collection mode
    print(f"[{timestamp}] === MAS-MCP Extended Health Check ===")
    print(f"[{timestamp}] Target: {args.base_url}")
    
    snapshot = collect_metrics(args.base_url)
    
    if not snapshot:
        print(f"[{timestamp}] ❌ ALERT: Dashboard unreachable")
        sys.exit(1)
    
    # Print results
    status_emoji = {"EXCELLENT": "🟢", "ACCEPTABLE": "🟡", "DEGRADED": "🔴", "CRITICAL": "💀"}
    print(f"[{timestamp}] Quality Score: {snapshot.quality_score}%")
    print(f"[{timestamp}] Latency P95: {snapshot.latency_p95}ms")
    print(f"[{timestamp}] Acceptance Rate: {snapshot.acceptance_rate}%")
    print(f"[{timestamp}] Entities: {snapshot.entity_count}")
    print(f"[{timestamp}] History Records: {snapshot.history_count}")
    print(f"[{timestamp}] Endpoints: {snapshot.endpoints_ok}/{snapshot.endpoints_total} OK")
    print(f"[{timestamp}] {status_emoji.get(snapshot.status, '❓')} Status: {snapshot.status}")
    
    # Append to CSV if path provided
    if csv_path:
        append_to_csv(snapshot, csv_path)
        print(f"[{timestamp}] 📝 Logged to {csv_path}")
        
        # Detect trend from recent history
        recent = read_csv_history(csv_path, TREND_WINDOW_HOURS)
        if len(recent) >= 4:
            trend = detect_trend(recent)
            trend_emoji = {"improving": "📈", "degrading": "📉", "stable": "➡️"}
            print(f"[{timestamp}] {trend_emoji.get(trend, '❓')} 24h Trend: {trend}")
    
    print(f"[{timestamp}] === Health Check Complete ===")
    
    # Exit codes
    if snapshot.status == "CRITICAL":
        sys.exit(3)
    elif snapshot.status == "DEGRADED":
        sys.exit(2)
    elif snapshot.endpoints_ok < snapshot.endpoints_total:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
