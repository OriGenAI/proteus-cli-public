from click.testing import CliRunner
from cli.debugger.commands import init_stress_test


def test_init_stress_test_X_files(user):
    # Given
    runner = CliRunner()
    bucket = "dba55075-1ccb-483a-afd7-cc7a42c1fcdd"
    workers = "4"
    iterations = "4"
    input = "\n".join([workers, iterations, user['username'], user['password']])
    file_ext = ".X"
    # When
    result = runner.invoke(init_stress_test, [bucket, file_ext], input=input)
    # Then
    assert result.exit_code == 0

def test_init_stress_test_INIT_files(user):
    # Given
    runner = CliRunner()
    bucket = "dba55075-1ccb-483a-afd7-cc7a42c1fcdd"
    workers = "4"
    iterations = "4"
    input = "\n".join([workers, iterations, user['username'], user['password']])
    file_ext = ".INIT"
    # When
    result = runner.invoke(init_stress_test, [bucket, file_ext], input=input)
    # Then
    assert result.exit_code == 0
