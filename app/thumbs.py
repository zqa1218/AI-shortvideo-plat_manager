import hashlib
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

from app.publishers.sau import SAU_DIR
from app.paths import ROOT, resource_path

THUMB_DIR = ROOT / "data" / "thumbs"
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".flv", ".avi"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def file_md5(path):
    digest = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_kind(path):
    ext = Path(path).suffix.lower()
    if ext in VIDEO_EXTS:
        return "video"
    return "image"


def make_thumbnail(path, kind):
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    target = THUMB_DIR / f"{file_md5(path)}.jpg"
    if target.exists():
        return str(target)
    if kind == "video":
        vendor_python = SAU_DIR / ".venv" / "Scripts" / "python.exe"
        script = resource_path("collectors") / "video_thumb.py"
        subprocess.run([str(vendor_python), str(script), path, str(target)],
                       capture_output=True, timeout=60)
    else:
        image = QImage(path)
        if not image.isNull():
            image.scaled(320, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation).save(str(target), "JPG", 85)
    return str(target) if target.exists() else ""
