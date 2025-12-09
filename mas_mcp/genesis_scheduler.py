#!/usr/bin/env python3
"""
Genesis Scheduler - Autonomous background entity synthesis (v2 Hardened).

Triggers run_cycle every 15 minutes, rotates logs daily, and emails
a brief summary of acceptance rate and latency percentiles after each cycle.

Hardening Features (v2):
- Cycle locking: Prevents overlapping runs via .lock file
- GPU provider validation: Checks GPU availability before each cycle
- VRAM watchdog: Degrades gracefully at high memory usage
- Retention policy: Auto-prunes logs/artifacts older than 7 days
- Zero-delta stall detection: Detects when no progress is being made
- TLS email hardening: STARTTLS with certificate verification
- Secrets handling: Reads SMTP credentials from env only, masks in logs

Usage:
    # Start scheduler (runs indefinitely)
    python genesis_scheduler.py

    # Run once and exit
    python genesis_scheduler.py --once

    # Custom interval (minutes)
    python genesis_scheduler.py --interval 30

    # Dry run (no email, no artifacts)
    python genesis_scheduler.py --dry-run

Environment variables:
    GENESIS_SMTP_HOST      SMTP server (default: localhost)
    GENESIS_SMTP_PORT      SMTP port (default: 587)
    GENESIS_SMTP_USER      SMTP username (optional)
    GENESIS_SMTP_PASS      SMTP password (optional)
    GENESIS_SMTP_FROM      From address (default: genesis@localhost)
    GENESIS_SMTP_TO        To address(es), comma-separated
    GENESIS_SMTP_TLS       Use TLS (default: true)
    GENESIS_STRICT_GPU     Refuse CPU-only starts (default: false)
    GENESIS_LOG_DIR        Log directory (default: logs/genesis)
    GENESIS_ARTIFACT_DIR   Artifact directory (default: genesis_artifacts)
    GENESIS_RETENTION_DAYS Days to keep logs/artifacts (default: 7)
    GENESIS_VRAM_THRESHOLD VRAM usage % for degraded mode (default: 75)
"""

from __future__ import annotations

import argparse
import atexit
import datetime
import gzip
import hashlib
import json
import os
import shutil
import signal
import smtplib
import socket
import ssl
import statistics
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SchedulerConfig:
    """Scheduler configuration with environment overrides."""
    
    # Timing
    interval_minutes: int = 15
    max_cycle_duration_s: int = 600  # 10 min timebox
    
    # Paths
    mpw_path: Path = field(default_factory=lambda: Path(__file__).parent.parent / ".github" / "copilot-instructions.md")
    artifact_dir: Path = field(default_factory=lambda: Path(os.environ.get("GENESIS_ARTIFACT_DIR", "genesis_artifacts")))
    log_dir: Path = field(default_factory=lambda: Path(os.environ.get("GENESIS_LOG_DIR", "logs/genesis")))
    
    # Synthesis
    target_accepts: int = 25
    tier: float = 3.0
    
    # Retention & Thresholds
    retention_days: int = field(default_factory=lambda: int(os.environ.get("GENESIS_RETENTION_DAYS", "7")))
    vram_threshold_pct: int = field(default_factory=lambda: int(os.environ.get("GENESIS_VRAM_THRESHOLD", "75")))
    
    # Email
    smtp_host: str = field(default_factory=lambda: os.environ.get("GENESIS_SMTP_HOST", "localhost"))
    smtp_port: int = field(default_factory=lambda: int(os.environ.get("GENESIS_SMTP_PORT", "587")))
    smtp_user: Optional[str] = field(default_factory=lambda: os.environ.get("GENESIS_SMTP_USER"))
    smtp_pass: Optional[str] = field(default_factory=lambda: os.environ.get("GENESIS_SMTP_PASS"))
    smtp_from: str = field(default_factory=lambda: os.environ.get("GENESIS_SMTP_FROM", "genesis@localhost"))
    smtp_to: List[str] = field(default_factory=lambda: [
        addr.strip() for addr in os.environ.get("GENESIS_SMTP_TO", "").split(",") if addr.strip()
    ])
    smtp_tls: bool = field(default_factory=lambda: os.environ.get("GENESIS_SMTP_TLS", "true").lower() == "true")
    
    # Flags
    dry_run: bool = False
    once: bool = False
    strict_gpu: bool = field(default_factory=lambda: os.environ.get("GENESIS_STRICT_GPU", "").lower() in ("1", "true"))


# ─────────────────────────────────────────────────────────────────────────────
# Cycle Lock (idempotent runs)
# ─────────────────────────────────────────────────────────────────────────────

