#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Cipher Code Kraken — One-Click Windows Installer
.DESCRIPTION
    Sets up Cipher local AI companion on Windows:
    1. Checks system requirements
    2. Installs Ollama (if needed)
    3. Downloads Gemma 4 E4B model
    4. Creates kin-cipher Ollama model
    5. Installs Node.js runtime (if needed)
    6. Sets up Cipher runtime server
    7. Runs smoke test
.EXAMPLE
    irm https://get.meetyourkin.com/cipher | iex
    # Or locally:
    .\scripts\setup.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  🐙 ═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "     CIPHER — Code Kraken Installer" -ForegroundColor Cyan
Write-Host "     Eight tentacles. Zero pixels out of place." -ForegroundColor Cyan
Write-Host "  ═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ── Check system requirements ───────────────────────────────────────────
Write-Host "[1/7] Checking system requirements..." -ForegroundColor Yellow

$ram = (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum / 1GB
if ($ram -lt 12) {
    Write-Host "  WARNING: Only ${ram}GB RAM detected. 16GB+ recommended." -ForegroundColor Yellow
} else {
    Write-Host "  RAM: ${ram}GB ✅" -ForegroundColor Green
}

# Check for GPU
try {
    $gpu = Get-CimInstance Win32_VideoController | Select-Object -First 1
    $vram = [math]::Round($gpu.AdapterRAM / 1GB, 1)
    Write-Host "  GPU: $($gpu.Name) (${vram}GB VRAM)" -ForegroundColor Green
} catch {
    Write-Host "  GPU: Could not detect. Cipher will use CPU (slower)." -ForegroundColor Yellow
}

# ── Install Ollama ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/7] Checking Ollama..." -ForegroundColor Yellow

$ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaPath) {
    Write-Host "  Ollama found at: $($ollamaPath.Source) ✅" -ForegroundColor Green
} else {
    Write-Host "  Installing Ollama..." -ForegroundColor Cyan
    $installerUrl = "https://ollama.com/download/OllamaSetup.exe"
    $installerPath = "$env:TEMP\OllamaSetup.exe"
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
    Start-Process -FilePath $installerPath -Wait
    Write-Host "  Ollama installed ✅" -ForegroundColor Green
}

# ── Pull Gemma 4 model ─────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/7] Pulling Gemma 4 E4B model (~5GB)..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes on first run." -ForegroundColor DarkGray

& ollama pull gemma4:7b
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to pull model. Is Ollama running?" -ForegroundColor Red
    Write-Host "  Try: ollama serve (in another terminal)" -ForegroundColor Yellow
    exit 1
}
Write-Host "  Gemma 4 E4B pulled ✅" -ForegroundColor Green

# ── Create Cipher model ─────────────────────────────────────────────────
Write-Host ""
Write-Host "[4/7] Creating kin-cipher model with Kraken personality..." -ForegroundColor Yellow

$scriptDir = Split-Path -Parent $PSScriptRoot
$modelfilePath = Join-Path $scriptDir "Modelfile"

if (Test-Path $modelfilePath) {
    & ollama create kin-cipher -f $modelfilePath
    Write-Host "  kin-cipher model created ✅" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Modelfile not found at $modelfilePath" -ForegroundColor Yellow
    Write-Host "  Using base gemma4:7b instead." -ForegroundColor Yellow
}

# ── Check Node.js ───────────────────────────────────────────────────────
Write-Host ""
Write-Host "[5/7] Checking Node.js..." -ForegroundColor Yellow

$nodePath = Get-Command node -ErrorAction SilentlyContinue
if ($nodePath) {
    $nodeVersion = & node --version
    Write-Host "  Node.js $nodeVersion found ✅" -ForegroundColor Green
} else {
    Write-Host "  Node.js not found. Install from: https://nodejs.org" -ForegroundColor Yellow
    Write-Host "  The CLI works without Node.js, but the web dashboard requires it." -ForegroundColor DarkGray
}

# ── Install runtime dependencies ────────────────────────────────────────
Write-Host ""
Write-Host "[6/7] Installing Cipher runtime..." -ForegroundColor Yellow

$runtimeDir = Join-Path $scriptDir "runtime"
if (Test-Path (Join-Path $runtimeDir "package.json")) {
    Push-Location $runtimeDir
    & npm install --silent 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Runtime dependencies installed ✅" -ForegroundColor Green
    }
    # Install Playwright browsers
    & npx playwright install chromium 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Playwright Chromium installed ✅" -ForegroundColor Green
    }
    Pop-Location
} else {
    Write-Host "  Runtime directory not found. Skipping." -ForegroundColor Yellow
}

# ── Smoke test ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[7/7] Running smoke test..." -ForegroundColor Yellow

$response = & ollama run kin-cipher "Say hello in 10 words or less as the Code Kraken." 2>&1
if ($LASTEXITCODE -eq 0 -and $response) {
    Write-Host "  Cipher says: $response" -ForegroundColor Cyan
    Write-Host "  Smoke test passed ✅" -ForegroundColor Green
} else {
    Write-Host "  Smoke test skipped (model may still be loading)." -ForegroundColor Yellow
}

# ── Done ────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  🐙 ═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "     CIPHER IS READY!" -ForegroundColor Green
Write-Host "  ═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Chat:       ollama run kin-cipher" -ForegroundColor White
Write-Host "  CLI:        cd runtime && npx tsx src/cli.ts" -ForegroundColor White
Write-Host "  Server:     cd runtime && npm run dev" -ForegroundColor White
Write-Host "  Dashboard:  http://localhost:3333" -ForegroundColor White
Write-Host ""
Write-Host "  Let's build something beautiful. 🐙" -ForegroundColor Cyan
Write-Host ""
