import os
import time
from functools import partial
from api import api, iterate_pagination
from cli.config import config
from tqdm import tqdm
from multiprocessing.pool import ThreadPool
from api.oidc import may_insist_up_to
from ecl.eclfile import EclFile


WORKERS_COUNT, STRESS_ITERATIONS = (config.WORKERS_COUNT, config.STRESS_ITERATIONS)


def keyword_check(bucket, workers=WORKERS_COUNT, iterations=STRESS_ITERATIONS):
    try:
        assert api.auth.access_token is not None
        print(f"This process will use {workers} simultaneous threads.")
        start = time.time()
        count_success = list_bucket_files(bucket, workers=workers, iterations=iterations)
        end = time.time()
        print(f"Succesful downloads: {count_success} of {iterations}, took: {end - start} seconds")
        return "Done"
    except KeyboardInterrupt:
        pass
    finally:
        api.auth.stop()

@may_insist_up_to(5, delay_in_secs=5)
def do_download(item, chunk_size=1024):
    url, path, size = item["url"], item["filepath"], item["size"]

    with tqdm(
        total=None,
        unit="B",
        unit_scale=True,
        unit_divisor=chunk_size,
        leave=False,
    ) as file_progress:
        file_progress.set_postfix_str(
            s=f"download file ...{path.split('/')[-1]}"
        )
        try:
            download = api.download_as_stream(url, 'tests/files', path.split('/')[-1])
            unrst = EclFile(f"tests/files/{path.split('/')[-1]}")
            unrst.iget_named_kw("SWAT", 0).numpy_copy()
            unrst.iget_named_kw("PRESSURE", 0).numpy_copy()
            os.remove(f"tests/files/{path.split('/')[-1]}")
        except:
            return False
        file_progress.total = size
        file_progress.refresh()
        return True

def list_bucket_files(bucket_uuid, workers=3, iterations=10):
    search = {"contains": ".X"}
    response = api.get(
        f"/api/v1/buckets/{bucket_uuid}/files", **search, per_page=iterations
    )
    total = response.json().get("total")
    count_success = 0
    progress = tqdm(total=total)
    download_partial = partial(do_download)
    items = response.json().get("results")
    with ThreadPool(processes=workers) as pool:
        for res in pool.imap(download_partial, items):
            if res:
                count_success += 1
            progress.update(1)
    return count_success

def is_file_already_present(filepath, size=None):
    try:
        found_size = os.stat(filepath).st_size
        if size is not None:
            return size == found_size
        return True
    except Exception:
        return False
