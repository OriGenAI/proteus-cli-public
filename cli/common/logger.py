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
loggin_path = os.path.abspath(os.path.join(__file__, '../../../logging.ini'))
logging.config.fileConfig(loggin_path, disable_existing_loggers=False)

azure_logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
azure_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
