import json
import logging
import os

DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default_formatter": {"format": "%(name)s : %(asctime)s : %(levelname)s : %(message)s"},
    },
    "handlers": {
        "stream_handler": {
            "class": "logging.StreamHandler",
            "formatter": "default_formatter",
        },
    },
    "root": {
        "handlers": [
            "stream_handler",
        ],
        "level": logging.DEBUG,
    },
}

DEFAULT_DATABASE = "bluebike.sqlite"


def load_config(config_path):
    if config_path is None or not os.path.exists(config_path):
        return DEFAULT_DATABASE, DEFAULT_LOGGING_CONFIG

    with open(config_path, "r") as conf:
        conf_dict = json.load(conf)
        return conf_dict.get("database", DEFAULT_DATABASE), conf_dict.get("logging", DEFAULT_LOGGING_CONFIG)
