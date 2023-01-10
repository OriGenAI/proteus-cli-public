import logging
import os
import shutil
import time
from functools import partial
from multiprocessing.pool import Pool, ThreadPool

from ecl.eclfile import EclFile, EclInitFile
from ecl.grid import EclGrid
from tqdm import tqdm

from cli.runtime import proteus
from cli.config import config

WORKERS_COUNT, STRESS_ITERATIONS = (
    config.WORKERS_COUNT,
    config.STRESS_ITERATIONS,
)

POOLS = {"processes": Pool, "threads": ThreadPool}

FILES_PATH = "tests/files"


def keyword_check(
    bucket,
    file_ext,
    parallel_method,
    workers=WORKERS_COUNT,
    iterations=STRESS_ITERATIONS,
):
    try:
        assert proteus.api.auth.access_token is not None
        print(f"This process will use {workers} simultaneous threads.")
        start = time.time()
        items = list_bucket_files(bucket, file_ext, iterations=iterations)
        count_success = download_files(items, parallel_method, workers=workers, iterations=iterations)
        end = time.time()
        print(f"Succesful downloads: {count_success} of {iterations}, " + f"took: {end - start:.2f} seconds")
        return "Done"
    except KeyboardInterrupt:
        pass
    finally:
        proteus.api.auth.stop()


@proteus.may_insist_up_to(5, delay_in_secs=5)
def do_download(item, chunk_size=1024):
    url, path, size, num = (
        item["url"],
        item["filepath"],
        item["size"],
        item["num"],
    )

    with tqdm(
        total=None,
        unit="B",
        unit_scale=True,
        unit_divisor=chunk_size,
        leave=False,
    ) as file_progress:
        file_name = f"{path.split('/')[-1]}_{num}"
        file_progress.set_postfix_str(s=f"download file ...{file_name}")

        try:
            if ".X" in file_name:
                _download_x(url, file_name)
            if ".INIT" in file_name:
                _download_init(url, file_name)
        except Exception as e:
            logging.exception(e)
            return False

        file_progress.total = size
        file_progress.refresh()
        return True


def list_bucket_files(bucket_uuid, file_ext, iterations=10):
    if os.path.exists(FILES_PATH):
        shutil.rmtree(FILES_PATH)

    os.mkdir(FILES_PATH)

    search = {"contains": file_ext}
    response = proteus.api.get(f"/api/v1/buckets/{bucket_uuid}/files", **search, per_page=1)

    return [{"num": i, **response.json().get("results")[0]} for i in range(iterations)]


def download_files(items, parallel_method, workers=3, iterations=10):
    count_success = 0
    progress = tqdm(total=iterations)
    download_partial = partial(do_download)
    SelectedPool = POOLS[parallel_method]

    with SelectedPool(processes=workers) as pool:
        for res in pool.imap(download_partial, items):
            count_success += 1 if res else 0
            progress.update(1)

    shutil.rmtree(FILES_PATH)

    return count_success


def _download_x(url, file_name):
    _ = proteus.api.store_download(url, FILES_PATH, file_name, timeout=600)
    unrst = EclFile(f"{FILES_PATH}/{file_name}")
    _validate_x_file(unrst)


def _download_init(url, file_name):
    _ = proteus.api.store_download(url, FILES_PATH, file_name, timeout=600)
    grid = _get_grid(url, file_name)
    init = EclInitFile(grid, f"{FILES_PATH}/{file_name}")
    _validate_init_file(init)


def _validate_x_file(file):
    file.iget_named_kw("SWAT", 0).numpy_copy()
    file.iget_named_kw("PRESSURE", 0).numpy_copy()


def _validate_init_file(file):
    file.iget_named_kw("PORO", 0).numpy_copy()
    file.iget_named_kw("TRANX", 0).numpy_copy()
    file.iget_named_kw("TRANY", 0).numpy_copy()
    file.iget_named_kw("TRANZ", 0).numpy_copy()


def _get_grid(url, file_name):
    egrid_url = url.replace("INIT", "EGRID")
    egrid_file_name = file_name.replace("INIT", "EGRID")
    _ = proteus.api.store_download(egrid_url, FILES_PATH, egrid_file_name, timeout=600)
    return EclGrid(f"{FILES_PATH}/{egrid_file_name}")
