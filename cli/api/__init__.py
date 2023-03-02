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
        data = proteus.api.get(next_, retry=True).json()
