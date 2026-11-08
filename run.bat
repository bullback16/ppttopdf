@echo off
chcp 65001 > nul
title PPT to PDF 변환 서버 (최대 100MB)

echo ====================================================================
echo   PPT / PPTX to PDF 변환기 서버 시작 중...
echo ====================================================================

cd /d "%~dp0"

REM 가상환경 확인 및 생성
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] 파이썬 가상환경(.venv)을 생성합니다...
    where uv >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        uv venv
        uv pip install -r requirements.txt
    ) else (
        python -m venv .venv
        .venv\Scripts\python.exe -m pip install -r requirements.txt
    )
)

echo [2/3] 의존성 패키지 확인 완료.
echo [3/3] 브라우저를 열고 서버를 실행합니다...
echo.

start "" "http://localhost:5000"

.venv\Scripts\python.exe app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 서버 실행 중 오류가 발생했습니다.
    pause
)
