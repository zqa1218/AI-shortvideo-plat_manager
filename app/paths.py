import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
ROOT = Path(sys.executable).parent if FROZEN else Path(__file__).resolve().parent.parent


def resource_path(name):
    local_resource = ROOT / name
    if local_resource.exists() or not FROZEN:
        return local_resource
    return Path(sys._MEIPASS) / name


def asset_path(name):
    return str(resource_path("assets") / name)


def sau_dir():
    candidates = [
        ROOT / "vendor" / "social-auto-upload",
        ROOT.parent / "vendor" / "social-auto-upload",
        ROOT.parent.parent / "vendor" / "social-auto-upload",
        Path(__file__).resolve().parent.parent / "vendor" / "social-auto-upload",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]
