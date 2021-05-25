import logging
import logging.config
import logging.handlers
import os
from config import config as configuration
import shutil

os.makedirs(configuration.LOG_LOC, exist_ok=True)


def _setup_logging():
    log_dir = configuration.LOG_LOC
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)
    os.makedirs(log_dir, exist_ok=True)


_setup_logging()


logging.config.fileConfig("logging.ini", disable_existing_loggers=False)


logger = logging.getLogger(__name__)
