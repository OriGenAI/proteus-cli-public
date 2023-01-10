import pytest
from requests.models import Response


@pytest.fixture
def mocked_api_get(mocker):
    mock = mocker.patch("proteus.api.API.get")
    mock.return_value = Response()
    mock.return_value.status_code = 200
    mock.return_value._content = b"Test content"
    return mock


@pytest.fixture
def mocked_api_post(mocker):
    mock = mocker.patch("proteus.api.API.post")
    mock.return_value = Response()
    mock.return_value.status_code = 200
    return mock


@pytest.fixture
def mocked_response(mocker):
    mock = mocker.patch("requests.models.Response.raise_for_status")
    mock.return_value = None
    return mock


@pytest.fixture
def mocked_auth(mocker):
    auth_mock = mocker.patch("proteus.oidc.OIDC.access_token")
    auth_mock.return_value = True
