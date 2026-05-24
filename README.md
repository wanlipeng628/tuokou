# 脱口 · tuokou

> Speak Chinese in your terminal. It understands.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)]()

**tuokou** is a zero-intrusion natural language layer for your terminal. No prefix. No mode switch. No terminal replacement. Type Chinese, press Enter — it translates your words into shell commands and runs them.

---

## Demo

```powershell
# 查看我的cpu型号
PS C:\Users\alan> 查看我的cpu型号
AMD Ryzen 7 9700X 8-Core Processor

# 查看我的ip地址
PS C:\Users\alan> 查看我的ip地址
Windows IP Configuration
  IPv4 Address . . . . . . : 192.168.31.213

# 查看磁盘还剩多少空间
PS C:\Users\alan> 查看磁盘还剩多少空间
  Filesystem  Size  Used  Avail  Use%

# 把当前目录下所有txt文件打包
PS C:\Users\alan> 把当前目录下所有txt文件打包
  Command: tar -czf archive.tar.gz *.txt
  Execute? [Y/n] y
  (archive created)
```

---

## Why

Everyone has this moment: you want to check CPU info, disk space, or install a package — but you can't recall the exact command. So you switch to a browser, search, copy, paste, run. The interruption breaks your flow.

Existing terminal AI tools (Warp, iFlow CLI, Shell-GPT, Claude CLI) either require a prefix command, a full terminal replacement, or an explicit "AI mode" switch. tuokou takes a different approach: **it hides in your shell's "command not found" handler**. You type normally; it only acts when it detects Chinese input.

---

## How it works

```
User types Chinese → shell can't find the "command"
  → triggers command_not_found_handle (bash/zsh)
    or PSReadLine Enter hook (PowerShell)
  → tuokou detects Chinese characters
  → sends to LLM for translation
  → classifies danger level (read / modify / dangerous)
  → executes (read: silent / modify: confirm / dangerous: warn+confirm)
  → returns result
```

English typos (e.g., `gti status`) fall through to the normal "command not found" behavior — tuokou ignores pure ASCII input.

---

## Daemon Architecture

tuokou runs as a persistent background daemon (HTTP server on `127.0.0.1:28630`), avoiding the cold-start cost of launching a Python process + loading the LLM client on every keystroke.

```
PowerShell profile → automatically starts daemon on login
  → PSReadLine hook intercepts Enter key
  → if input contains Chinese:
      HTTP GET → /translate?q=...
      daemon (warm LLM) → translates → classifies → executes
      returns JSON → displays result
```

---

## Installation

### PowerShell (Windows)

Install Python 3.10+ first, then:

```powershell
git clone https://github.com/yourname/tuokou.git
cd tuokou
powershell -ExecutionPolicy Bypass -File install.ps1
```

### Bash / Zsh (Linux / macOS)

```bash
git clone https://github.com/yourname/tuokou.git
cd tuokou
bash install.sh
```

### Configuration

Edit `~/.tuokou/config.yaml`:

```yaml
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key"
  model: "gpt-4o-mini"
```

Supports any OpenAI-compatible API: OpenAI, DeepSeek, Qwen, Ollama (local), etc.

> ⚠️ **Security Warning**: `config.yaml` contains your API key. **Do NOT commit it to Git repositories**. The project includes a `.gitignore` that automatically excludes this file, but please ensure you don't manually add it.

> **Note for Windows users:** After install, open a **new** terminal window. The profile script auto-starts the daemon.

---

## Safety Levels

Commands are classified into three tiers:

| Level | Type | Example | Behavior |
|-------|------|---------|----------|
| 🟢 **read** | Query-only | `wmic cpu`, `ipconfig`, `ls` | Executes immediately, shows output |
| 🟡 **modify** | Write/install | `mkdir`, `pip install`, `mv` | Shows command, asks `[Y/n]` before executing |
| 🔴 **dangerous** | Delete/system config | `rm -rf`, `format`, `reg delete` | Shows warning, asks `[yes/NO]` before executing |

Rules are keyword-based (not semantic), ensuring zero-latency classification. Customizable in `config.yaml`.

---

## Project Structure

```
tuokou/
├── README.md               # You are here
├── config.yaml             # LLM configuration template
├── requirements.txt        # Python dependencies
├── install.ps1             # PowerShell installer
├── install.sh              # Bash/Zsh installer
├── tuokou_handler.py       # CLI entry point (also: daemon mode)
└── src/
    ├── router.py           # Chinese character detection
    ├── translator.py       # LLM translation (OpenAI-compatible API)
    ├── safety.py           # Command safety classification
    ├── executor.py         # Cross-platform command execution
    ├── daemon.py           # HTTP daemon (background persistent server)
    └── shell_hook.py       # Orchestration: route → translate → safety → execute
```

---

## Technical Notes

- **Zero-intrusion design:** No prefix commands, no mode switching, no terminal replacement.
- **Daemon architecture:** Persistent LLM client eliminates cold starts. ~30ms per request vs ~3s for fresh Python launch.
- **Safety-first:** 3-tier keyword-based classifier. Mutating operations always require user confirmation.
- **Cross-platform:** Designed for Windows (PowerShell) and *nix (bash/zsh).
- **BYOM (Bring Your Own Model):** Any OpenAI-compatible API — cloud or local.

---

## For Job Interviewers

This project demonstrates:

- **System design:** A clear 4-layer architecture (route → translate → classify → execute) with a daemon-server split for performance.
- **Pragmatic decision-making:** Chinese character heuristic for intent routing (exploiting the fact that shell commands are pure ASCII); keyword-based safety instead of over-engineered semantic analysis.
- **Cross-platform engineering:** Works on Windows PowerShell 5.1, PowerShell 7+, bash, and zsh.
- **Product thinking:** Zero-intrusion UX ("it just works") designed to solve a real, personal pain point.

---

## License

MIT