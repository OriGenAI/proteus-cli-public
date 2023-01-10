import datetime
import os
import platform
import time
from pathlib import Path

from ..upload import get_source
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


def download_file(source_path, destination_path, source_url):
    """
    Download a file from the allowed providers. Ex: local, az, etc.

    Args:
        source_url (string): The url from which we are going to
            download the file
        source_path (string): Path of the file inside the source
        destination_path (string): Path where we are going to
            save the file

    Returns: -
    """
    source = get_source(source_url)
    source_path = source_path.replace("\\", "/")
    destination_path = destination_path.replace("\\", "/")
    items_and_paths = source.list_contents(starts_with=source_path)

    path_list = destination_path.split("/")[0:-1]
    Path("/".join(path_list)).mkdir(parents=True, exist_ok=True)

    if os.path.isfile(destination_path):
        return
    elif os.path.isfile(f"{destination_path}.tmp"):
        wait_until_file_is_downloaded(destination_path)
    else:
        Path(f"{destination_path}.tmp").touch()

        try:
            _, _, reference = next(items_and_paths)

            stream = source.download(reference)

            with open(f"{destination_path}.tmp", "wb") as file:
                file.write(stream)

            # FIXME: Having issues with local files
            # with open(f"{destination_path}.tmp", "wb") as file:
            #     for chunk in source.chunks(reference):
            #         file.write(chunk)

            os.rename(f"{destination_path}.tmp", destination_path)
        except StopIteration:
            proteus.logger.info(f"The following file was not found: {source_path}")


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
        proteus.api.post_file(
            url,
            source_path,
            content=file_content,
            modified=modified,
        )
    try:
        if not os.path.isdir(file_path):
            os.remove(file_path)
    except Exception:
        pass


""" Destructuring helper function of an object """


def pluck(dict, *args):
    return (dict.get(arg, None) for arg in args)


def find_ext(case_loc, ext):
    """
    Finds if file exists in the directory
    Args:
        case_loc (string): Path of the folder
        ext (string): Extension of the file to find

    Returns: file_path (string): Path of the file if exists
    """
    return next(Path(case_loc).rglob(f"*.{ext}"))


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
