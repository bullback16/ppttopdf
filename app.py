import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote
from flask import Flask, jsonify, request, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="static", static_url_path="")

# 파일 크기 제한: 100MB (멀티파트 헤더 오버헤드를 고려해 105MB로 넉넉하게 설정)
MAX_FILE_SIZE_MB = 100
app.config["MAX_CONTENT_LENGTH"] = 105 * 1024 * 1024
ALLOWED_EXTENSIONS = {"ppt", "pptx"}


def get_local_ip() -> str:
    """모바일 기기에서 접속할 수 있는 현재 PC의 로컬 네트워크 IP 주소를 가져옵니다."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 외부로 실제로 패킷을 보내지 않고 라우팅 테이블에서 사용 중인 IP를 감지합니다.
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        if local_ip and not local_ip.startswith("127."):
            return local_ip
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                return ip
    except Exception:
        pass

    return "127.0.0.1"


def find_libreoffice() -> str | None:
    """시스템 및 로컬 디렉터리에서 LibreOffice 실행 파일을 탐색합니다."""
    # 1. 환경 변수 확인
    configured_path = os.environ.get("LIBREOFFICE_PATH")
    if configured_path and Path(configured_path).is_file():
        return configured_path

    # 2. PATH 검색
    for name in ("soffice", "libreoffice", "soffice.exe", "libreoffice.exe"):
        executable = shutil.which(name)
        if executable and Path(executable).is_file():
            return executable

    # 3. 프로젝트 내부 또는 상대 경로 포터블 검색
    project_root = Path(__file__).resolve().parent
    portable_candidates = [
        project_root / "tools" / "LibreOffice" / "program" / "soffice.exe",
        project_root / "tools" / "LibreOfficePortable" / "App" / "libreoffice" / "program" / "soffice.exe",
        project_root / "libreoffice" / "program" / "soffice.exe",
        Path("C:/LibreOfficePortable/App/libreoffice/program/soffice.exe"),
    ]
    for candidate in portable_candidates:
        if candidate.is_file():
            return str(candidate)

    # 4. OS별 표준 설치 경로 검색
    if os.name == "nt":
        candidates = [
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "LibreOffice/program/soffice.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "LibreOffice/program/soffice.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/LibreOffice/program/soffice.exe",
            Path("C:/Program Files/LibreOffice/program/soffice.exe"),
            Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
        ]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
    elif os.name == "posix":
        candidates = [
            Path("/usr/bin/libreoffice"),
            Path("/usr/bin/soffice"),
            Path("/usr/local/bin/libreoffice"),
            Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
        ]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)

    return None


def sanitize_download_filename(filename: str) -> str:
    """한글, 영문, 숫자, 특수기호를 안전하게 보존하면서 파일명을 정제합니다."""
    base_name = Path(filename).stem
    # 파일시스템 및 브라우저에서 위험한 문자 제거
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", base_name).strip()
    return cleaned if cleaned else "presentation"


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/status")
def status():
    """서버 상태, 로컬 접속 IP, LibreOffice 설치 여부 등을 프론트엔드에 제공합니다."""
    libreoffice_path = find_libreoffice()
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", "5000"))
    return jsonify({
        "libreoffice_installed": bool(libreoffice_path),
        "libreoffice_path": libreoffice_path if libreoffice_path else None,
        "max_size_mb": MAX_FILE_SIZE_MB,
        "local_ip": local_ip,
        "port": port,
        "mobile_url": f"http://{local_ip}:{port}",
    })


@app.post("/api/convert")
def convert_presentation():
    uploaded_file = request.files.get("file")
    if not uploaded_file or not uploaded_file.filename:
        return jsonify(error="변환할 파일을 선택해 주세요."), 400

    original_filename = uploaded_file.filename
    raw_extension = Path(original_filename).suffix.lower().lstrip(".")
    if raw_extension not in ALLOWED_EXTENSIONS:
        return jsonify(error="PPT 또는 PPTX 파일만 변환할 수 있어요."), 400

    converter = find_libreoffice()
    if not converter:
        return jsonify(
            error=(
                "서버에 LibreOffice가 설치되어 있지 않습니다. "
                "서버 컴퓨터에 LibreOffice를 설치하거나 LIBREOFFICE_PATH를 지정해 주세요."
            )
        ), 503

    # 동시 변환 요청 충돌 방지를 위해 고유 임시 디렉터리 생성
    work_directory = Path(tempfile.mkdtemp(prefix="ppttopdf2-"))
    source_path = work_directory / f"source.{raw_extension}"
    output_path = work_directory / "source.pdf"
    profile_path = work_directory / "libreoffice_profile"

    try:
        uploaded_file.save(source_path)
    except Exception as e:
        shutil.rmtree(work_directory, ignore_errors=True)
        return jsonify(error=f"파일을 업로드하는 도중 오류가 발생했습니다: {str(e)}"), 500

    # LibreOffice 헤드리스 변환 실행
    command = [
        converter,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(work_directory),
        f"-env:UserInstallation={profile_path.as_uri()}",
        str(source_path),
    ]

    try:
        # 대용량 100MB 파일도 변환될 수 있도록 타임아웃을 300초(5분)로 설정
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        shutil.rmtree(work_directory, ignore_errors=True)
        return jsonify(error="변환 시간이 5분을 초과하여 작업이 취소되었습니다. 파일 크기나 슬라이드 수를 줄여보세요."), 504
    except subprocess.CalledProcessError as e:
        shutil.rmtree(work_directory, ignore_errors=True)
        err_msg = e.stderr if e.stderr else "파일이 손상되었거나 암호가 걸려있을 수 있습니다."
        return jsonify(error=f"파일 변환에 실패했습니다: {err_msg[:200]}"), 422
    except Exception as e:
        shutil.rmtree(work_directory, ignore_errors=True)
        return jsonify(error=f"변환 중 알 수 없는 오류가 발생했습니다: {str(e)}"), 500

    if not output_path.is_file():
        shutil.rmtree(work_directory, ignore_errors=True)
        return jsonify(error="PDF 파일이 생성되지 않았습니다. 다른 파일로 다시 시도해 주세요."), 422

    # 안전한 한글 및 유니코드 다운로드 파일명 생성
    stem_name = sanitize_download_filename(original_filename)
    download_filename = f"{stem_name}.pdf"

    # RFC 5987 호환 한글 인코딩
    encoded_name = quote(download_filename)
    ascii_safe_name = secure_filename(download_filename) or "presentation.pdf"

    response = send_file(
        output_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=download_filename,
    )
    # Content-Disposition 헤더를 UTF-8로 지정하여 iOS Safari, Android Chrome, Windows 브라우저 모두에서 한글 파일명이 깨지지 않게 보장
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{ascii_safe_name}"; filename*=UTF-8\'\'{encoded_name}'
    )
    # 캐시 방지
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    # 응답이 완료된 후 임시 디렉터리 자동 삭제
    response.call_on_close(lambda: shutil.rmtree(work_directory, ignore_errors=True))
    return response


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify(error=f"파일 크기가 {MAX_FILE_SIZE_MB}MB를 초과했습니다. 100MB 이하의 파일만 변환할 수 있습니다."), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    local_ip = get_local_ip()
    libreoffice_path = find_libreoffice()

    print("=" * 64)
    print(" 🚀 PPT/PPTX -> PDF 변환 웹 서버가 시작되었습니다!")
    print(f" 💻 [Windows PC 접속]:      http://localhost:{port}")
    print(f"                           http://127.0.0.1:{port}")
    print(f" 📱 [안드로이드/iOS 접속]:   http://{local_ip}:{port}")
    print("   (스마트폰과 PC가 같은 Wi-Fi 공유기에 연결되어 있어야 합니다)")
    print("-" * 64)
    if libreoffice_path:
        print(f" ✅ LibreOffice 감지됨: {libreoffice_path}")
    else:
        print(" ⚠️  경고: LibreOffice를 찾을 수 없습니다!")
        print("    변환 기능을 사용하려면 LibreOffice를 설치해야 합니다.")
        print("    다운로드: https://ko.libreoffice.org/download/download/")
    print("=" * 64)

    # 0.0.0.0으로 바인딩하여 안드로이드, iOS, 타 PC 등 동일 네트워크 모든 기기에서 접속 허용
    app.run(host="0.0.0.0", port=port, debug=False)
