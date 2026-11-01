import os
import subprocess

from app import database
from app.models import fit_tags, fit_title, platform_issues, platform_name
from app.paths import sau_dir
from app.publishers.base import PlatformResult, Publisher

SAU_DIR = sau_dir()

# 各内容类型的超时预算：视频要等上传 + 转码，图文主要是传图片。
# 之前没有超时，遇到平台卡住只能等用户手动关窗口，整个任务永远停在"发布中"。
PLATFORM_TIMEOUTS = {"video": 900, "note": 600}


def sau_executable():
    if os.name == "nt":
        return SAU_DIR / ".venv" / "Scripts" / "sau.exe"
    return SAU_DIR / ".venv" / "bin" / "sau"


def available():
    return sau_executable().exists()


def _run_env():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_sau(args, timeout=600):
    """执行 sau 子进程；返回 (退出码, 输出)。超时返回 (None, 说明)，不抛异常。"""
    try:
        proc = subprocess.run(
            [str(sau_executable()), *args],
            cwd=SAU_DIR,
            env=_run_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, f"超过 {timeout} 秒仍未结束，已强制放弃（多为平台页面卡住或元素定位失败）"
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def explain_failure(output):
    """把 sau 的原始报错翻译成用户能处理的一句话；认不出来就返回空串。"""
    text = output or ""
    low = text.lower()
    if "locator" in low and "timeout" in low:
        return "页面元素迟迟没有出现（平台可能改版，需要更新该平台的选择器）"
    if "timeout" in low:
        return "操作超时"
    if "cookie" in low or "登录态" in text:
        return "登录态失效，请到账号管理重新扫码"
    if "net::err" in low or "connect" in low:
        return "网络连接失败"
    return ""


def open_console(args):
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    return subprocess.Popen([str(sau_executable()), *args], cwd=SAU_DIR, env=_run_env(), **kwargs)


def open_login(platform, account):
    args = [platform, "login", "--account", account]
    if platform in {"douyin", "xiaohongshu"}:
        args.append("--headed")
    return open_console(args)


def find_account(platform):
    rows = database.query(
        "SELECT nickname FROM accounts WHERE platform=? ORDER BY id DESC LIMIT 1", (platform,))
    return rows[0]["nickname"] if rows else ""


class SauPublisher(Publisher):
    name = "sau"

    def publish(self, task, platforms, options=None):
        options = options or {}
        return [self.publish_one(task, platform, options) for platform in platforms]

    def publish_one(self, task, platform, options=None):
        """单个平台一个结果：平台之间互不影响，某个平台失败不会拖累其它平台。"""
        options = options or {}
        name = platform_name(platform)
        if not available():
            return PlatformResult(platform, "failed", "未安装 social-auto-upload，无法自动发布")

        blocking = [
            text for level, text in platform_issues(
                platform, task.kind, task.title, len(task.images), task.tags)
            if level == "error"
        ]
        if blocking:
            return PlatformResult(platform, "failed", "；".join(blocking))

        account = find_account(platform)
        if not account:
            return PlatformResult(
                platform, "failed",
                f"未配置{name}账号，请先在账号管理中添加账号并完成扫码登录")

        args = self._build_args(platform, account, task, options)
        timeout = PLATFORM_TIMEOUTS.get(task.kind, 600)
        code, output = run_sau(args, timeout)
        tail = (output or "")[-600:]
        if code is None:
            return PlatformResult(platform, "failed", f"{name}发布超时（超过 {timeout} 秒）\n{tail}")
        if code == 0:
            return PlatformResult(platform, "done", f"{name}发布成功\n{tail}")
        hint = explain_failure(output)
        head = f"{name}发布失败（退出码 {code}）"
        if hint:
            head += f"：{hint}"
        return PlatformResult(platform, "failed", f"{head}\n{tail}")

    def _build_args(self, platform, account, task, options):
        # 标题与话题按目标平台的上限裁剪，避免一个平台的字数限制让整单失败
        title, _ = fit_title(platform, task.kind, task.title)
        tags, _ = fit_tags(platform, task.tags)
        if task.kind == "note":
            return self._build_note_args(platform, account, task, title, tags)
        return self._build_video_args(platform, account, task, title, tags, options)

    def _build_note_args(self, platform, account, task, title, tags):
        args = [platform, "upload-note", "--account", account,
                "--images", *task.images, "--title", title]
        if task.content:
            args += ["--note", task.content]
        if tags:
            args += ["--tags", ",".join(tags)]
        return args

    def _build_video_args(self, platform, account, task, title, tags, options):
        args = [platform, "upload-video", "--account", account,
                "--file", task.media_path, "--title", title]
        if platform == "bilibili":
            # 分区是 B 站专有参数，其它平台不传
            args += ["--desc", task.content or title,
                     "--tid", str(options.get("tid") or "249")]
        elif task.content:
            args += ["--desc", task.content]
        if tags:
            args += ["--tags", ",".join(tags)]
        return args
