import os
from dataclasses import dataclass


@dataclass
class Config:
    BOT_TOKEN: str
    ADMIN_ID: int
    CHANNEL_ID: str
    DB_PATH: str = "/data/shop.db"


def load_config() -> Config:
    token = os.environ.get("BOT_TOKEN", "")
    admin_id = int(os.environ.get("ADMIN_ID", "0"))
    channel_id = os.environ.get("CHANNEL_ID", "")
    if not token or not admin_id:
        raise ValueError("BOT_TOKEN and ADMIN_ID are required")
    return Config(BOT_TOKEN=token, ADMIN_ID=admin_id, CHANNEL_ID=channel_id)


config = load_config()
