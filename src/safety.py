"""安全分级：判断命令的危险等级并决定是否需要用户确认。

三级划分：
- 🟢 READ：只读操作，直接执行
- 🟡 MODIFY：修改文件/安装软件，展示命令后确认
- 🔴 DANGEROUS：删除/系统配置，加警告后确认

策略：关键词匹配 + 可配置规则。
"""

from enum import Enum
from typing import Optional


class DangerLevel(Enum):
    READ = "read"
    MODIFY = "modify"
    DANGEROUS = "dangerous"


# -----------------------------------------------------------
# 默认关键词规则
# -----------------------------------------------------------

# 危险关键词（匹配到任意一个 → DANGEROUS）
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

# 修改关键词（匹配到任意一个 → MODIFY）
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

# 查询关键词（匹配到任意一个 → READ，无须确认）
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
    """判断命令的危险等级。

    参数:
        command: 翻译后的 shell 命令。

    返回:
        (等级, 警告信息)。警告信息仅在 DANGEROUS 时有值。
    """
    lower = command.lower().strip()

    for kw in DANGEROUS_KEYWORDS:
        if kw.lower() in lower:
            return DangerLevel.DANGEROUS, (
                "警告：该操作可能造成数据丢失或系统损坏。"
            )

    for kw in MODIFY_KEYWORDS:
        if kw.lower() in lower:
            return DangerLevel.MODIFY, None

    for kw in READ_KEYWORDS:
        if kw.lower() in lower:
            return DangerLevel.READ, None

    # 默认保守策略：按修改处理
    return DangerLevel.MODIFY, None


def get_user_confirmation(command: str, level: DangerLevel, warning: Optional[str] = None) -> bool:
    """请求用户确认。

    参数:
        command: 待执行命令。
        level: 危险等级。
        warning: 额外警告信息（仅 DANGEROUS 时有值）。

    返回:
        用户确认返回 True，否则 False。
    """
    if warning:
        print(f"\n{warning}")

    print(f"  待执行: {command}")

    if level == DangerLevel.DANGEROUS:
        prompt = "  是否继续? [yes/NO] "
        try:
            answer = input(prompt).strip().lower()
            return answer in ("yes", "y")
        except (KeyboardInterrupt, EOFError):
            return False

    else:  # MODIFY
        prompt = "  是否执行? [Y/n] "
        try:
            answer = input(prompt).strip().lower()
            return answer in ("", "y", "yes")
        except (KeyboardInterrupt, EOFError):
            return False