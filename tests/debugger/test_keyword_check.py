from click.testing import CliRunner
from cli.debugger.commands import init_stress_test
from cli.config import config

USERNAME, PASSWORD = config.USERNAME, config.PASSWORD

def test_init_stress_test_X_files():
    # Given
    runner = CliRunner()
    bucket = "dba55075-1ccb-483a-afd7-cc7a42c1fcdd"
    workers = "4"
    iterations = "4"
    input = "\n".join([workers, iterations, USERNAME, PASSWORD])
    file_ext = ".X"
    # When
    result = runner.invoke(init_stress_test, [bucket, file_ext], input=input)
    # Then
    assert result.exit_code == 0

def test_init_stress_test_INIT_files():
    # Given
    runner = CliRunner()
    bucket = "dba55075-1ccb-483a-afd7-cc7a42c1fcdd"
    workers = "4"
    iterations = "4"
    input = "\n".join([workers, iterations, USERNAME, PASSWORD])
    file_ext = ".INIT"
    # When
    result = runner.invoke(init_stress_test, [bucket, file_ext], input=input)
    # Then
    assert result.exit_code == 0

if __name__ == "__main__":
    test_init_stress_test_X_files()