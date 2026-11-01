import argparse
import json
import re
from pathlib import Path

from patchright.sync_api import sync_playwright

CONFIG = {
    "douyin": {
        "url": "https://creator.douyin.com/creator-micro/content/manage",
        "cards": [".card-list-item", "[class*='work-card']", "[class*='video-card']", "[class*='work-item']"],
    },
    "xiaohongshu": {
        "url": "https://creator.xiaohongshu.com/creator/notes",
        "cards": [".note-item", "[class*='note-card']", "[class*='note-item']"],
    },
}


def parse_number(text):
    match = re.search(r"(\d+(?:\.\d+)?)\s*([万亿wW]?)", text.replace(",", ""))
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    if unit in ("万", "w", "W"):
        value *= 10000
    elif unit == "亿":
        value *= 100000000
    return int(value)


def extract_cards(page, platform):
    works = []
    raw_cards = []
    for selector in CONFIG[platform]["cards"]:
        cards = page.query_selector_all(selector)
        if not cards:
            continue
        for card in cards[:50]:
            text = card.inner_text().strip()
            if not text:
                continue
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            numbers = [n for n in (parse_number(line) for line in lines) if n is not None]
            raw_cards.append({"selector": selector, "lines": lines})
            if not numbers:
                continue
            title = lines[0][:80]
            works.append({
                "platform": platform,
                "work_id": "",
                "work_title": title,
                "plays": numbers[0] if len(numbers) > 0 else 0,
                "likes": numbers[1] if len(numbers) > 1 else 0,
                "comments": numbers[2] if len(numbers) > 2 else 0,
                "favorites": numbers[3] if len(numbers) > 3 else 0,
                "shares": 0,
                "url": page.url,
            })
        if works:
            break
    return works, raw_cards


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True, choices=list(CONFIG))
    parser.add_argument("--cookie-file", required=True)
    parser.add_argument("--debug-dir", required=True)
    args = parser.parse_args()
    debug_dir = Path(args.debug_dir)
    debug_dir.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state=args.cookie_file)
            page = context.new_page()
            page.goto(CONFIG[args.platform]["url"], wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(8000)
            if "login" in page.url:
                raise RuntimeError("登录态失效，请重新扫码登录")
            works, raw_cards = extract_cards(page, args.platform)
            (debug_dir / f"{args.platform}_page.html").write_text(page.content(), encoding="utf-8")
            (debug_dir / f"{args.platform}_cards.json").write_text(
                json.dumps(raw_cards, ensure_ascii=False, indent=2), encoding="utf-8")
            page.screenshot(path=str(debug_dir / f"{args.platform}_page.png"), full_page=False)
            browser.close()
        if works:
            message = f"解析到 {len(works)} 条作品（字段映射为通用规则，建议核对首条数据）"
        else:
            message = "未解析到作品，已保存页面调试文件，需按实际页面校准选择器"
        print(json.dumps({"success": bool(works), "works": works, "message": message}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"success": False, "works": [], "message": str(exc)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
