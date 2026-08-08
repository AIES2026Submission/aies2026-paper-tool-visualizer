import datetime as dt
import os
import pathlib
import threading
from typing import Optional

DEBUG_ENV_VAR = "AI_DEOLOGY_DEBUG"
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
_LOCK = threading.Lock()
__all__ = ["DebugLogger", "is_debug_enabled", "DEBUG_ENV_VAR"]


def is_debug_enabled(flag_override: Optional[bool] = None) -> bool:
    if flag_override is not None:
        return bool(flag_override)

    raw_value = os.getenv(DEBUG_ENV_VAR, "")
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


class DebugLogger:
    def __init__(self, script_name: str, debug_enabled: Optional[bool] = None) -> None:
        self.script_name = script_name
        self.log_path = LOG_DIR / f"{script_name}.log"
        self.debug_enabled = is_debug_enabled(debug_enabled)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    def set_debug(self, enabled: bool) -> None:
        self.debug_enabled = bool(enabled)

    def _write(self, level: str, message: str) -> None:
        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{timestamp} [{self.script_name}] [{level}] {message}"

        with _LOCK:
            with self.log_path.open("a", encoding="utf-8") as log_file:
                log_file.write(entry + "\n")

        if self.debug_enabled:
            print(f"[DEBUG:{self.script_name}] {message}")

    def debug(self, message: str) -> None:
        self._write("DEBUG", message)

    def info(self, message: str) -> None:
        self._write("INFO", message)

    def warning(self, message: str) -> None:
        self._write("WARNING", message)

    def error(self, message: str) -> None:
        self._write("ERROR", message)

    def exception(self, error_obj: BaseException, context: Optional[str] = None) -> None:
        prefix = f"{context}: " if context else ""
        self._write("ERROR", f"{prefix}{type(error_obj).__name__}: {error_obj}")
