import click
from config import config
from api import login as api_login, runs_authentified
from api.main import may_fail_on_http_error

USERNAME, PASSWORD, PROMPT = config.USERNAME, config.PASSWORD, config.PROMPT
WORKERS_COUNT = config.WORKERS_COUNT


@click.group()
def main():
    """
    Simple CLI for PROTEUS auxiliary utils
    """
    pass


@main.command()
@click.option("--user", prompt=True, default=USERNAME)
@click.option("--password", prompt=True, default=PASSWORD, hide_input=True)
@may_fail_on_http_error(exit_code=1)
def login(user, password):
    """Will perfom a login to test current credentials"""
    session = api_login(username=user, password=password, auto_update=False)
    click.echo(session.access_token_parsed)


@main.command()
@click.option("--user", prompt=PROMPT, default=USERNAME)
@click.option("--password", prompt=PROMPT, default=PASSWORD, hide_input=True)
@click.option("--workers", prompt=PROMPT, default=WORKERS_COUNT)
@click.argument("bucket")
@click.argument("dataset_uuid")
@may_fail_on_http_error(exit_code=1)
@runs_authentified
def upload(bucket, dataset_uuid, workers=WORKERS_COUNT):
    """This uploads an S3 bucket into a dataset"""
    from upload import upload_dataset

    click.echo(upload_dataset(bucket, dataset_uuid, workers=workers))


@main.command()
@click.option("--user", prompt=PROMPT, default=USERNAME)
@click.option("--password", prompt=PROMPT, default=PASSWORD, hide_input=True)
@click.argument("source_folder")
@click.option("--batch_uuid", prompt=False)
@click.option("--model_uuid", prompt=False)
@click.option("--batch_name", prompt=False)
@may_fail_on_http_error(exit_code=1)
@runs_authentified
def simulations(
    source_folder, batch_uuid=None, model_uuid=None, batch_name=None
):
    """This creates a new simulation batch and upload the DATA files
    and related dependencies from a source folder"""
    if batch_uuid is None and model_uuid is None:
        raise click.UsageError(
            "model_uuid is necessary to create a new batch" ""
        )
    from simulations import upload_to_batch, create_batch

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


@main.command()
@click.option("--user", prompt=PROMPT, default=USERNAME)
@click.option("--password", prompt=PROMPT, default=PASSWORD, hide_input=True)
@click.argument(
    "job_type", type=click.Choice(["samplings", "models", "simulations"])
)
@may_fail_on_http_error(exit_code=1)
@runs_authentified
def listjobs(job_type, *args):
    """Lists the jobs for a entity type"""
    from jobs import list_jobs

    list_jobs(job_type)


@main.command()
@click.option("--user", prompt=PROMPT, default=USERNAME)
@click.option("--password", prompt=PROMPT, default=PASSWORD, hide_input=True)
@click.argument("job_uuid")
@may_fail_on_http_error(exit_code=1)
@runs_authentified
def jobstatus(job_uuid):
    """Lists the latests status for a given job uuid"""
    from jobs import get_status
    from pprint import pprint

    pprint(get_status(job_uuid))


if __name__ == "__main__":
    main()
