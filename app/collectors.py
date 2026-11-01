import json
import subprocess
from pathlib import Path

from app import database
from app.paths import ROOT, resource_path
from app.publishers.sau import SAU_DIR

PROJECT_ROOT = ROOT
COLLECTORS_DIR = resource_path("collectors")
DEBUG_DIR = PROJECT_ROOT / "data" / "collector_debug"


def vendor_python():
    return SAU_DIR / ".venv" / "Scripts" / "python.exe"


def cookie_file(platform, account):
    return SAU_DIR / "cookies" / f"{platform}_{account}.json"


def _run_collector(args):
    proc = subprocess.run(
        [str(vendor_python()), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    output = (proc.stdout or "").strip().splitlines()
    if not output:
        return {"success": False, "works": [], "message": (proc.stderr or "采集器无输出")[-300:]}
    try:
        return json.loads(output[-1])
    except ValueError:
        return {"success": False, "works": [], "message": output[-1][-300:]}


def collect_account(account):
    platform = account["platform"]
    nickname = account["nickname"]
    cookies = cookie_file(platform, nickname)
    if not cookies.exists():
        return {"success": False, "works": [], "message": f"未找到登录态文件 {cookies.name}，请先扫码登录"}
    if platform == "bilibili":
        return _run_collector([
            str(COLLECTORS_DIR / "bilibili_collector.py"),
            "--cookie-file", str(cookies),
        ])
    return _run_collector([
        str(COLLECTORS_DIR / "browser_collector.py"),
        "--platform", platform,
        "--cookie-file", str(cookies),
        "--debug-dir", str(DEBUG_DIR),
    ])


def save_works(works):
    for work in works:
        database.execute(
            "INSERT INTO metrics (platform, work_title, plays, likes, comments, favorites, shares, work_id, url)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (work["platform"], work["work_title"], work["plays"], work["likes"],
             work["comments"], work["favorites"], work["shares"],
             work.get("work_id", ""), work.get("url", "")),
        )


def collect_all():
    accounts = database.query("SELECT * FROM accounts ORDER BY id")
    if not accounts:
        return [{"account": "-", "success": False, "count": 0, "message": "请先在账号管理中添加账号并扫码登录"}]
    summaries = []
    for account in accounts:
        try:
            result = collect_account(account)
        except Exception as exc:
            result = {"success": False, "works": [], "message": str(exc)}
        if result["works"]:
            save_works(result["works"])
        summaries.append({
            "account": f"{account['platform']}:{account['nickname']}",
            "success": result["success"],
            "count": len(result["works"]),
            "message": result["message"],
        })
    return summaries
