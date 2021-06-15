import os
import requests
from config import config
from common.logger import logger


API_HOST = config.API_HOST


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
        url = f"{API_HOST}/{url}"
        return requests.post(url, headers=headers, json=data)

    def post_files(self, url, files, headers={}):
        headers = {
            "Authorization": "Bearer {}".format(self.auth.access_token),
            **headers,
        }
        url = f"{API_HOST}/{url}"
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response

    def post_file(self, url, filepath, content=None, modified=None):
        headers = {
            "Authorization": "Bearer {}".format(self.auth.access_token),
        }
        if modified is not None:
            headers["x-last-modified"] = modified.isoformat()
        files = dict(file=(filepath, content))
        url = f"{API_HOST}/{url}"
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
        url = f"{API_HOST}/{url}"
        response = requests.get(url, headers=headers, params=query_args)
        response.raise_for_status()
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
