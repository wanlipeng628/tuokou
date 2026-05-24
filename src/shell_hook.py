"""Shell hook entry point: orchestration layer called by the PSReadLine handler.

This is the core orchestration layer that coordinates:
  route → translate → classify → execute
"""

import sys
import os


def handle_unknown_command(raw_input: str) -> int:
    """Process an unknown command from the shell.

    Called by:
      - bash/zsh command_not_found_handle
      - PowerShell PSReadLine hook (via tuokou_handler.py)

    Args:
        raw_input: The raw text the user typed.

    Returns:
        Exit code: 0 on success, 127 on failure (shell convention).
    """
    from .router import is_natural_language

    if not is_natural_language(raw_input):
        print(f"command not found: {raw_input}", file=sys.stderr)
        return 127

    print(f"\n[tuokou] Translating...", end="", flush=True)

    from .translator import Translator

    translator = Translator()
    command = translator.translate(raw_input)
    print(f"\r\033[K", end="")

    if not command:
        print(f"[tuokou] Sorry, didn't understand what you want.", file=sys.stderr)
        return 127

    from .safety import classify, get_user_confirmation, DangerLevel

    level, warning = classify(command)

    if level == DangerLevel.READ:
        print(f"\n[tuokou] → {command}")
        from .executor import execute

        output = execute(command)
        if output:
            print(output)
        return 0

    elif level in (DangerLevel.MODIFY, DangerLevel.DANGEROUS):
        confirmed = get_user_confirmation(command, level, warning)

        if not confirmed:
            print("[tuokou] Cancelled.")
            return 0

        from .executor import execute

        print(f"\n[tuokou] Executing...")
        output = execute(command)
        if output:
            print(output)
        return 0

    return 127