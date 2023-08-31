import importlib
import os
import shutil
import tempfile
from contextlib import contextmanager
from typing import List

from cli.api.hooks import TqdmUpWithReport
from cli.config import config
from cli.datasets.preprocessor.config import (
    BaseConfig,
    PREPROCESSING_PHASES,
    StepConfigWithMetadata,
    PREPROCESSING_PHASE_CASE,
    PREPROCESSING_PHASE_STEP,
)
from cli.datasets.preprocessor.process_step import process_step
from cli.datasets.sources.az import AZSource
from cli.datasets.sources.common import Source
from cli.datasets.sources.local import LocalSource
from cli.datasets.sources.s3 import S3Source

from cli import proteus

AVAILABLE_SOURCES = [S3Source, AZSource, LocalSource]

PROTEUS_HOST, WORKERS_COUNT, DATASET_VERSION = (
    config.PROTEUS_HOST,
    config.WORKERS_COUNT,
    config.DATASET_VERSION,
)


def upload(
    bucket, dataset_uuid, workers=WORKERS_COUNT, replace=False, allow_missing_files=tuple(), temp_folder_override=False
):
    assert proteus.auth.access_token is not None
    set_dataset_version(dataset_uuid)

    proteus.logger.info(f"This process will use {workers} simultaneous threads.")
    proteus.reporting.send("Starting", status="processing", progress=0)
    with TqdmUpWithReport(total=0, unit="files") as progress:

        progress.set_description("Retrieving dataset metadata...")
        cases = get_cases(dataset_uuid, progress)
        bucket_url, cases_url, workflow = get_dataset_info(dataset_uuid)
        steps = get_steps(cases, workflow)

        total_files = sum(len(x.output) for x in list(steps))
        progress.total = total_files

        progress.set_description("Starting...")
        progress.refresh()

        process_files(
            bucket,
            bucket_url,
            cases_url,
            steps,
            progress=progress,
            workers=workers,
            replace=replace,
            allow_missing_files=allow_missing_files,
            temp_folder_override=temp_folder_override,
        )

    proteus.reporting.send("Done", status="completed", progress=100)


def set_dataset_version(dataset_uuid):
    new_version = dict(
        major_version=DATASET_VERSION.get("major"),
        minor_version=DATASET_VERSION.get("minor"),
        patch_version=DATASET_VERSION.get("patch"),
    )

    dataset_version_url = f"/api/v1/datasets/{dataset_uuid}/versions"
    proteus.api.post(dataset_version_url, new_version)


def get_steps(cases, workflow) -> List[StepConfigWithMetadata]:
    steps = []
    # Generate all the files-pairs with a generator
    for preprocessing_phase in PREPROCESSING_PHASES:
        module_name = f'cli.datasets.preprocessor.config.{workflow.replace("-", "_")}.{preprocessing_phase}'
        config_module = importlib.import_module(module_name)
        config_classes = [
            getattr(config_module, x)
            for x in dir(config_module)
            if isinstance(getattr(config_module, x), type)
            and issubclass(getattr(config_module, x), BaseConfig)
            and getattr(config_module, x).__module__ == config_module.__name__
        ]
        assert len(config_classes) == 1
        try:
            for step in config_classes[0](cases).return_iterator():
                steps.append(step)
        except BaseException as e:
            raise RuntimeError(f"Error reading {module_name}.{config_classes[0].__name__}") from e

    return sorted(steps, key=lambda x: x.step_name)


def get_dataset_info(dataset_uuid):
    response = proteus.api.get(f"/api/v1/datasets/{dataset_uuid}")
    dataset_json = response.json().get("dataset")
    workflow = dataset_json.get("workflow").get("workflow") or dataset_json.get("workflow").get("name")
    return dataset_json.get("bucket_url"), dataset_json.get("cases_url"), workflow


def get_cases(dataset_uuid, progress):
    progress.set_description("Retrieving cases and expected files")
    progress.refresh()

    cases_url = f"/api/v1/datasets/{dataset_uuid}/cases"
    response = proteus.api.get(cases_url)

    cases = response.json().get("cases")

    return sorted(cases, key=lambda d: d["root"])


def get_source(source_uri):
    for candidate in AVAILABLE_SOURCES:
        if candidate.accepts(source_uri):
            return candidate(source_uri)


@contextmanager
def _tmp_output_folder(bucket_url, temp_folder_override):
    tmpdirname = None
    try:
        tmpdirname = (
            tempfile.TemporaryDirectory(prefix="proteus-", suffix=bucket_url.split("/")[-1]).name
            if not temp_folder_override
            else temp_folder_override
        )
        os.makedirs(tmpdirname, exist_ok=True)

        yield tmpdirname

    finally:
        if tmpdirname and not temp_folder_override:
            shutil.rmtree(tmpdirname, ignore_errors=True)


def process_files(
    bucket,
    bucket_url,
    cases_url,
    steps,
    progress,
    workers=WORKERS_COUNT,
    replace=False,
    allow_missing_files=tuple(),
    temp_folder_override=False,
):

    # Create temporary folder
    with _tmp_output_folder(bucket_url, temp_folder_override) as tmpdirname:

        process_step_partial = generate_process_step_partial(
            progress,
            base_input_source=get_source(bucket),
            base_output_source=get_source(tmpdirname),
            cases_url=cases_url,
            allow_missing_files=allow_missing_files,
        )

        for step in proteus.bucket.each_item_parallel(
            total=len(steps), items=steps, each_item_fn=process_step_partial, workers=workers, progress=False
        ):
            proteus.reporting.send(
                f"Step finished: {step.step_name}",
                status="processing",
                progress=round(progress.n / progress.total, 0),
                number=progress.n,
                total=progress.total,
            )

        assert progress.n == progress.total


def generate_process_step_partial(
    progress, base_input_source: Source, base_output_source: LocalSource, cases_url: str, allow_missing_files=tuple()
):
    def step_partial(step: StepConfigWithMetadata):

        progress.set_description(step.step_name)
        progress.refresh()

        if not step.enabled:
            for _ in step.output:
                progress.update(1)
            return step

        if step.preprocessing_phase in (PREPROCESSING_PHASE_CASE, PREPROCESSING_PHASE_STEP):
            input_source = base_input_source.cd(step.root)
            output_source = base_output_source.cd(step.root)
        else:
            input_source = base_input_source
            output_source = base_output_source

        return process_step(
            progress,
            step,
            input_source=input_source,
            output_source=output_source,
            base_output_source=base_output_source,
            cases_url=cases_url,
            allow_missing_files=allow_missing_files,
        )

    return step_partial
