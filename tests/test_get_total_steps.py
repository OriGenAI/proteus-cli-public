import pytest
from pytest_bdd import scenario, given, when, then, parsers
from requests.models import Response

from cli.datasets.upload import get_total_steps


@given("a list of cases", target_fixture="cases")
def cases():
    return [{"group": "training", "number": 1, "case_url": "test-case-get"}]


@given("setting a mock for case details")
def set_get_case_mock(mocker):
    mock = mocker.patch("proteus.api.get")
    mock.return_value = Response()
    mock.return_value.status_code = 200
    mock.return_value._content = (
        b'{"case": {"root": "", "group": 1, '
        b'"number": 2, "initialStep": 1, "finalStep": 10}}'
    )


@scenario("features/get_total_steps.feature", "Get total steps of a case")
def test_get_total_steps():
    pass


@when(
    parsers.parse("I get the total steps of cases with workflow {workflow}"),
    target_fixture="num_of_steps",
)
def get_workflow_total_steps(cases, workflow):
    return get_total_steps(cases, workflow)


@then(parsers.parse("I should get {expected_steps:d} steps"))
def num_of_steps_match(num_of_steps, expected_steps):
    assert num_of_steps == expected_steps


@scenario(
    "features/get_total_steps.feature",
    "Get total steps of a case with an unknown workflow",
)
def test_get_total_steps_failing_on_not_found_workflow():
    pass


@then(parsers.parse("It throws a KeyError when workflow is {workflow}"))
def get_workflow_total_steps_with_not_found_workflow(cases, workflow):
    with pytest.raises(KeyError):
        get_total_steps(cases, workflow)
