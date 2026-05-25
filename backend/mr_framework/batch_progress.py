"""Batch run progress: stderr display + files for tail -f (background runs)."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TextIO

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROGRESS_JSON = PROJECT_ROOT / "output" / "batch_progress.json"
DEFAULT_PROGRESS_TXT = PROJECT_ROOT / "output" / "batch_progress.txt"


def _fmt_duration(seconds: float) -> str:
    if seconds < 0 or seconds != seconds:  # NaN
        return "--"
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m"


def _bar(done: int, total: int, width: int = 24) -> str:
    if total <= 0:
        return "[" + " " * width + "]"
    filled = min(int(width * done / total), width)
    return "[" + "=" * filled + " " * (width - filled) + "]"


@dataclass
class BatchProgressState:
    status: str  # pending | running | done | error
    total: int
    current: int
    global_total: int
    global_current: int
    shard_label: str
    percent: float
    current_sample_id: str
    current_component: str
    library: str
    category: str
    last_touch_rate: float | None
    last_coverage_rate: float | None
    elapsed_sec: float
    eta_sec: float | None
    avg_sec_per_sample: float | None
    failed_count: int
    started_at: str
    updated_at: str
    message: str


class BatchProgressReporter:
    """Updates stderr and optional progress files each sample."""

    def __init__(
        self,
        *,
        total: int,
        enabled: bool = True,
        json_path: Path | None = DEFAULT_PROGRESS_JSON,
        txt_path: Path | None = DEFAULT_PROGRESS_TXT,
        stream: TextIO | None = None,
        global_total: int | None = None,
        global_offset: int = 0,
        shard_label: str = "",
    ) -> None:
        self.total = max(total, 0)
        self.global_total = global_total if global_total is not None else self.total
        self.global_offset = global_offset
        self.shard_label = shard_label
        self.enabled = enabled and total > 0
        self.json_path = json_path
        self.txt_path = txt_path
        self.stream: TextIO = stream if stream is not None else sys.stderr
        self._t0 = time.monotonic()
        self._started_iso = _iso_now()
        self._current = 0
        self._failed = 0
        self._last_meta: dict[str, str] = {}
        self._last_rates: tuple[float | None, float | None] = (None, None)
        self._tty = hasattr(self.stream, "isatty") and self.stream.isatty()

    def start(self) -> None:
        if not self.enabled:
            return
        self._flush_state(
            status="running",
            current=0,
            message=f"Starting batch ({self.total} samples)",
        )

    def begin_sample(self, index: int, sample_id: str, library: str, category: str, component_name: str) -> None:
        if not self.enabled:
            return
        self._current = index
        self._last_meta = {
            "sample_id": sample_id,
            "library": library,
            "category": category,
            "component_name": component_name,
        }
        self._flush_state(
            status="running",
            current=index - 1,
            message=f"Processing {sample_id}",
            force_line=True,
        )

    def end_sample(
        self,
        index: int,
        *,
        touch_rate: float | None = None,
        coverage_rate: float | None = None,
        failed: bool = False,
        error_message: str | None = None,
    ) -> None:
        if not self.enabled:
            return
        if failed:
            self._failed += 1
        self._last_rates = (touch_rate, coverage_rate)
        self._current = index
        msg = error_message or f"Done {self._last_meta.get('sample_id', '')}"
        self._flush_state(
            status="running",
            current=index,
            message=msg,
            touch_rate=touch_rate,
            coverage_rate=coverage_rate,
            force_line=failed or not self._tty,
        )

    def finish(self, *, extra_message: str = "") -> None:
        if not self.enabled:
            return
        msg = extra_message or f"Batch complete ({self._current}/{self.total}, failed={self._failed})"
        self._flush_state(status="done", current=self._current, message=msg, force_line=True)

    def _flush_state(
        self,
        *,
        status: str,
        current: int,
        message: str,
        touch_rate: float | None = None,
        coverage_rate: float | None = None,
        force_line: bool = False,
    ) -> None:
        elapsed = time.monotonic() - self._t0
        tr = touch_rate if touch_rate is not None else self._last_rates[0]
        cr = coverage_rate if coverage_rate is not None else self._last_rates[1]
        done = current
        total = self.total
        pct = (100.0 * done / total) if total else 0.0
        avg = (elapsed / done) if done > 0 else None
        eta = (avg * (total - done)) if avg is not None and done < total else (0.0 if done >= total and total else None)

        global_done = self.global_offset + done
        shard_label = self.shard_label
        state = BatchProgressState(
            status=status,
            total=total,
            current=done,
            global_total=self.global_total,
            global_current=global_done,
            shard_label=shard_label,
            percent=round(pct, 2),
            current_sample_id=self._last_meta.get("sample_id", ""),
            current_component=self._last_meta.get("component_name", ""),
            library=self._last_meta.get("library", ""),
            category=self._last_meta.get("category", ""),
            last_touch_rate=round(tr, 4) if tr is not None else None,
            last_coverage_rate=round(cr, 4) if cr is not None else None,
            elapsed_sec=round(elapsed, 2),
            eta_sec=round(eta, 2) if eta is not None else None,
            avg_sec_per_sample=round(avg, 2) if avg is not None else None,
            failed_count=self._failed,
            started_at=self._started_iso,
            updated_at=_iso_now(),
            message=message,
        )
        self._write_files(state)
        self._print_line(state, force_newline=force_line or not self._tty or status == "done")

    def _write_files(self, state: BatchProgressState) -> None:
        payload = asdict(state)
        if self.json_path:
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            self.json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if self.txt_path:
            self.txt_path.parent.mkdir(parents=True, exist_ok=True)
            line = _format_progress_line(state)
            self.txt_path.write_text(line + "\n", encoding="utf-8")

    def _print_line(self, state: BatchProgressState, *, force_newline: bool) -> None:
        line = _format_progress_line(state)
        if force_newline:
            print(line, file=self.stream, flush=True)
        else:
            # Single-line refresh on TTY
            print("\r" + line + " " * 8, file=self.stream, end="", flush=True)
        if state.status == "done":
            print("", file=self.stream, flush=True)


def _format_progress_line(state: BatchProgressState) -> str:
    bar = _bar(state.current, state.total)
    idx = f"{state.current:>{len(str(state.total))}}/{state.total}"
    eta = _fmt_duration(state.eta_sec) if state.eta_sec is not None else "--"
    elapsed = _fmt_duration(state.elapsed_sec)
    comp = state.current_component or state.current_sample_id or "—"
    lib_cat = f"{state.library}/{state.category}" if state.library else ""
    cov = (
        f"cov={state.last_coverage_rate * 100:.0f}%"
        if state.last_coverage_rate is not None
        else "cov=--"
    )
    fail = f" fail={state.failed_count}" if state.failed_count else ""
    global_part = ""
    if state.global_total and state.global_total != state.total:
        g_done = state.global_current
        global_part = f" | global {g_done}/{state.global_total}"
    shard = f" {state.shard_label}" if state.shard_label else ""
    return (
        f"{bar} {idx} ({state.percent:5.1f}%){shard}{global_part} "
        f"{lib_cat} {comp} | {cov} | {elapsed} elapsed, ETA {eta}{fail}"
    )


def _iso_now() -> str:
    from .models import utc_now_iso

    return utc_now_iso()


def collect_sample_metas(
    *,
    library: str | None = None,
    category: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    shard_index: int | None = None,
    num_shards: int | None = None,
    sample_id: str | None = None,
) -> list:
    from .samples import iter_samples

    return list(
        iter_samples(
            library=library,
            category=category,
            limit=limit,
            offset=offset,
            shard_index=shard_index,
            num_shards=num_shards,
            sample_id=sample_id,
        )
    )
