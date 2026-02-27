import json
from pathlib import Path


def load_global_config() -> dict[str, str]:
    """Load global view configuration from ~/.config/tuido/config.json.

    Returns:
        Dictionary containing global view configuration.
        Empty dict if config file doesn't exist.
    """
    config_path = Path.home() / ".config" / "tuido" / "config.json"

    if not config_path.exists():
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except (json.JSONDecodeError, IOError):
        return {}


def get_global_view_config() -> dict[str, str]:
    """
    Get global view configuration from config file.
    Load config from ~/.config/tuido/config.json

    Returns:
        Dictionary with keys:
        - feishu_api_endpoint
        - feishu_table_app_token
        - feishu_table_id
        - feishu_table_view_id
        - feishu_bot_app_id
        - feishu_bot_app_secret
    """
    config = load_global_config()
    return {
        "feishu_api_endpoint": config.get("feishu_api_endpoint", ""),
        "feishu_table_app_token": config.get("feishu_table_app_token", ""),
        "feishu_table_id": config.get("feishu_table_id", ""),
        "feishu_table_view_id": config.get("feishu_table_view_id", ""),
        "feishu_bot_app_id": config.get("feishu_bot_app_id", ""),
        "feishu_bot_app_secret": config.get("feishu_bot_app_secret", ""),
    }
