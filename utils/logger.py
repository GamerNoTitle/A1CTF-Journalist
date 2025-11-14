"""简单统一日志模块。

提供 `log(message, level="INFO")` 接口并支持同时输出到控制台和文件。
默认输出格式：`[YYYY-MM-DD HH:MM:SS] LEVEL message`。
"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any


# 配置
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_FILE = os.getenv("LOG_FILE", os.path.join(LOG_DIR, "app.log"))
MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 5 * 1024 * 1024))
BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 3))

os.makedirs(LOG_DIR, exist_ok=True)

_logger = logging.getLogger("a1ctf_journalist")
_logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    fmt="[%(asctime)s] %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
_logger.addHandler(ch)

# File handler with rotation
fh = RotatingFileHandler(LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
_logger.addHandler(fh)


def log(message: Any, level: str = "INFO") -> None:
    """统一日志接口。

    Args:
        message: 要记录的内容，任意类型会被转换为字符串。
        level: 日志级别，支持 'DEBUG','INFO','WARNING','ERROR'. 默认为 'INFO'.
    """
    try:
        msg = str(message)
    except Exception:
        msg = repr(message)

    level = (level or "INFO").upper()
    if level == "DEBUG":
        _logger.debug(msg)
    elif level == "WARNING" or level == "WARN":
        _logger.warning(msg)
    elif level == "ERROR":
        _logger.error(msg)
    else:
        _logger.info(msg)


def debug(message: Any) -> None:
    log(message, level="DEBUG")


def info(message: Any) -> None:
    log(message, level="INFO")


def warning(message: Any) -> None:
    log(message, level="WARNING")


def error(message: Any) -> None:
    log(message, level="ERROR")

