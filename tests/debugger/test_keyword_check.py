from click.testing import CliRunner
from cli.debugger.commands import init_stress_test
from cli.config import config

USERNAME, PASSWORD = config.USERNAME, config.PASSWORD

def test_init_stress_test():
    # Given
    runner = CliRunner()
    bucket = "6ed65156-64c1-4e06-bbbd-1827b2c54336"
    folder= "tests/files"
    workers = "5"
    iterations = "10"
    input = "\n".join([workers, iterations, USERNAME, PASSWORD])
    # When
    result = runner.invoke(init_stress_test, [bucket, folder], input=input)
    # Then
    assert result.exit_code == 0
    assert result.output == "Done"


if __name__ == "__main__":
    test_init_stress_test()