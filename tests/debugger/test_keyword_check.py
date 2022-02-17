from click.testing import CliRunner
from cli.debugger.commands import x_stress_test, init_stress_test


def test_stress_x_files(user):
    # Given
    runner = CliRunner()
    bucket = "dba55075-1ccb-483a-afd7-cc7a42c1fcdd"
    workers = "4"
    iterations = "4"
    input = "\n".join(
        [workers, iterations, user["username"], user["password"]]
    )
    # When
    result = runner.invoke(x_stress_test, [bucket], input=input)
    # Then
    assert result.exit_code == 0


def test_stress_init_files(user):
    # Given
    runner = CliRunner()
    bucket = "dba55075-1ccb-483a-afd7-cc7a42c1fcdd"
    workers = "4"
    iterations = "4"
    input = "\n".join(
        [workers, iterations, user["username"], user["password"]]
    )
    # When
    result = runner.invoke(init_stress_test, [bucket], input=input)
    # Then
    assert result.exit_code == 0
