# PowerShell 실행 스크립트
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  PPT / PPTX to PDF 변환기 서버 시작 중..." -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[1/3] 파이썬 가상환경(.venv)을 생성합니다..." -ForegroundColor Yellow
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv venv
        uv pip install -r requirements.txt
    } else {
        python -m venv .venv
        & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    }
}

Write-Host "[2/3] 의존성 패키지 확인 완료." -ForegroundColor Green
Write-Host "[3/3] 브라우저를 열고 서버를 실행합니다..." -ForegroundColor Green

Start-Process "http://localhost:5000"

& .\.venv\Scripts\python.exe app.py
