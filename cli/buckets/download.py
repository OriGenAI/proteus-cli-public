import os
from multiprocessing.dummy import Pool

from cli.api import iterate_pagination
from tqdm import tqdm

from cli import config, proteus

PROTEUS_HOST, S3_REGION, WORKERS_COUNT, AZURE_STORAGE_CONNECTION_STRING = (
    config.PROTEUS_HOST,
    config.S3_REGION,
    config.WORKERS_COUNT,
    config.AZURE_STORAGE_CONNECTION_STRING,
)


def _each_file_bucket(bucket_uuid, each_file_fn, workers=3, **search):
    assert proteus.api.auth.access_token is not None
    response = proteus.api.get(f"/api/v1/buckets/{bucket_uuid}/files", per_page=10, **search)
    total = response.json().get("total")

    for res in _each_item_parallel(
        total, items=iterate_pagination(response), each_item_fn=each_file_fn, workers=workers
    ):
        yield res


def _each_item_parallel(total, items, each_item_fn, workers=3):
    progress = tqdm(total=total)
    with Pool(processes=workers) as pool:
        for res in pool.imap(each_item_fn, items):
            progress.update(1)
            yield res


def store_stream_in(stream, filepath, progress, chunk_size=1024):
    folder_path = os.path.join(*filepath.split("/")[:-1])
    os.makedirs(folder_path, exist_ok=True)
    temp_filepath = f"{filepath}.partial"
    try:
        os.remove(temp_filepath)
    except OSError:
        pass
    os.makedirs(os.path.dirname(temp_filepath), exist_ok=True)
    with open(temp_filepath, "wb+") as _file:
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
    def do_download(item, chunk_size=1024):
        url, path, size, ready = item["url"], item["filepath"], item["size"], item["ready"]

        if not ready:
            proteus.logger.warning(f"File {path} is not ready, skipping")
            return

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
            download = proteus.api.download(url, stream=True, retry=True)
            file_progress.total = size
            file_progress.refresh()
            store_stream_in(download, target_filepath, file_progress, chunk_size=chunk_size)

    return do_download


def download(bucket_uuid, target_folder, workers=WORKERS_COUNT, replace=False, **search):
    replacement = "Previous files will be overwritten" if replace else "Existing files will be kept."
    proteus.logger.info(f"This process will use {workers} simultaneous threads. {replacement}")
    do_download = will_do_file_download(target_folder, force_replace=replace)

    for file in _each_file_bucket(bucket_uuid, do_download, workers=workers, **search):
        yield file
