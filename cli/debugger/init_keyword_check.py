import os
import re
from functools import partial
from api import api, iterate_pagination
from cli.config import config
from tqdm import tqdm
from multiprocessing.pool import Pool
from api.oidc import may_insist_up_to


PROTEUS_HOST, S3_REGION, WORKERS_COUNT, AZURE_STORAGE_CONNECTION_STRING, STRESS_ITERATIONS = (
    config.PROTEUS_HOST,
    config.S3_REGION,
    config.WORKERS_COUNT,
    config.AZURE_STORAGE_CONNECTION_STRING,
    config.STRESS_ITERATIONS

)

@may_insist_up_to(5, delay_in_secs=5)
def do_download(item, target, chunk_size=1024, force_replace=False):
    url, path, size = item["url"], item["filepath"], item["size"]
    target_filepath = os.path.normpath(os.path.join(target, path))
    if not force_replace and is_file_already_present(
        target_filepath, size=size
    ):
        return False
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
        store_stream_in(
            download, target_filepath, file_progress, chunk_size=chunk_size
        )

def keyword_check(bucket, folder, workers=WORKERS_COUNT, iterations=STRESS_ITERATIONS):
    try:
        assert api.auth.access_token is not None
        print(f"This process will use {workers} simultaneous threads.")
        list_bucket_files(bucket, folder, workers=workers)
        return "Done"
    except KeyboardInterrupt:
        pass
    finally:
        api.auth.stop()

def list_bucket_files(bucket_uuid, target, workers=3):
    response = api.get(
        f"/api/v1/buckets/{bucket_uuid}/files", per_page=10
    )
    total = response.json().get("total")
    progress = tqdm(total=total)
    download_partial = partial(do_download, target=target)
    with Pool(processes=workers) as pool:
        for res in pool.imap(download_partial, iterate_pagination(response)):
            progress.update(1)


def store_stream_in(stream, filepath, progress, chunk_size=1024):
    folder_path = os.path.join(*filepath.split("/")[:-1])
    os.makedirs(folder_path, exist_ok=True)
    temp_filepath = f"{filepath}.partial"
    temp_filepath = "/dev/null"
    with open(temp_filepath, "wb") as _file:
        for data in stream.iter_content(chunk_size):
            progress.update(len(data))
            _file.write(data)
    try:
        os.remove(filepath)
    except OSError:
        pass

def is_file_already_present(filepath, size=None):
    try:
        found_size = os.stat(filepath).st_size
        if size is not None:
            return size == found_size
        return True
    except Exception:
        return False

