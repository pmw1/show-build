"""Centralized color/symbol scheme used across all panels."""

# Statuses (rich-style markup tags so the same constants work in tables and Static widgets)
STATUS = {
    "completed":  ("green",       "✓"),
    "processing": ("cyan",        "▶"),
    "queued":     ("white",       "◌"),
    "stuck":      ("yellow",      "◔"),
    "failed":     ("red",         "✗"),
    "lost":       ("red on yellow", "⚠"),
    "superseded": ("dim red",     "↻"),
    "unknown":    ("white",       "·"),
}

# Worker dot colors
WORKER = {
    "online":    ("green",  "●"),
    "active":    ("cyan",   "▶"),
    "degraded":  ("yellow", "⚠"),
    "offline":   ("red",    "✗"),
    "unknown":   ("dim white", "◌"),
}

# Event source colors used in the timeline
SOURCE = {
    "DB":     "magenta",
    "FS":     "blue",
    "CELERY": "cyan",
    "HTTP":   "green",
    "WORKER": "white",
    "RULE":   "yellow",
    "ALERT":  "red",
}

# Severity for alerts/reports
SEVERITY = {
    "info":     "white",
    "warn":     "yellow",
    "error":    "red",
    "critical": "red on yellow",
}


def status_markup(status: str) -> str:
    color, sym = STATUS.get(status, STATUS["unknown"])
    return f"[{color}]{sym} {status.upper()}[/{color}]"


def worker_markup(state: str) -> str:
    color, sym = WORKER.get(state, WORKER["unknown"])
    return f"[{color}]{sym}[/{color}]"
