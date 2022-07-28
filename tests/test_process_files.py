import os
import pytest
import shutil
from pathlib import Path
from pytest_bdd import scenario, given, when, then, parsers

from cli.datasets.upload import process_files
from api.hooks import TqdmUpWithReport


@given("a set of cases", target_fixture="cases")
def cases():
    return [
        {
            "group": "training",
            "number": 1,
            "case_url": (
                "/api/v1/datasets/"
                "3f1b7126-95e4-4db0-b303-0ca476c28cb1/cases/validation/2"
            ),
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
            "case_url": (
                "/api/v1/datasets/"
                "3f1b7126-95e4-4db0-b303-0ca476c28cb1/cases/SIMULATION_1"
            ),
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


@given("a keywords mock", target_fixture="keywords_mock")
def keywords_mock(mocker):
    mock = mocker.patch(
        "cli.datasets.preprocessor.config."
        "defaultConfig.DefaultConfig._get_mapping"
    )
    mock.return_value = [
        {"name": "ACTNUM", "source": "BOOLEAN"},
        {"name": "LITHO", "source": "LITHO"},
        {"name": "PORO", "source": "PORO"},
        {"name": "PERMX", "source": "PERM"},
        {"name": "V-CLAI", "source": "VCL"},
    ]
    return mock


@given("setted up mocks")
def set_up_mocks(
    process_mock, keywords_mock, tqdm_mock, description_mock, refresh_mock
):
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


@given("a bucket mock", target_fixture="bucket_mock")
def bucket_mock(mocker):
    return mocker.patch(
        "cli.datasets.preprocessor.process_step.files_exist_in_bucket"
    )


@given("a download mock", target_fixture="download_mock")
def download_mock(mocker):
    return mocker.patch("cli.datasets.preprocessor.process_step.download_file")


@given("a temporary dir mock", target_fixture="tmp_mock")
def tmp_mock(mocker):
    return mocker.patch("tempfile.TemporaryDirectory.__enter__")


@given("a dataset get mock", target_fixture="dataset_get_mock")
def dataset_get_mock(mocker):
    from requests.models import Response

    json = (
        b'{"dataset": {"sampling": {"config": { "cnn_pca_design": { '
        b'"keywords": [{"name": "ACTNUM", "source": "BOOLEAN"}, '
        b'{"name": "LITHO","source": "LITHO"}, '
        b'{"name": "PORO", "source": "PORO"}, '
        b'{"name": "PERMX", "source": "PERM"}, '
        b'{"name": "V-CLAI", "source": "VCL"}]}}}}}'
    )
    mock = mocker.patch("proteus.api.get")
    mock.return_value = Response()
    mock.return_value.status_code = 200
    mock.return_value._content = json
    return mock


@given("setted up mocks for cnn-pca")
def set_up_mocks_cnn(
    bucket_mock,
    tmp_mock,
    download_mock,
    tqdm_mock,
    description_mock,
    refresh_mock,
    keywords_mock,
    dataset_get_mock,
):
    from distutils.dir_util import copy_tree

    copy_tree(
        f"{os.path.dirname(__file__)}/files/cnn-pca-preprocessing",
        f"{os.path.dirname(__file__)}/files/cnn-pca-preprocessing-cp",
    )
    bucket_mock.return_value = False
    tmp_mock.return_value = (
        f"{os.path.dirname(__file__)}/files/cnn-pca-preprocessing-cp"
    )
    download_mock.return_value = True
    tqdm_mock.return_value = True
    description_mock.return_value = True
    refresh_mock.return_value = True


@scenario(
    "features/process_files.feature",
    "Process cnn-pca files",
)
def test_process_cnnpca_files():
    pass


@when("I process cnn-pca files")
def process_cnnpca_files(
    source_url, bucket_url, cases_url, progress, cases_without_split, workers
):
    process_files(
        source_url,
        bucket_url,
        cases_url,
        progress,
        cases_without_split,
        workers,
        "cnn-pca",
    )


@then("the bucket mock is called")
def bucket_mock_called(bucket_mock):
    bucket_mock.assert_called()


@then("the preprocessed files are created")
def files_created():
    filenames = [
        "litho.h5",
        "permx.h5",
        "actnum.h5",
        "poro.h5",
        "v-clai.h5",
        "runspec.p",
        "well_spec.p",
    ]

    path = f"{os.path.dirname(__file__)}/files/cnn-pca-preprocessing-cp"

    are_all_present = True
    for filename in filenames:
        try:
            next(Path(path).rglob(f"{filename}"))
        except StopIteration:
            are_all_present = False
    shutil.rmtree(
        f"{os.path.dirname(__file__)}/files/cnn-pca-preprocessing-cp"
    )
    assert are_all_present
