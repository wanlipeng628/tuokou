"""Shell 钩子入口：被 PSReadLine Enter 钩子调用的主编排层。

这个文件是整个工具的核心编排层，协调：
  路由 → 翻译 → 分级 → 执行
"""

import sys
import os


def handle_unknown_command(raw_input: str) -> int:
    """处理用户在终端输入的中文文本。

    由以下方式调用：
      - bash/zsh 的 command_not_found_handle
      - PowerShell 的 PSReadLine 钩子（通过 tuokou_handler.py）

    参数:
        raw_input: 用户输入的原始文本。

    返回:
        退出码：成功 0，失败 127（保持 shell 约定）。
    """
    from .router import is_natural_language

    if not is_natural_language(raw_input):
        print(f"command not found: {raw_input}", file=sys.stderr)
        return 127

    print(f"\n[脱口] 正在理解...", end="", flush=True)

    from .translator import Translator

    translator = Translator()
    command = translator.translate(raw_input)
    print(f"\r\033[K", end="")

    if not command:
        print(f"[脱口] 抱歉，没听懂你想做什么。", file=sys.stderr)
        return 127

    from .safety import classify, get_user_confirmation, DangerLevel

    level, warning = classify(command)

    if level == DangerLevel.READ:
        print(f"\n[脱口] → {command}")
        from .executor import execute

        output = execute(command)
        if output:
            summary = translator.summarize(raw_input, command, output)
            if summary:
                print(summary)
            else:
                print(output)
        return 0

    elif level in (DangerLevel.MODIFY, DangerLevel.DANGEROUS):
        confirmed = get_user_confirmation(command, level, warning)

        if not confirmed:
            print("[脱口] 已取消。")
            return 0

        from .executor import execute

        print(f"\n[脱口] 正在执行...")
        output = execute(command)
        if output:
            summary = translator.summarize(raw_input, command, output)
            if summary:
                print(summary)
            else:
                print(output)
        return 0

    return 127