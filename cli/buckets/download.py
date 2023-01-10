import os
from functools import partial
from multiprocessing.dummy import Pool

from tqdm import tqdm

from cli import config, proteus
from cli.api import iterate_pagination

PROTEUS_HOST, S3_REGION, WORKERS_COUNT, AZURE_STORAGE_CONNECTION_STRING = (
    config.PROTEUS_HOST,
    config.S3_REGION,
    config.WORKERS_COUNT,
    config.AZURE_STORAGE_CONNECTION_STRING,
)


def list_bucket_files(bucket_uuid, each_item, workers=3, **search):
    assert proteus.api.auth.access_token is not None
    response = proteus.api.get(f"/api/v1/buckets/{bucket_uuid}/files", per_page=10, **search)
    total = response.json().get("total")
    progress = tqdm(total=total)
    download_partial = partial(each_item)
    with Pool(processes=workers) as pool:
        for res in pool.imap(download_partial, iterate_pagination(response)):
            progress.update(1)


def store_stream_in(stream, filepath, progress, chunk_size=1024):
    folder_path = os.path.join(*filepath.split("/")[:-1])
    os.makedirs(folder_path, exist_ok=True)
    temp_filepath = f"{filepath}.partial"
    try:
        os.remove(temp_filepath)
    except OSError:
        pass
    with open(temp_filepath, "wb") as _file:
        for data in stream.iter_content(chunk_size):
            progress.update(len(data))
            _file.write(data)
    os.rename(temp_filepath, filepath)


def is_file_already_present(filepath, size=None):
    try:
        found_size = os.stat(filepath).st_size
        if size is not None:
            return size == found_size
        return True
    except Exception:
        return False


def will_do_file_download(target, force_replace=False):
    @proteus.may_insist_up_to(5, delay_in_secs=5)
    def do_download(item, chunk_size=1024):
        url, path, size = item["url"], item["filepath"], item["size"]
        target_filepath = os.path.normpath(os.path.join(target, path))
        if not force_replace and is_file_already_present(target_filepath, size=size):
            return False
        with tqdm(
            total=None,
            unit="B",
            unit_scale=True,
            unit_divisor=chunk_size,
            leave=False,
        ) as file_progress:
            file_progress.set_postfix_str(s=f"transfering file ...{path[-20:]}")
            download = proteus.api.download(url, stream=True)
            file_progress.total = size
            file_progress.refresh()
            store_stream_in(download, target_filepath, file_progress, chunk_size=chunk_size)

    return do_download


def download(bucket_uuid, target_folder, workers=WORKERS_COUNT, replace=False, **search):
    replacement = "Previous files will be overwritten" if replace else "Existing files will be kept."
    proteus.logger.info(f"This process will use {workers} simultaneous threads. {replacement}")
    do_download = will_do_file_download(target_folder, force_replace=replace)

    list_bucket_files(bucket_uuid, do_download, workers=workers, **search)
