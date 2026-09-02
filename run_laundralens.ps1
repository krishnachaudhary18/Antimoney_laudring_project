# LaundraLens X — PowerShell Launcher
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " LaundraLens X — Agentic Anti-Money Laundering Intelligence Platform" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot
$laundraRoot = Join-Path $root "laundralens-x"

Write-Host "[1/2] Starting FastAPI Backend Engine on http://127.0.0.1:8000..." -ForegroundColor Green
$apiProcess = Start-Process -FilePath "uvicorn" -ArgumentList "src.api.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory $laundraRoot -PassThru -NoNewWindow

Start-Sleep -Seconds 3

Write-Host "[2/2] Launching Streamlit Analyst Workstation on http://localhost:8501..." -ForegroundColor Green
Start-Process -FilePath "streamlit" -ArgumentList "run dashboard/app.py" -WorkingDirectory $laundraRoot
