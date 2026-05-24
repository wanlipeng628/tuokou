"""脱口 CLI 入口。

用法：
  tuokou_handler.py <中文输入>   # 单次翻译（用于调试）
  tuokou_handler.py daemon       # 启动后台守护进程
  tuokou_handler.py stop         # 停止守护进程
  tuokou_handler.py status       # 检查守护进程状态
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  tuokou_handler.py <中文文本>    # 单次翻译")
        print("  tuokou_handler.py daemon        # 启动守护进程")
        print("  tuokou_handler.py stop          # 停止守护进程")
        print("  tuokou_handler.py status        # 检查状态")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "daemon":
        from src.daemon import run_daemon
        run_daemon()
        return

    if cmd == "stop":
        from src.daemon import stop_daemon
        stop_daemon()
        return

    if cmd == "status":
        from src.daemon import is_running
        if is_running():
            print("[脱口] 守护进程运行中")
        else:
            print("[脱口] 守护进程未运行")
        return

    # 单次翻译模式（用于调试）
    from src.shell_hook import handle_unknown_command

    raw_input = " ".join(sys.argv[1:])
    exit_code = handle_unknown_command(raw_input)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()