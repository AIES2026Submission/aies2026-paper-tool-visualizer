import traceback
from typing import List, Tuple


class DebugConsole:

    def __init__(self, title: str = "Debug Menu") -> None:
        self.title = title
        self.messages: List[Tuple[str, str]] = []
        self.exceptions: List[Tuple[str, str]] = []
        self.rendered = False

    def info(self, message: str) -> None:
        self._add("INFO", message)

    def warn(self, message: str) -> None:
        self._add("WARNING", message)

    def error(self, message: str) -> None:
        self._add("ERROR", message)

    def _add(self, level: str, message: str) -> None:
        self.messages.append((level, message))

    def record_exception(self, context: str, exc: BaseException) -> None:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self.exceptions.append((context, tb.strip()))

    def has_messages(self) -> bool:
        return bool(self.messages or self.exceptions)

    def render_if_messages(self) -> None:
        if self.has_messages():
            self.render()

    def render(self, force: bool = False) -> None:
        if self.rendered and not force:
            return
        print(f"\n=== {self.title} ===")
        if not self.messages and not self.exceptions:
            print("| (no debug messages)")
        else:
            for level, message in self.messages:
                print(f"| {level:7}: {message}")
            if self.exceptions:
                print("| Exceptions:")
                for idx, (context, tb) in enumerate(self.exceptions, 1):
                    print(f"|   [{idx}] {context}")
                    for line in tb.splitlines():
                        print(f"|       {line}")
        print("=" * (len(self.title) + 8))
        self.rendered = True
