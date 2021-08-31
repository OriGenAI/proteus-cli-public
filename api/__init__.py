from .oidc import OIDC
from .main import API
from functools import wraps


auth = OIDC()
api = API(auth)


def login(**kwargs):
    global auth
    auth.do_login(**kwargs)
    return auth


def iterate_pagination(response, current=0):
    assert response.status_code == 200
    data = response.json()
    total = data.get("total")
    for item in data.get("results"):
        yield item
        current += 1
    if current < total:
        next_ = data.get("next")
        return iterate_pagination(api.get(next_), current=current)


def runs_authentified(func):
    """Decorator that authentifies and keeps token updated during execution."""

    @wraps(func)
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
