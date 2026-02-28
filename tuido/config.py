from pathlib import Path

import yaml

from tuido.models import FeishuConfig


def load_global_config() -> FeishuConfig:
    """Load global view configuration from ~/.config/tuido/config.yaml.

    Returns:
        FeishuConfig instance containing global view configuration.
    """
    return FeishuConfig.from_default_path()


def save_global_theme(theme: str) -> None:
    """Save theme setting to global config file.

    Args:
        theme: Theme name to save.
    """
    config_path = Path.home() / ".config" / "tuido" / "config.yaml"

    # Load existing config or create new
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except (yaml.YAMLError, IOError):
            config = {}
    else:
        config = {}
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

    # Update theme at root level
    config["theme"] = theme

    # Save back to file
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
