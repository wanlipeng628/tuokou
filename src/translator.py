"""LLM translator: converts natural language into executable shell commands.

Uses an OpenAI-compatible API to call a large language model.
Returns the translated command as a plain string.

TODO(v0.2): command correction mode — when a user mistypes an English command,
attempt to infer their intent and suggest a fix.
"""

import subprocess
import sys
from typing import Optional

import yaml

# -----------------------------------------------------------
# System prompt
# -----------------------------------------------------------

SYSTEM_PROMPT = """You are a command-line translator. The user describes what they want to do in Chinese, and you translate it into a single executable shell command.

Rules:
1. Output only the command itself — no explanation, no markdown code blocks, no extra text.
2. The command must be directly executable in the current shell.
3. If the user's description is ambiguous, choose the most common, reasonable implementation.
4. Use the paths the user describes — do not substitute them.
5. Output one command at a time. Chain multi-step operations with &&."""


# -----------------------------------------------------------
# Shell context collector
# -----------------------------------------------------------

def _get_shell_context() -> dict:
    """Collect current shell environment info to help the LLM generate accurate commands.

    Uses Python built-in modules only (no subprocess calls to the shell).
    This avoids deadlocks when called from within a PowerShell CommandNotFoundAction hook.
    """
    import os as os_module
    import platform

    system = platform.system().lower()

    ctx = {
        "os": system if system else "windows",
        "shell": "",
        "current_dir": os_module.getcwd(),
    }

    if system == "windows":
        ctx["shell"] = "powershell"
    else:
        ctx["shell"] = "bash"

    return ctx


# -----------------------------------------------------------
# LLM call
# -----------------------------------------------------------

class Translator:
    """Translator: natural language → shell command."""

    def __init__(self, config_path: str = "~/.tuokou/config.yaml"):
        import os
        self.config_path = os.path.expanduser(config_path)
        self.config = self._load_config()
        self._client = None

    def _load_config(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            llm = self.config.get("llm", {})
            self._client = OpenAI(
                api_key=llm.get("api_key", ""),
                base_url=llm.get("base_url", "https://api.openai.com/v1"),
            )
        return self._client

    def translate(self, user_input: str) -> Optional[str]:
        """Translate Chinese input into a shell command.

        Args:
            user_input: Chinese text entered by the user.

        Returns:
            Translated command string, or None on failure.
        """
        llm = self.config.get("llm", {})
        model = llm.get("model", "gpt-4o")

        ctx = _get_shell_context()
        context_hint = (
            f"Current OS: {ctx['os']}, Shell: {ctx['shell']}, "
            f"Current dir: {ctx.get('current_dir', 'unknown')}"
        )

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"[{context_hint}]\nUser input: {user_input}"},
                ],
                temperature=0.1,
                max_tokens=500,
                timeout=15,
            )
            command = response.choices[0].message.content.strip()
            # Strip potential markdown wrapping
            command = command.removeprefix("```").removesuffix("```").strip()
            return command if command else None

        except Exception as e:
            print(f"\n[tuokou] Translation failed: {e}")
            return None


# Remove unused json import at top
