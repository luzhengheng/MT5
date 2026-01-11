import os
from pathlib import Path
from dotenv import load_dotenv

current_path = Path(__file__).resolve()
ROOT_DIR = current_path.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

class Config:
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_USER = os.getenv("POSTGRES_USER", "postgres")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "password")
    DB_NAME = os.getenv("POSTGRES_DB", "mt5_crs")
    DATA_DIR = ROOT_DIR / "data"
    
    @staticmethod
    def get_db_url():
        return f"postgresql://{Config.DB_USER}:{Config.DB_PASS}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
