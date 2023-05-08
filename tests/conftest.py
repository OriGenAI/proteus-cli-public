import pytest
from requests.models import Response


class FakeResponse(Response):

    _override_content = ''
    mock = None

    def __init__(self, *args, mocker=None, **kwargs):
        self.mock = mocker
        super().__init__(*args, **kwargs)

    @property
    def _content(self):
        if callable(self._override_content):
            return self._override_content(self, self.mock)

        return self._override_content

    @_content.setter
    def _content(self, val):
        self._override_content = val


@pytest.fixture(autouse=True)
def _mock_azcopy_command(mocker):
    """
    Ensure azcopy is never really called
    """
    class FakeAZCopyDownload:
        def wait(self):
            pass

    mock = mocker.patch("proteus.bucket.Bucket._download_via_azcopy_process", return_value=FakeAZCopyDownload())
    return mock


@pytest.fixture
def mocked_api_get(mocker):
    mock = mocker.patch("proteus.api.API.get")
    mock.return_value = FakeResponse(mocker=mock)
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
