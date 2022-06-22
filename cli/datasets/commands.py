import click
from cli.config import config
from proteus import runs_authentified
from api.decorators import may_fail_on_http_error


@click.group()
def datasets():
    """
    Commands to manage datasets
    """


@datasets.command()
@click.option("--workers", prompt=config.PROMPT, default=config.WORKERS_COUNT)
@click.option("--user", prompt=True, default=config.USERNAME)
@click.option("--password", prompt=True, default=config.PASSWORD, hide_input=True)
@click.argument("bucket")
@click.argument("dataset_uuid")
@may_fail_on_http_error(exit_code=1)
@runs_authentified
def upload(bucket, dataset_uuid, workers=config.WORKERS_COUNT):
    """This uploads an S3 or local bucket into a dataset"""
    from .upload import upload as upload_dataset

    click.echo(upload_dataset(bucket, dataset_uuid, workers=workers))
