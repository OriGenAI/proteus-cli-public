import os
import glob
import shutil

from proteus import api
from . import preprocess_functions
from .utils import pluck, upload_file, download_file


def files_exist_in_bucket(outputs, bucket_url):
    result = False
    for output in outputs:
        response = api.get(
            bucket_url, headers={}, stream=False, contains=output
        )
        files = response.json().get("results")
        result = len(files) > 0

    return result


def process_step(step, tmpdirname, source_url, bucket_url, cases_url):
    try:
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

        if files_exist_in_bucket(outputs, bucket_url):
            return outputs[0]

        if "cases/SIMULATION_" in outputs[0]:
            path_name = os.path.join(tmpdirname, "cases", f"SIMULATION_{case}")
        else:
            path_name = (
                os.path.join(tmpdirname, "cases", f"{split}/SIMULATION_{case}")
                if (split and case)
                else tmpdirname
            )
        try:
            os.makedirs(path_name)
        except Exception:
            pass

        # Download the required files. Keep the file if necessary
        for input in inputs:
            download_file(
                f"/{input}", os.path.join(tmpdirname, input), source_url
            )

        # Process the files
        func = getattr(preprocess_functions, preprocessing_function_name)
        func_input = None
        if len(inputs) > 1:
            func_input = inputs
        if len(inputs) == 1:
            func_input = inputs[0]

        source_dir, _, output = func(
            path_name,
            path_name,
            func_input,
            source_url,
            cases_url,
            **(additional_info or {}),
        )

        # Post-Process the files
        if post_processing_function_name:
            post_func = getattr(
                preprocess_functions, post_processing_function_name
            )
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

        return output
    except Exception:
        pass
