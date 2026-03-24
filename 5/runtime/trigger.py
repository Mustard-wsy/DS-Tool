from .scheduler import scheduler


def trigger():
    scheduler.request_update()
