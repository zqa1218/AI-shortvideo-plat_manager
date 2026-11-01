def get_publisher(name):
    if name == "sau":
        from app.publishers.sau import SauPublisher
        return SauPublisher()
    from app.publishers.manual import ManualPublisher
    return ManualPublisher()
