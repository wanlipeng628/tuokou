# 脱口 · tuokou

> 在命令行里说中文，它听得懂。

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)]()

**脱口**是一个零侵入的终端自然语言层。不换终端、不打前缀、不切模式。你在命令行输入中文，它自动翻译成 shell 命令并执行。

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

# 把当前目录下所有txt打包
PS C:\Users\alan> 把当前目录下所有txt打包
  待执行: tar -czf archive.tar.gz *.txt
  是否执行? [Y/n] y
  (archive created)
```

---

## 为什么需要它

每个人都有这种时刻：你想查一下 CPU 型号、想看看磁盘还剩多少空间、想装一个软件——但命令记不清了。于是你切到浏览器去搜，找到命令，复制回来执行。整个操作打断了你的心流。

现有的终端 AI 工具（Warp、iFlow CLI、Shell-GPT、Claude CLI）要么需要打前缀命令，要么要求你换一个终端，要么切换到专门的"AI 模式"。脱口不一样——它藏在 shell 的钩子里。你像平常一样打字，它只在检测到中文时悄然介入。

---

## 原理

```
用户输入中文 → shell 找不到这个"命令"
  → 触发 PSReadLine Enter 钩子 (PowerShell)
  → 脱口检测到汉字
  → 发送 HTTP 请求给后台守护进程
  → 守护进程调用 LLM 翻译为命令
  → 安全分级（只读 / 修改 / 危险）
  → 执行命令，返回结果
```

英文拼写错误（如 `gti status`）不受影响，正常提示"命令找不到"。

---

## 守护进程架构

脱口以常驻后台守护进程的方式运行（HTTP 服务，`127.0.0.1:28630`），避免了每次按键都启动一个 Python 进程的冷启动开销。

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

### Windows（PowerShell）

先安装 Python 3.10+，然后：

```powershell
git clone https://github.com/wanlipeng628/tuokou.git
cd tuokou
powershell -ExecutionPolicy Bypass -File install.ps1
```

### Linux / macOS（Bash/Zsh）

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
  api_key: "你的 API Key"
  model: "gpt-4o-mini"
```

支持任意 OpenAI 兼容接口：OpenAI、DeepSeek、通义千问、Ollama（本地）等。

> Windows 用户安装后，**重新打开一个终端**即可使用。profile 脚本会自动启动守护进程。

---

## 安全分级

命令分为三个等级：

| 等级 | 类型 | 示例 | 行为 |
|------|------|------|------|
| 🟢 **只读** | 查询操作 | `wmic cpu`、`ipconfig`、`dir` | 直接执行，显示结果 |
| 🟡 **修改** | 写入/安装 | `mkdir`、`pip install`、`mv` | 显示命令，询问 `[Y/n]` |
| 🔴 **危险** | 删除/系统配置 | `rm -rf`、`format`、`reg delete` | 显示警告，询问 `[yes/NO]` |

规则基于关键词匹配（零延迟），可在 `config.yaml` 中自定义。

---

## 项目结构

```
tuokou/
├── README.md               # 英文文档
├── README.zh.md            # 中文文档（你在这里）
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
    ├── daemon.py           # HTTP 守护进程
    └── shell_hook.py       # 主编排层：路由 → 翻译 → 安全 → 执行
```

---

## License

MIT