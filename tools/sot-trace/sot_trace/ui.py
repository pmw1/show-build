"""Textual TUI — full screen, mouse-clickable workers, sortable jobs, live timeline."""
from __future__ import annotations

import time
from datetime import datetime, timezone

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Static

from . import colors as C
from .store import JobState, Store, WorkerState


def _age(epoch: float) -> str:
    if not epoch:
        return "—"
    s = max(0, int(time.time() - epoch))
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h"
    return f"{s // 86400}d"


def _fmt_size(n: int) -> str:
    for unit in ("B", "K", "M", "G"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.0f}T"


def _ts_short(epoch: float) -> str:
    if not epoch:
        return "         "
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%H:%M:%S")


# ────────────────────── Worker card ──────────────────────

class WorkerCard(Static):
    """Single clickable worker card in the top strip."""

    DEFAULT_CSS = """
    WorkerCard {
        width: 28; height: 7;
        border: round $primary;
        padding: 0 1;
        margin: 0 1;
        content-align: left top;
    }
    WorkerCard.online    { border: round green; }
    WorkerCard.active    { border: round cyan; }
    WorkerCard.degraded  { border: round yellow; }
    WorkerCard.offline   { border: round red; }
    WorkerCard.unknown   { border: round grey; }
    WorkerCard:hover     { background: $boost; }
    WorkerCard.-selected { background: $accent 30%; }
    """

    def __init__(self, name: str) -> None:
        super().__init__("", id=f"wc-{name.replace('@','-').replace('.','-')}")
        self.worker_name = name

    def update_from(self, w: WorkerState) -> None:
        self.set_class(w.state == "online", "online")
        self.set_class(w.state == "active", "active")
        self.set_class(w.state == "degraded", "degraded")
        self.set_class(w.state == "offline", "offline")
        self.set_class(w.state == "unknown", "unknown")
        dot_color, dot_sym = C.WORKER.get(w.state, C.WORKER["unknown"])
        queues = " ".join((w.queues or [])[:4]) or "—"
        spark = _sparkline(list(w.load_history), width=10)
        cpu = f"{int(w.cpu * 100)}%" if w.cpu else "  0%"
        text = (
            f"[{dot_color}]{dot_sym}[/] [bold]{w.name}[/]\n"
            f"[dim]{queues}[/]\n"
            f"load: {spark}  {cpu}\n"
            f"active: {w.active}  ✓ {w.succeeded}  ✗ {w.failed}"
        )
        self.update(text)


SPARKBARS = "▁▂▃▄▅▆▇█"


def _sparkline(values: list[float], width: int = 10) -> str:
    if not values:
        return "▁" * width
    vals = values[-width:]
    if len(vals) < width:
        vals = [0.0] * (width - len(vals)) + vals
    hi = max(vals) or 1.0
    return "".join(SPARKBARS[min(int(v / hi * (len(SPARKBARS) - 1)), len(SPARKBARS) - 1)] for v in vals)


# ────────────────────── Worker detail modal ──────────────────────

class WorkerDetail(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Close"), Binding("q", "dismiss", "Close")]
    DEFAULT_CSS = """
    WorkerDetail { align: center middle; }
    #detail-box {
        width: 90%; height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    """

    def __init__(self, store: Store, name: str) -> None:
        super().__init__()
        self.store = store
        self.worker_name = name

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="detail-box"):
            yield Static(self._render(), id="detail-content")

    def _render(self) -> str:
        w = self.store.workers.get(self.worker_name)
        if not w:
            return f"[red]No data for worker {self.worker_name}[/]"
        hb_age = _age(w.last_heartbeat)
        first_seen_age = _age(w.first_seen)
        queues = "\n".join(f"  {q}" for q in (w.queues or ["—"]))
        spark = _sparkline(list(w.load_history), width=30)
        recent = "\n".join(_recent_events_for_worker(self.store, w.name)[:15]) or "  (none observed)"
        raw = w.raw or {}
        sw_ident = raw.get("sw_ident", "?")
        sw_ver = raw.get("sw_ver", "?")
        sw_sys = raw.get("sw_sys", "?")
        return (
            f"[bold]{w.name}[/]\n\n"
            f"[bold]STATUS[/]\n"
            f"  State            {C.worker_markup(w.state)} {w.state}\n"
            f"  First seen       {first_seen_age} ago\n"
            f"  Last heartbeat   {hb_age} ago\n\n"
            f"[bold]CONSUMING QUEUES[/]\n{queues}\n\n"
            f"[bold]LOAD (last 60s)[/]\n  {spark}  cpu≈{int(w.cpu * 100)}%\n\n"
            f"[bold]TASK COUNTERS[/]\n"
            f"  active     {w.active}\n"
            f"  succeeded  {w.succeeded}\n"
            f"  failed     {w.failed}\n"
            f"  lost       {w.lost}\n\n"
            f"[bold]VERSIONS (from celery stats)[/]\n"
            f"  software   {sw_ident} {sw_ver}\n"
            f"  system     {sw_sys}\n\n"
            f"[bold]RECENT TASK EVENTS[/]\n{recent}\n\n"
            f"[dim]Esc/q to close[/]"
        )


