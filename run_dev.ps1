# DocuVerify AI - Unified Local Development Launcher
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DocuVerify AI - Enterprise Multi-Agent Verification Platform" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start FastAPI Backend in background
Write-Host "[1/2] Starting FastAPI Multi-Agent Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$backendProc = Start-Process -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" -WorkingDirectory "backend" -PassThru

# 2. Start Vite Frontend
Write-Host "[2/2] Starting Vite React Frontend on http://localhost:5173..." -ForegroundColor Green
Set-Location frontend
try {
    npm run dev
} finally {
    Write-Host "Stopping backend process..." -ForegroundColor Yellow
    Stop-Process -Id $backendProc.Id -Force
}

