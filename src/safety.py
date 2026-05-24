"""Safety classifier: determine command danger level and prompt for confirmation.

Three tiers:
- 🟢 READ: read-only, execute directly
- 🟡 MODIFY: write/install, show command then ask for confirmation
- 🔴 DANGEROUS: delete/system config, show warning then ask for confirmation

Strategy: keyword matching + configurable rules.
"""

from enum import Enum
from typing import Optional


class DangerLevel(Enum):
    READ = "read"
    MODIFY = "modify"
    DANGEROUS = "dangerous"


# -----------------------------------------------------------
# Default keyword rules
# -----------------------------------------------------------

DANGEROUS_KEYWORDS = [
    "rm ", "rmdir", "del ", "erase",
    "rm -rf", "rm -r", "rd /s", "rd /q",
    "remove-item -recurse",
    "format ", "mkfs.",
    "reg delete", "reg add",
    "chmod 777",
    "shutdown", "reboot", "restart-computer", "stop-computer",
    "iptables -f", "iptables -x",
    "git push --force", "git reset --hard",
    "dd if=",
]

MODIFY_KEYWORDS = [
    "mkdir", "touch", "new-item",
    "mv ", "move-item", "cp ", "copy-item",
    "ren ", "rename-item",
    "write-", "out-file", "set-content",
    ">", ">>", "tee ",
    "pip install", "npm install", "apt install", "apt-get",
    "brew install", "choco install", "winget install",
    "install-package", "install-module",
    "compress-", "tar ", "zip ",
    "git commit", "git add", "git merge", "git rebase",
    "chmod ", "chown ", "icacls ",
    "kill ", "stop-process", "start-process",
    "docker rm ", "docker stop ", "docker-compose down",
    "export ", "setx", "set-env",
]

READ_KEYWORDS = [
    "ls", "dir", "get-childitem",
    "cat ", "type ", "get-content",
    "head ", "tail ", "more ",
    "grep ", "findstr", "select-string",
    "find ", "where ", "which ", "whereis",
    "echo ", "write-host", "printf ",
    "pwd", "get-location",
    "whoami", "hostname", "uname",
    "df ", "du ", "free ",
    "ps ", "get-process", "top ",
    "wmic ", "systeminfo", "get-wmiobject",
    "docker ps", "docker images", "docker logs",
    "git status", "git log", "git diff", "git branch",
    "git remote -v",
    "netstat ", "ipconfig", "ifconfig",
    "curl ", "wget ", "invoke-webrequest", "invoke-restmethod",
    "ping ", "nslookup", "tracert",
    "python --version", "python -v", "node --version",
    "dotnet --version", "java --version",
    "pip list", "pip show", "npm list",
    "--help", "-h ", "/?",
    "man ", "help ", "get-help",
    "history", "get-history",
    "get-ciminstance", "get-service", "get-process",
    "get-wmiobject", "get-item",
    "select-object", "select -first", "select -property",
]


def classify(command: str) -> tuple[DangerLevel, Optional[str]]:
    """Classify a command's danger level.

    Args:
        command: The translated shell command.

    Returns:
        (level, warning_message). warning_message is only set for DANGEROUS.
    """
    lower = command.lower().strip()

    for kw in DANGEROUS_KEYWORDS:
        if kw.lower() in lower:
            return DangerLevel.DANGEROUS, (
                "WARNING: This operation may cause data loss or system damage."
            )

    for kw in MODIFY_KEYWORDS:
        if kw.lower() in lower:
            return DangerLevel.MODIFY, None

    for kw in READ_KEYWORDS:
        if kw.lower() in lower:
            return DangerLevel.READ, None

    # Default conservative: treat as MODIFY
    return DangerLevel.MODIFY, None


def get_user_confirmation(command: str, level: DangerLevel, warning: Optional[str] = None) -> bool:
    """Prompt the user for confirmation.

    Args:
        command: The command about to be executed.
        level: Danger level.
        warning: Additional warning (only for DANGEROUS).

    Returns:
        True if user confirms, False otherwise.
    """
    if warning:
        print(f"\n{warning}")

    print(f"  Command: {command}")

    if level == DangerLevel.DANGEROUS:
        prompt = "  Continue? [yes/NO] "
        try:
            answer = input(prompt).strip().lower()
            return answer in ("yes", "y")
        except (KeyboardInterrupt, EOFError):
            return False

    else:  # MODIFY
        prompt = "  Execute? [Y/n] "
        try:
            answer = input(prompt).strip().lower()
            return answer in ("", "y", "yes")
        except (KeyboardInterrupt, EOFError):
            return False