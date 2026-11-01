import argparse
import json
import sys
import time

import requests

API_NAV = "https://api.bilibili.com/x/web-interface/nav"
API_WORKS = "https://api.bilibili.com/x/space/arc/search"
API_STAT = "https://api.bilibili.com/x/web-interface/archive/stat"


def load_cookies(path):
    data = json.loads(open(path, encoding="utf-8").read())
    if "cookie_info" in data:
        return {c["name"]: c["value"] for c in data["cookie_info"]["cookies"]}
    return {c["name"]: c["value"] for c in data.get("cookies", [])}


def api_get(session, url, params=None):
    resp = session.get(url, params=params, timeout=20)
    payload = resp.json()
    if payload.get("code") != 0:
        raise RuntimeError(f"{url} 返回错误: {payload.get('code')} {payload.get('message')}")
    return payload["data"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cookie-file", required=True)
    parser.add_argument("--max-works", type=int, default=30)
    args = parser.parse_args()
    try:
        session = requests.Session()
        session.cookies.update(load_cookies(args.cookie_file))
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
        nav = api_get(session, API_NAV)
        if not nav.get("isLogin"):
            raise RuntimeError("B站登录态失效，请重新扫码登录")
        mid = nav["mid"]
        works_data = api_get(session, API_WORKS, {
            "mid": mid, "ps": args.max_works, "pn": 1,
            "order": "pubdate", "platform": "web",
        })
        vlist = works_data.get("list", {}).get("vlist", [])
        works = []
        for item in vlist:
            stat = api_get(session, API_STAT, {"bvid": item["bvid"]})["stat"]
            works.append({
                "platform": "bilibili",
                "work_id": item["bvid"],
                "work_title": item["title"],
                "plays": stat.get("view", 0),
                "likes": stat.get("like", 0),
                "comments": stat.get("reply", 0),
                "favorites": stat.get("favorite", 0),
                "shares": stat.get("share", 0),
                "url": f"https://www.bilibili.com/video/{item['bvid']}",
            })
            time.sleep(0.3)
        print(json.dumps({"success": True, "works": works, "message": f"采集到 {len(works)} 条B站作品"}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"success": False, "works": [], "message": str(exc)}, ensure_ascii=False))
        sys.exit(0)


if __name__ == "__main__":
    main()
