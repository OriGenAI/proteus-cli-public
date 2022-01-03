import os
import requests
from cli.config import config
from cli.common.logger import logger
from .oidc import auth
from requests.exceptions import HTTPError
from functools import wraps


def refresh_authentication():
    def refresh_authentication_if_authenticated(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except HTTPError as error:
                print(error.response.content)
                if error.response.status_code == 401:
                    global auth
                    auth.do_login()

                    return fn(*args, **kwargs)

                raise error

        return wrapped

    return refresh_authentication_if_authenticated

class API:
    def __init__(self, auth):
        self.auth = auth

    def report(
        self, set_status="processing", message=None, progress=0, result=None
    ):
        pass

    def put(self, url, data, headers={}):
        headers = {
            "Authorization": "Bearer {}".format(self.auth.access_token),
            "Content-Type": "application/json",
            **headers,
        }
        url = f"{config.PROTEUS_HOST}/{url}"
        return requests.put(url, headers=headers, json=data)

    def post(self, url, data, headers={}):
        headers = {
            "Authorization": "Bearer {}".format(self.auth.access_token),
            "Content-Type": "application/json",
            **headers,
        }
        url = f"{config.PROTEUS_HOST}/{url}"
        return requests.post(url, headers=headers, json=data)

    def post_files(self, url, files, headers={}):
        headers = {
            "Authorization": "Bearer {}".format(self.auth.access_token),
            **headers,
        }
        url = f"{config.PROTEUS_HOST}/{url}"
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response

    @refresh_authentication()
    def post_file(self, url, filepath, content=None, modified=None):
        content.seek(0, 2)
        size = content.tell()
        content.seek(0)

        headers = {
            "Authorization": "Bearer {}".format(self.auth.access_token),
            "Content-Disposition": f"form-data; name=''; filename={filepath}",
            "Content-Range": f"bytes */{size}"
        }
        if modified is not None:
            headers["x-last-modified"] = modified.isoformat()
        files = dict(file=(filepath, content))
        url = f"{config.PROTEUS_HOST}/{url}"
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response

    def get(self, url, headers={}, stream=False, **query_args):
        headers = {
            "Authorization": "Bearer {}".format(self.auth.access_token),
            "Content-Type": "application/json",
            **headers,
        }
        url = f"{config.PROTEUS_HOST}/{url}"
        response = requests.get(
            url, headers=headers, params=query_args, stream=stream
        )
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

    def download_as_stream(self, url, localpath, localname, timeout=60):
        r = self.get(url, stream=True, timeout=timeout)
        os.makedirs(localpath, exist_ok=True)
        local = localpath
        if localname is not None:
            local = os.path.join(local, localname)

        with open(local, "wb") as f:
            f.write(r.content)

        return r.status_code
