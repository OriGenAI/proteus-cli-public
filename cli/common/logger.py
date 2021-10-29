# Logging
import logging
import logging.config
import logging.handlers
import os
from cli.config import config


def _setup_logging(config):
    log_dir = config.LOG_LOC
    os.makedirs(log_dir, exist_ok=True)


_setup_logging(config=config)
logging.config.fileConfig("logging.ini", disable_existing_loggers=False)

logger = logging.getLogger(__name__)
