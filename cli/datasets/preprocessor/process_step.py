import glob
import inspect
import os
import shutil
from collections import OrderedDict

from . import preprocess_functions
from .utils import pluck, upload_file, download_file, PathMeta
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
        continue_if_missing,
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
        "continue_if_missing",
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

    def process_input(input):
        # Preserve RequiredFilePath with input.__class__
        source_path = getattr(input, "clone", input.__class__)(f"/{input}")
        try:
            transformed_input, output_path = download_file(source_path, os.path.join(tmpdirname, str(input)), source)
        except FileNotFoundError:
            transformed_input, output_path = None, None

        if transformed_input is None and getattr(input, "replace_with", None) is not None:
            transformed_input, output_path = process_input(input.replace_with)
            transformed_input.replaces = input
        elif transformed_input is not None:
            transformed_input = getattr(input, "clone", lambda x: PathMeta(x, download_name=input))(transformed_input)
        else:
            transformed_input = input

        return transformed_input, output_path

    for transformed_input, output_path in proteus.bucket.each_item_parallel(
        total=len(inputs), items=inputs, each_item_fn=process_input, workers=download_workers
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

    # Upload the files
    for output in outputs:
        upload_file(output, os.path.join(tmpdirname, output), cases_url)

    return outputs
