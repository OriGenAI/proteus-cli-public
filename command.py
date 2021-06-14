import click
import sys
from config import config
from api import login as api_login, runs_authentified

USERNAME, PASSWORD, PROMPT = config.USERNAME, config.PASSWORD, config.PROMPT
print(config, PROMPT)


@click.group()
def main():
    """
    Simple CLI for PROTEUS auxiliary utils
    """
    pass


@main.command()
@click.option("--user", prompt=True, default=USERNAME)
@click.option("--password", prompt=True, default=PASSWORD, hide_input=True)
def login(user, password):
    """Will perfom a login to test current credentials"""
    session = api_login(username=user, password=password, auto_update=False)
    click.echo(session.access_token)


@main.command()
@click.option("--user", prompt=PROMPT, default=USERNAME)
@click.option("--password", prompt=PROMPT, default=PASSWORD, hide_input=True)
@click.argument("bucket")
@click.argument("dataset_uuid")
def upload(user, password, bucket, dataset_uuid):
    """This search and return results corresponding to the given query from Google Books"""
    from upload import upload_dataset
    auth = api_login(username=user, password=password, auto_update=True)
    click.echo(upload_dataset(bucket, dataset_uuid))


@main.command()
@click.option("--user", prompt=PROMPT, default=USERNAME)
@click.option("--password", prompt=PROMPT, default=PASSWORD, hide_input=True)
@click.argument("source_folder")
@click.option("--batch_uuid", prompt=False)
@click.option("--model_uuid", prompt=False)
@click.option("--batch_name", prompt=False)
@runs_authentified
def simulations(source_folder, batch_uuid=None, model_uuid=None, batch_name=None):
    """This creates a new simulation batch and upload the DATA files and related dependencies from a source folder"""
    if batch_uuid is None and model_uuid is None:
        raise click.UsageError('model_uuid is necessary to create a new batch, for existing ones set batch_uuid')
    from simulations import upload_to_batch, create_batch
    if model_uuid is not None:
        batch_uuid = create_batch(model_uuid, batch_name)
    upload_to_batch(source_folder, batch_uuid)


@main.command()
@click.option("--user", prompt=PROMPT, default=USERNAME)
@click.option("--password", prompt=PROMPT, default=PASSWORD, hide_input=True)
@click.argument("job_uuid")
def jobstatus(user, password, job_uuid):
    """This search and return results corresponding to the given query from Google Books"""
    from jobs import get_status
    from pprint import pprint 
    auth = api_login(username=user, password=password, auto_update=True)
    pprint(get_status(job_uuid))


@main.command()
def test_az_bucket():
    """Tests Azure access"""
    sys.path.insert(0, ".")
    from test_az_bucket import do as do_test_az_bucket

    click.echo("Running azure connection tests")
    do_test_az_bucket()


if __name__ == "__main__":
    main()
