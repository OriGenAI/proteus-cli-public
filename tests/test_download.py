import os
import re
import shutil
from glob import glob

from pytest_bdd import scenario, given, when, then

from cli.runtime import proteus


@scenario("features/download.feature", "Download bucket")
def test_download(mocked_auth):
    pass


@given("an api mock", target_fixture="updated_mocked_api_get")
def updated_mocked_api_get(mocked_api_get):

    FILE_URL = "/api/v1/buckets/files/22-22"

    def response_setter(response, mocker):
        bucket_info = b'{"url": "my_url", "filepath": "test-file", "presigned_url": {"url": "http://example.com"}, "size": 0, "ready": true}'

        url = mocker.call_args[0][0]

        if re.match(r"^/api/v1/buckets/[^/]+$", url):
            uuid = re.findall(r"^/api/v1/buckets/([^/]+)", url)[0]
            return b'{"bucket":' + bucket_info + b"}"
        elif re.match(r"^/api/v1/buckets/$", url):
            uuid = re.findall(r"^/api/v1/buckets/([^/]+)", url)[0]
            return b'{"total": 1, ' b'"results":[' + bucket_info + b"]}"
        elif re.match(r"^/api/v1/buckets/[^/]+/files$", url):
            uuid = re.findall(r"^/api/v1/buckets/([^/]+)", url)[0]
            return """{{
                "results": [
                    {{
                        "ready": true,
                        "filepath": "test-file",
                        "uuid":  "aaaa-bbbb-cccc",
                        "url": "{}",
                        "size": 22
                    }}
                ],
                "total": 1,
                "next": null
            }}""".format(
                FILE_URL
            ).encode()
        elif url == FILE_URL:
            return b"my-file-content"
        else:
            raise AssertionError("Unknown URL")

        return

    mocked_api_get.return_value._content = response_setter
    return mocked_api_get


@given("a bucket uuid", target_fixture="bucket_uuid")
def bucket_uuid():
    return "1222222-2222-2222-222"


@given("a target folder", target_fixture="target_folder")
def target_folder():

    for file in glob("tests/files/test_download/*", recursive=True):
        if file.startswith("tests/files/test_download/tmp"):
            continue

        if os.path.isdir(file):
            shutil.rmtree(file)
        else:
            os.remove(file)

    assert os.listdir("tests/files/test_download/") == ["tmp"]
    return "tests/files/test_download"


@when("I download")
def download_bucket(bucket_uuid, target_folder, updated_mocked_api_get):
    list(proteus.bucket.download(bucket_uuid, target_folder, workers=1, via="api_files"))


@then("there are logged messages")
def logged_messages(caplog):
    assert caplog.messages


@then("the file is downloaded")
def is_file_downloaded(target_folder):
    os.path.exists(f"{target_folder}/test-file")
    os.remove(f"{target_folder}/test-file")
