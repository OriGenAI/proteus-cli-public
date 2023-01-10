import time
from functools import wraps

from requests.exceptions import HTTPError

from cli.runtime import proteus


def message_or_content_of(http_error):
    response = http_error.response
    request = http_error.request
    reason = response.content
    try:
        response_json = response.json()
        if "msg" in response_json:
            reason = response_json["msg"]
        elif "message" in response_json:
            reason = response_json["message"]
    except Exception:
        pass
    return (
        f"Petition failed with status {response.status_code}"
        f", reason: {reason}\n"
        f"while performing {request.method} on {request.url}"
    )


def may_fail_on_http_error(exit_code=None):
    def execution_may_fail_on_http_error(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except HTTPError as error:
                proteus.logger.error(message_or_content_of(error))
                raise

        return wrapped

    return execution_may_fail_on_http_error


def may_insist_up_to(times, delay_in_secs=0):
    def will_retry_till_depleted(fn):
        if times == 0:
            return fn

        @wraps(fn)
        def wrapped(*args, **kwargs):
            failures = 0
            while failures < times:
                try:
                    return fn(*args, **kwargs)
                except Exception as error:
                    proteus.logger.error(error)
                    failures += 1
                    if failures > times:
                        raise error
                    else:
                        print("+", end="")
                        time.sleep(delay_in_secs)

        return wrapped

    return will_retry_till_depleted
