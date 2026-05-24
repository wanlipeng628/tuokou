#!/usr/bin/env bash
# 脱口 tuokou - Bash/Zsh 安装脚本
# 用法：curl -sSL https://.../install.sh | bash

set -e

echo ""
echo "  脱口 tuokou  - 终端自然语言层"
echo "  ================================="
echo ""

# -------------------------------------------------------
# 1. 检查 Python
# -------------------------------------------------------
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "[错误] 未找到 Python，请先安装 Python 3.10+"
    exit 1
fi

PY_VERSION=$($PYTHON_CMD --version 2>&1)
echo "[✓] 找到 $PY_VERSION"

# -------------------------------------------------------
# 2. 安装目录
# -------------------------------------------------------
TUOKOU_DIR="$HOME/.tuokou"

# 检测脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] 安装到 $TUOKOU_DIR"
mkdir -p "$TUOKOU_DIR"

# 复制源代码
cp -r "$SCRIPT_DIR/src" "$TUOKOU_DIR/"
cp "$SCRIPT_DIR/tuokou_handler.py" "$TUOKOU_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$TUOKOU_DIR/"

# 复制配置文件模板 (不覆盖已有配置)
if [ ! -f "$TUOKOU_DIR/config.yaml" ]; then
    cp "$SCRIPT_DIR/config.yaml" "$TUOKOU_DIR/"
    echo "[✓] 已创建配置文件模板"
else
    echo "[*] 配置文件已存在，跳过"
fi

# -------------------------------------------------------
# 3. 安装 Python 依赖
# -------------------------------------------------------
echo "[*] 安装 Python 依赖..."
$PYTHON_CMD -m pip install -r "$TUOKOU_DIR/requirements.txt" -q 2>/dev/null || {
    echo "[警告] pip 安装可能失败，请手动执行: pip install -r $TUOKOU_DIR/requirements.txt"
}

# -------------------------------------------------------
# 4. 配置 Shell Hook
# -------------------------------------------------------
HOOK_CODE='
# ===== 脱口 tuokou =====
command_not_found_handle() {
    local cmd="$1"
    shift
    local full_input="$cmd $*"
    full_input="${full_input%"${full_input##*[![:space:]]}"}"  # trim trailing spaces

    # 查找 Python
    local py=""
    for p in python3 python; do
        if command -v "$p" &>/dev/null; then
            py="$p"
            break
        fi
    done

    if [ -n "$py" ]; then
        "$py" "$HOME/.tuokou/tuokou_handler.py" "$full_input"
        local ret=$?
        if [ $ret -eq 0 ]; then
            return 0
        fi
    fi

    # 脱口未处理（无中文或失败），走回默认提示
    echo "bash: command not found: $cmd" >&2
    return 127
}
# ===== 脱口 tuokou END =====
'

# 检测当前 shell 并写入对应 rc 文件
detect_and_install() {
    local current_shell
    current_shell=$(basename "$SHELL")

    # 优先写入 .bashrc，因为 bash 最通用
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [ -f "$rc" ]; then
            if ! grep -q "脱口 tuokou" "$rc" 2>/dev/null; then
                echo "$HOOK_CODE" >> "$rc"
                echo "[✓] 已注入钩子到 $rc"
            else
                echo "[*] $rc 中钩子已存在，跳过"
            fi
            return 0
        fi
    done

    # 如果都没有，创建 .bashrc
    if ! grep -q "脱口 tuokou" "$HOME/.bashrc" 2>/dev/null; then
        echo "$HOOK_CODE" >> "$HOME/.bashrc"
        echo "[✓] 已创建 $HOME/.bashrc 并注入钩子"
    fi
}

detect_and_install

# -------------------------------------------------------
# 5. 完成
# -------------------------------------------------------
echo ""
echo "  安装完成！"
echo ""
echo "  下一步："
echo "  1. 编辑 $TUOKOU_DIR/config.yaml，填入你的 LLM API Key"
echo "  2. 执行 source ~/.bashrc (或 source ~/.zshrc)"
echo "  3. 直接在命令行输入中文试试：查看我的IP地址"
echo ""