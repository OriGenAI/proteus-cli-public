import datetime
import os
import platform
import time
from pathlib import Path

from tqdm import tqdm

from ... import proteus


def get_creation_date(path_to_file):
    """
    Calculate the creation date of a file in the system

    Args:
        path_to_file (string): Path of the file

    Returns:
        datetime: creation date of the file
    """
    if platform.system() == "Windows":
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return datetime.datetime.fromtimestamp(stat.st_birthtime)
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return datetime.datetime.fromtimestamp(stat.st_mtime)


def download_file(source_path, destination_path, source, progress=False):
    """
    Download a file from the allowed providers. Ex: local, az, etc.

    Args:
        source (string): The url from which we are going to
            download the file
        source_path (string): Path of the file inside the source
        destination_path (string): Path where we are going to
            save the file

    Returns: -
    """
    # Preserve RequiredFilePath with input.__class__
    source_path = source_path.__class__(source_path.replace("\\", "/"))
    destination_path = destination_path.replace("\\", "/")
    if "*" in source_path:
        prefix, suffix = source_path.split("*", 1)
        if "*" in suffix:
            raise RuntimeError("A file path can not include more than one glob symbol ('*')")
        items_and_paths = list(source.list_contents(starts_with=prefix, ends_with=suffix))

        if len(items_and_paths) > 1:
            globbed_paths = ",".join(str(x) for x in items_and_paths)
            raise RuntimeError(f'"f{source_path}" defines more than one file: {globbed_paths}')

        if len(items_and_paths) != 1:
            raise FileNotFoundError(f'Cannot resolve glob "{source_path}"')

        assert len(destination_path.split("*")) in (1, 2)

        glob_replacement_in_destination_path = suffix.join(
            items_and_paths[0].path.split(prefix, 1)[1].split(suffix)[:-1]
        )

        if "*" in destination_path:
            destination_path_parts = destination_path.split("*")
            destination_path = (
                destination_path_parts[0] + glob_replacement_in_destination_path + destination_path_parts[1]
            )

        if "*" in source_path:
            transformed_source_path = prefix + glob_replacement_in_destination_path + suffix
        else:
            transformed_source_path = source_path

        proteus.logger.info(
            f'Glob "{source_path}" resolved to {items_and_paths[0]}. Output path rewritten to f{destination_path}'
        )

        items_and_paths = iter(items_and_paths)

    else:
        items_and_paths = source.list_contents(starts_with=source_path)
        transformed_source_path = source_path

    path_list = destination_path.split("/")[0:-1]
    Path("/".join(path_list)).mkdir(parents=True, exist_ok=True)

    if os.path.isfile(destination_path):
        return transformed_source_path, destination_path
    elif os.path.isfile(f"{destination_path}.tmp"):
        wait_until_file_is_downloaded(destination_path)
        return transformed_source_path, destination_path
    else:
        try:
            _, path, reference, size = next(items_and_paths)

            destination_file = f"{destination_path}.tmp"

            if not source.fastcopy(reference, destination_file):
                Path(f"{destination_path}.tmp").touch()

                if callable(size):
                    size = callable(size)

                with open(f"{destination_path}.tmp", "wb") as file:
                    with tqdm(
                        total=size,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        desc=f"Retrieving file {path}",
                        disable=not progress,
                    ) as pbar:
                        read = 0
                        for chunk in source.chunks(reference):
                            file.write(chunk)
                            read += len(chunk)
                            pbar.update(len(chunk))

                        pbar.set_description("Done")

            os.rename(f"{destination_path}.tmp", destination_path)

            return transformed_source_path, destination_path
        except StopIteration:
            if isinstance(source_path, RequiredFilePath):
                raise FileNotFoundError(f"Required file {source_path} is not found")
            proteus.logger.error(f"The following file was not found: {source_path}")


@proteus.may_insist_up_to()
def upload_file(source_path, file_path, url):
    """
    Upload a file to proteus

    Args:
        source_path (string): Path of the file inside proteus
        file_path (string): Path of the file in the local system
        bucket_uuid (string): Uuid of the proteus bucket

    Returns: -
    """
    modified = get_creation_date(file_path)
    with open(file_path, "rb") as file_content:
        proteus.api.post_file(url, source_path, content=file_content, modified=modified, retry=False)
    try:
        if not os.path.isdir(file_path):
            os.remove(file_path)
    except Exception:
        pass


""" Destructuring helper function of an object """


def pluck(dict, *args):
    return (dict.get(arg, None) for arg in args)


def find_ext(case_loc, ext, required=False, one=False, first=True, last=False):
    """
    Finds if file exists in the directory
    Args:
        case_loc (string): Path of the folder
        ext (string): Extension of the file to find
        required (bool): Fails if no file is found
        one (bool): Fails if more than one file is found
        first (bool): sort files alphabetically and returns the first
        last (bool): sort files alphabetically and returns the last

    Returns: file_path (string): Path of the file if exists
    """
    files = list(Path(case_loc).rglob(f"*.{ext}"))

    if (one or required) and len(files) == 0:
        raise FileNotFoundError(os.path.join(case_loc, f"*.{ext}"))

    if one and len(files) > 1:
        raise FileNotFoundError(
            f"More than one file for {os.path.join(case_loc, f'*.{ext}')}: {','.join(str(x) for x in files)}"
        )

    if last or first:
        files = sorted(files)

    if last:
        files = [next(iter(reversed(files)), None)]

    if first:
        files = [next(iter(files), None)]

    return next(iter(files), None)


def find_file(case_loc, name):
    """
    Finds if file exists in the directory
    Args:
        case_loc (string): Path of the folder
        name (string): File name plus extension

    Returns: file_path (string): Path of the file if exists
    """
    return next(Path(case_loc).rglob(name))


def wait_until_file_is_downloaded(file_path, period=5, timeout=500):
    """
    Waits until the file is completely downloaded
    Args:
        case_loc (string): Path of the folder
        ext (string): Extension of the file to find

    Returns: file_path (string): Path of the file if exists
    """
    mustend = time.time() + timeout
    while time.time() < mustend:
        try:
            with open(file_path, "rb") as _:
                return True
        except FileNotFoundError:
            time.sleep(period)
    return False


def get_case_info(case_url):
    r = proteus.api.get(case_url)
    return r.json().get("case")


class PathMeta(str):
    download_name = None
    cloned_from = None
    full_path = None

    def __new__(cls, value, download_name=None, cloned_from=None, full_path=None):
        path_meta = str.__new__(cls, value)
        path_meta.download_name = download_name
        path_meta.cloned_from = cloned_from
        path_meta.full_path = full_path
        return path_meta

    def clone(self, value):
        return self.__class__(value, download_name=self.download_name, cloned_from=self)


class RequiredFilePath(PathMeta):
    pass
