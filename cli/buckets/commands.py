import click

from cli.api.decorators import may_fail_on_http_error
from cli.config import config
from cli.runtime import proteus

PROMPT = config.PROMPT
WORKERS_COUNT = config.WORKERS_COUNT


@click.group()
def buckets():
    """
    Commands to manage buckets
    """


@buckets.command()
@click.option("--workers", prompt=PROMPT, default=WORKERS_COUNT)
@click.argument("bucket_uuid")
@click.argument("folder")
@click.option("--replace/--no-replace", default=False)
@click.option("--ends-with", prompt=False, default=None)
@click.option("--starts-with", prompt=False, default=None)
@click.option("--user", prompt=True, default=config.USERNAME)
@click.option("--password", prompt=True, default=config.PASSWORD, hide_input=True)
@may_fail_on_http_error(exit_code=1)
@proteus.runs_authentified
def download(bucket_uuid, folder, workers=WORKERS_COUNT, replace=False, **search):
    """downloads a bucket's content to de specified folder"""
    from .download import download as download_bucket

    click.echo(download_bucket(bucket_uuid, folder, workers=workers, replace=replace, **search))
