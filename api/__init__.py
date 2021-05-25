from .oidc import OIDC
from .main import API


auth = OIDC()
api = API(auth)


def login(**kwargs):
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
