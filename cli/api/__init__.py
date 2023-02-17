from functools import partial

from cli.runtime import proteus


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
        data = proteus.may_insist_up_to(
            partial(proteus.api.get, next_),
            times=5,
            delay_in_secs=1
        )().json()
