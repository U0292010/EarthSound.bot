import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    database_path: Path


def load_config() -> Config:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token or bot_token == "your_telegram_bot_token_here":
        raise RuntimeError("BOT_TOKEN ni .env faylida sozlang.")

    database_path = Path(os.getenv("DATABASE_PATH", "data/earth_jukebox.sqlite3"))
    return Config(bot_token=bot_token, database_path=database_path)