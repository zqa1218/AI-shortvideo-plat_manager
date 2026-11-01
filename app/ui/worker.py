from PySide6.QtCore import QThread, Signal

from app import database
from app.publishers import get_publisher
from app.publishers.base import PlatformResult


class PublishWorker(QThread):
    platform_done = Signal(int, object)
    finished_all = Signal(int)

    def __init__(self, task_id, task, publisher_name="manual", options=None):
        super().__init__()
        self.task_id = task_id
        self.task = task
        self.publisher_name = publisher_name
        self.options = options or {}

    def run(self):
        publisher = get_publisher(self.publisher_name)
        database.execute("UPDATE tasks SET status='publishing' WHERE id=?", (self.task_id,))

        # 逐平台执行、逐平台落库：小红书成功不该等抖音超时才显示，
        # 一个平台异常也不会中断其它平台。
        results = []
        for platform in self.task.platforms:
            try:
                platform_results = publisher.publish(self.task, [platform], self.options) or []
            except Exception as exc:  # noqa: BLE001 - 发布器异常要转成平台级失败，不能让任务卡死
                platform_results = [PlatformResult(platform, "failed", f"发布异常：{exc}")]
            if not platform_results:
                platform_results = [PlatformResult(platform, "failed", "发布器没有返回结果")]
            for result in platform_results:
                database.execute(
                    "INSERT INTO task_results (task_id, platform, status, message)"
                    " VALUES (?, ?, ?, ?)",
                    (self.task_id, result.platform, result.status, result.message),
                )
                results.append(result)
                self.platform_done.emit(self.task_id, result)

        if any(result.status == "failed" for result in results):
            final_status = "failed"
        elif any(result.status == "manual_pending" for result in results):
            final_status = "manual_pending"
        elif results:
            final_status = "done"
        else:
            final_status = "failed"
        database.execute("UPDATE tasks SET status=? WHERE id=?", (final_status, self.task_id))
        self.finished_all.emit(self.task_id)
