import json


def load_config(path):
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    return config
