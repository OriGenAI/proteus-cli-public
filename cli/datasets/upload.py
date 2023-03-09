import os
import re
import shutil
import tempfile
import time
from functools import partial
from multiprocessing.pool import ThreadPool

import numpy as np
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper

from cli.api.hooks import TqdmUpWithReport
from cli.config import config
from cli.datasets.preprocessor.config import (
    CaseConfigMapper,
    CommonConfigMapper,
    StepConfigMapper,
)
from .sources.az import AZSource
from .sources.local import LocalSource
from .sources.s3 import S3Source
from .. import proteus

AVAILABLE_SOURCES = [S3Source, AZSource, LocalSource]


PROTEUS_HOST, WORKERS_COUNT, DATASET_VERSION = (
    config.PROTEUS_HOST,
    config.WORKERS_COUNT,
    config.DATASET_VERSION,
)

_sheet_extension = re.compile(r".*(?P<extension>DATA|EGRID|INIT|SMSPEC|GRDECL)$")

case_re = re.compile(
    r"(?P<root>.*/(?P<group>validation|training|testing)" r"/SIMULATION_(?P<number>\d+))/(?P<content>.*)"
)

_timestep = re.compile(r".*(?P<extension>X\d{4}|S\d{4})$")


def set_dataset_version(dataset_uuid):
    new_version = dict(
        major_version=DATASET_VERSION.get("major"),
        minor_version=DATASET_VERSION.get("minor"),
        patch_version=DATASET_VERSION.get("patch"),
    )

    dataset_version_url = f"/api/v1/datasets/{dataset_uuid}/versions"
    proteus.api.post(dataset_version_url, new_version)


def get_total_steps(cases, workflow):
    training_cases = [*filter(lambda c: c["group"] == "training" and c["number"] == 1, cases)]
    if not training_cases and cases:
        first_training_case = cases[0]
    else:
        first_training_case = next(iter(training_cases), None)
    first_case_response = proteus.api.get(first_training_case.get("case_url"))
    first_case_json = first_case_response.json().get("case")
    initial_step = first_case_json.get("initialStep")
    final_step = first_case_json.get("finalStep")
    workflow = workflow.lower()
    common_step = CommonConfigMapper[workflow].number_of_steps()
    cases_steps = CaseConfigMapper[workflow].number_of_steps()
    timesteps_steps = (
        StepConfigMapper[workflow].number_of_steps() - 1 if StepConfigMapper[workflow].number_of_steps() > 0 else 0
    )
    return common_step + (cases_steps + timesteps_steps * (final_step - initial_step + 1)) * len(cases)


def upload(
    bucket, dataset_uuid, workers=WORKERS_COUNT, replace=False, allow_missing_files=tuple(), temp_folder_override=False
):
    assert proteus.api.auth.access_token is not None
    set_dataset_version(dataset_uuid)
    source = get_source(bucket)

    proteus.logger.info(f"This process will use {workers} simultaneous threads.")
    proteus.reporting.send("started upload", status="processing", progress=0)
    with TqdmUpWithReport(total=0) as progress:
        cases = get_cases(dataset_uuid, progress)

        progress.set_description("Setting the dataset version")
        progress.refresh()
        response = proteus.api.get(f"/api/v1/datasets/{dataset_uuid}")
        dataset_json = response.json().get("dataset")
        bucket_url = dataset_json.get("bucket_url")
        cases_url = dataset_json.get("cases_url")
        workflow = dataset_json.get("workflow").get("workflow") or dataset_json.get("workflow").get("name")

        total_steps = get_total_steps(cases, workflow)

        progress.total = total_steps
        progress.set_description("Starting processing files")
        progress.refresh()
        process_files(
            source,
            bucket_url,
            cases_url,
            progress=progress,
            cases=cases,
            workers=workers,
            workflow=workflow,
            replace=replace,
            allow_missing_files=allow_missing_files,
            temp_folder_override=temp_folder_override,
        )

    proteus.reporting.send("upload finished", status="completed", progress=100)


def get_cases(dataset_uuid, progress):
    progress.set_description("Retrieving cases and expected files")
    progress.refresh()

    cases_url = f"/api/v1/datasets/{dataset_uuid}/cases"
    response = proteus.api.get(cases_url)

    return response.json().get("cases")


def find_target(case_by_group_and_number, group=None, number=None, **other):
    if group is None or number is None:
        return None
    return case_by_group_and_number.get(f"{group}-{number}")


def get_source(source_uri):
    for candidate in AVAILABLE_SOURCES:
        if candidate.accepts(source_uri):
            return candidate(source_uri)


def parallelized_upload(item_and_path, case_by_group_and_number, processed, skipped_count):
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
                done, skipped = send_as(target, item, reference, **terms, **matchs.groupdict())
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


def send_as(target, source, reference, group=None, number=None, extension=None, **other):
    target_url = target.get("case_url")
    source_path, file_size, modified, stream = source.open(reference)
    done = 0
    skipped = 0
    transfer = None
    try:
        with tqdm(total=file_size, unit="B", unit_scale=True, unit_divisor=1024) as progress:
            progress.set_description(f"uploading {source_path}")
            wrapped_file = CallbackIOWrapper(progress.update, stream, "read")
            transfer = proteus.api.post_file(
                target_url, source_path, content=wrapped_file, modified=modified, retry=True
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
        proteus.logger.error(f"Failed upload: {source_path}")
        if transfer is not None:
            proteus.logger.error(error, transfer.content)
        raise error
    return done, skipped


def process_files(
    source,
    bucket_url,
    cases_url,
    progress,
    cases=[],
    workers=WORKERS_COUNT,
    workflow="hm",
    replace=False,
    allow_missing_files=tuple(),
    temp_folder_override=False,
):
    from .preprocessor.config import Config
    from .preprocessor.process_step import process_step

    # Download common.p if exists
    common_content = download_common(f"{bucket_url}/common.p")

    # Generate all the files-pairs with a generator
    sortedCases = sorted(cases, key=lambda d: d["root"])
    config = Config(cases=sortedCases, common_data=common_content, workflow=workflow)
    steps = config.return_iterator()

    # Create temporary folder
    tmpdirname = None
    try:
        tmpdirname = (
            tempfile.TemporaryDirectory(prefix="proteus-", suffix=bucket_url.split("/")[-1]).name
            if not temp_folder_override
            else temp_folder_override
        )
        os.makedirs(tmpdirname, exist_ok=True)
        with ThreadPool(processes=workers) as pool:
            process_step_partial = partial(
                process_step,
                tmpdirname=tmpdirname,
                source=source,
                bucket_url=bucket_url,
                cases_url=cases_url,
                replace=replace,
                allow_missing_files=allow_missing_files,
            )
            for res in pool.imap(process_step_partial, steps):
                for output in res[:-1]:
                    progress.update(n=1 / len(res))
                    progress.set_description(f"File uploaded: {output}")
                    time.sleep(1)
                progress.set_description(f"File uploaded: {res[-1]}")
                progress.update_with_report(n=1 / len(res))
                progress.refresh()
    finally:
        if tmpdirname and not temp_folder_override:
            shutil.rmtree(tmpdirname, ignore_errors=True)


def download_common(url):
    try:
        r = proteus.api.get(url)
        open("/tmp/common.p", "wb").write(r.content)

        download = np.load("/tmp/common.p", allow_pickle=True)
        return download
    except Exception:
        return None
