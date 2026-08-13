from .loader import load_config


def get_config():
    return load_config()


def describe():
    cfg = get_config()
    return f"{cfg.get('host')}:{cfg.get('port')} debug={cfg.get('debug')}"
