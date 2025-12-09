#!/usr/bin/env bash
# MAS-MCP Genesis Dashboard — Post-Deployment Monitor
# Usage: ./monitor_dashboard.sh [BASE_URL]
# Cron: */15 * * * * /path/to/monitor_dashboard.sh https://your-app.vercel.app >> /var/log/mas_mcp_monitor.log 2>&1

set -euo pipefail

BASE_URL="${1:-http://localhost:3000}"
TIMESTAMP=$(date -Iseconds)
LOG_PREFIX="[$TIMESTAMP]"

# SLO Thresholds
SLO_EXCELLENT=90
SLO_ACCEPTABLE=70

echo "$LOG_PREFIX === MAS-MCP Dashboard Health Check ==="
echo "$LOG_PREFIX Target: $BASE_URL"

# Fetch /api/metrics
echo "$LOG_PREFIX Checking /api/metrics..."
METRICS=$(curl -sf "$BASE_URL/api/metrics" 2>/dev/null) || {
    echo "$LOG_PREFIX ❌ ALERT: /api/metrics unreachable"
    exit 1
}

QUALITY_SCORE=$(echo "$METRICS" | jq -r '.qualityScore // 0')
LATENCY_P95=$(echo "$METRICS" | jq -r '.latencyP95 // 0')
ACCEPTANCE_RATE=$(echo "$METRICS" | jq -r '.acceptanceRate // 0')

echo "$LOG_PREFIX Quality Score: ${QUALITY_SCORE}%"
echo "$LOG_PREFIX Latency P95: ${LATENCY_P95}ms"
echo "$LOG_PREFIX Acceptance Rate: ${ACCEPTANCE_RATE}%"

# Evaluate SLO
if (( $(echo "$QUALITY_SCORE >= $SLO_EXCELLENT" | bc -l) )); then
    echo "$LOG_PREFIX 🟢 Status: EXCELLENT"
elif (( $(echo "$QUALITY_SCORE >= $SLO_ACCEPTABLE" | bc -l) )); then
    echo "$LOG_PREFIX 🟡 Status: ACCEPTABLE"
else
    echo "$LOG_PREFIX 🔴 ALERT: Quality score below SLO threshold ($QUALITY_SCORE% < $SLO_ACCEPTABLE%)"
    # Optional: send alert (uncomment and configure)
    # curl -X POST "https://hooks.slack.com/services/YOUR/WEBHOOK" \
    #   -H 'Content-Type: application/json' \
    #   -d "{\"text\": \"🔴 MAS-MCP Dashboard: Quality score degraded to ${QUALITY_SCORE}%\"}"
fi

# Fetch /api/metrics/history
echo "$LOG_PREFIX Checking /api/metrics/history..."
HISTORY_COUNT=$(curl -sf "$BASE_URL/api/metrics/history" 2>/dev/null | jq 'length') || {
    echo "$LOG_PREFIX ❌ ALERT: /api/metrics/history unreachable"
    exit 1
}
echo "$LOG_PREFIX Historical records: $HISTORY_COUNT"

# Fetch /api/monitoring
echo "$LOG_PREFIX Checking /api/monitoring..."
curl -sf "$BASE_URL/api/monitoring" >/dev/null 2>&1 && \
    echo "$LOG_PREFIX ✅ /api/monitoring OK" || \
    echo "$LOG_PREFIX ⚠️ /api/monitoring failed"

# Fetch /api/entities
echo "$LOG_PREFIX Checking /api/entities..."
ENTITY_COUNT=$(curl -sf "$BASE_URL/api/entities" 2>/dev/null | jq '.entities | length // 0') || ENTITY_COUNT=0
echo "$LOG_PREFIX Entities registered: $ENTITY_COUNT"

echo "$LOG_PREFIX === Health Check Complete ==="
