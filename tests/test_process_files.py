import pytest
from pytest_bdd import scenario, given, when, then, parsers

from cli.api.hooks import TqdmUpWithReport
from cli.datasets.upload import process_files


@pytest.fixture
def process_mock(mocker):
    return mocker.patch("cli.datasets.preprocessor.process_step.process_step", return_value=["dims.h5"])


@pytest.fixture
def tqdm_mock(mocker):
    return mocker.patch("cli.api.hooks.TqdmUpWithReport.update_with_report", return_value=True)


@pytest.fixture
def description_mock(mocker):
    return mocker.patch("tqdm.std.tqdm.set_description", return_value=True)


@pytest.fixture
def refresh_mock(mocker):
    return mocker.patch("tqdm.std.tqdm.refresh", return_value=True)


@pytest.fixture
def keywords_mock(mocker):
    mock = mocker.patch("cli.datasets.preprocessor.config.defaultConfig.DefaultConfig._get_mapping")
    mock.return_value = [
        {"name": "ACTNUM", "source": "BOOLEAN"},
        {"name": "LITHO", "source": "LITHO"},
        {"name": "LITHO_INPUT", "source": "LITHO_INPUT"},
        {"name": "PORO", "source": "PORO"},
        {"name": "PERMX", "source": "PERM"},
        {"name": "V-CLAI", "source": "VCL"},
    ]
    return mock


@given("a set of cases", target_fixture="cases")
def cases():
    return [
        {
            "group": "training",
            "number": 1,
            "case_url": ("/api/v1/datasets/3f1b7126-95e4-4db0-b303-0ca476c28cb1/cases/validation/2"),
            "root": 1,
            "initialStep": 1,
            "finalStep": 10,
        }
    ]


@given("a set of cases without split", target_fixture="cases_without_split")
def cases_without_split():
    return [
        {
            "number": 1,
            "case_url": ("/api/v1/datasets/3f1b7126-95e4-4db0-b303-0ca476c28cb1/cases/SIMULATION_1"),
            "root": "cases/SIMULATION_1",
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


@scenario("features/process_files.feature", "Process file uploads")
def test_process_files(process_mock, tqdm_mock, description_mock, refresh_mock, keywords_mock):
    "Process file uploads"


@when(parsers.parse("I process files with workflow {workflow}"))
def process_file_uploads(source_url, bucket_url, cases_url, progress, cases, workers, workflow):
    process_files(source_url, bucket_url, cases_url, progress, cases, workers, workflow)


@then(parsers.parse("Is it {called_process_mock} that I called the process_step method"))
def process_called(process_mock, called_process_mock):
    assert process_mock.called == (called_process_mock == "True")


@then(parsers.parse("Is it {called_tqdm_mock} that I called the update_with_report method"))
def tqdm_called(tqdm_mock, called_tqdm_mock):
    assert tqdm_mock.called == (called_tqdm_mock == "True")


@then(parsers.parse("Is it {called_description_mock} that I called the set_description method"))
def description_called(description_mock, called_description_mock):
    assert description_mock.called == (called_description_mock == "True")


@then(parsers.parse("Is it {called_refresh_mock} that I called the refresh method"))
def refresh_called(refresh_mock, called_refresh_mock):
    assert refresh_mock.called == (called_refresh_mock == "True")


@scenario(
    "features/process_files.feature",
    "Process file uploads with an unknown workflow",
)
def test_process_files_failing_on_not_found_workflow(
    process_mock, tqdm_mock, description_mock, refresh_mock, keywords_mock
):
    "Process file uploads with an unknown workflow"


@then(parsers.parse("It throws a KeyError when workflow is {workflow}"))
def process_files_with_not_found_workflow(source_url, bucket_url, cases_url, progress, cases, workers, workflow):
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
