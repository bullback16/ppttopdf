# 🚀 PPT to PDF 변환기 (최대 100MB 지원)

PowerPoint 프레젠테이션 파일(`.ppt`, `.pptx`)을 원본 서식과 폰트를 고품질로 유지하며 깔끔한 PDF 문서로 변환해 주는 반응형 웹 애플리케이션입니다.

**최대 100MB** 크기의 대용량 프레젠테이션을 지원하며, **Windows PC, 안드로이드(Android), 아이폰·아이패드(iOS)** 등 모든 디바이스에서 브라우저를 통해 접속하여 즉시 이용할 수 있습니다.

---

## ✨ 핵심 기능

1. **대용량 파일 100MB 지원 & 실시간 진행률 표시**
   - 파일당 최대 100MB까지 지원
   - 실시간 업로드 프로그레스 바(전송률 %, 전송량, 전송 속도 표시)
   - 300초(5분) 변환 타임아웃 지원으로 수백 장의 슬라이드도 안전하게 변환
2. **모든 기기(Windows, Android, iOS) 접속 지원**
   - 모바일 & 데스크톱 반응형 웹 디자인
   - **스마트폰 간편 접속 QR 코드 모달 내장** (카메라로 QR을 비추면 즉시 접속)
   - iOS Safari 특화: 'PDF 다운로드' 및 '새 탭에서 미리보기' 동시 제공
   - Android Chrome 특화: 내 파일 및 구글 드라이브 파일 선택 완벽 호환
3. **한글 및 유니코드 파일명 완벽 보존**
   - RFC 5987 표준 지원으로 한글 파일명이 깨지지 않고 다운로드됨
4. **강력한 개인정보 보호 및 보안**
   - 변환 작업이 완료되면 서버의 임시 파일은 즉시 영구 삭제됨
5. **오픈소스 LibreOffice 기반 변환 엔진**
   - MS Office가 설치되어 있지 않아도 LibreOffice 헤드리스 CLI를 통해 차트, 도형, 폰트를 고품질로 변환

---

## 📋 필수 요구사항

1. **Python 3.9 이상** (가상환경 자동 구성 지원)
2. **LibreOffice** (오픈소스 무료 오피스 엔진)
   - [공식 한국어 다운로드 사이트](https://ko.libreoffice.org/download/download/)에서 설치하거나,
   - `install_libreoffice.bat`을 실행하여 설치할 수 있습니다.

---

## 🏃 실행 방법

### 1. Windows에서 가장 간단한 실행 (권장)
폴더 내의 **`run.bat`** 파일을 더블 클릭합니다.
- 필요한 가상환경과 패키지를 자동으로 확인 및 설치합니다.
- 기본 브라우저에서 `http://localhost:5000` 웹페이지가 자동으로 열립니다.

### 2. 콘솔에서 수동 실행

```powershell
# 가상환경 활성화
.venv\Scripts\Activate.ps1

# 서버 실행 (모든 네트워크 기기 접속 허용)
python app.py
```

---

## 📱 기기별 접속 방법 (Android, Windows, iOS)

서버가 실행되면 콘솔 창 및 웹페이지에 접속 주소가 표시됩니다.

- **Windows PC**: `http://localhost:5000` 또는 `http://127.0.0.1:5000`
- **스마트폰 (안드로이드, iOS)**: `http://192.168.1.8:5000` *(PC의 현재 로컬 IP)*

### 🔍 QR 코드로 1초 만에 스마트폰 접속하기
1. PC 브라우저에서 우측 상단의 **[📱 스마트폰 접속 QR]** 버튼을 클릭합니다.
2. 스마트폰(갤럭시, 아이폰)의 기본 카메라 앱을 켭니다.
3. 화면의 QR 코드를 비추면 뜨는 노란색 링크를 터치하여 웹사이트로 바로 접속합니다.

> 💡 **참고:** 스마트폰과 PC가 같은 Wi-Fi 공유기(동일 로컬 네트워크)에 연결되어 있어야 합니다. 만약 모바일에서 접속이 안 될 경우 Windows Defender 방화벽에서 5000번 포트 또는 Python 통신을 허용해 주세요.

---

## 🌐 외부 네트워크(LTE/5G)에서 접속하고 싶을 때

집 밖이나 외부에서 스마트폰 LTE/5G로 이 웹사이트를 이용하고 싶다면, 무료 터널링 도구(Cloudflare Tunnel 등)를 사용하면 포트포워딩 없이도 안전한 `https://` 도메인이 생성됩니다:

```powershell
# Cloudflare Tunnel 사용 예시 (별도 가입 불필요)
npx cloudflared tunnel --url http://localhost:5000
```
출력되는 고유한 `https://xxxx.trycloudflare.com` 링크로 접속하면 어디서나 사용할 수 있습니다.

---

## ☁️ Render.com 또는 Railway로 24시간 무료 배포하기

이 프로젝트에는 **Dockerfile**, **한글 폰트(Noto Sans/나눔)**, **LibreOffice**, **Gunicorn** 및 **render.yaml** 배포 설정이 이미 완벽하게 포함되어 있습니다.

### [방법 1] Render.com 배포 (무료 플랜 추천)
1. **[GitHub](https://github.com/)** 에 로그인하고 새 리포지토리(Repository)를 만듭니다. (예: `ppttopdf`)
2. 이 프로젝트 폴더(`ppttopdf2`)의 파일들을 GitHub 리포지토리에 올립니다.
   *(Git이 없으시다면 GitHub 웹 화면에서 **`Add file` > `Upload files`** 로 파일들을 끌어다 놓으시면 됩니다)*
3. **[Render.com](https://render.com/)** 에 가입(GitHub로 간편 로그인)합니다.
4. 대시보드 우측 상단 **[New +]** > **[Web Service]** 를 클릭합니다.
5. 조금 전 생성한 GitHub 리포지토리를 선택(Connect)합니다.
6. **Environment** 항목에서 **`Docker`** 를 선택하고, 하단의 **[Create Web Service]** 를 누릅니다.
7. 약 2~3분 후 빌드가 완료되면 고유한 무료 도메인(예: `https://ppttopdf-xxxx.onrender.com`)이 발급됩니다!
   - 전 세계 어디서나 PC, 안드로이드, 아이폰으로 24시간 접속하여 100MB 변환을 무료로 이용할 수 있습니다.

### [방법 2] Railway 배포
1. **[Railway.app](https://railway.app/)** 에 가입(GitHub 로그인)합니다.
2. **[New Project]** > **[Deploy from GitHub repo]** 를 선택합니다.
3. 내 GitHub 리포지토리를 클릭하면 `Dockerfile`을 자동으로 인식하여 즉시 배포가 시작됩니다.
4. **Settings** 탭의 **Networking** > **Generate Domain** 을 클릭하면 무료 도메인이 생성됩니다.

---

## 📂 프로젝트 구조

```
ppttopdf2/
├── app.py                  # 백엔드 서버 (Flask, LibreOffice 연동, 100MB 처리, 멀티 IP)
├── requirements.txt        # 파이썬 의존성 (Flask, Werkzeug)
├── run.bat                 # 윈도우 원클릭 실행 배치 파일
├── run.ps1                 # PowerShell 실행 스크립트
├── install_libreoffice.bat # LibreOffice 설치 안내 도우미
├── README.md               # 프로젝트 안내 문서
└── static/
    ├── index.html          # 반응형 웹 UI (100MB 업로드 진행률, QR 모달, 미리보기)
    └── qrcode.min.js       # 오프라인 순수 JS QR 코드 생성기
```
