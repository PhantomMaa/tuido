from pathlib import Path
from tuido.models import GlobalConfig


def load_global_config() -> GlobalConfig:
    """Load global view configuration from ~/.config/tuido/config.yaml.

    Returns:
        GlobalConfig instance containing global view configuration.
    """
    config_path = Path.home() / ".config" / "tuido" / "config.yaml"
    return GlobalConfig.from_yaml(config_path)


def save_global_theme(theme: str) -> None:
    """Save theme setting to global config file.

    Args:
        theme: Theme name to save.
    """
    config_path = Path.home() / ".config" / "tuido" / "config.yaml"

    # Load existing config or create new
    if config_path.exists():
        config = GlobalConfig.from_yaml(config_path)
    else:
        config = GlobalConfig()

    # Update theme
    config.theme = theme

    # Save back to file
    config.save(config_path)
