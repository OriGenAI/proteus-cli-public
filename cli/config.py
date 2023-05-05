import os

from proteus import Config as ProteusConfig

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    DEVELOPMENT = False

    OUTPUT_LOC = "output"
    TEMPLATE_NAME = "case_template"
    INPUT_LOC = "input"
    LOG_LOC = "logs"

    SLEEP_TIME = 30
    PROMPT = True
    AUTH_HOST = os.getenv("AUTH_HOST", "https://auth.dev.origen.ai")
    PROTEUS_HOST = os.getenv("PROTEUS_HOST", "https://proteus-test.dev.origen.ai")
    API_SSL_VERIFY = os.getenv("API_SSL_VERIFY", "1").lower() not in ("0", "false", "f")
    USERNAME = os.getenv("PROTEUS_USERNAME", None)
    PASSWORD = os.getenv("PROTEUS_PASSWORD", None)
    REALM = os.getenv("REALM", "origen")
    CLIENT_ID = os.getenv("CLIENT_ID", "proteus-front")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", None)

    WORKERS_REALM = os.getenv("WORKERS_REALM", "robots")
    WORKERS_CLIENT_ID = os.getenv("WORKERS_CLIENT_ID", "workers")
    WORKERS_CLIENT_SECRET = os.getenv("WORKERS_CLIENT_SECRET", None)

    RETRY_INTERVAL = 25  # Seconds
    REFRESH_GAP = 100  # Seconds
    S3_REGION = "eu-west-3"
    WORKERS_COUNT = 5
    WORKERS_DOWNLOAD_COUNT = 10
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
    AZURE_SAS_TOKEN = os.getenv("AZURE_SAS_TOKEN")

    STRESS_ITERATIONS = 10

    DATASET_VERSION = {
        "major": os.getenv("DATASET_MAJOR_VERSION", 1),
        "minor": os.getenv("DATASET_MINOR_VERSION", 0),
        "patch": os.getenv("DATASET_PATCH_VERSION", 0),
    }
    OPM_FLOW_PATH = os.getenv("OPM_FLOW_PATH", "/usr/bin/flow")

    if not API_SSL_VERIFY:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    RUNTIME_CONFIG = ProteusConfig(
        log_loc=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        client_secret=CLIENT_SECRET,
        auth_host=AUTH_HOST,
        api_host=PROTEUS_HOST,
        username=USERNAME,
        password=PASSWORD,
        realm=REALM,
        client_id=CLIENT_ID,
        refresh_gap=REFRESH_GAP,
        ssl_verify=API_SSL_VERIFY,
        default_retry_times=10,
        default_retry_wait=20,
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
