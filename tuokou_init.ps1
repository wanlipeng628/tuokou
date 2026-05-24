# tuokou init script
# This file is loaded from PowerShell profile

$tuokouPort = 28630
$tuokouUrl = "http://127.0.0.1:$tuokouPort"
$tuokouHandler = "$env:USERPROFILE\.tuokou\tuokou_handler.py"

# 保存原始 prompt 函数，后面用它来恢复提示符文本
$global:__tuokouOriginalPrompt = $function:prompt
$global:__tuokouOutput = $null
$global:__tuokouOutputColor = "Green"

# 覆盖 prompt：每次 PSReadLine 画提示符时，先检查有没有待显示的脱口结果
function global:prompt {
    if ($global:__tuokouOutput) {
        $text = $global:__tuokouOutput
        $color = $global:__tuokouOutputColor
        $global:__tuokouOutput = $null
        $global:__tuokouOutputColor = "Green"
        Write-Host $text -ForegroundColor $color
    }
    if ($global:__tuokouOriginalPrompt) {
        & $global:__tuokouOriginalPrompt
    } else {
        "PS $($executionContext.SessionState.Path.CurrentLocation)$('>' * ($nestedPromptLevel + 1)) "
    }
}

function Start-TuokouDaemon {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = '"' + $tuokouHandler + '" daemon'
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $psi.CreateNoWindow = $true
    $psi.UseShellExecute = $false
    [System.Diagnostics.Process]::Start($psi) | Out-Null
    Start-Sleep -Milliseconds 1000
}

function Invoke-TuokouApi {
    param([string]$Path)
    try {
        $wc = New-Object System.Net.WebClient
        $wc.Encoding = [System.Text.Encoding]::UTF8
        return $wc.DownloadString($tuokouUrl + $Path)
    } catch {
        return $null
    }
}

# auto start daemon
if (-not (Invoke-TuokouApi "/status")) {
    Start-TuokouDaemon
}

if (Get-Module -Name PSReadLine -ErrorAction SilentlyContinue) {
    Set-PSReadLineKeyHandler -Key Enter -ScriptBlock {
        $line = $null
        $cursor = $null
        [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState([ref]$line, [ref]$cursor)

        if ($line -match '[\u4e00-\u9fff]') {
            # 回显用户输入
            $prompt = "PS $($executionContext.SessionState.Path.CurrentLocation)> "
            Write-Host "$prompt$line"
            [Microsoft.PowerShell.PSConsoleReadLine]::AddToHistory($line)

            # 调用守护进程处理，结果存入全局变量，由 prompt 函数负责显示
            $q = [System.Uri]::EscapeDataString($line)
            $json = Invoke-TuokouApi "/translate?q=$q"
            if ($json) {
                $r = $json | ConvertFrom-Json
                if ($r.error) {
                    $global:__tuokouOutput = "[tuokou] $($r.error)"
                    $global:__tuokouOutputColor = "Red"
                } elseif ($r.level -eq "read" -and $r.output) {
                    if ($r.summary) {
                        $global:__tuokouOutput = $r.summary
                    } else {
                        $global:__tuokouOutput = $r.output
                    }
                    $global:__tuokouOutputColor = "Green"
                } elseif ($r.command) {
                    $global:__tuokouOutput = "  Command: $($r.command)" + "`n"
                    if ($r.warning) {
                        $global:__tuokouOutput += "  $($r.warning)"
                    }
                    $global:__tuokouOutputColor = "Yellow"
                    if ($r.level -eq "dangerous") {
                        $confirm = Read-Host "  Continue? [yes/NO]"
                    } else {
                        $confirm = Read-Host "  Execute? [Y/n]"
                    }
                    if ($confirm -eq "" -or $confirm -eq "y" -or $confirm -eq "yes") {
                        $cmdEnc = [System.Uri]::EscapeDataString($r.command)
                        $qEnc = [System.Uri]::EscapeDataString($line)
                        $execJson = Invoke-TuokouApi "/execute?cmd=$cmdEnc&q=$qEnc"
                        if ($execJson) {
                            $execR = $execJson | ConvertFrom-Json
                            if ($execR.summary) {
                                $global:__tuokouOutput = $execR.summary
                            } elseif ($execR.output) {
                                $global:__tuokouOutput = $execR.output
                            }
                            $global:__tuokouOutputColor = "Green"
                        }
                    } else {
                        $global:__tuokouOutput = "Cancelled"
                        $global:__tuokouOutputColor = "Gray"
                    }
                }
            } else {
                $global:__tuokouOutput = "[tuokou] Daemon not ready, restarting..."
                $global:__tuokouOutputColor = "Yellow"
                Start-TuokouDaemon
                $q = [System.Uri]::EscapeDataString($line)
                $json = Invoke-TuokouApi "/translate?q=$q"
                if (-not $json) {
                    $global:__tuokouOutput = "[tuokou] Failed, run manually: python $tuokouHandler daemon"
                    $global:__tuokouOutputColor = "Red"
                }
            }

            # 清空缓冲区提交空行，PowerShell 调用 prompt → 我们的 prompt 显示结果 → 画新提示符
            [Microsoft.PowerShell.PSConsoleReadLine]::SelectAll()
            [Microsoft.PowerShell.PSConsoleReadLine]::KillRegion()
            [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
            return
        }

        [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
    }
}