@echo off
chcp 65001 > nul
title LibreOffice 무료 설치 안내

echo ====================================================================
echo   PPT to PDF 변환을 위한 LibreOffice 설치 도우미
echo ====================================================================
echo.
echo PPT 및 PPTX 문서를 서식 깨짐 없이 고품질 PDF로 변환하기 위해
echo 무료 오픈소스 오피스인 'LibreOffice'가 필요합니다.
echo.
echo [설치 방법 1] 공식 홈페이지에서 다운로드하여 설치 (권장)
echo [설치 방법 2] winget 명령어로 자동 설치
echo.
echo --------------------------------------------------------------------
set /p choice="공식 다운로드 웹사이트를 지금 열겠습니까? (Y/N, 기본값: Y): "
if /i "%choice%"=="N" goto SKIP_WEB
start "" "https://ko.libreoffice.org/download/download/"
:SKIP_WEB

echo.
echo winget 패키지 관리자로 자동 설치를 시도하려면 아래를 확인하세요:
echo winget install TheDocumentFoundation.LibreOffice
echo.
echo 설치가 완료되면 run.bat을 실행하여 변환기 웹사이트를 사용하시면 됩니다.
echo ====================================================================
pause
