"""Command executor: run translated commands and capture output."""

import subprocess
import sys
from typing import Optional


def execute(command: str, timeout: int = 60) -> Optional[str]:
    """Execute a shell command and return its stdout.

    On Windows, runs via powershell -NoProfile -Command.
    On Linux/macOS, runs via a subprocess shell.

    Args:
        command: The command to execute.
        timeout: Timeout in seconds.

    Returns:
        stdout on success, None on failure (stderr is printed).
    """
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="gbk",
                errors="replace",
            )
        else:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            print(f"\n[tuokou] Command failed (exit code: {result.returncode})")
            if stderr:
                print(stderr)
            return None

        if stderr:
            print(stderr, file=sys.stderr)

        return output

    except subprocess.TimeoutExpired:
        print(f"\n[tuokou] Command timed out ({timeout}s)")
        return None
    except Exception as e:
        print(f"\n[tuokou] Execution error: {e}")
        return None