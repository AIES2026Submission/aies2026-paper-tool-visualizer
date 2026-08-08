from __future__ import annotations

from typing import Any


class DependencyUnavailableError(Exception):
    pass


try:
    import openai as openai  # type: ignore[no-redef]
except ImportError:
    openai = None  # type: ignore[assignment]

try:
    import anthropic as anthropic  # type: ignore[no-redef]
except ImportError:
    anthropic = None  # type: ignore[assignment]

try:
    import google.generativeai as genai  # type: ignore[no-redef]
except ImportError:
    genai = None  # type: ignore[assignment]

try:
    import requests as requests  # type: ignore[no-redef]
except ImportError:
    requests = None  # type: ignore[assignment]

try:
    from dotenv import load_dotenv as load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False


OpenAIRateLimitError = getattr(openai, "RateLimitError", DependencyUnavailableError)
OpenAIAPIConnectionError = getattr(openai, "APIConnectionError", DependencyUnavailableError)
AnthropicRateLimitError = getattr(anthropic, "RateLimitError", DependencyUnavailableError)
AnthropicAPIConnectionError = getattr(anthropic, "APIConnectionError", DependencyUnavailableError)


def missing_dependency_message(
    feature_name: str,
    package_name: str,
    env_var_name: str | None = None,
) -> str:
    actions = [f"install the '{package_name}' package"]
    if env_var_name:
        actions.append(f"set {env_var_name}")

    if len(actions) == 1:
        action_text = actions[0]
    else:
        action_text = ", then ".join(actions)

    return f"{feature_name} unavailable; {action_text}."
