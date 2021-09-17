import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    DEVELOPMENT = False

    OUTPUT_LOC = "output"
    TEMPLATE_NAME = "case_template"
    INPUT_LOC = "input"

    SLEEP_TIME = 30
    PROMPT = True
    AUTH_HOST = os.getenv("AUTH_HOST", "https://auth.dev.origen.ai")
    PROTEUS_HOST = os.getenv(
        "PROTEUS_HOST", "https://proteus-test.dev.origen.ai"
    )
    REALM = os.getenv("REALM", "origen")
    USERNAME = os.getenv("PROTEUS_USERNAME", "user-not-configured")
    PASSWORD = os.getenv("PROTEUS_PASSWORD", "password-not-configured")
    CLIENT_ID = os.getenv("CLIENT_ID", "proteus-front")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", None)
    RETRY_INTERVAL = 25  # Seconds
    REFRESH_GAP = 100  # Seconds
    S3_REGION = "eu-west-3"
    WORKERS_COUNT = 5
    AZURE_STORAGE_CONNECTION_STRING = os.getenv(
        "AZURE_STORAGE_CONNECTION_STRING"
    )


class ProductionConfig(Config):
    pass


class StagingConfig(Config):
    pass


class DevelopmentConfig(Config):
    pass


configs = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "staging": StagingConfig,
    "default": ProductionConfig,
}

config_name = os.getenv("DEPLOYMENT") or "default"

config = configs[config_name]
