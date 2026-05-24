# 脱口 tuokou - PowerShell 安装脚本
# 用法：powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host ""
Write-Host "  脱口 tuokou  - 终端自然语言层" -ForegroundColor Cyan
Write-Host "  =================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Python
$pythonCmd = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $v = & $cmd --version 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "[错误] 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    Write-Host "       下载: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] 找到 Python" -ForegroundColor Green

# 2. 安装目录
$tuokouDir = "$env:USERPROFILE\.tuokou"
$srcDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[*] 安装到 $tuokouDir"
New-Item -ItemType Directory -Path $tuokouDir -Force | Out-Null

Copy-Item -Path "$srcDir\src" -Destination "$tuokouDir\src" -Recurse -Force
Copy-Item -Path "$srcDir\tuokou_handler.py" -Destination "$tuokouDir\tuokou_handler.py" -Force
Copy-Item -Path "$srcDir\requirements.txt" -Destination "$tuokouDir\requirements.txt" -Force

$configExists = Test-Path "$tuokouDir\config.yaml"
if (-not $configExists) {
    Copy-Item -Path "$srcDir\config.yaml" -Destination "$tuokouDir\config.yaml"
    Write-Host "[OK] 已创建配置文件模板" -ForegroundColor Green
}
else {
    Write-Host "[*] 配置文件已存在，跳过" -ForegroundColor Yellow
}

# 3. 安装 Python 依赖
Write-Host "[*] 安装 Python 依赖..."
& $pythonCmd -m pip install openai pyyaml rich -q 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] pip 安装可能失败，请手动执行: pip install openai pyyaml rich"
}

# 4. 配置 PowerShell Profile（守护进程 + PSReadLine 钩子）
$profilePath = $PROFILE.CurrentUserCurrentHost
$profileDir = Split-Path -Parent $profilePath
New-Item -ItemType Directory -Path $profileDir -Force | Out-Null

$hookCode = @"
# ===== tuokou =====
`$tuokouPort = 28630
`$tuokouUrl = "http://127.0.0.1:`$tuokouPort"
`$tuokouHandler = "`$env:USERPROFILE\.tuokou\tuokou_handler.py"