class CycleLock:
    """
    Prevents overlapping scheduler runs via a lock file.
    
    Usage:
        with CycleLock(log_dir) as acquired:
            if not acquired:
                return  # Another instance is running
            # ... run cycle ...
    """
    
    def __init__(self, log_dir: Path):
        self.lock_file = log_dir / ".genesis.lock"
        self._acquired = False
    
    def __enter__(self) -> bool:
        """Try to acquire lock. Returns True if acquired, False if already held."""
        try:
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if lock file exists and is recent (within 2x max cycle time)
            if self.lock_file.exists():
                lock_age = time.time() - self.lock_file.stat().st_mtime
                if lock_age < 1200:  # 20 minutes = 2x default timebox
                    return False  # Lock is held by another process
                # Stale lock - proceed to claim it
            
            # Write lock with PID and timestamp
            lock_data = {
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "acquired": datetime.datetime.now().isoformat(),
            }
            self.lock_file.write_text(json.dumps(lock_data))
            self._acquired = True
            return True
        
        except OSError:
            return False
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock if we acquired it."""
        if self._acquired:
            try:
                self.lock_file.unlink(missing_ok=True)
            except OSError:
                pass
        return False  # Don't suppress exceptions


# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

class DailyRotatingLog:
    """Thread-safe daily rotating log writer with gzip compression."""
    
    def __init__(self, log_dir: Path, prefix: str = "genesis"):
        self.log_dir = log_dir
        self.prefix = prefix
        self._lock = threading.Lock()
        self._current_date: Optional[str] = None
        self._file: Optional[Any] = None
        self._ensure_dir()
    
    def _ensure_dir(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _rotate_if_needed(self):
        today = datetime.date.today().isoformat()
        if self._current_date != today:
            self._close()
            self._compress_old_logs()
            self._current_date = today
            log_path = self.log_dir / f"{self.prefix}_{today}.log"
            self._file = open(log_path, "a", encoding="utf-8")
    
    def _close(self):
        if self._file:
            self._file.close()
            self._file = None
    
    def _compress_old_logs(self):
        """Compress logs older than 1 day."""
        today = datetime.date.today()
        for log_file in self.log_dir.glob(f"{self.prefix}_*.log"):
            try:
                # Extract date from filename
                date_str = log_file.stem.replace(f"{self.prefix}_", "")
                log_date = datetime.date.fromisoformat(date_str)
                if log_date < today:
                    gz_path = log_file.with_suffix(".log.gz")
                    with open(log_file, "rb") as f_in:
                        with gzip.open(gz_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    log_file.unlink()
            except (ValueError, OSError):
                pass  # Skip malformed or inaccessible files
    
    def write(self, message: str, level: str = "INFO"):
        with self._lock:
            self._rotate_if_needed()
            timestamp = datetime.datetime.now().isoformat(timespec="milliseconds")
            line = f"[{timestamp}] [{level}] {message}\n"
            if self._file:
                self._file.write(line)
                self._file.flush()
            # Also print to stdout
            print(line.rstrip())
    
    def info(self, message: str):
        self.write(message, "INFO")
    
    def warn(self, message: str):
        self.write(message, "WARN")
    
    def error(self, message: str):
        self.write(message, "ERROR")
    
    def close(self):
        with self._lock:
            self._close()


# ─────────────────────────────────────────────────────────────────────────────
# Cycle Report
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CycleReport:
    """Summary of a single genesis cycle."""
    
    cycle_id: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    
    # Counts
    accepted: int = 0
    rejected: int = 0
    attempts: int = 0
    
    # Latencies (ms)
    latencies_ms: List[float] = field(default_factory=list)
    
    # Status
    status: str = "unknown"
    error: Optional[str] = None
    
    # Thresholds used
    novelty_threshold: float = 0.04
    derivation_tolerance: float = 0.005
    
    # GPU info
    gpu_enabled: bool = False
    providers: List[str] = field(default_factory=list)
    
    # Artifacts
    artifact_hashes: Dict[str, str] = field(default_factory=dict)
    
    # Hardening (v2)
    degraded_mode: bool = False
    degraded_reason: Optional[str] = None
    lock_acquired: bool = True
    vram_usage_pct: Optional[float] = None
    
    @property
    def duration_s(self) -> float:
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def acceptance_rate(self) -> float:
        return self.accepted / max(1, self.attempts)
    
    @property
    def p50_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return statistics.median(self.latencies_ms)
    
    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_lat = sorted(self.latencies_ms)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]
    
    @property
    def p99_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_lat = sorted(self.latencies_ms)
        idx = int(len(sorted_lat) * 0.99)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_s": round(self.duration_s, 2),
            "accepted": self.accepted,
            "rejected": self.rejected,
            "attempts": self.attempts,
            "acceptance_rate": round(self.acceptance_rate, 4),
            "latency_p50_ms": round(self.p50_latency_ms, 2),
            "latency_p95_ms": round(self.p95_latency_ms, 2),
            "latency_p99_ms": round(self.p99_latency_ms, 2),
            "status": self.status,
            "error": self.error,
            "novelty_threshold": self.novelty_threshold,
            "derivation_tolerance": self.derivation_tolerance,
            "gpu_enabled": self.gpu_enabled,
            "providers": self.providers,
            "artifact_hashes": self.artifact_hashes,
            "degraded_mode": self.degraded_mode,
            "degraded_reason": self.degraded_reason,
            "vram_usage_pct": self.vram_usage_pct,
        }
    
    def to_email_body(self) -> str:
        """Generate email-friendly summary."""
        lines = [
            f"Genesis Cycle Report: {self.cycle_id}",
            "=" * 50,
            "",
            f"Status: {self.status.upper()}",
            f"Duration: {self.duration_s:.1f}s",
            "",
            "── Synthesis ──",
            f"  Accepted:  {self.accepted}",
            f"  Rejected:  {self.rejected}",
            f"  Attempts:  {self.attempts}",
            f"  Rate:      {self.acceptance_rate:.1%}",
            "",
            "── Latency (ms) ──",
            f"  p50: {self.p50_latency_ms:.2f}",
            f"  p95: {self.p95_latency_ms:.2f}",
            f"  p99: {self.p99_latency_ms:.2f}",
            "",
            "── Configuration ──",
            f"  Novelty threshold:    {self.novelty_threshold}",
            f"  Derivation tolerance: {self.derivation_tolerance}",
            f"  GPU enabled:          {self.gpu_enabled}",
            f"  Providers:            {', '.join(self.providers) or 'N/A'}",
            "",
        ]
        
        if self.degraded_mode:
            lines.extend([
                "── Degraded Mode ──",
                f"  Reason: {self.degraded_reason}",
                f"  VRAM usage: {self.vram_usage_pct:.1f}%" if self.vram_usage_pct else "  VRAM usage: N/A",
                "",
            ])
        
        if self.error:
            lines.extend([
                "── Error ──",
                self.error,
                "",
            ])
        
        if self.artifact_hashes:
            lines.extend([
                "── Artifacts (SHA-256) ──",
            ])
            for name, sha in sorted(self.artifact_hashes.items()):
                lines.append(f"  {name}: {sha[:16]}...")
        
        lines.extend([
            "",
            f"Generated: {self.end_time.isoformat()}",
            f"Host: {socket.gethostname()}",
        ])
        
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Daily Digest
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DailyDigest:
    """Aggregated stats for daily summary email."""
    date: str
    total_cycles: int = 0
    completed_cycles: int = 0
    degraded_cycles: int = 0
    stalled_cycles: int = 0
    skipped_cycles: int = 0
    error_cycles: int = 0
    total_accepted: int = 0
    total_rejected: int = 0
    total_attempts: int = 0
    all_latencies_ms: List[float] = field(default_factory=list)
    all_vram_pcts: List[float] = field(default_factory=list)
    provider_counts: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    @property
    def acceptance_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.total_accepted / self.total_attempts
    
    @property
    def p50_latency_ms(self) -> float:
        return statistics.median(self.all_latencies_ms) if self.all_latencies_ms else 0.0
    
    @property
    def p95_latency_ms(self) -> float:
        if not self.all_latencies_ms:
            return 0.0
        sorted_lat = sorted(self.all_latencies_ms)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]
    
    @property
    def avg_vram_pct(self) -> float:
        return statistics.mean(self.all_vram_pcts) if self.all_vram_pcts else 0.0
    
    @property
    def max_vram_pct(self) -> float:
        return max(self.all_vram_pcts) if self.all_vram_pcts else 0.0
    
    @property
    def gpu_usage_pct(self) -> float:
        """Percentage of cycles using TensorRT or CUDA (not CPU-only)."""
        total = sum(self.provider_counts.values())
        if total == 0:
            return 0.0
        gpu_count = self.provider_counts.get("TensorrtExecutionProvider", 0) + \
                    self.provider_counts.get("CUDAExecutionProvider", 0)
        return (gpu_count / total) * 100.0
    
    def to_email_body(self) -> str:
        """Generate compact daily digest email."""
        flags = []
        if self.degraded_cycles > 0:
            flags.append(f"DEGRADED({self.degraded_cycles})")
        if self.stalled_cycles > 0:
            flags.append(f"STALLED({self.stalled_cycles})")
        if self.error_cycles > 0:
            flags.append(f"ERRORS({self.error_cycles})")
        flags_str = " ".join(flags) if flags else "OK"
        
        # SLO status indicators
        acceptance_slo = "✓" if 0.18 <= self.acceptance_rate <= 0.28 else "✗"
        latency_slo = "✓" if self.p95_latency_ms <= 2.0 else "✗"
        gpu_slo = "✓" if self.gpu_usage_pct >= 95 else "✗"
        vram_slo = "✓" if self.max_vram_pct < 75 else "✗"
        
        lines = [
            f"Genesis Daily Digest: {self.date}",
            "=" * 42,
            f"Status: {flags_str}",
            "",
            f"── Cycles ──",
            f"  Total:     {self.total_cycles:>4}  Completed: {self.completed_cycles:>4}",
            f"  Degraded:  {self.degraded_cycles:>4}  Stalled:   {self.stalled_cycles:>4}",
            f"  Skipped:   {self.skipped_cycles:>4}  Errors:    {self.error_cycles:>4}",
            "",
            f"── Acceptance ──",
            f"  Accepted:  {self.total_accepted:>5}  Rejected: {self.total_rejected:>5}",
            f"  Rate:      {self.acceptance_rate:>5.1%}  SLO 18-28%: {acceptance_slo}",
            "",
            f"── Latency (ms) ──",
            f"  p50:       {self.p50_latency_ms:>5.2f}  SLO ≤1.0: {'✓' if self.p50_latency_ms <= 1.0 else '✗'}",
            f"  p95:       {self.p95_latency_ms:>5.2f}  SLO ≤2.0: {latency_slo}",
            "",
            f"── GPU/VRAM ──",
            f"  GPU usage: {self.gpu_usage_pct:>5.1f}%  SLO ≥95%: {gpu_slo}",
            f"  VRAM avg:  {self.avg_vram_pct:>5.1f}%  max: {self.max_vram_pct:.1f}%  SLO <75%: {vram_slo}",
        ]
        
        if self.errors:
            lines.extend(["", "── Recent Errors ──"])
            for err in self.errors[:3]:  # Show first 3
                lines.append(f"  • {err[:60]}...")
        
        lines.extend([
            "",
            f"Generated: {datetime.datetime.now().isoformat()}",
            f"Host: {socket.gethostname()}",
        ])
        
        return "\n".join(lines)


def generate_daily_digest(log_dir: Path, date: Optional[str] = None) -> DailyDigest:
    """
    Aggregate all cycle reports for a given date into a daily digest.
    
    Args:
        log_dir: Directory containing cycle_*.json files
        date: Date string YYYYMMDD (default: today)
    
    Returns:
        DailyDigest with aggregated stats
    """
    if date is None:
        date = datetime.datetime.now().strftime("%Y%m%d")
    
    digest = DailyDigest(date=date)
    
    # Find all cycle files for this date
    pattern = f"cycle_{date}_*.json"
    cycle_files = list(log_dir.glob(pattern))
    
    for path in cycle_files:
        try:
            data = json.loads(path.read_text())
            digest.total_cycles += 1
            
            status = data.get("status", "unknown").lower()
            if "complete" in status:
                digest.completed_cycles += 1
            elif "stall" in status:
                digest.stalled_cycles += 1
            elif "skip" in status or "lock" in status:
                digest.skipped_cycles += 1
            elif "error" in status:
                digest.error_cycles += 1
                if data.get("error"):
                    digest.errors.append(data["error"][:100])
            
            if data.get("degraded_mode"):
                digest.degraded_cycles += 1
            
            digest.total_accepted += data.get("accepted", 0)
            digest.total_rejected += data.get("rejected", 0)
            digest.total_attempts += data.get("attempts", 0)
            
            # Latencies (from p50/p95 stored, or raw if available)
            p50 = data.get("latency_p50_ms", 0.0)
            p95 = data.get("latency_p95_ms", 0.0)
            if p50 > 0:
                digest.all_latencies_ms.append(p50)
            if p95 > 0:
                digest.all_latencies_ms.append(p95)
            
            # VRAM
            vram = data.get("vram_usage_pct")
            if vram is not None:
                digest.all_vram_pcts.append(vram)
            
            # Providers
            providers = data.get("providers", [])
            for prov in providers:
                digest.provider_counts[prov] = digest.provider_counts.get(prov, 0) + 1
        
        except Exception:
            pass  # Skip malformed files
    
    return digest


# ─────────────────────────────────────────────────────────────────────────────
# GPU & VRAM Checks
# ─────────────────────────────────────────────────────────────────────────────

def check_gpu_available() -> tuple[bool, list[str]]:
    """Check if GPU is available and return providers list."""
    try:
        from milf_genesis_v2 import GPU_AVAILABLE, ONNX_PROVIDERS
        return GPU_AVAILABLE, list(ONNX_PROVIDERS) if ONNX_PROVIDERS else []
    except ImportError:
        return False, []


def check_vram_usage() -> Optional[float]:
    """
    Check VRAM usage percentage. Returns None if unavailable.
    Uses CuPy's memory info which queries CUDA runtime.
    """
    try:
        import cupy as cp
        mem_info = cp.cuda.runtime.memGetInfo()
        free, total = mem_info
        used = total - free
        return (used / total) * 100.0
    except Exception:
        return None


def should_degrade(vram_threshold_pct: int) -> tuple[bool, Optional[str], Optional[float]]:
    """
    Determine if we should run in degraded mode.
    Returns (should_degrade, reason, vram_pct).
    """
    vram_pct = check_vram_usage()
    
    if vram_pct is not None and vram_pct >= vram_threshold_pct:
        return True, f"VRAM usage {vram_pct:.1f}% >= threshold {vram_threshold_pct}%", vram_pct
    
    gpu_ok, providers = check_gpu_available()
    if not gpu_ok:
        return True, "GPU not available", vram_pct
    
    # Check if we're missing preferred providers (TensorRT)
    if providers and "TensorrtExecutionProvider" not in providers:
        return True, f"TensorRT not available (have: {providers})", vram_pct
    
    return False, None, vram_pct


# ─────────────────────────────────────────────────────────────────────────────
# Retention Policy (auto-pruning)
# ─────────────────────────────────────────────────────────────────────────────

def prune_old_files(directory: Path, max_age_days: int, log: "DailyRotatingLog"):
    """
    Delete files and directories older than max_age_days.
    Only operates on genesis-related files (logs, artifacts, reports).
    """
    if not directory.exists():
        return
    
    cutoff = datetime.datetime.now() - datetime.timedelta(days=max_age_days)
    cutoff_ts = cutoff.timestamp()
    pruned_count = 0
    
    try:
        for item in directory.iterdir():
            # Skip lock files and current heartbeat
            if item.name.startswith(".") or item.name == "heartbeat.json":
                continue
            
            try:
                mtime = item.stat().st_mtime
                if mtime < cutoff_ts:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    pruned_count += 1
            except OSError as e:
                log.warn(f"Failed to prune {item}: {e}")
    
    except OSError as e:
        log.warn(f"Failed to scan {directory} for pruning: {e}")
    
    if pruned_count > 0:
        log.info(f"Pruned {pruned_count} items older than {max_age_days} days from {directory}")


# ─────────────────────────────────────────────────────────────────────────────
# Email (TLS Hardened)
# ─────────────────────────────────────────────────────────────────────────────

def send_email(config: SchedulerConfig, report: CycleReport, log: DailyRotatingLog):
    """Send cycle report via email with TLS hardening."""
    if not config.smtp_to:
        log.info("No SMTP recipients configured, skipping email")
        return
    
    if config.dry_run:
        log.info("Dry run: would send email to " + ", ".join(config.smtp_to))
        return
    
    server = None
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Genesis] {report.status.upper()} - {report.acceptance_rate:.1%} acceptance ({report.accepted}/{report.attempts})"
        msg["From"] = config.smtp_from
        msg["To"] = ", ".join(config.smtp_to)
        
        # Plain text body
        text_body = report.to_email_body()
        msg.attach(MIMEText(text_body, "plain"))
        
        # HTML body (simple formatting)
        html_body = f"<pre style='font-family: monospace;'>{text_body}</pre>"
        msg.attach(MIMEText(html_body, "html"))
        
        # Connect with TLS hardening
        server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30)
        
        if config.smtp_tls:
            # Create SSL context with certificate verification
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            server.starttls(context=context)
        
        if config.smtp_user and config.smtp_pass:
            # Log with masked password
            log.info(f"SMTP auth: user={config.smtp_user}, pass=****")
            server.login(config.smtp_user, config.smtp_pass)
        
        server.sendmail(config.smtp_from, config.smtp_to, msg.as_string())
        log.info(f"Email sent to {', '.join(config.smtp_to)}")
    
    except Exception as e:
        log.error(f"Failed to send email: {e}")
        
        # Write email_error.json for debugging
        error_path = config.log_dir / f"email_error_{report.cycle_id}.json"
        error_data = {
            "cycle_id": report.cycle_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e),
            "error_type": type(e).__name__,
            "smtp_host": config.smtp_host,
            "smtp_port": config.smtp_port,
            "smtp_tls": config.smtp_tls,
            "smtp_user": config.smtp_user if config.smtp_user else None,  # Never log password
        }
        try:
            error_path.write_text(json.dumps(error_data, indent=2))
            log.info(f"Email error details written to {error_path}")
        except OSError as write_err:
            log.error(f"Failed to write email error: {write_err}")
    
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# Genesis Runner
# ─────────────────────────────────────────────────────────────────────────────

class GenesisRunner:
    """Wraps the genesis engine for scheduled execution."""
    
    def __init__(self, config: SchedulerConfig, log: DailyRotatingLog):
        self.config = config
        self.log = log
        self._service = None
        self._init_time = None
        self._last_hash: Optional[str] = None  # For zero-delta detection
    
    def _lazy_init(self):
        """Lazy-load the genesis service to avoid import-time GPU init."""
        if self._service is not None:
            return
        
        self.log.info("Initializing genesis service...")
        start = time.time()
        
        try:
            from milf_genesis_v2 import BackgroundGenesisService, GPU_AVAILABLE, ONNX_PROVIDERS
            
            if self.config.strict_gpu and not GPU_AVAILABLE:
                raise RuntimeError("GENESIS_STRICT_GPU=1 but no GPU available")
            
            self._service = BackgroundGenesisService(
                mpw_path=self.config.mpw_path,
                artifacts_dir=self.config.artifact_dir,
            )
            
            self._init_time = time.time() - start
            self.log.info(f"Genesis service initialized in {self._init_time:.2f}s, GPU={GPU_AVAILABLE}, providers={ONNX_PROVIDERS}")
        
        except Exception as e:
            self.log.error(f"Failed to initialize genesis service: {e}")
            raise
    
    def _compute_state_hash(self) -> str:
        """Compute hash of current artifact state for zero-delta detection."""
        try:
            if not self.config.artifact_dir.exists():
                return "empty"
            
            # Hash the directory listing (names + mtimes)
            items = []
            for p in sorted(self.config.artifact_dir.rglob("*.json")):
                try:
                    items.append(f"{p.relative_to(self.config.artifact_dir)}:{p.stat().st_mtime}")
                except OSError:
                    pass
            
            content = "\n".join(items)
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        except Exception:
            return "unknown"
    
    def run_cycle(self) -> CycleReport:
        """Execute one synthesis cycle and return report."""
        self._lazy_init()
        
        cycle_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        start_time = datetime.datetime.now()
        
        report = CycleReport(
            cycle_id=cycle_id,
            start_time=start_time,
            end_time=start_time,  # Will be updated
        )
        
        try:
            from milf_genesis_v2 import GPU_AVAILABLE, ONNX_PROVIDERS, VALIDATION_POLICY
            
            report.gpu_enabled = GPU_AVAILABLE
            report.providers = list(ONNX_PROVIDERS) if ONNX_PROVIDERS else []
            report.novelty_threshold = VALIDATION_POLICY.get("novelty_min_distance", 0.04)
            report.derivation_tolerance = VALIDATION_POLICY.get("epsilon_derivation", 0.005)
            
            # Check for degraded mode
            degrade, reason, vram_pct = should_degrade(self.config.vram_threshold_pct)
            report.degraded_mode = degrade
            report.degraded_reason = reason
            report.vram_usage_pct = vram_pct
            
            if degrade:
                self.log.warn(f"Running in DEGRADED MODE: {reason}")
            
            # Capture state hash before cycle for zero-delta detection
            pre_hash = self._compute_state_hash()
            
            self.log.info(f"Starting cycle {cycle_id}: target={self.config.target_accepts}, tier={self.config.tier}, degraded={degrade}")
            
            if self.config.dry_run:
                # Simulate a cycle
                time.sleep(1)
                report.accepted = 5
                report.rejected = 20
                report.attempts = 25
                report.latencies_ms = [0.5, 0.6, 0.7, 0.8, 1.2]
                report.status = "complete (dry run)"
            else:
                # Run actual cycle
                result = self._service.run_cycle(
                    target_accepts=self.config.target_accepts,
                    tier=self.config.tier,
                )
                
                report.accepted = result.get("accepted", 0)
                report.rejected = result.get("rejected", 0)
                report.attempts = result.get("attempts", 0)
                report.status = result.get("status", "unknown")
                
                # Extract latencies if available
                if "scores" in result:
                    for score in result["scores"]:
                        if "latency_ms" in score:
                            report.latencies_ms.append(score["latency_ms"])
                
                # Extract artifact hashes if available
                if "artifact_hashes" in result:
                    report.artifact_hashes = result["artifact_hashes"]
                
                # Zero-delta detection
                post_hash = self._compute_state_hash()
                if pre_hash == post_hash and report.accepted == 0:
                    if self._last_hash == post_hash:
                        self.log.warn(f"Zero-delta stall detected: state hash unchanged ({post_hash})")
                        report.status = "stalled"
                    self._last_hash = post_hash
                else:
                    self._last_hash = post_hash
        
        except Exception as e:
            report.status = "error"
            report.error = traceback.format_exc()
            self.log.error(f"Cycle {cycle_id} failed: {e}")
        
        finally:
            report.end_time = datetime.datetime.now()
        
        self.log.info(
            f"Cycle {cycle_id} complete: "
            f"status={report.status}, "
            f"accepted={report.accepted}/{report.attempts}, "
            f"rate={report.acceptance_rate:.1%}, "
            f"duration={report.duration_s:.1f}s"
        )
        
        return report
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current synthesis stats."""
        self._lazy_init()
        return self._service.get_synthesis_stats()


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler
# ─────────────────────────────────────────────────────────────────────────────

