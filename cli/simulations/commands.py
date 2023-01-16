import click

from cli.api.decorators import may_fail_on_http_error
from cli.config import config
from cli.runtime import proteus


@click.group()
def simulations():
    """
    Commands to manage simulations
    """


CREATE_USAGE_ERROR = (
    "Usage error: You may create/modify a "
    + "simulation batch one of two ways:\n"
    + "\n  a) use a project_uuid, a pressure_model_uuid,"
    + " a swat_model_uuid, and a batch_name to create a new batch.\n"
    + "\n"
    + "  b) use a batch_uuid to modify an existing batch."
)


@simulations.command()
@click.argument("source_folder")
@click.option("--batch_uuid", prompt=False)
@click.option("--model_uuid", prompt=False)
@click.option("--batch_name", prompt=False)
@click.option("--reupload/--no-reupload", prompt=False, default=False)
@click.option("--user", prompt=config.USERNAME is None, default=config.USERNAME)
@click.option("--password", prompt=config.PASSWORD is None, default=config.PASSWORD, hide_input=True)
@may_fail_on_http_error(exit_code=1)
@proteus.runs_authentified
def create(
    source_folder,
    batch_uuid=None,
    batch_name=None,
    model_uuid=None,
    reupload=False,
):
    """This creates a new simulation batch and uploads the DATA files
    and related dependencies from a source folder"""

    proteus.logger.info("Create simulation command")
    from .create import (
        upload_to_batch,
        create_batch,
        set_batch_model_and_typed_status,
    )

    try:
        if batch_uuid is None:
            assert model_uuid is not None and batch_name is not None, CREATE_USAGE_ERROR

            assert len(batch_name) > 0, "batch_name can't be empty to create a new batch"

            batch_uuid = create_batch(
                model_uuid=model_uuid,
                batch_name=batch_name,
            )
            proteus.logger.info("Created a new batch. to resume use " f'--batch_uuid="{batch_uuid}"')
        set_batch_model_and_typed_status(batch_uuid, model_uuid)
        proteus.logger.info("Simulation batch assigned to model")

        from .opm import opm_flow_is_available

        opm_flow_is_available()
    except AssertionError as error:
        raise click.UsageError(error)

    proteus.logger.info("Uploading files and dependencies to simulation batch")
    try:
        upload_to_batch(source_folder, batch_uuid, reupload)
    except AssertionError as error:
        proteus.logger.error(f"Error during process: {error}", exc_info=False)
