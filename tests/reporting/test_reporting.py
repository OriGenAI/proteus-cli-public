from pytest_bdd import scenario, given, when, then, parsers

from cli.common.reporting import Reporting

from api import api


@given("a reporting instance", target_fixture="reporting")
def reporting():
    return Reporting.new(api)


@scenario("features/reporting.feature", "Log info message")
def test_log_info():
    pass


@when(parsers.parse("I log the messsage: {msg}"), target_fixture="logged_msg")
def log_info(reporting, caplog, msg):
    reporting.info(msg)
    return caplog.messages[0]


@then(parsers.parse("I get a stdout message with: {msg}"))
def done_logging_info(logged_msg, msg):
    assert logged_msg == msg


@scenario("features/reporting.feature", "Log error message")
def test_log_error():
    pass


@when(
    parsers.parse("I log the error messsage: {msg}"),
    target_fixture="logged_error",
)
def log_error(reporting, caplog, msg):
    reporting.error(msg)
    return caplog.messages[0]


@then(parsers.parse("I get a stderr message with: {msg}"))
def done_logging_error(logged_error, msg):
    assert logged_error == msg


@scenario("features/reporting.feature", "Log info message with abstract")
def test_log_info_abstract():
    pass


@when(
    parsers.parse("(abstract) I log the messsage: {msg}"),
    target_fixture="logged_msg",
)
def log_info_abs(caplog, msg):
    Reporting.info(msg)
    return caplog.messages[0]


@scenario("features/reporting.feature", "Log error message with abstract")
def test_log_error_abstract():
    pass


@when(
    parsers.parse("(abstract) I log the error messsage: {msg}"),
    target_fixture="logged_error",
)
def log_error_abs(caplog, msg):
    Reporting.error(msg)
    return caplog.messages[0]