class GenesisScheduler:
    """Main scheduler coordinating timed cycle execution."""
    
    def __init__(self, config: SchedulerConfig):
        self.config = config
        self.log = DailyRotatingLog(config.log_dir, prefix="genesis")
        self.runner = GenesisRunner(config, self.log)
        self._stop_event = threading.Event()
        self._cycle_count = 0
        self._total_accepted = 0
        self._total_rejected = 0
    
    def _write_heartbeat(self, status: str, next_run: Optional[datetime.datetime] = None):
        """Write heartbeat file for external monitoring."""
        heartbeat_path = self.config.log_dir / "heartbeat.json"
        heartbeat = {
            "status": status,
            "cycle_count": self._cycle_count,
            "total_accepted": self._total_accepted,
            "total_rejected": self._total_rejected,
            "last_update": datetime.datetime.now().isoformat(),
            "next_run": next_run.isoformat() if next_run else None,
            "pid": os.getpid(),
            "host": socket.gethostname(),
        }
        try:
            heartbeat_path.write_text(json.dumps(heartbeat, indent=2))
        except OSError as e:
            self.log.warn(f"Failed to write heartbeat: {e}")
    
    def _run_one_cycle(self) -> Optional[CycleReport]:
        """Run a single cycle with locking and email notification."""
        # Try to acquire lock
        with CycleLock(self.config.log_dir) as acquired:
            if not acquired:
                self.log.warn("Cycle skipped: another instance is already running")
                # Create a minimal report indicating lock conflict
                report = CycleReport(
                    cycle_id=datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                    start_time=datetime.datetime.now(),
                    end_time=datetime.datetime.now(),
                    status="skipped (locked)",
                    lock_acquired=False,
                )
                return report
            
            self._cycle_count += 1
            report = self.runner.run_cycle()
            
            self._total_accepted += report.accepted
            self._total_rejected += report.rejected
            
            # Write cycle report to log dir
            report_path = self.config.log_dir / f"cycle_{report.cycle_id}.json"
            try:
                report_path.write_text(json.dumps(report.to_dict(), indent=2))
            except OSError as e:
                self.log.warn(f"Failed to write cycle report: {e}")
            
            # Send email
            send_email(self.config, report, self.log)
            
            return report
    
    def _run_retention_policy(self):
        """Prune old logs and artifacts based on retention policy."""
        if self.config.retention_days <= 0:
            return
        
        prune_old_files(self.config.log_dir, self.config.retention_days, self.log)
        prune_old_files(self.config.artifact_dir, self.config.retention_days, self.log)
    
    def run_once(self) -> Optional[CycleReport]:
        """Run a single cycle and exit."""
        self.log.info("Running single cycle...")
        self._write_heartbeat("running")
        
        # Run retention before cycle
        self._run_retention_policy()
        
        report = self._run_one_cycle()
        self._write_heartbeat("idle")
        return report
    
    def run_forever(self):
        """Run cycles on interval until stopped."""
        self.log.info(
            f"Starting scheduler: interval={self.config.interval_minutes}min, "
            f"target={self.config.target_accepts}, tier={self.config.tier}, "
            f"retention={self.config.retention_days}d, vram_threshold={self.config.vram_threshold_pct}%"
        )
        
        # Register signal handlers
        def handle_signal(signum, frame):
            self.log.info(f"Received signal {signum}, stopping...")
            self._stop_event.set()
        
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        
        # Cleanup on exit
        atexit.register(self.log.close)
        
        try:
            while not self._stop_event.is_set():
                # Calculate next run time
                next_run = datetime.datetime.now() + datetime.timedelta(minutes=self.config.interval_minutes)
                
                # Run retention policy periodically (once per cycle is fine)
                self._run_retention_policy()
                
                # Run cycle
                self._write_heartbeat("running")
                self._run_one_cycle()
                self._write_heartbeat("waiting", next_run)
                
                # Wait for next interval
                wait_seconds = self.config.interval_minutes * 60
                self.log.info(f"Next cycle at {next_run.isoformat()}")
                
                # Interruptible sleep
                if self._stop_event.wait(timeout=wait_seconds):
                    break
        
        except Exception as e:
            self.log.error(f"Scheduler error: {e}")
            self._write_heartbeat("error")
            raise
        
        finally:
            self._write_heartbeat("stopped")
            self.log.info(
                f"Scheduler stopped: {self._cycle_count} cycles, "
                f"{self._total_accepted} accepted, {self._total_rejected} rejected"
            )
    
    def stop(self):
        """Signal the scheduler to stop."""
        self._stop_event.set()


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genesis Scheduler - Autonomous background entity synthesis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--once", "-1",
        action="store_true",
        help="Run one cycle and exit",
    )
    
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=15,
        help="Interval between cycles in minutes (default: 15)",
    )
    
    parser.add_argument(
        "--target", "-t",
        type=int,
        default=25,
        help="Target number of accepted entities per cycle (default: 25)",
    )
    
    parser.add_argument(
        "--tier",
        type=float,
        default=3.0,
        help="Target tier for synthesis (default: 3.0)",
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Simulate cycles without writing artifacts or sending emails",
    )
    
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=None,
        help="Log directory (default: logs/genesis or GENESIS_LOG_DIR)",
    )
    
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="Artifact directory (default: genesis_artifacts or GENESIS_ARTIFACT_DIR)",
    )
    
    parser.add_argument(
        "--digest",
        type=str,
        nargs="?",
        const="today",
        metavar="YYYYMMDD",
        help="Generate daily digest for date (default: today). Use with --send to email.",
    )
    
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send email (for --digest mode)",
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    config = SchedulerConfig(
        interval_minutes=args.interval,
        target_accepts=args.target,
        tier=args.tier,
        once=args.once,
        dry_run=args.dry_run,
    )
    
    if args.log_dir:
        config.log_dir = args.log_dir
    if args.artifact_dir:
        config.artifact_dir = args.artifact_dir
    
    # Handle digest mode
    if args.digest:
        date = args.digest if args.digest != "today" else None
        digest = generate_daily_digest(config.log_dir, date)
        
        print(digest.to_email_body())
        
        if args.send and config.smtp_to:
            log = DailyRotatingLog(config.log_dir)
            try:
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"[Genesis] Daily Digest {digest.date}: {digest.acceptance_rate:.1%} rate, {digest.total_cycles} cycles"
                msg["From"] = config.smtp_from
                msg["To"] = ", ".join(config.smtp_to)
                
                text_body = digest.to_email_body()
                msg.attach(MIMEText(text_body, "plain"))
                
                html_body = f"<pre style='font-family: monospace;'>{text_body}</pre>"
                msg.attach(MIMEText(html_body, "html"))
                
                server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30)
                if config.smtp_tls:
                    import ssl
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                if config.smtp_user and config.smtp_pass:
                    server.login(config.smtp_user, config.smtp_pass)
                
                server.sendmail(config.smtp_from, config.smtp_to, msg.as_string())
                server.quit()
                print(f"\nDigest sent to: {', '.join(config.smtp_to)}")
            except Exception as e:
                print(f"\nFailed to send digest email: {e}")
        elif args.send:
            print("\nNo SMTP recipients configured (set GENESIS_SMTP_TO)")
        
        sys.exit(0)
    
    scheduler = GenesisScheduler(config)
    
    if config.once:
        report = scheduler.run_once()
        print("\n" + report.to_email_body())
        sys.exit(0 if report.status in ("complete", "complete (dry run)") else 1)
    else:
        scheduler.run_forever()


if __name__ == "__main__":
    main()
