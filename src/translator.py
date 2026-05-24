"""LLM 翻译器：将自然语言翻译为可执行的 shell 命令。

通过 OpenAI 兼容 API 调用大模型，返回翻译后的命令。

TODO(v0.2): 支持命令纠错模式——当用户输入一个不存在的英文命令时，
尝试猜测用户意图并给出纠正建议。
"""

import subprocess
import sys
from typing import Optional

import yaml

# -----------------------------------------------------------
# 系统提示词
# -----------------------------------------------------------

SYSTEM_PROMPT = """你是一个命令行翻译器。用户会用中文描述他想做的事，你需要翻译成一条可执行的 shell 命令。

规则：
1. 只输出命令本身，不要加任何解释、markdown 代码块标记、或前后缀文字
2. 命令应该能直接在当前 shell 中执行
3. 如果用户描述模糊，选择最常见、最合理的实现方式
4. 涉及路径时使用用户描述的路径，不要随意替换
5. 一次只输出一条命令。如果需要多步操作，用 && 连接"""


# -----------------------------------------------------------
# 收集当前 shell 环境
# -----------------------------------------------------------

def _get_shell_context() -> dict:
    """收集当前 shell 环境信息，帮助 LLM 生成更准确的命令。

    只用 Python 自带模块（不调 shell 子进程），
    避免在 PowerShell 钩子里造成死锁。
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
# LLM 调用
# -----------------------------------------------------------

class Translator:
    """翻译器：自然语言 → shell 命令。"""

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
        """将用户的中文输入翻译为 shell 命令。

        参数:
            user_input: 用户在终端输入的中文文本。

        返回:
            翻译后的命令字符串，失败时返回 None。
        """
        llm = self.config.get("llm", {})
        model = llm.get("model", "gpt-4o")

        ctx = _get_shell_context()
        context_hint = (
            f"当前系统: {ctx['os']}, Shell: {ctx['shell']}, "
            f"当前目录: {ctx.get('current_dir', '未知')}"
        )

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"[{context_hint}]\n用户输入：{user_input}"},
                ],
                temperature=0.1,
                max_tokens=500,
                timeout=15,
            )
            command = response.choices[0].message.content.strip()
            # 去掉可能的 markdown 包裹
            command = command.removeprefix("```").removesuffix("```").strip()
            return command if command else None

        except Exception as e:
            print(f"\n[脱口] 翻译失败: {e}")
            return None