import os
import re
from functools import partial
from api import api, iterate_pagination
from cli.config import config
from tqdm import tqdm
from multiprocessing.pool import ThreadPool
from api.oidc import may_insist_up_to


PROTEUS_HOST, S3_REGION, WORKERS_COUNT, AZURE_STORAGE_CONNECTION_STRING, STRESS_ITERATIONS = (
    config.PROTEUS_HOST,
    config.S3_REGION,
    config.WORKERS_COUNT,
    config.AZURE_STORAGE_CONNECTION_STRING,
    config.STRESS_ITERATIONS

)

@may_insist_up_to(5, delay_in_secs=5)
def do_download(item, chunk_size=1024, force_replace=False):
    url, path, size = item["url"], item["filepath"], item["size"]

    with tqdm(
        total=None,
        unit="B",
        unit_scale=True,
        unit_divisor=chunk_size,
        leave=False,
    ) as file_progress:
        file_progress.set_postfix_str(
            s=f"transfering file ...{path[-20:]}"
        )
        download = api.download_as_stream(url)
        file_progress.total = size
        file_progress.refresh()

def keyword_check(bucket, workers=WORKERS_COUNT, iterations=STRESS_ITERATIONS):
    try:
        assert api.auth.access_token is not None
        print(f"This process will use {workers} simultaneous threads.")
        list_bucket_files(bucket, workers=workers)
        return "Done"
    except KeyboardInterrupt:
        pass
    finally:
        api.auth.stop()

def list_bucket_files(bucket_uuid, workers=3):
    search = {"contains": ".INIT"}
    response = api.get(
        f"/api/v1/buckets/{bucket_uuid}/files", **search, per_page=10
    )
    total = response.json().get("total")
    progress = tqdm(total=total)
    download_partial = partial(do_download)
    with ThreadPool(processes=workers) as pool:
        for res in pool.imap(download_partial, iterate_pagination(response)):
            progress.update(1)

def is_file_already_present(filepath, size=None):
    try:
        found_size = os.stat(filepath).st_size
        if size is not None:
            return size == found_size
        return True
    except Exception:
        return False
