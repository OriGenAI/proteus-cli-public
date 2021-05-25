import click
from api import login as api_login
from config import config
from project import name
import sys
import os

USERNAME, PASSWORD, PROMPT = config.USERNAME, config.PASSWORD, config.PROMPT


@click.group()
def main():
    """
    Simple CLI for PROTEUS Worker utils
    """
    pass


@main.command()
@click.option("--user", prompt=True, default=USERNAME)
@click.option("--password", prompt=True, default=PASSWORD)
def login(user, password):
    """Will perfom a login to test current credentials"""
    session = api_login(username=user, password=password, auto_update=False)
    click.echo(session.access_token)


@main.command()
@click.option("--user", prompt=PROMPT, default=USERNAME)
@click.option("--password", prompt=PROMPT, default=PASSWORD)
def run(user, password):
    """Will start worker lifecycle"""
    exit_code = os.EX_OK
    try:
        image_ref = os.getenv("CURRENT_IMAGE")
        print("starting ", name, image_ref)
        auth = api_login(username=user, password=password, auto_update=True)
        from common.safe import safely

        safely.init(auth, image_ref)
        safely.protected(basepath="private")
        from private.lifecycle.main import Lifecycle

        lifecycle = Lifecycle()
        lifecycle.run()
    except Exception as error:
        print(error)
        exit_code = os.EX_SOFTWARE
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
