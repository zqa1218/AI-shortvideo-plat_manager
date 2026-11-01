from dataclasses import dataclass, field

# 平台之间不是"同一套流程换个网址"：支持的内容类型、标题字数、图片与话题上限都不同。
# 这里集中声明差异，发布前的校验、参数裁剪、提示文案都从这里取，避免各页面各写一套。
#   kinds       支持的发布类型
#   limits      video_title / note_title 为标题上限（0 表示该类型不支持），
#               images 为图文图片张数上限（0 表示不支持图文），
#               tags 为话题数量上限（None 表示不做限制）
PLATFORMS = {
    "bilibili": {
        "name": "B站",
        "upload_url": "https://member.bilibili.com/platform/upload/video/frame",
        "kinds": ("video",),
        "limits": {"video_title": 80, "note_title": 0, "images": 0, "tags": 12},
    },
    "xiaohongshu": {
        "name": "小红书",
        "upload_url": "https://creator.xiaohongshu.com/publish/publish",
        "kinds": ("video", "note"),
        "limits": {"video_title": 20, "note_title": 20, "images": 18, "tags": 10},
    },
    "douyin": {
        "name": "抖音",
        "upload_url": "https://creator.douyin.com/creator-micro/content/upload",
        "kinds": ("video", "note"),
        "limits": {"video_title": 30, "note_title": 20, "images": 35, "tags": None},
    },
}

STATUS_LABELS = {
    "draft": "草稿",
    "queued": "排队中",
    "scheduled": "已排期",
    "publishing": "发布中",
    "done": "已完成",
    "manual_pending": "待手动确认",
    "failed": "失败",
}

KIND_LABELS = {"video": "视频", "note": "图文笔记"}


def platform_name(platform):
    return PLATFORMS.get(platform, {}).get("name", platform)


def supports_kind(platform, kind):
    return kind in PLATFORMS.get(platform, {}).get("kinds", ())


def title_limit(platform, kind):
    """该平台该内容类型的标题上限，0 或缺失表示不支持。"""
    limits = PLATFORMS.get(platform, {}).get("limits", {})
    return limits.get(f"{kind}_title") or 0


def images_limit(platform):
    return PLATFORMS.get(platform, {}).get("limits", {}).get("images") or 0


def tags_limit(platform):
    return PLATFORMS.get(platform, {}).get("limits", {}).get("tags")


def fit_title(platform, kind, title):
    """按平台上限裁剪标题，返回 (可用标题, 是否被裁剪)。"""
    limit = title_limit(platform, kind)
    text = (title or "").strip()
    if limit and len(text) > limit:
        return text[:limit], True
    return text, False


def fit_tags(platform, tags):
    """tags 为逗号分隔字符串，返回 (可用标签列表, 是否被裁剪)。"""
    items = [tag.strip() for tag in (tags or "").replace("，", ",").split(",") if tag.strip()]
    limit = tags_limit(platform)
    if limit and len(items) > limit:
        return items[:limit], True
    return items, False


def platform_issues(platform, kind, title, image_count=0, tags=None):
    """发布前按平台规则体检，返回 [(级别, 说明)]；级别为 error 表示该平台发不了。"""
    name = platform_name(platform)
    issues = []
    if not supports_kind(platform, kind):
        issues.append(("error", f"{name} 不支持{KIND_LABELS.get(kind, kind)}发布"))
        return issues
    limit = title_limit(platform, kind)
    if limit and len((title or "").strip()) > limit:
        issues.append((
            "warning",
            f"{name}{KIND_LABELS.get(kind, kind)}标题上限 {limit} 字，将自动截断为「{(title or '').strip()[:limit]}」",
        ))
    if kind == "note":
        max_images = images_limit(platform)
        if image_count <= 0:
            issues.append(("error", f"{name} 图文笔记需要至少 1 张图片"))
        elif max_images and image_count > max_images:
            issues.append(("error", f"{name} 图文最多 {max_images} 张图片，当前 {image_count} 张"))
    tag_items = [tag for tag in str(tags or "").replace("，", ",").split(",") if tag.strip()]
    tag_cap = tags_limit(platform)
    if tag_cap and len(tag_items) > tag_cap:
        issues.append(("warning", f"{name} 话题最多 {tag_cap} 个，超出部分将忽略"))
    return issues


@dataclass
class Task:
    title: str
    content: str = ""
    tags: str = ""
    media_path: str = ""
    kind: str = "video"
    images: list = field(default_factory=list)
    platforms: list = field(default_factory=list)
    scheduled_at: str = ""
    tid: str = "249"
    id: int = 0
    status: str = "draft"
    created_at: str = ""
