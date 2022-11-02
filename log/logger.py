from datetime import datetime
from colored import fg
from colored import attr

current_logging_level = 0

logging_levels = {
    "debug-info": 1,
    "info": 2,
    "warning": 3,
    "error": 4,
    "fatal-error": 5,
    "disabled": 6
}


def set_level(level: int):
    global current_logging_level
    current_logging_level = level


def log_message(level: int, tag: str, message_type: str, message: str):
    if level < current_logging_level: return
    if level > 3: label_color = fg(124)
    else: label_color = fg(67)
    print(
        f"{fg(33)}[{datetime.now().strftime('%d/%m/%y %H:%M:%S')}] {attr(0)}"
        f"[{tag}] - {label_color}{message_type}{attr(0)}: {message}"
    )


def debug(tag: str, message: str):
    log_message(1, tag, "DEBUG", message)


def info(tag: str, message: str):
    log_message(2, tag, "INFO", message)


def warn(tag: str, message: str):
    log_message(3, tag, "WARNING", message)


def error(tag: str, message: str):
    log_message(4, tag, "ERROR", message)


def fatal(tag: str, message: str):
    log_message(5, tag, "FATAL", message)
