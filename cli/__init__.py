import click

from cli.api.decorators import may_fail_on_http_error  # noqa: E402
from cli.runtime import proteus
from cli.buckets.commands import buckets as buckets_commands
from cli.config import config
from cli.datasets.commands import datasets as datasets_commands
from cli.debugger.commands import debugger as debugger_commands
from cli.jobs.commands import jobs as jobs_commands
from cli.simulations.commands import simulations as simulations_commands

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
@click.option("--user", prompt=USERNAME is None, default=USERNAME)
@click.option("--password", prompt=PASSWORD is None, default=PASSWORD, hide_input=True)
@may_fail_on_http_error(exit_code=1)
def login(user, password):
    """Will perfom a login to test current credentials"""
    session = proteus.login(username=user, password=password, auto_update=False)
    click.echo(session.access_token_parsed)


if __name__ == "__main__":
    main()

__all__ = ["main"]
