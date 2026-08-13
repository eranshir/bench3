from .loader import load_config


def describe():
    cfg = load_config()
    return f"{cfg.get('host')}:{cfg.get('port')} debug={cfg.get('debug')}"
