import os
import pytest
from dotenv import load_dotenv
from cli.config import config
from api import login as api_login


@pytest.fixture
def session():
    load_dotenv(".testenv")
    user = os.getenv("PROTEUS_USERNAME", "user-not-configured")
    password = os.getenv("PROTEUS_PASSWORD", "password-not-configured")
    host = os.getenv("PROTEUS_HOST", "https://proteus-test.dev.origen.ai")
    config.PROTEUS_HOST = host
    return api_login(username=user, password=password, auto_update=False)

@pytest.fixture
def user(session):
    user = os.getenv("PROTEUS_USERNAME", "user-not-configured")
    password = os.getenv("PROTEUS_PASSWORD", "password-not-configured")

    return {"username": user, "password": password}
