import click
from api import runs_authentified
from api.decorators import may_fail_on_http_error


@click.group()
def simulations():
    """
    Commands to manage simulations
    """


@simulations.command()
@click.argument("source_folder")
@click.option("--batch_uuid", prompt=False)
@click.option("--model_uuid", prompt=False)
@click.option("--batch_name", prompt=False)
@may_fail_on_http_error(exit_code=1)
@runs_authentified
def create(source_folder, batch_uuid=None, model_uuid=None, batch_name=None):
    """This creates a new simulation batch and upload the DATA files
    and related dependencies from a source folder"""
    if batch_uuid is None and model_uuid is None:
        raise click.UsageError(
            "model_uuid is necessary to create a new batch" ""
        )
    from .create import upload_to_batch, create_batch

    if model_uuid is not None:
        if batch_name is None or len(batch_name) == 0:
            raise click.UsageError(
                "batch_name is mandatory to create a new batch"
            )
        batch_uuid = create_batch(model_uuid, batch_name)
        print(
            f'Created a new batch. to resume use --batch_uuid="{batch_uuid}"'
        )
    upload_to_batch(source_folder, batch_uuid)
