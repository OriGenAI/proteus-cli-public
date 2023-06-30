import glob
import inspect
import os
import shutil
from collections import OrderedDict
from contextlib import contextmanager, ExitStack
from threading import RLock
from typing import Iterator, Union

from . import preprocess_functions
from .config import StepConfigWithMetadata
from .utils import pluck, upload_file, download_file, PathMeta, RequiredFilePath
from ..sources.common import Source
from ..sources.local import LocalSource
from ... import proteus, config


def files_exist_in_bucket(outputs, bucket_url):
    for output in outputs:
        response = proteus.api.get(bucket_url, headers={}, stream=False, contains=output, retry=True)
        files = response.json().get("results")
        if len(files) == 0:
            return False

    return True


def process_step(
    step,
    tmpdirname,
    source,
    bucket_url,
    cases_url,
    replace=False,
    allow_missing_files=tuple(),
    download_workers=config.WORKERS_DOWNLOAD_COUNT,
):

    (
        inputs,
        outputs,
        preprocessing_function_name,
        split,
        case,
        keep,
        additional_info,
        post_processing_info,
        post_processing_function_name,
    ) = pluck(
        step,
        "input",
        "output",
        "preprocessing",
        "split",
        "case",
        "keep",
        "additional_info",
        "post_processing_info",
        "post_processing_function_name",
    )

    additional_info = additional_info or {}

    if not replace and files_exist_in_bucket(outputs, bucket_url):
        return outputs

    if "cases/SIMULATION_" in outputs[0]:
        path_name = os.path.join(tmpdirname, "cases", f"SIMULATION_{case}")
    else:
        path_name = os.path.join(tmpdirname, "cases", f"{split}/SIMULATION_{case}") if (split and case) else tmpdirname
    os.makedirs(path_name, exist_ok=True)

    # Download the required files. Keep the file if necessary
    downloaded_inputs = OrderedDict()

    for transformed_input, output_path in proteus.bucket.each_item_parallel(
        total=len(inputs), items=inputs, each_item_fn=download_input_file, workers=download_workers
    ):
        if output_path:
            downloaded_inputs.setdefault(getattr(transformed_input, "download_name", transformed_input), []).append(
                output_path
            )

    # Process the files
    func = getattr(preprocess_functions, preprocessing_function_name)
    func_input = None
    if len(inputs) > 1:
        func_input = downloaded_inputs
    if len(inputs) == 1:
        download_name, output_path = next(iter(downloaded_inputs.items()), (inputs[0], None))
        if output_path and len(output_path) == 1:
            output_path = output_path[0]

        func_input = PathMeta(download_name, download_name=download_name, full_path=output_path)

    # Parameters not fully supported by old preprocessing configurations
    fn_args = set(inspect.getfullargspec(func).args).union(inspect.getfullargspec(func).kwonlyargs)
    if "allow_missing_files" in fn_args:
        additional_info["allow_missing_files"] = list(allow_missing_files)

    if continue_if_missing:
        additional_info.setdefault("allow_missing_files", []).extend(continue_if_missing)

    if "base_dir" in fn_args:
        additional_info["base_dir"] = tmpdirname

    source_dir, _, output = func(
        path_name,
        path_name,
        func_input,
        source,
        cases_url,
        **(additional_info or {}),
    )

    # Post-Process the files
    if post_processing_function_name:
        post_func = getattr(preprocess_functions, post_processing_function_name)
        post_func(
            os.path.join(tmpdirname, "cases"),
            output,
            bucket_url,
            **post_processing_info,
        )

    # Delete not necessary files
    if (not keep) and source_dir:
        fileList = glob.glob(str(source_dir))
        for filePath in fileList:
            try:
                if os.path.isdir(filePath):
                    shutil.rmtree(filePath)
                else:
                    os.remove(filePath)
            except Exception:
                pass

    def upload_output(output):
        return upload_file(output, os.path.join(tmpdirname, output), cases_url)

    # Upload the files
    # for _ in proteus.bucket.each_item_parallel(
    #     total=len(outputs), items=outputs, each_item_fn=upload_output, workers=download_workers, progress=False
    # ):
    #     pass

    for output in outputs:
        upload_output(output)

    return outputs


def process_step_2(
    progress,
    step: StepConfigWithMetadata,
    input_source: Source,
    output_source: LocalSource,
    cases_url,
    base_output_source: LocalSource,
):

    with ExitStack() as lock_input_files:
        # Download inputs
        files = OrderedDict()
        for input_file in step.input:
            found_input = lock_input_files.enter_context(download_input_file(input_file, input_source, output_source, step.keep))
            files[found_input.download_name or input_file] = found_input

        # Preprocess inputs
        if step.preprocessing_fn:
            def download_func(dependency_file, dir_path):
                subpath = output_source.to_relative(dir_path)
                local_input_source = input_source.cd(subpath)
                local_output_source = output_source.cd(subpath)

                return lock_input_files.enter_context(download_input_file(dependency_file, local_input_source, local_output_source, step.keep)).full_path

            step.preprocessing_fn(
                download_func=download_func,
                output_source=output_source,
                base_output_source=base_output_source,
                **{**files}
            )

        # Find and upload outputs
        found_outputs = []
        for output in step.output:
            found_output_files = list(output_source.list_contents(output))
            if len(found_output_files) != 1 and isinstance(output, RequiredFilePath):
                raise FileNotFoundError(f'Output {output} was suposed to be generated by {step.name} from {step.root}, but the file was not found.')

            found_output = found_output_files[0]
            found_outputs.append(output)
            upload_file(base_output_source.to_relative(found_output.path), found_output.path, cases_url)
            progress.set_description(step.step_name)
            progress.update(1)
            progress.refresh()

    return found_outputs



INPUT_FIND_LOCKS = {}
CREATE_INPUT_FILE_LOCK = RLock()


@contextmanager
def download_input_file(input_file: Union[PathMeta, str], input_source: Source, output_source: LocalSource, keep: bool) -> Iterator[PathMeta]:
    if not isinstance(input_file, PathMeta):
        input_file = PathMeta(input_file)

    dir_output_file = os.path.join(output_source.uri, input_file)

    lock_key = (input_source.uri, input_file)
    file_lock = None
    with CREATE_INPUT_FILE_LOCK:
        file_lock = next(iter(INPUT_FIND_LOCKS.get(lock_key, [None]) or [None]))

        if file_lock is None:
            file_lock = RLock()

        INPUT_FIND_LOCKS.setdefault(lock_key, []).append(file_lock)

    with file_lock:
        # Try to download the file
        try:
            transformed_input, output_path = download_file(input_file, dir_output_file, input_source)
        except FileNotFoundError:
            transformed_input = None
            # Try to download the replacement if the file was not found
            try:
                if input_file.replace_with is not None:
                    transformed_input = download_input_file(output_source, input_file.replace_with, input_source)
            except FileNotFoundError:
                pass

            if transformed_input is None:
                raise

        if transformed_input is not None:
            transformed_input = input_file.clone(transformed_input)
            transformed_input.full_path = output_path
        else:
            transformed_input = input_file

        yield transformed_input

        if not keep:
            os.remove(output_path)

        with CREATE_INPUT_FILE_LOCK:
            INPUT_FIND_LOCKS[lock_key].pop()
