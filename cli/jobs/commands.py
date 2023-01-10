import click

from cli.api.decorators import may_fail_on_http_error
from cli.config import config
from cli.runtime import proteus

USERNAME, PASSWORD, PROMPT = config.USERNAME, config.PASSWORD, config.PROMPT
WORKERS_COUNT = config.WORKERS_COUNT


@click.group()
def jobs():
    """
    Commands to list jobs or job status
    """


@jobs.command()
@click.argument("job_type", type=click.Choice(["samplings", "models", "simulations"]))
@click.option("--user", prompt=config.USERNAME is None, default=config.USERNAME)
@click.option("--password", prompt=config.PASSWORD is None, default=config.PASSWORD, hide_input=True)
@may_fail_on_http_error(exit_code=1)
@proteus.runs_authentified
def list(job_type, *args):
    """Lists the jobs for a entity type"""
    from .list import list_jobs

    list_jobs(job_type)
    print("Bye")


@jobs.command()
@click.argument("job_uuid")
@click.option("--user", prompt=config.USERNAME is None, default=config.USERNAME)
@click.option("--password", prompt=config.PASSWORD is None, default=config.PASSWORD, hide_input=True)
@may_fail_on_http_error(exit_code=1)
@proteus.runs_authentified
def status(job_uuid):
    """Lists the latests status for a given job uuid"""
    from .list import list_job_status

    list_job_status(job_uuid)
    print("Bye")
