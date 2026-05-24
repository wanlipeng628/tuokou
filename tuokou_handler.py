"""tuokou CLI entry point.

Usage:
  tuokou_handler.py <chinese input>   # Single-shot translation (for debugging)
  tuokou_handler.py daemon            # Start background daemon
  tuokou_handler.py stop              # Stop daemon
  tuokou_handler.py status            # Check daemon status
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  tuokou_handler.py <chinese text>    # Single translation")
        print("  tuokou_handler.py daemon            # Start daemon")
        print("  tuokou_handler.py stop              # Stop daemon")
        print("  tuokou_handler.py status            # Check status")
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
            print("[tuokou] Daemon is running")
        else:
            print("[tuokou] Daemon is not running")
        return

    # Single-shot translation mode (for debugging)
    from src.shell_hook import handle_unknown_command

    raw_input = " ".join(sys.argv[1:])
    exit_code = handle_unknown_command(raw_input)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()