# 脱口 · tuokou

> 在终端里说中文，它听得懂。

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)]()

**tuokou** 是一个零侵入的终端自然语言层。不打前缀、不切模式、不换终端。输入中文，按回车——它自动翻译成 shell 命令并执行。

---

## 演示

```powershell
# 查看我的cpu型号
PS C:\Users\alan> 查看我的cpu型号
AMD Ryzen 7 9700X 8-Core Processor

# 查看我的ip地址
PS C:\Users\alan> 查看我的ip地址
Windows IP 配置
  IPv4 地址 . . . . . . . : 192.168.31.213

# 查看磁盘还剩多少空间
PS C:\Users\alan> 查看磁盘还剩多少空间
  Filesystem  Size  Used  Avail  Use%

# 把当前目录下所有txt文件打包
PS C:\Users\alan> 把当前目录下所有txt文件打包
  待执行: tar -czf archive.tar.gz *.txt
  是否执行? [Y/n] y
  (archive created)
```

---

## 为什么

每个人都有这种时刻：想查一下 CPU 信息、磁盘空间、或者装个软件——但记不得具体命令。于是切到浏览器搜索、复制、粘贴、执行。操作被打断了。

现有的终端 AI 工具（Warp、iFlow CLI、Shell-GPT、Claude CLI）要么需要打前缀命令，要么要你换一个终端，要么需要切到专门的"AI 模式"。脱口走了一条不同的路：**它藏在 shell 的命令找不到钩子里**。你正常打字，只有检测到中文时才介入。

---

## 原理

```
用户输入中文 → shell 找不到这个"命令"
  → 触发 PSReadLine Enter 钩子（PowerShell）
    或 command_not_found_handle（bash/zsh）
  → tuokou 检测到汉字
  → 发送给 LLM 翻译
  → 安全分级（只读 / 修改 / 危险）
  → 执行（只读：直接执行 / 修改：确认 / 危险：警告+确认）
  → 返回结果
```

英文拼写错误（如 `gti status`）不受影响，正常提示"命令找不到"——tuokou 忽略纯 ASCII 输入。

---

## 守护进程架构

tuokou 以常驻后台守护进程的方式运行（HTTP 服务 `127.0.0.1:28630`），避免了每次按键都启动一个 Python 进程 + 加载 LLM 客户端的冷启动开销。

```
PowerShell 启动 → 自动启动守护进程
  → PSReadLine 钩子拦截 Enter 键
  → 如果输入包含中文:
      HTTP GET → /translate?q=...
      守护进程（LLM 常驻热机）→ 翻译 → 安全分级 → 执行
      返回 JSON → 展示结果
```

---

## 安装

### PowerShell（Windows）

先安装 Python 3.10+，然后：

```powershell
git clone https://github.com/wanlipeng628/tuokou.git
cd tuokou
powershell -ExecutionPolicy Bypass -File install.ps1
```

### Bash / Zsh（Linux / macOS）

```bash
git clone https://github.com/wanlipeng628/tuokou.git
cd tuokou
bash install.sh
```

### 配置

编辑 `~/.tuokou/config.yaml`：

```yaml
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key"
  model: "gpt-4o-mini"
```

支持任意 OpenAI 兼容接口：OpenAI、DeepSeek、通义千问、Ollama（本地）等。

> **Windows 用户注意：** 安装后重新打开一个终端。profile 脚本会自动启动守护进程。

---

## 安全分级

命令分为三个等级：

| 等级 | 类型 | 示例 | 行为 |
|------|------|------|------|
| 🟢 **只读** | 查询操作 | `wmic cpu`、`ipconfig`、`ls` | 直接执行，显示输出 |
| 🟡 **修改** | 写入/安装 | `mkdir`、`pip install`、`mv` | 显示命令，询问 `[Y/n]` |
| 🔴 **危险** | 删除/系统配置 | `rm -rf`、`format`、`reg delete` | 显示警告，询问 `[yes/NO]` |

规则基于关键词匹配（非语义），保证零延迟分级。可在 `config.yaml` 中自定义。

---

## 项目结构

```
tuokou/
├── README.md               # 英文文档
├── README.zh.md            # 中文文档
├── config.yaml.example     # 配置模板
├── requirements.txt        # Python 依赖
├── install.ps1             # PowerShell 安装脚本
├── install.sh              # Bash/Zsh 安装脚本
├── tuokou_handler.py       # CLI 入口（支持单次翻译和守护进程模式）
└── src/
    ├── router.py           # 汉字检测
    ├── translator.py       # LLM 翻译（OpenAI 兼容接口）
    ├── safety.py           # 命令安全分级
    ├── executor.py         # 跨平台命令执行
    ├── daemon.py           # HTTP 守护进程（后台常驻服务）
    └── shell_hook.py       # 主编排层：路由 → 翻译 → 安全 → 执行
```

---

## 技术要点

- **零侵入设计：** 不打断现有使用习惯，不需要前缀命令、切模式或换终端。
- **守护进程架构：** LLM 客户端常驻热机，消除冷启动。每次请求约 30ms（vs 启动新 Python 进程的 ~3s）。
- **安全优先：** 3 级关键词分类器。任何修改操作都要求用户确认。
- **跨平台：** 支持 Windows（PowerShell 5.1+）和 \*nix（bash/zsh）。
- **自带模型（BYOM）：** 任意 OpenAI 兼容接口——云端或本地均可。

---

## 给面试官

这个项目展示了以下能力：

- **系统设计：** 清晰的 4 层架构（路由 → 翻译 → 分级 → 执行），通过守护进程拆分优化性能。
- **务实的设计决策：** 用汉字匹配做意图路由（利用了 shell 命令纯 ASCII 的事实）；用关键词做安全分级，不堆语义分析。
- **跨平台工程：** 兼容 Windows PowerShell 5.1、PowerShell 7+、bash 和 zsh。
- **产品思维：** 零侵入的体验设计，解决了一个真实、具体的个人痛点。

---

## License

MIT