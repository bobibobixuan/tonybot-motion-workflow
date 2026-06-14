param(
  [int]$Port = 8123,
  [switch]$NoBrowser,
  [int]$AutoStopAfterSec = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ContentType {
  param([string]$Path)

  switch ([System.IO.Path]::GetExtension($Path).ToLowerInvariant()) {
    ".html" { return "text/html; charset=utf-8" }
    ".js" { return "text/javascript; charset=utf-8" }
    ".json" { return "application/json; charset=utf-8" }
    ".css" { return "text/css; charset=utf-8" }
    ".svg" { return "image/svg+xml" }
    ".png" { return "image/png" }
    ".jpg" { return "image/jpeg" }
    ".jpeg" { return "image/jpeg" }
    ".rob" { return "application/octet-stream" }
    default { return "application/octet-stream" }
  }
}

function Get-PythonLauncher {
  $candidates = @(
    @{ Command = "py"; Prefix = @("-3") },
    @{ Command = "python"; Prefix = @() },
    @{ Command = "python3"; Prefix = @() },
    @{ Command = "C:\Users\21996\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"; Prefix = @() }
  )

  foreach ($candidate in $candidates) {
    $command = $candidate.Command
    if ([System.IO.Path]::IsPathRooted($command)) {
      if (Test-Path -LiteralPath $command -PathType Leaf) {
        return $candidate
      }
      continue
    }

    $resolved = Get-Command $command -ErrorAction SilentlyContinue
    if ($resolved) {
      return @{ Command = $resolved.Source; Prefix = $candidate.Prefix }
    }
  }

  return $null
}

function Open-SimulatorBrowser {
  param([string]$Url)
  Start-Job -ScriptBlock {
    param($TargetUrl)
    Start-Sleep -Milliseconds 800
    Start-Process $TargetUrl | Out-Null
  } -ArgumentList $Url | Out-Null
}

function Start-PythonServer {
  param(
    [string]$PythonExe,
    [string[]]$PrefixArgs,
    [string]$RootDir,
    [string]$Url,
    [int]$ListenPort,
    [switch]$SkipBrowser,
    [int]$StopAfterSec
  )

  $httpArgs = @()
  $httpArgs += $PrefixArgs
  $httpArgs += @("-m", "http.server", "$ListenPort", "--bind", "127.0.0.1", "--directory", $RootDir)

  Write-Host "Tonybot Action Simulator local server running at $Url"
  Write-Host "Repo root: $RootDir"

  if ($StopAfterSec -gt 0) {
    $proc = Start-Process -FilePath $PythonExe -ArgumentList $httpArgs -PassThru -WindowStyle Hidden
    try {
      Start-Sleep -Seconds $StopAfterSec
    } finally {
      if (-not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force
      }
    }
    return
  }

  Write-Host "Press Ctrl+C to stop."
  if (-not $SkipBrowser) {
    Open-SimulatorBrowser -Url $Url
  }
  & $PythonExe @httpArgs
}

function Start-FallbackServer {
  param(
    [string]$RootDir,
    [string]$BaseUrl,
    [string]$Url,
    [switch]$SkipBrowser,
    [int]$StopAfterSec
  )

  $listener = [System.Net.HttpListener]::new()
  $listener.Prefixes.Add($BaseUrl)

  try {
    $listener.Start()
  } catch {
    throw "无法启动本地模拟器服务：$BaseUrl。$_"
  }

  Write-Host "Tonybot Action Simulator local server running at $Url"
  Write-Host "Repo root: $RootDir"
  Write-Host "Using PowerShell fallback server."
  if (-not $SkipBrowser) {
    Open-SimulatorBrowser -Url $Url
  }
  if ($StopAfterSec -le 0) {
    Write-Host "Press Ctrl+C to stop."
  }

  $utf8 = [System.Text.UTF8Encoding]::new($false)
  $stopAt = if ($StopAfterSec -gt 0) { [DateTime]::UtcNow.AddSeconds($StopAfterSec) } else { $null }

  try {
    while ($listener.IsListening) {
      if ($stopAt -and [DateTime]::UtcNow -ge $stopAt) {
        break
      }

      $contextTask = $listener.GetContextAsync()
      if (-not $contextTask.Wait(250)) {
        continue
      }

      $context = $contextTask.Result
      $requestPath = [System.Uri]::UnescapeDataString($context.Request.Url.AbsolutePath.TrimStart('/'))
      if ([string]::IsNullOrWhiteSpace($requestPath)) {
        $requestPath = "simulator/index.html"
      } elseif ($requestPath.EndsWith('/')) {
        $requestPath = $requestPath + "index.html"
      }

      $relativePath = $requestPath.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
      $candidatePath = [System.IO.Path]::GetFullPath((Join-Path $RootDir $relativePath))
      $response = $context.Response

      try {
        if (-not $candidatePath.StartsWith($RootDir, [System.StringComparison]::OrdinalIgnoreCase)) {
          $response.StatusCode = 403
          $buffer = $utf8.GetBytes("forbidden")
          $response.OutputStream.Write($buffer, 0, $buffer.Length)
          continue
        }

        if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) {
          $response.StatusCode = 404
          $buffer = $utf8.GetBytes("not found")
          $response.OutputStream.Write($buffer, 0, $buffer.Length)
          continue
        }

        $bytes = [System.IO.File]::ReadAllBytes($candidatePath)
        $response.StatusCode = 200
        $response.ContentType = Get-ContentType -Path $candidatePath
        $response.ContentLength64 = $bytes.Length
        $response.OutputStream.Write($bytes, 0, $bytes.Length)
      } catch {
        $response.StatusCode = 500
        $buffer = $utf8.GetBytes("server error")
        $response.OutputStream.Write($buffer, 0, $buffer.Length)
        Write-Warning $_
      } finally {
        $response.OutputStream.Close()
        $response.Close()
      }
    }
  } finally {
    if ($listener.IsListening) {
      $listener.Stop()
    }
    $listener.Close()
  }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDir ".."))
$baseUrl = "http://127.0.0.1:$Port/"
$simulatorUrl = "${baseUrl}simulator/"

$python = Get-PythonLauncher
if ($python) {
  Start-PythonServer -PythonExe $python.Command -PrefixArgs $python.Prefix -RootDir $repoRoot -Url $simulatorUrl -ListenPort $Port -SkipBrowser:$NoBrowser -StopAfterSec $AutoStopAfterSec
  if (Get-Variable -Name LASTEXITCODE -ErrorAction SilentlyContinue) {
    exit $LASTEXITCODE
  }
  exit 0
}

Start-FallbackServer -RootDir $repoRoot -BaseUrl $baseUrl -Url $simulatorUrl -SkipBrowser:$NoBrowser -StopAfterSec $AutoStopAfterSec
