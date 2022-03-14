import click
from api import runs_authentified
from api.decorators import may_fail_on_http_error
from cli.common import Reporting


@click.group()
def simulations():
    """
    Commands to manage simulations
    """


@simulations.command()
@click.argument("source_folder")
@click.option("--batch_uuid", prompt=False)
@click.option("--project_uuid", prompt=False)
@click.option("--pressure_model_uuid", prompt=False)
@click.option("--swat_model_uuid", prompt=False)
@click.option("--batch_name", prompt=False)
@click.option("--reupload/--no-reupload", prompt=False, default=False)
@may_fail_on_http_error(exit_code=1)
@runs_authentified
def create(
    source_folder,
    batch_uuid=None,
    project_uuid=None,
    swat_model_uuid=None,
    pressure_model_uuid=None,
    batch_name=None,
    reupload=False,
):
    """This creates a new simulation batch and uploads the DATA files
    and related dependencies from a source folder"""
    Reporting.info("Create simulation command")
    if batch_uuid is None and (
        swat_model_uuid is None
        or pressure_model_uuid is None
        or project_uuid is None
        or batch_name is None
    ):
        raise click.UsageError(
            "Useage error: You may create/modify a "
            + "simulation batch one of two ways:"
            + "\n  1) use a project_uuid, a pressure_model_uuid,"
            + " a swat_model_uuid, and a batch_name to create a new batch.\n"
            + "  2) use a batch_uuid to modify an existing batch."
        )
    from .create import upload_to_batch, create_batch

    if swat_model_uuid is not None and pressure_model_uuid is not None:
        if batch_name is None or len(batch_name) == 0:
            raise click.UsageError(
                "batch_name is mandatory to create a new batch"
            )
        batch_uuid = create_batch(
            project_uuid=project_uuid,
            pressure_model_uuid=pressure_model_uuid,
            swat_model_uuid=swat_model_uuid,
            batch_name=batch_name,
        )
        Reporting.info(
            f'Created a new batch. to resume use --batch_uuid="{batch_uuid}"'
        )
    Reporting.info("Uploading files and dependencies to simulation batch")
    upload_to_batch(source_folder, batch_uuid, reupload)
