import os
from pathlib import Path
from dotenv import load_dotenv

dotenv_path = Path(os.getcwd()) / ".env"
if not dotenv_path.exists():
    raise FileNotFoundError(f".env file not found at {dotenv_path}")

load_dotenv(dotenv_path, override=True)


bot_app_id = os.getenv("BOT_APP_ID", "")
if not bot_app_id:
    raise ValueError("BOT_APP_ID environment variable not set. " "Please set it with: export BOT_APP_ID=your-app-id")

bot_app_secret = os.getenv("BOT_APP_SECRET", "")
if not bot_app_secret:
    raise ValueError("BOT_APP_SECRET environment variable not set. " "Please set it with: export BOT_APP_SECRET=your-app-secret")

# Global view configuration (from .env)
global_view_table_app_token = os.getenv("GLOBAL_VIEW_TABLE_APP_TOKEN", "")
global_view_table_id = os.getenv("GLOBAL_VIEW_TABLE_ID", "")
global_view_table_view_id = os.getenv("GLOBAL_VIEW_TABLE_VIEW_ID", "")
