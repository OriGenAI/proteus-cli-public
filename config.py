import os


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    DEVELOPMENT = False

    OUTPUT_LOC = "output"
    TEMPLATE_NAME = "case_template"
    INPUT_LOC = "input"

    LOG_LOC = "logs"
    LOG_LEVEL = "info"

    OVERWRITE = True

    CONSOLE = False

    SLEEP_TIME = 30

    AUTH_HOST = os.getenv("AUTH_HOST", "https://auth.dev.origen.ai")
    API_HOST = os.getenv("API_HOST", "https://api.dev.origen.ai")
    REALM = os.getenv("REALM", "origen")
    USERNAME = os.getenv("WORKER_USERNAME", "user-not-configured")
    PASSWORD = os.getenv("WORKER_PASSWORD", "password-not-configured")
    CLIENT_ID = os.getenv("CLIENT_ID", "proteus-front")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", None)
    STATUS_URL = os.getenv("STATUS_URL", None)
    ENTITY_URL = os.getenv("ENTITY_URL", None)
    RETRY_INTERVAL = 25  # Seconds
    REFRESH_GAP = 10  # Seconds
    PROMPT = False
    VAULT_HOST = "https://vault.dev.origen.ai"


class ProductionConfig(Config):
    DEBUG = False
    USERNAME = os.getenv("USERNAME", "user-not-configured")
    PASSWORD = os.getenv("PASSWORD", "user-not-configured")
    REALM = os.getenv("REALM", "zeroone")


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    LOG_LEVEL = "debug"
    OVERWRITE = True
    PROMPT = True


configs = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "staging": StagingConfig,
    "default": ProductionConfig,
}

config_name = os.getenv("DEPLOYMENT") or "default"

config = configs[config_name]
