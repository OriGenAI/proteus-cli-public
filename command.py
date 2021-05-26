import click
import sys
from config import config
from api import login as api_login

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
