import pytest

from cli.datasets.upload import get_total_steps, process_files
from api.hooks import TqdmUpWithReport


def test_get_total_steps_hm(requests_mock):
    # Given
    cases = [{"group": "training", "number": 1, "case_url": "test-case-get"}]
    requests_mock.get(
        "https://proteus-test.dev.origen.ai/test-case-get",
        json={
            "case": {
                "initialStep": 1,
                "finalStep": 10,
            }
        },
    )
    # When
    res = get_total_steps(cases, "hm")
    # Then
    assert res == 17


def test_get_total_steps_cnnpca(requests_mock):
    # Given
    cases = [{"group": "training", "number": 1, "case_url": "test-case-get"}]
    requests_mock.get(
        "https://proteus-test.dev.origen.ai/test-case-get",
        json={
            "case": {
                "initialStep": 1,
                "finalStep": 10,
            }
        },
    )
    # When
    res = get_total_steps(cases, "cnn-pca")
    # Then
    assert res == 17


def test_get_total_steps_failing_on_not_found_workflow(requests_mock):
    # Given
    cases = [{"group": "training", "number": 1, "case_url": "test-case-get"}]
    requests_mock.get(
        "https://proteus-test.dev.origen.ai/test-case-get",
        json={
            "case": {
                "initialStep": 1,
                "finalStep": 10,
            }
        },
    )
    # When
    with pytest.raises(KeyError):
        res = get_total_steps(cases, "fail")


def test_process_files_hm(mocker):
    # Given
    source_url = ""
    bucket_url = ""
    cases_url = ""
    progress = TqdmUpWithReport()
    cases = [
        {
            "group": "training",
            "number": 1,
            "case_url": "test-case-get",
            "root": 1,
            "initialStep": 1,
            "finalStep": 10,
        }
    ]
    workers = 3
    workflow = "hm"

    process_mock = mocker.patch("cli.datasets.preprocessor.process_step.process_step")
    tqdm_mock = mocker.patch("api.hooks.TqdmUpWithReport.update_with_report")
    description_mock = mocker.patch("tqdm.std.tqdm.set_description")
    refresh_mock = mocker.patch("tqdm.std.tqdm.refresh")
    process_mock.return_value = True
    tqdm_mock.return_value = True
    description_mock.return_value = True
    refresh_mock.return_value = True
    # When
    process_files(source_url, bucket_url, cases_url, progress, cases, workers, workflow)
    # Then
    assert process_mock.called
    assert tqdm_mock.called
    assert description_mock.called
    assert refresh_mock.called


def test_process_files_cnnpca(mocker):
    # Given
    source_url = ""
    bucket_url = ""
    cases_url = ""
    progress = TqdmUpWithReport()
    cases = [
        {
            "group": "training",
            "number": 1,
            "case_url": "test-case-get",
            "root": 1,
            "initialStep": 1,
            "finalStep": 10,
        }
    ]
    workers = 3
    workflow = "cnn-pca"

    process_mock = mocker.patch("cli.datasets.preprocessor.process_step.process_step")
    tqdm_mock = mocker.patch("api.hooks.TqdmUpWithReport.update_with_report")
    description_mock = mocker.patch("tqdm.std.tqdm.set_description")
    refresh_mock = mocker.patch("tqdm.std.tqdm.refresh")
    process_mock.return_value = True
    tqdm_mock.return_value = True
    description_mock.return_value = True
    refresh_mock.return_value = True
    # When
    process_files(source_url, bucket_url, cases_url, progress, cases, workers, workflow)
    # Then
    assert process_mock.called
    assert tqdm_mock.called
    assert description_mock.called
    assert refresh_mock.called


def test_process_files_failing_on_not_found_workflow():
    # Given
    source_url = ""
    bucket_url = ""
    cases_url = ""
    progress = TqdmUpWithReport()
    cases = [
        {
            "group": "training",
            "number": 1,
            "case_url": "test-case-get",
            "root": 1,
            "initialStep": 1,
            "finalStep": 10,
        }
    ]
    workers = 3
    workflow = "fail"

    # When
    with pytest.raises(KeyError):
        process_files(
            source_url, bucket_url, cases_url, progress, cases, workers, workflow
        )
