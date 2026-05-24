"""意图路由：判断用户输入是自然语言还是拼写错误。

策略：只要包含汉字（CJK 统一表意文字区间），就视为自然语言查询。
这利用了 shell 命令全 ASCII 的底层事实——中文用户的日常命令不会出现汉字。
"""

import re

# CJK 统一表意文字 + 中文标点
_CJK_PATTERN = re.compile(
    r"[\u4e00-\u9fff"  # CJK 统一表意文字
    r"\u3400-\u4dbf"   # CJK 扩展 A
    r"\uf900-\ufaff"   # CJK 兼容表意文字
    r"\u3000-\u303f"   # CJK 标点
    r"\uff00-\uffef"   # 全角字符
    r"]"
)


def is_natural_language(text: str) -> bool:
    """判断输入是否为自然语言（包含中文）。

    参数:
        text: 用户在终端输入的原始文本。

    返回:
        包含汉字返回 True，纯 ASCII 返回 False。
    """
    return bool(_CJK_PATTERN.search(text))