# 保存原始 prompt 函数，用于劫持 PSReadLine 提示符渲染管线
`$global:__tuokouOriginalPrompt = `$function:prompt
`$global:__tuokouOutput = `$null
`$global:__tuokouOutputColor = "Green"

# 覆盖 prompt：每次画提示符时先检查有没有脱口待显示的结果
function global:prompt {
    if (`$global:__tuokouOutput) {
        `$text = `$global:__tuokouOutput
        `$color = `$global:__tuokouOutputColor
        `$global:__tuokouOutput = `$null
        `$global:__tuokouOutputColor = "Green"
        Write-Host `$text -ForegroundColor `$color
    }
    if (`$global:__tuokouOriginalPrompt) {
        & `$global:__tuokouOriginalPrompt
    } else {
        "PS `$(`$executionContext.SessionState.Path.CurrentLocation)`$('>' * (`$nestedPromptLevel + 1)) "
    }
}

function Start-TuokouDaemon {
    `$psi = New-Object System.Diagnostics.ProcessStartInfo
    `$psi.FileName = "python"
    `$psi.Arguments = "`"`$tuokouHandler`" daemon"
    `$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    `$psi.CreateNoWindow = `$true
    `$psi.UseShellExecute = `$false
    [System.Diagnostics.Process]::Start(`$psi) | Out-Null
    Start-Sleep -Milliseconds 1000
}

function Invoke-TuokouApi {
    param([string]`$Path)
    try {
        `$wc = New-Object System.Net.WebClient
        `$wc.Encoding = [System.Text.Encoding]::UTF8
        return `$wc.DownloadString("`$tuokouUrl`$Path")
    } catch {
        return `$null
    }
}

# 自动启动守护进程
if (-not (Invoke-TuokouApi "/status")) {
    Start-TuokouDaemon
}

if (Get-Module -Name PSReadLine -ErrorAction SilentlyContinue) {
    Set-PSReadLineKeyHandler -Key Enter -ScriptBlock {
        `$line = `$null
        `$cursor = `$null
        [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState([ref]`$line, [ref]`$cursor)

        if (`$line -match '[\u4e00-\u9fff]') {
            # 回显用户输入
            `$prompt = "PS `$(`$executionContext.SessionState.Path.CurrentLocation)> "
            Write-Host "`$prompt`$line"
            [Microsoft.PowerShell.PSConsoleReadLine]::AddToHistory(`$line)

            # 调用守护进程，结果存入全局变量，由 prompt 函数负责显示
            `$q = [System.Uri]::EscapeDataString(`$line)
            `$json = Invoke-TuokouApi "/translate?q=`$q"
            if (`$json) {
                `$r = `$json | ConvertFrom-Json
                if (`$r.error) {
                    `$global:__tuokouOutput = "[脱口] `$(`$r.error)"
                    `$global:__tuokouOutputColor = "Red"
                } elseif (`$r.level -eq "read" -and `$r.output) {
                    if (`$r.summary) {
                        `$global:__tuokouOutput = `$r.summary
                    } else {
                        `$global:__tuokouOutput = `$r.output
                    }
                    `$global:__tuokouOutputColor = "Green"
                } elseif (`$r.command) {
                    `$global:__tuokouOutput = "  待执行: `$(`$r.command)" + "`n"
                    if (`$r.warning) {
                        `$global:__tuokouOutput += "  `$(`$r.warning)"
                    }
                    `$global:__tuokouOutputColor = "Yellow"
                    if (`$r.level -eq "dangerous") {
                        `$confirm = Read-Host "  是否继续? [yes/NO]"
                    } else {
                        `$confirm = Read-Host "  是否执行? [Y/n]"
                    }
                    if (`$confirm -eq "" -or `$confirm -eq "y" -or `$confirm -eq "yes") {
                        `$cmdEnc = [System.Uri]::EscapeDataString(`$r.command)
                        `$qEnc = [System.Uri]::EscapeDataString(`$line)
                        `$execJson = Invoke-TuokouApi "/execute?cmd=`$cmdEnc&q=`$qEnc"
                        if (`$execJson) {
                            `$execR = `$execJson | ConvertFrom-Json
                            if (`$execR.summary) {
                                `$global:__tuokouOutput = `$execR.summary
                            } elseif (`$execR.output) {
                                `$global:__tuokouOutput = `$execR.output
                            }
                            `$global:__tuokouOutputColor = "Green"
                        }
                    } else {
                        `$global:__tuokouOutput = "已取消"
                        `$global:__tuokouOutputColor = "Gray"
                    }
                }
            } else {
                `$global:__tuokouOutput = "[脱口] 守护进程未就绪，尝试重新启动..."
                `$global:__tuokouOutputColor = "Yellow"
                Start-TuokouDaemon
                `$q = [System.Uri]::EscapeDataString(`$line)
                `$json = Invoke-TuokouApi "/translate?q=`$q"
                if (-not `$json) {
                    `$global:__tuokouOutput = "[脱口] 启动失败，请手动执行: python `$tuokouHandler daemon"
                    `$global:__tuokouOutputColor = "Red"
                }
            }

            # 清空缓冲区提交空行，PowerShell 调用 prompt → 显示结果 → 画新提示符
            [Microsoft.PowerShell.PSConsoleReadLine]::SelectAll()
            [Microsoft.PowerShell.PSConsoleReadLine]::KillRegion()
            [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
            return
        }

        [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
    }
}
# ===== tuokou END =====
"@

$alreadyInstalled = $false
if (Test-Path $profilePath) {
    $content = Get-Content $profilePath -Raw
    if ($content -match "tuokou") {
        $alreadyInstalled = $true
    }
}

if ($alreadyInstalled) {
    Write-Host "[*] 钩子已存在，跳过" -ForegroundColor Yellow
}
else {
    Add-Content -Path $profilePath -Value "`n$hookCode"
    Write-Host "[OK] 已注入 PSReadLine 钩子" -ForegroundColor Green
}

# 5. 启动守护进程
Write-Host "[*] 启动守护进程..."
Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "`"$tuokouDir\tuokou_handler.py`" daemon"
Start-Sleep -Seconds 1
Write-Host "[OK] 守护进程已启动" -ForegroundColor Green

# 6. 完成
Write-Host ""
Write-Host "大功告成！" -ForegroundColor Green
Write-Host ""
Write-Host "  下一步：" -ForegroundColor Yellow
Write-Host "  1. 编辑 $tuokouDir\config.yaml（填入 API Key）"
Write-Host "  2. 重新打开终端"
Write-Host "  3. 直接输入中文：查看我的cpu型号"
Write-Host ""