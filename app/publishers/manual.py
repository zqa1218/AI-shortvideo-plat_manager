import webbrowser

from app.models import PLATFORMS
from app.publishers.base import PlatformResult, Publisher


class ManualPublisher(Publisher):
    name = "manual"

    def publish(self, task, platforms, options=None):
        results = []
        for platform in platforms:
            info = PLATFORMS[platform]
            webbrowser.open(info["upload_url"])
            results.append(PlatformResult(
                platform=platform,
                status="manual_pending",
                message=f"已打开{info['name']}创作者后台，请在浏览器中完成上传",
            ))
        return results
