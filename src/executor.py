"""命令执行器：执行翻译后的命令并捕获输出。"""

import subprocess
import sys
from typing import Optional


def execute(command: str, timeout: int = 60) -> Optional[str]:
    """执行 shell 命令并返回输出。

    在 Windows 下通过 powershell -NoProfile -Command 执行，
    在 Linux/macOS 下通过子进程 shell 执行。

    参数:
        command: 待执行命令。
        timeout: 超时时间（秒）。

    返回:
        成功时返回 stdout，失败时返回 None（stderr 会被打印）。
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
            print(f"\n[脱口] 命令执行失败 (exit code: {result.returncode})")
            if stderr:
                print(stderr)
            return None

        if stderr:
            print(stderr, file=sys.stderr)

        return output

    except subprocess.TimeoutExpired:
        print(f"\n[脱口] 命令超时 ({timeout}s)")
        return None
    except Exception as e:
        print(f"\n[脱口] 执行出错: {e}")
        return None