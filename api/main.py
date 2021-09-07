import os
import requests
from config import config
from common.logger import logger
from functools import wraps


PROTEUS_HOST = config.PROTEUS_HOST


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
            except requests.exceptions.HTTPError as error:
                print(message_or_content_of(error))
                if exit_code is not None:
                    import sys

                    sys.exit(exit_code)
                raise error

        return wrapped

    return execution_may_fail_on_http_error


class API:
    def __init__(self, auth):
        self.auth = auth

    def report(
        self, set_status="processing", message=None, progress=0, result=None
    ):
        pass

    def post(self, url, data, headers={}):
        headers = {
            "Authorization": "Bearer {}".format(self.auth.access_token),
            "Content-Type": "application/json",
            **headers,
        }
        url = f"{PROTEUS_HOST}/{url}"
        return requests.post(url, headers=headers, json=data)

    def post_files(self, url, files, headers={}):
        headers = {
            "Authorization": "Bearer {}".format(self.auth.access_token),
            **headers,
        }
        url = f"{PROTEUS_HOST}/{url}"
        response = requests.post(url, headers=headers, files=files)
        try:
            response.raise_for_status()
        except Exception as error:
            print(response.content)
            raise error
        return response

    def post_file(self, url, filepath, content=None, modified=None):
        headers = {
            "Authorization": "Bearer {}".format(self.auth.access_token),
        }
        if modified is not None:
            headers["x-last-modified"] = modified.isoformat()
        files = dict(file=(filepath, content))
        url = f"{PROTEUS_HOST}/{url}"
        response = requests.post(url, headers=headers, files=files)
        try:
            response.raise_for_status()
        except Exception as error:
            print(response.content)
            raise error
        return response

    def get(self, url, headers={}, **query_args):
        headers = {
            "Authorization": "Bearer {}".format(self.auth.access_token),
            "Content-Type": "application/json",
            **headers,
        }
        url = f"{PROTEUS_HOST}/{url}"
        response = requests.get(url, headers=headers, params=query_args)
        try:
            response.raise_for_status()
        except Exception as error:
            print("HTTP error:", response.content)
            raise error
        return response

    def download_file(self, url, localpath, localname):
        target = os.path.join(localpath)
        logger.info(f"Downloading {url} to {target}")
        self.download(
            url=url,
            localpath=localpath,
            localname=localname,
        )
        logger.info("Download complete")

    def download(self, url, localpath, localname):
        r = self.get(url)
        os.makedirs(localpath, exist_ok=True)
        local = localpath
        if localname is not None:
            local = os.path.join(local, localname)

        with open(local, "wb") as f:
            f.write(r.content)

        return r.status_code
