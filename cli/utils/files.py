import datetime
import os
import platform
import re
from pathlib import Path
from threading import RLock

from cli import proteus
from cli.api.hooks import TqdmUpWithReport
from cli.utils.sync import TaskDependencySemaphore


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


DOWNLOAD_FILE_LOCK = RLock()
DOWNLOAD_FILE_SEMAPHORES = {}


def download_file(source_path, destination_path, input_source, progress: TqdmUpWithReport = None):
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

    # First, resolve which files have to be downloaded
    source_path = getattr(source_path, "clone", source_path.__class__)(source_path.replace("\\", "/"))
    destination_path = destination_path.replace("\\", "/")
    if "*" in source_path:
        prefix, suffix = source_path.split("*", 1)
        if "*" in suffix:
            raise RuntimeError("A file path can not include more than one glob symbol ('*')")
        items_and_paths = list(input_source.list_contents(starts_with=prefix, ends_with=suffix))

        if len(items_and_paths) > 1:
            globbed_paths = ",".join(str(x) for x in items_and_paths)
            full_path_not_found = input_source.join(input_source.subpath, source_path)
            error = f'"{full_path_not_found}" defines more than one file: {globbed_paths}'
            proteus.logger.error(error)
            proteus.reporting.send()
            raise RuntimeError(error)

        cannot_resolve_glob = (
            len(items_and_paths) > 1 or len(items_and_paths) == 0 and isinstance(source_path, RequiredFilePath)
        )
        if cannot_resolve_glob:
            full_path_not_found = input_source.join(input_source.subpath, source_path)
            error = f'Cannot find any file matching the following glob "{full_path_not_found}"'
            raise FileNotFoundError(error)

        assert len(destination_path.split("*")) in (1, 2)

        if items_and_paths:
            asterisk_replace_with = items_and_paths[0].path_rel
            if prefix:
                asterisk_replace_with = re.sub(rf"^{prefix}", "", asterisk_replace_with)
            if suffix:
                asterisk_replace_with = re.sub(rf"{suffix}$", "", asterisk_replace_with)

            transformed_source_path = source_path.replace("*", asterisk_replace_with)

            if "*" in destination_path:
                destination_path = destination_path.replace("*", asterisk_replace_with)

            proteus.logger.info(
                f'Glob "{source_path}" resolved to {items_and_paths[0].path}. '
                f"Output path rewritten to {destination_path}"
            )

        items_and_paths = iter(items_and_paths)
    else:
        assert "*" not in destination_path, "* can only be used in destionation path if also present in source_path"

        items_and_paths = input_source.list_contents(starts_with=source_path)
        transformed_source_path = source_path

    destination_path = os.path.abspath(destination_path)

    Path(os.path.dirname(destination_path)).mkdir(parents=True, exist_ok=True)

    # Create a semaphore for each file to be downloaded so that multiple download
    # processes for the same file cannot start at the same time.
    with DOWNLOAD_FILE_LOCK:
        file_semaphore = DOWNLOAD_FILE_SEMAPHORES.get(destination_path)
        if not file_semaphore:
            file_semaphore = TaskDependencySemaphore()
            DOWNLOAD_FILE_SEMAPHORES[destination_path] = file_semaphore

    try:
        file_semaphore.acquire()

        if os.path.isfile(destination_path):
            file_semaphore.release()
            return transformed_source_path, destination_path, True

        _, path, reference, size = next(items_and_paths)

        temp_dst_path = f"{destination_path}.tmp"

        if progress:
            progress.set_postfix({"downloading": reference.name})

        if not input_source.fastcopy(reference, temp_dst_path):
            Path(f"{destination_path}.tmp").touch()

            with open(f"{destination_path}.tmp", "wb") as file:
                for chunk in input_source.chunks(reference):
                    file.write(chunk)

        try:
            os.rename(temp_dst_path, destination_path)
        except FileNotFoundError:
            if not os.path.exists(destination_path):
                raise

        progress.set_postfix({})

        return transformed_source_path, destination_path, False
    except StopIteration:
        full_path_not_found = input_source.join(input_source.subpath, source_path)
        error = f"The following file was not found: {full_path_not_found}"
        if isinstance(source_path, RequiredFilePath):
            raise FileNotFoundError(error)
        return None, None, False
    finally:
        file_semaphore.release()


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
    file_path = Path(file_path)
    proteus.api.post_file(url, source_path, content=file_path, modified=modified, retry=False)


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


class PathMeta(str):
    download_name = None
    cloned_from = None
    full_path = None
    replace_with = None
    replaces = None

    def __new__(cls, value, download_name=None, cloned_from=None, full_path=None, replace_with=None):
        path_meta = str.__new__(cls, value)
        path_meta.download_name = download_name
        path_meta.cloned_from = cloned_from
        path_meta.full_path = full_path
        path_meta.replace_with = replace_with
        return path_meta

    def clone(self, value):
        cloned = self.__class__(
            value,
            download_name=self.download_name,
            cloned_from=self,
            full_path=self.full_path,
            replace_with=self.replace_with,
        )
        cloned.replaces = self.replaces
        return cloned


class RequiredFilePath(PathMeta):
    pass


class OptionalFilePath(PathMeta):
    pass
