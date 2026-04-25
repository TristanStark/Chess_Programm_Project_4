DEBUG = False


def is_debug() -> bool:
    return DEBUG


def set_debug(enabled: bool) -> bool:
    global DEBUG
    DEBUG = bool(enabled)
    return DEBUG


def toggle_debug() -> bool:
    return set_debug(not DEBUG)


def debug_print(*args, **kwargs) -> None:
    if DEBUG:
        print(*args, **kwargs)
