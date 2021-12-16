import re
from functools import partial
from api import api
from cli.config import config
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper
from multiprocessing.pool import Pool
from api.oidc import may_insist_up_to
from .sources.s3 import S3Source
from .sources.az import AZSource
from .sources.local import LocalSource

AVAILABLE_SOURCES = [S3Source, AZSource, LocalSource]


PROTEUS_HOST, WORKERS_COUNT = (
    config.PROTEUS_HOST,
    config.WORKERS_COUNT,
)

_sheet_extension = re.compile(
    r".*(?P<extension>DATA|EGRID|INIT|SMSPEC|GRDECL)$"
)

case_re = re.compile(
    r"(?P<root>.*/(?P<group>validation|training|testing)"
    r"/SIMULATION_(?P<number>\d+))/(?P<content>.*)"
)

_timestep = re.compile(r".*(?P<extension>X\d{4}|S\d{4})$")


def upload(bucket, dataset_uuid, workers=WORKERS_COUNT):
    try:
        assert api.auth.access_token is not None
        print(f"This process will use {workers} simultaneous threads.")
        with tqdm(total=0) as progress:
            total_expected, case_by_group_and_number = get_cases(
                api.auth, dataset_uuid, progress
            )
            load_from(
                case_by_group_and_number, bucket, progress, workers=workers
            )
    except KeyboardInterrupt:
        pass
    finally:
        api.auth.stop()


def get_cases(auth, dataset_uuid, progress):
    progress.set_description("retrieving cases and expected files")
    progress.refresh()
    cases_url = f"/api/v1/datasets/{dataset_uuid}/cases"
    response = api.get(cases_url)
    cases = response.json().get("cases")
    case_by_group_and_number = {}
    total = 0
    for case in cases:
        case_details = api.get(case.get("case_url")).json().get("case")
        key = f"{case.get('group')}-{case.get('number')}"
        case_by_group_and_number[key] = case_details
        total += 5 + (2 * case.get("steps", 0))
        progress.total = total
        progress.refresh()
    return total, case_by_group_and_number


def find_target(case_by_group_and_number, group=None, number=None, **other):
    if group is None or number is None:
        return None
    return case_by_group_and_number.get(f"{group}-{number}")


def get_source(source_uri):
    for candidate in AVAILABLE_SOURCES:
        if candidate.accepts(source_uri):
            return candidate(source_uri)


def load_from(
    case_by_group_and_number, source_uri, progress, workers=WORKERS_COUNT
):
    skipped_count = 0
    processed = 0
    progress.update(processed)
    source = get_source(source_uri)
    items_and_paths = source.list_contents()
    upload_partial = partial(
        parallelized_upload,
        case_by_group_and_number=case_by_group_and_number,
        processed=processed,
        skipped_count=skipped_count,
    )
    with Pool(processes=workers) as pool:
        for res in pool.imap_unordered(upload_partial, items_and_paths):
            progress.update(res if res else 0)
            progress.refresh()

@may_insist_up_to(5, delay_in_secs=5)
def parallelized_upload(
    item_and_path, case_by_group_and_number, processed, skipped_count
):
    item, path, reference = item_and_path
    matchs_as_case = case_re.match(path)
    terms = matchs_as_case.groupdict() if matchs_as_case is not None else {}
    target = find_target(case_by_group_and_number, **terms)
    if target is None:
        skipped_count += 1
    else:
        content = terms.get("content")
        matchs = _timestep.match(content) or _sheet_extension.match(content)
        if matchs:
            if is_pending(matchs, target):
                done, skipped = send_as(
                    target, item, reference, **terms, **matchs.groupdict()
                )
                processed += done
                skipped_count += skipped
            else:
                processed += 1

    return processed


def is_pending(match, target):
    extension = match.groupdict().get("extension")
    missing_core = target.get("missing_parts").get("core")
    if extension in missing_core:
        return True
    missing_steps = target.get("missing_parts").get("steps")
    if extension in missing_steps:
        return True
    return False


def send_as(
    target, source, reference, group=None, number=None, extension=None, **other
):
    target_url = target.get("case_url")
    source_path, file_size, modified, stream = source.open(reference)
    done = 0
    skipped = 0
    transfer = None
    try:
        with tqdm(
            total=file_size, unit="B", unit_scale=True, unit_divisor=1024
        ) as progress:
            progress.set_description(f"uploading {source_path}")
            wrapped_file = CallbackIOWrapper(progress.update, stream, "read")
            transfer = api.post_file(
                target_url,
                source_path,
                content=wrapped_file,
                modified=modified,
            )
            progress.set_description(f"uploaded {source_path[-20:]}")
            stream.close()
            assert transfer.json()
            progress.close()
            if transfer.status_code == 201:
                done = 1
            elif transfer.status_code == 200:
                skipped = 1
            else:
                raise Exception("transfer failed")
    except Exception as error:
        print(f"Failed upload: {source_path}")
        if transfer is not None:
            print(error, transfer.content)
        raise error
    return done, skipped