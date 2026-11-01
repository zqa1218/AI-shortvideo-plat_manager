from dataclasses import dataclass


@dataclass
class PlatformResult:
    platform: str
    status: str
    message: str = ""


class Publisher:
    name = "base"

    def publish(self, task, platforms, options=None):
        raise NotImplementedError