def _recent_events_for_worker(store: Store, worker_name: str) -> list[str]:
    rows: list[tuple[float, str]] = []
    for j in store.jobs.values():
        for ev in list(j.events):
            if ev.get("source") != "CELERY":
                continue
            if ev.get("hostname") != worker_name:
                continue
            ts = float(ev.get("ts", 0))
            t = ev.get("type", "?")
            jid = j.temp_job_id[-8:]
            rows.append((ts, f"  {_ts_short(ts)}  {t:<18}  {jid}  {j.slug[:24]}"))
    rows.sort(reverse=True)
    return [r[1] for r in rows]


# ────────────────────── Main app ──────────────────────

class SotTraceApp(App):
    """Read-only TUI observer for SOT pipeline."""

    CSS = """
    #worker-strip {
        height: 9;
        padding: 0 1;
        border-bottom: solid $primary;
    }
    #jobs-pane     { height: 14; padding: 0 1; }
    #timeline-pane { padding: 0 1; }
    #alerts-pane   { height: 7; padding: 0 1; border-top: solid $primary; }
    DataTable      { height: 100%; }
    """

    BINDINGS = [
        Binding("q", "quit",            "Quit"),
        Binding("p", "toggle_pause",    "Pause"),
        Binding("c", "clear_alerts",    "Clear alerts"),
        Binding("r", "manual_report",   "Report"),
        Binding("F", "toggle_failed",   "Failed only"),
    ]

    selected_job: reactive[str | None] = reactive(None)
    show_failed_only: reactive[bool] = reactive(False)

    def __init__(self, store: Store) -> None:
        super().__init__()
        self.store = store
        self._worker_cards: dict[str, WorkerCard] = {}
        self._last_version = -1

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Horizontal(id="worker-strip"):
                pass  # cards added dynamically
            with Container(id="jobs-pane"):
                t = DataTable(id="jobs-table", cursor_type="row", zebra_stripes=True)
                t.add_columns("Job", "Slug", "Ep", "Status", "Phase", "Age", "Worker")
                yield t
            with VerticalScroll(id="timeline-pane"):
                yield Static("Select a job to view its timeline.", id="timeline-content")
            with Container(id="alerts-pane"):
                t = DataTable(id="alerts-table", zebra_stripes=True, cursor_type="row")
                t.add_columns("Time", "Sev", "Rule", "Job", "Message")
                yield t
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.5, self.refresh_view)

    # ───── refresh ─────
    def refresh_view(self) -> None:
        if self._last_version == self.store.version:
            return
        self._last_version = self.store.version
        self._refresh_workers()
        self._refresh_jobs()
        self._refresh_timeline()
        self._refresh_alerts()

    def _refresh_workers(self) -> None:
        strip = self.query_one("#worker-strip", Horizontal)
        for name, w in sorted(self.store.workers.items()):
            if name not in self._worker_cards:
                card = WorkerCard(name)
                self._worker_cards[name] = card
                strip.mount(card)
            self._worker_cards[name].update_from(w)

    def _refresh_jobs(self) -> None:
        table = self.query_one("#jobs-table", DataTable)
        rows = self.store.jobs_sorted(limit=40)
        if self.show_failed_only:
            rows = [r for r in rows if r.status in ("failed",) or r.status == "unknown"]
        table.clear()
        for j in rows:
            color, _ = C.STATUS.get(j.status, C.STATUS["unknown"])
            table.add_row(
                j.temp_job_id[-8:],
                (j.slug or "")[:30],
                j.episode or "—",
                f"[{color}]{j.status}[/]",
                j.current_phase or "—",
                _age(j.updated_at or j.created_at),
                j.worker.split("@")[0] if j.worker else "—",
                key=j.temp_job_id,
            )

    def _refresh_timeline(self) -> None:
        widget = self.query_one("#timeline-content", Static)
        jid = self.selected_job
        if not jid or jid not in self.store.jobs:
            widget.update("[dim]Select a job (↑/↓) to view its timeline.[/]")
            return
        j = self.store.jobs[jid]
        lines = [f"[bold]{j.temp_job_id}[/]  [dim]{j.slug}  ep={j.episode}  type={j.job_type}[/]\n"]
        for ev in list(j.events)[-100:]:
            src = ev.get("source", "?")
            color = C.SOURCE.get(src, "white")
            ts = _ts_short(ev.get("ts", 0))
            text = _format_timeline_line(ev)
            lines.append(f"  {ts}  [{color}]{src:<6}[/]  {text}")
        widget.update("\n".join(lines))

    def _refresh_alerts(self) -> None:
        table = self.query_one("#alerts-table", DataTable)
        table.clear()
        for a in list(self.store.alerts)[-30:][::-1]:
            color = C.SEVERITY.get(a.severity, "white")
            table.add_row(
                _ts_short(a.ts),
                f"[{color}]{a.severity}[/]",
                a.rule_id,
                a.job_id[-8:] if a.job_id else "—",
                a.message[:80],
            )

    # ───── events ─────
    @on(DataTable.RowHighlighted, "#jobs-table")
    def _on_job_highlight(self, ev: DataTable.RowHighlighted) -> None:
        if ev.row_key and ev.row_key.value:
            self.selected_job = str(ev.row_key.value)
            self._refresh_timeline()

    def on_click(self, event) -> None:
        # Walk up to find a WorkerCard
        w = event.widget
        while w is not None and not isinstance(w, WorkerCard):
            w = w.parent
        if isinstance(w, WorkerCard):
            self.push_screen(WorkerDetail(self.store, w.worker_name))

    # ───── actions ─────
    def action_toggle_pause(self) -> None:
        self.store.paused = not self.store.paused
        self.notify(f"{'Paused' if self.store.paused else 'Resumed'} ingestion.")

    def action_clear_alerts(self) -> None:
        self.store.alerts.clear()
        self._refresh_alerts()

    def action_toggle_failed(self) -> None:
        self.show_failed_only = not self.show_failed_only

    def action_manual_report(self) -> None:
        if not self.selected_job:
            self.notify("Select a job first.", severity="warning")
            return
        from .reports import write_report
        from .store import Alert
        j = self.store.jobs.get(self.selected_job)
        if not j:
            return
        a = Alert(ts=time.time(), severity="info", rule_id="manual",
                  job_id=j.temp_job_id, message="manual report")
        path = write_report(self.store, j, a)
        self.notify(f"Report saved: {path}")


def _format_timeline_line(ev: dict) -> str:
    src = ev.get("source", "?")
    if src == "DB":
        row = ev.get("row", {})
        err = (row.get("error_message") or "")[:60]
        return f"status={row.get('status','?')} phase={row.get('current_phase','?')}" + (f"  err={err}" if err else "")
    if src == "CELERY":
        return f"{ev.get('type','?'):<16}  {ev.get('task_id','')[:8]}  {ev.get('hostname','')}"
    if src == "FS":
        return f"{ev.get('action','?'):<8}  {_fmt_size(ev.get('size', 0))}  {ev.get('path','')}"
    if src == "HTTP":
        return f"{ev.get('method','?')} {ev.get('path','?')} → {ev.get('status','?')}"
    if src == "WORKER":
        return ev.get("text", "")
    return str(ev)
