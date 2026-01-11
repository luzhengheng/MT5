import pandas as pd
from sqlalchemy import create_engine, text
from src.config.env_loader import Config

class TimescaleClient:
    def __init__(self):
        self.engine = create_engine(Config.get_db_url())

    def check_connection(self):
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT version();")).fetchone()
                print(f"✅ DB Version: {res[0]}")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
                conn.commit()
                print("✅ TimescaleDB Ready.")
            return True
        except Exception as e:
            print(f"❌ DB Error: {e}")
            return False
