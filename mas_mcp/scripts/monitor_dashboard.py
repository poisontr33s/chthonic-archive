#!/usr/bin/env python3
"""
MAS-MCP Genesis Dashboard — Post-Deployment Monitor
Usage: python monitor_dashboard.py [BASE_URL]
Cron: */15 * * * * /usr/bin/python3 /path/to/monitor_dashboard.py https://your-app.vercel.app >> /var/log/mas_mcp_monitor.log 2>&1
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

# SLO Thresholds
SLO_EXCELLENT = 90
SLO_ACCEPTABLE = 70

@dataclass
class HealthCheckResult:
    endpoint: str
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None

def fetch_json(url: str, timeout: int = 10) -> HealthCheckResult:
    """Fetch JSON from endpoint with error handling."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            return HealthCheckResult(endpoint=url, success=True, data=data)
    except urllib.error.URLError as e:
        return HealthCheckResult(endpoint=url, success=False, error=str(e))
    except json.JSONDecodeError as e:
        return HealthCheckResult(endpoint=url, success=False, error=f"Invalid JSON: {e}")

def evaluate_slo(quality_score: float) -> tuple[str, str]:
    """Evaluate SLO and return status emoji + label."""
    if quality_score >= SLO_EXCELLENT:
        return "🟢", "EXCELLENT"
    elif quality_score >= SLO_ACCEPTABLE:
        return "🟡", "ACCEPTABLE"
    else:
        return "🔴", "DEGRADED"

def send_alert(message: str, webhook_url: Optional[str] = None):
    """Send alert to Slack/Discord webhook (optional)."""
    if not webhook_url:
        return
    try:
        data = json.dumps({"text": message}).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"[ALERT] Failed to send webhook: {e}")

def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
    timestamp = datetime.now().isoformat()
    
    print(f"[{timestamp}] === MAS-MCP Dashboard Health Check ===")
    print(f"[{timestamp}] Target: {base_url}")
    
    # Optional: Configure webhook for alerts
    webhook_url = None  # Set to your Slack/Discord webhook URL
    
    # Check /api/metrics
    print(f"[{timestamp}] Checking /api/metrics...")
    metrics = fetch_json(f"{base_url}/api/metrics")
    
    if not metrics.success:
        print(f"[{timestamp}] ❌ ALERT: /api/metrics unreachable - {metrics.error}")
        send_alert(f"🔴 MAS-MCP Dashboard: /api/metrics unreachable", webhook_url)
        sys.exit(1)
    
    quality_score = metrics.data.get('qualityScore', 0)
    latency_p95 = metrics.data.get('latencyP95', 0)
    acceptance_rate = metrics.data.get('acceptanceRate', 0)
    
    print(f"[{timestamp}] Quality Score: {quality_score}%")
    print(f"[{timestamp}] Latency P95: {latency_p95}ms")
    print(f"[{timestamp}] Acceptance Rate: {acceptance_rate}%")
    
    # Evaluate SLO
    emoji, status = evaluate_slo(quality_score)
    print(f"[{timestamp}] {emoji} Status: {status}")
    
    if status == "DEGRADED":
        send_alert(
            f"🔴 MAS-MCP Dashboard: Quality score degraded to {quality_score}%",
            webhook_url
        )
    
    # Check /api/metrics/history
    print(f"[{timestamp}] Checking /api/metrics/history...")
    history = fetch_json(f"{base_url}/api/metrics/history")
    
    if history.success:
        count = len(history.data) if isinstance(history.data, list) else 0
        print(f"[{timestamp}] Historical records: {count}")
    else:
        print(f"[{timestamp}] ⚠️ /api/metrics/history failed: {history.error}")
    
    # Check /api/monitoring
    print(f"[{timestamp}] Checking /api/monitoring...")
    monitoring = fetch_json(f"{base_url}/api/monitoring")
    
    if monitoring.success:
        print(f"[{timestamp}] ✅ /api/monitoring OK")
    else:
        print(f"[{timestamp}] ⚠️ /api/monitoring failed: {monitoring.error}")
    
    # Check /api/entities
    print(f"[{timestamp}] Checking /api/entities...")
    entities = fetch_json(f"{base_url}/api/entities")
    
    if entities.success:
        entity_list = entities.data.get('entities', [])
        count = len(entity_list) if isinstance(entity_list, list) else 0
        print(f"[{timestamp}] Entities registered: {count}")
    else:
        print(f"[{timestamp}] ⚠️ /api/entities failed: {entities.error}")
    
    print(f"[{timestamp}] === Health Check Complete ===")
    
    # Exit with error code if degraded
    if status == "DEGRADED":
        sys.exit(2)

if __name__ == "__main__":
    main()
