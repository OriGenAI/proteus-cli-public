import pytest
from pytest_bdd import scenario, given, when, then, parsers

from cli.datasets.upload import process_files
from api.hooks import TqdmUpWithReport


@given("a set of cases", target_fixture="cases")
def cases():
    return [
        {
            "group": "training",
            "number": 1,
            "case_url": "test-case-get",
            "root": 1,
            "initialStep": 1,
            "finalStep": 10,
        }
    ]


@given("a source url", target_fixture="source_url")
def source_url():
    return ""


@given("a bucket url", target_fixture="bucket_url")
def bucket_url():
    return ""


@given("a cases url", target_fixture="cases_url")
def cases_url():
    return ""


@given("a number of workers", target_fixture="workers")
def workers():
    return 2


@given("a tqdm instance", target_fixture="progress")
def progress():
    return TqdmUpWithReport()


@given("a process mock", target_fixture="process_mock")
def process_mock(mocker):
    return mocker.patch("cli.datasets.preprocessor.process_step.process_step")


@given("a tqdm mock", target_fixture="tqdm_mock")
def tqdm_mock(mocker):
    return mocker.patch("api.hooks.TqdmUpWithReport.update_with_report")


@given("a description mock", target_fixture="description_mock")
def description_mock(mocker):
    return mocker.patch("tqdm.std.tqdm.set_description")


@given("a refresh mock", target_fixture="refresh_mock")
def refresh_mock(mocker):
    return mocker.patch("tqdm.std.tqdm.refresh")


@given("setted up mocks")
def set_up_mocks(process_mock, tqdm_mock, description_mock, refresh_mock):
    process_mock.return_value = True
    tqdm_mock.return_value = True
    description_mock.return_value = True
    refresh_mock.return_value = True


@scenario("features/process_files.feature", "Process file uploads")
def test_process_files():
    pass


@when(parsers.parse("I process files with workflow {workflow}"))
def process_file_uploads(
    source_url, bucket_url, cases_url, progress, cases, workers, workflow
):
    process_files(
        source_url, bucket_url, cases_url, progress, cases, workers, workflow
    )


@then(
    parsers.parse(
        "Is it {called_process_mock} that I called the process_step method"
    )
)
def process_called(process_mock, called_process_mock):
    assert process_mock.called == (called_process_mock == "True")


@then(
    parsers.parse(
        "Is it {called_tqdm_mock} that I called the update_with_report method"
    )
)
def tqdm_called(tqdm_mock, called_tqdm_mock):
    assert tqdm_mock.called == (called_tqdm_mock == "True")


@then(
    parsers.parse(
        "Is it {called_description_mock} that"
        + " I called the set_description method"
    )
)
def description_called(description_mock, called_description_mock):
    assert description_mock.called == (called_description_mock == "True")


@then(
    parsers.parse(
        "Is it {called_refresh_mock} that I called the refresh method"
    )
)
def refresh_called(refresh_mock, called_refresh_mock):
    assert refresh_mock.called == (called_refresh_mock == "True")


@scenario(
    "features/process_files.feature",
    "Process file uploads with an unknown workflow",
)
def test_process_files_failing_on_not_found_workflow():
    pass


@then(parsers.parse("It throws a KeyError when workflow is {workflow}"))
def process_files_with_not_found_workflow(
    source_url, bucket_url, cases_url, progress, cases, workers, workflow
):
    with pytest.raises(KeyError):
        process_files(
            source_url,
            bucket_url,
            cases_url,
            progress,
            cases,
            workers,
            workflow,
        )
