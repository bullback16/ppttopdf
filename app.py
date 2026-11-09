import io
import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote
from flask import Flask, jsonify, request, send_file
import pymupdf
from pptx import Presentation
from pptx.util import Pt
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="static", static_url_path="")

# 파일 크기 제한: 100MB (헤더 오버헤드를 고려해 105MB로 넉넉하게 설정)
MAX_FILE_SIZE_MB = 100
app.config["MAX_CONTENT_LENGTH"] = 105 * 1024 * 1024
ALLOWED_EXTENSIONS = {"ppt", "pptx", "pdf"}


def get_local_ip() -> str:
    """모바일 기기에서 접속할 수 있는 현재 PC의 로컬 네트워크 IP 주소를 가져옵니다."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
    """시스템 및 로컬 디렉터리에서 LibreOffice 실행 파일을 탐색합니다 (PPT -> PDF 변환용)."""
    configured_path = os.environ.get("LIBREOFFICE_PATH")
    if configured_path and Path(configured_path).is_file():
        return configured_path

    for name in ("soffice", "libreoffice", "soffice.exe", "libreoffice.exe"):
        executable = shutil.which(name)
        if executable and Path(executable).is_file():
            return executable

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
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", base_name).strip()
    return cleaned if cleaned else "presentation"


def convert_pdf_to_pptx(pdf_path: Path, output_pptx_path: Path):
    """PDF 문서를 고화질 16:9/원본 비율의 파워포인트(PPTX) 슬라이드로 변환합니다."""
    doc = pymupdf.open(str(pdf_path))
    prs = Presentation()
    blank_layout = prs.slide_layouts[6]

    if len(doc) > 0:
        first_page = doc[0]
        # fitz pt 단위를 python-pptx Pt로 동적 매핑 (원본 종횡비 100% 보존)
        prs.slide_width = Pt(first_page.rect.width)
        prs.slide_height = Pt(first_page.rect.height)

    for page in doc:
        # 2.0 배율(144 DPI) 고해상도 벡터 렌더링
        zoom = 2.0
        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img_bytes = pix.tobytes("png")
        img_stream = io.BytesIO(img_bytes)

        slide = prs.slides.add_slide(blank_layout)
        slide.shapes.add_picture(
            img_stream,
            left=Pt(0),
            top=Pt(0),
            width=Pt(page.rect.width),
            height=Pt(page.rect.height),
        )

    doc.close()
    prs.save(str(output_pptx_path))


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/status")
def status():
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
def convert_document():
    uploaded_file = request.files.get("file")
    if not uploaded_file or not uploaded_file.filename:
        return jsonify(error="변환할 파일을 선택해 주세요."), 400

    original_filename = uploaded_file.filename
    raw_extension = Path(original_filename).suffix.lower().lstrip(".")
    if raw_extension not in ALLOWED_EXTENSIONS:
        return jsonify(error="PPT, PPTX 또는 PDF 파일만 변환할 수 있어요."), 400

    work_directory = Path(tempfile.mkdtemp(prefix="doc-converter-"))
    source_path = work_directory / f"source.{raw_extension}"

    try:
        uploaded_file.save(source_path)
    except Exception as e:
        shutil.rmtree(work_directory, ignore_errors=True)
        return jsonify(error=f"파일 업로드 중 오류가 발생했습니다: {str(e)}"), 500

    stem_name = sanitize_download_filename(original_filename)

    # 1. [PDF -> PPTX 변환 모드]
    if raw_extension == "pdf":
        output_path = work_directory / "output.pptx"
        try:
            convert_pdf_to_pptx(source_path, output_path)
        except Exception as e:
            shutil.rmtree(work_directory, ignore_errors=True)
            return jsonify(error=f"PDF를 PPTX로 변환하지 못했습니다: {str(e)}"), 422

        download_filename = f"{stem_name}.pptx"
        mimetype = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    # 2. [PPT/PPTX -> PDF 변환 모드]
    else:
        converter = find_libreoffice()
        if not converter:
            shutil.rmtree(work_directory, ignore_errors=True)
            return jsonify(
                error="서버에 LibreOffice가 설치되어 있지 않습니다. PPT to PDF 변환을 위해 LibreOffice가 필요합니다."
            ), 503

        output_path = work_directory / "source.pdf"
        profile_path = work_directory / "libreoffice_profile"

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
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            shutil.rmtree(work_directory, ignore_errors=True)
            return jsonify(error="변환 시간이 5분을 초과하여 작업이 중단되었습니다."), 504
        except subprocess.CalledProcessError as e:
            shutil.rmtree(work_directory, ignore_errors=True)
            err_msg = e.stderr if e.stderr else "파일이 손상되었거나 암호가 걸려있을 수 있습니다."
            return jsonify(error=f"파일 변환에 실패했습니다: {err_msg[:200]}"), 422
        except Exception as e:
            shutil.rmtree(work_directory, ignore_errors=True)
            return jsonify(error=f"변환 중 알 수 없는 오류가 발생했습니다: {str(e)}"), 500

        download_filename = f"{stem_name}.pdf"
        mimetype = "application/pdf"

    if not output_path.is_file():
        shutil.rmtree(work_directory, ignore_errors=True)
        return jsonify(error="결과 파일이 생성되지 않았습니다. 다른 파일로 시도해 주세요."), 422

    # 안전한 UTF-8 Content-Disposition 헤더 처리
    encoded_name = quote(download_filename)
    ascii_safe_name = secure_filename(download_filename) or ("document.pptx" if raw_extension == "pdf" else "document.pdf")

    response = send_file(
        output_path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=download_filename,
    )
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{ascii_safe_name}"; filename*=UTF-8\'\'{encoded_name}'
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

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
    print(" 🚀 PPT ⇄ PDF 양방향 변환 웹 서버가 시작되었습니다!")
    print(f" 💻 [Windows PC 접속]:      http://localhost:{port}")
    print(f" 📱 [안드로이드/iOS 접속]:   http://{local_ip}:{port}")
    print("   (스마트폰과 PC가 같은 Wi-Fi 공유기에 연결되어 있어야 합니다)")
    print("-" * 64)
    print(" ✅ PDF ➔ PPTX 고화질 변환 엔진: 준비 완료 (PyMuPDF)")
    if libreoffice_path:
        print(f" ✅ PPT ➔ PDF 변환 엔진 (LibreOffice): {libreoffice_path}")
    else:
        print(" ⚠️  주의: PPT ➔ PDF 변환을 위한 LibreOffice가 아직 감지되지 않았습니다.")
        print("    (PDF ➔ PPTX 변환 기능은 바로 정상 사용 가능합니다)")
    print("=" * 64)

    app.run(host="0.0.0.0", port=port, debug=False)
