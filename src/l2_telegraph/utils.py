import sys

from loguru import logger
from pydantic import BaseModel
from yaml import safe_load


class Config(BaseModel):
    zksync_rpc: str


def load_config(path: str) -> Config:
    with open(path, "r") as f:
        return Config(**safe_load(f))


def init_logger():
    logger.remove()

    logger.add(
        "logs/{time:MM_D}/{time:HH_mm}.log",
        format="{time:HH:mm:ss} | {function}:{line} | {level} - {message}",
    )
    logger.add(
        sys.stdout,
        format="<level>{time:HH:mm:ss}</level> | <lk>{function}</lk>:<lk>{line}</lk> | <level>{level}</level> - 🐷 <magenta>{message}</magenta>",
        colorize=True,
    )
