import sys
import time
from typing import Optional, Tuple


RATING_BRIEFS = {
    "strongly agree": ("SA", "++", "strongly agree"),
    "agree": ("AG", "+", "agree"),
    "neutral": ("NE", "0", "neutral"),
    "disagree": ("DI", "-", "disagree"),
    "strongly disagree": ("SD", "--", "strongly disagree"),
}


def format_rating_brief(rating: Optional[str]) -> Tuple[str, str]:
    normalized = (rating or "").strip().lower()
    if normalized in RATING_BRIEFS:
        abbr, signal, label = RATING_BRIEFS[normalized]
    elif normalized:
        abbr = normalized[:2].upper()
        signal = "?"
        label = normalized
    else:
        abbr, signal, label = ("??", "?", rating or "pending")

    display = f"[{abbr}|{signal}] {label}"
    return display, abbr


def compact_text(text: Optional[str], limit: int = 90) -> str:
    if not text:
        return ""
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    cutoff = max(0, limit - 3)
    return collapsed[:cutoff] + "..."


class ProgressDisplay:

    def __init__(self, total_steps: int, label: str = "Progress", bar_width: int = 40, total_turns: Optional[int] = None):
        self.total_steps = max(1, total_steps)
        self.label = label
        self.bar_width = max(10, bar_width)
        self.completed_steps = 0
        self.status_text = ""
        self.start_time: Optional[float] = None
        self.started = False
        self.is_tty = sys.stdout.isatty()
        self.active = False
        self.total_turns = max(1, total_turns) if total_turns else self.total_steps
        self.completed_turns = 0
        self.turn_time_total = 0.0

    def start(self) -> None:
        if self.started:
            return
        self.started = True
        self.start_time = time.time()
        if not self.is_tty:
            print(self._render_line(), flush=True)
            return

        line = self._render_line()
        sys.stdout.write(line + "\n")
        sys.stdout.write("\033[1A")
        sys.stdout.write("\r")
        sys.stdout.write("\033[s")
        sys.stdout.write("\033[1B")
        sys.stdout.flush()
        self.active = True

    def increment(self, step: int = 1, status: Optional[str] = None) -> None:
        if not self.started:
            self.start()
        self.completed_steps = min(self.total_steps, self.completed_steps + step)
        if status is not None:
            self.status_text = status
        self._refresh_line()

    def update(self, completed: int, status: Optional[str] = None) -> None:
        if not self.started:
            self.start()
        self.completed_steps = max(0, min(self.total_steps, completed))
        if status is not None:
            self.status_text = status
        self._refresh_line()

    def finish(self) -> None:
        self.completed_steps = self.total_steps
        self.completed_turns = self.total_turns
        self._refresh_line()
        self.active = False

    def record_turn(self, duration: Optional[float], turns: int = 1) -> None:
        """Record a completed turn (e.g., test or judge call) with its duration."""
        if not self.started:
            self.start()
        self.completed_turns = min(self.total_turns, self.completed_turns + max(0, turns))
        if duration is not None:
            self.turn_time_total += max(0.0, duration)
        self._refresh_line()

    def _refresh_line(self) -> None:
        line = self._render_line()
        if not self.is_tty or not self.active:
            print(line, flush=True)
            return
        sys.stdout.write("\033[u")
        sys.stdout.write("\r")
        sys.stdout.write(line)
        sys.stdout.write("\033[K")
        sys.stdout.write("\033[s")
        sys.stdout.write("\033[1B")
        sys.stdout.flush()

    def _render_line(self) -> str:
        pct = self.completed_steps / self.total_steps
        filled = int(self.bar_width * pct)
        bar = "#" * filled + "-" * (self.bar_width - filled)
        eta = self._eta_text()
        return f"{self.label} [{bar}] {pct*100:5.1f}% | {self.completed_steps}/{self.total_steps} | ETA {eta} {self.status_text}".rstrip()

    def _eta_text(self) -> str:
        remaining_turns = max(0, self.total_turns - self.completed_turns)
        if remaining_turns == 0:
            return "00:00"
        if self.completed_turns == 0:
            return "--:--"
        if self.turn_time_total > 0:
            avg = self.turn_time_total / self.completed_turns
        else:
            if not self.start_time:
                return "--:--"
            elapsed = max(0.0, time.time() - self.start_time)
            avg = elapsed / self.completed_turns
        eta_seconds = int(max(0.0, avg * remaining_turns))
        return self._format_seconds(eta_seconds)

    @staticmethod
    def _format_seconds(seconds: int) -> str:
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{sec:02d}"
        return f"{minutes:02d}:{sec:02d}"
