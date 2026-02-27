from tuido.models import FeishuConfig


def load_global_config() -> FeishuConfig:
    """Load global view configuration from ~/.config/tuido/config.yaml.

    Returns:
        FeishuConfig instance containing global view configuration.
    """
    return FeishuConfig.from_default_path()
