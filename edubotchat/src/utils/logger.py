"""
logger.py - Cấu hình logging cho toàn bộ ứng dụng.
"""

import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "StudyPlanner",
    level: int = logging.DEBUG,
    log_file: str = "logs/app.log"
) -> logging.Logger:
    """Tạo và cấu hình logger.

    Args:
        name: Tên logger
        level: Mức log
        log_file: Đường dẫn file log (sẽ tự tạo thư mục nếu chưa có)
    """
    # Tạo thư mục logs nếu chưa tồn tại
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Tránh duplicate handler nếu gọi lại nhiều lần
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(level)
    fh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


# Logger mặc định
logger = setup_logger()