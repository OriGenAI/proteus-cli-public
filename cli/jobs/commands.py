import click
from cli.config import config
from proteus import runs_authentified
from api.decorators import may_fail_on_http_error

USERNAME, PASSWORD, PROMPT = config.USERNAME, config.PASSWORD, config.PROMPT
WORKERS_COUNT = config.WORKERS_COUNT


@click.group()
def jobs():
    """
    Commands to list jobs or job status
    """


@jobs.command()
@click.argument(
    "job_type", type=click.Choice(["samplings", "models", "simulations"])
)
@may_fail_on_http_error(exit_code=1)
@runs_authentified
def list(job_type, *args):
    """Lists the jobs for a entity type"""
    from .list import list_jobs

    list_jobs(job_type)
    print("Bye")


@jobs.command()
@click.argument("job_uuid")
@may_fail_on_http_error(exit_code=1)
@runs_authentified
def status(job_uuid):
    """Lists the latests status for a given job uuid"""
    from .list import list_job_status

    list_job_status(job_uuid)
    print("Bye")
