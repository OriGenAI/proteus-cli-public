import click

from cli.api.decorators import may_fail_on_http_error  # noqa: E402
from cli.runtime import proteus
from .buckets.commands import buckets as buckets_commands
from .config import config
from .datasets.commands import datasets as datasets_commands
from .debugger.commands import debugger as debugger_commands
from .jobs.commands import jobs as jobs_commands
from .simulations.commands import simulations as simulations_commands

USERNAME, PASSWORD, PROMPT = config.USERNAME, config.PASSWORD, config.PROMPT
WORKERS_COUNT = config.WORKERS_COUNT


@click.group()
def main():
    """
    Simple CLI for PROTEUS auxiliary utils
    """
    pass


main.add_command(jobs_commands)
main.add_command(simulations_commands)
main.add_command(datasets_commands)
main.add_command(buckets_commands)
main.add_command(debugger_commands)


@main.command()
@click.option("--user", prompt=True, default=USERNAME)
@click.option("--password", prompt=True, default=PASSWORD, hide_input=True)
@may_fail_on_http_error(exit_code=1)
def login(user, password):
    """Will perfom a login to test current credentials"""
    session = proteus.login(username=user, password=password, auto_update=False)
    click.echo(session.access_token_parsed)


if __name__ == "__main__":
    main()

__all__ = ["main"]
