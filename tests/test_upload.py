from pytest_bdd import scenario, given, when, then
from requests.models import Response
from cli.datasets.upload import upload


@scenario("features/upload.feature", "Upload dataset to bucket")
def test_upload(mocked_auth, mocked_api_post, mocked_api_get):
    pass


@given("a bucket", target_fixture="bucket")
def bucket():
    return None


@given("a dataset uuid", target_fixture="dataset_uuid")
def dataset_uuid():
    return ""


@given("a set of mocks", target_fixture="report_mock")
def report_mock(mocker):
    report_mock = mocker.patch("api.hooks.TqdmUpWithReport.update_with_report")
    report_mock.return_value = True

    cases_mock = mocker.patch("cli.datasets.upload.get_cases")
    cases_mock.return_value = [
        {"root": "", "group": 1, "number": 2, "initialStep": 1, "finalStep": 2}
    ]
    total_steps_mock = mocker.patch("cli.datasets.upload.get_total_steps")
    total_steps_mock.return_value = 1

    dataset_mock = mocker.patch("proteus.api.get")
    dataset_mock.return_value = Response()
    dataset_mock.return_value.status_code = 200
    dataset_mock.return_value._content = (
        b'{"dataset": {"bucket_url": "",'
        b'"cases_url": "","workflow": {"name": "hm"}}}'
    )
    preprocess_mock = mocker.patch(
        "cli.datasets.preprocessor.process_step.process_step"
    )
    preprocess_mock.return_value = True

    return report_mock


@when("I upload a dataset")
def upload_bucket(bucket, dataset_uuid):
    upload(bucket, dataset_uuid, workers=1)


@then("there are logged messages")
def logged_messages(caplog):
    assert "started upload" in caplog.messages
    assert "This process will use 1 simultaneous threads." in caplog.messages


@then("the files are uploaded")
def are_files_uploaded(report_mock):
    assert report_mock.call_count == 9
