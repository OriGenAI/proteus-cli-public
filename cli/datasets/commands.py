import click

from cli.api.decorators import may_fail_on_http_error
from cli.config import config
from cli.runtime import proteus


@click.group()
def datasets():
    """
    Commands to manage datasets
    """


@datasets.command()
@click.option("--workers", prompt=config.PROMPT, default=config.WORKERS_COUNT)
@click.option("--user", prompt=config.USERNAME is None, default=config.USERNAME)
@click.option("--password", prompt=config.PASSWORD is None, default=config.PASSWORD, hide_input=True)
@click.option("--replace/--no-replace", default=False)
@click.option("--allow-missing-file", "-m", multiple=True)
@click.option("--temp-folder-override", "-t", multiple=False)
@click.argument("bucket")
@click.argument("dataset_uuid")
@may_fail_on_http_error(exit_code=1)
@proteus.runs_authentified
def upload(
    bucket,
    dataset_uuid,
    workers=config.WORKERS_COUNT,
    replace=False,
    allow_missing_file=tuple(),
    temp_folder_override=False,
):
    """This uploads an S3 or local bucket into a dataset"""
    from .upload import upload as upload_dataset

    click.echo(
        upload_dataset(
            bucket,
            dataset_uuid,
            workers=workers,
            replace=replace,
            allow_missing_files=allow_missing_file,
            temp_folder_override=temp_folder_override,
        )
    )
