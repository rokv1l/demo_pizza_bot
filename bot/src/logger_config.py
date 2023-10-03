from loguru import logger

from config import logs_path


logger.add(
    f"{logs_path}data.log",
    format="{name} {time} {level} {message}",
    level="DEBUG",
    rotation="15MB",
    compression="zip",
)
