from .oidc import auth
from .main import API
from functools import wraps
import click
from cli.config import config


api = API(auth)


def login(**kwargs):
    global auth
    auth.do_login(**kwargs)
    return auth

def iterate_pagination(response, current=0):
    assert response.status_code == 200
    data = response.json()
    while True:
        for item in data.get("results"):
            yield item
            current += 1
        next_ = data.get("next")
        if next_ is None:
            break
        data = api.get(next_).json()


USERNAME, PASSWORD, PROMPT = config.USERNAME, config.PASSWORD, config.PROMPT


def runs_authentified(func):
    """Decorator that authentifies and keeps token updated during execution."""

    @wraps(func)
    @click.option("--user", prompt=PROMPT, default=USERNAME)
    @click.option(
        "--password", prompt=PROMPT, default=PASSWORD, hide_input=True
    )
    def wrapper(user, password, *args, **kwargs):
        global auth
        try:
            if not auth.do_login(
                username=user, password=password, auto_update=True
            ):
                print("Authentication failure, exiting")
                import sys

                sys.exit(1)
            print(f"Welcome, {auth.access_token_parsed.get('given_name')}")
            return func(*args, **kwargs)
        except Exception as error:
            raise error
        finally:
            auth.stop()

    return wrapper
