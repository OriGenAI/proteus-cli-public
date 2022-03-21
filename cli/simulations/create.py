import os
from api import api
from tqdm import tqdm
from datetime import datetime
from dateutil import tz
from cli.config import config
from cli.simulations.dependencySolver import DependencySolver
from reporting import Reporting

WORKERS_COUNT = config.WORKERS_COUNT


def create_batch(
    project_uuid, pressure_model_uuid, swat_model_uuid, batch_name
):
    """[summary]

    Args:
        project_uuid (string): the UUID of the project this
            new batch will belong to
        pressure_model_uuid (string): the UUID of the
            pressure model
        swat_model_uuid (string): the UUID of the
            swat model
        batch_name (string): The name of this simulation batch.

    Returns:
        string: the UUID of the newly created simulation batch
    """
    simulations_url = "api/v1/simulations"

    # CREATE BATCH
    new_simulation = dict(name=batch_name, project_uuid=project_uuid)
    response = api.post(f"{simulations_url}/batches", new_simulation)
    assert (
        response.status_code == 201
    ), f"Expectend batch to be created but got {response.content}"
    simulation = response.json().get("batch")
    batch_uuid = simulation.get("uuid")
    Reporting.info("Simulation batch creation successful")

    # UPDATE BATCH WITH MODELS
    sim_batch_url = f"{simulations_url}/{batch_uuid}"
    mod_simulation = dict(
        pressure_model_uuid=pressure_model_uuid,
        swat_model_uuid=swat_model_uuid,
        set_status="typed",
    )
    response = api.put(sim_batch_url, mod_simulation)
    assert (
        response.status_code == 200
    ), f"Expectend batch to be created but got {response.content}"
    Reporting.info("Simulation batch models updated")
    return batch_uuid


def get_batch(batch_uuid):
    """Gets the batch with the given UUID

    Args:
        batch_uuid (string): the UUID of the batch
    Returns:
        (dict, string): the simulation batch object,
            the url for this simulation batch
    """
    simulations_batch_url = f"api/v1/simulations/{batch_uuid}"
    response = api.get(simulations_batch_url)
    assert "simulation_batch" in response.json()
    return response.json().get("simulation_batch"), simulations_batch_url


def upload_file_to_batch(url, source_path, filepath):
    """Uploads the given file to the url

    Args:
        url (string): the url to upload to
        source_path (string): the source path for this file (locally)
        filepath (string): the dest path for this file (remote location)

    Returns:
        string: the response for the upload request
    """
    try:
        modification_ts = os.path.getmtime(source_path)
        modified = datetime.fromtimestamp(modification_ts, tz.tzlocal())
        with open(source_path, "rb") as source:
            response = api.post_file(
                url, filepath, content=source, modified=modified
            )
            response_json = response.json()
            assert "case" in response_json
            return response_json.get("case")
    except FileNotFoundError:
        print(f"File not found: {source_path}")
        return False


def find_files(source_folder, extension):
    """Finds all files that have the extension within the source folder

    Args:
        source_folder (string): the source folder location
        extension (string): the file extension to filter for

    Yields:
        string: a filepath with this extension
    """
    for root, dirs, files in os.walk(source_folder):
        for file_ in files:
            if file_.endswith(extension):
                yield os.path.join(root, file_)


def provide_batch_initial_state(batch_url, missing_expression, source_folder):
    extension = missing_expression.replace("*", "")
    for source_path in find_files(source_folder, extension):
        filepath = source_path.replace(f"{source_folder}/", "")
        upload_file_to_batch(batch_url, source_path, filepath)
    else:
        return False
    return True


def provide_batch_dependencies(batch_url, dependencies, source_folder):
    """Loops through all batch dependencies and uploads to the batch input folder

    Args:
        batch_url (string): the batch input bucket url to upload to
        dependencies (list): a list of file dependencies
        source_folder (string): the source folder path
    """
    dependencies_progress = tqdm(dependencies, leave=False)
    missing_count = 0
    for filepath in dependencies_progress:
        dependencies_progress.set_description(
            f"uploading dependency {filepath}"
        )
        provided = False
        if filepath in ["*.X0000", "*.EGRID"]:
            provided = provide_batch_initial_state(
                batch_url, filepath, source_folder
            )
        else:
            source_path = f"{source_folder}/{filepath}"
            provided = upload_file_to_batch(batch_url, source_path, filepath)
        if not provided:
            missing_count += 1
            dependencies_progress.set_description(
                f"cant provide any {filepath}"
            )
            dependencies_progress.set_postfix({"missing": missing_count})


def report_batch_status(batch):
    """Prints the batch's status on the terminal

    Args:
        batch (string): The batch object
    """
    print(f"name: {batch['name']}")
    print(f"uuid: {batch['uuid']}")
    print(f"status: {batch['status']}")
    dependencies = batch.get("pending_dependencies")
    if len(dependencies) > 0:
        print("missing dependencies:")
        for dependency in dependencies:
            print("*", dependency)


def parse_path(source_folder, source_path):
    """Parse file path
    Arguments:
        source_folder {string}: the folder that holds
            all batch cases
        source_path {string}: the path of the case
    Returns:
        parsed_path {string}: the new parsed path of the case
        has_case_folder {bool}: boolean indicating if
            the `case` folder was removed
    """
    # Remove `cases` from source_path if exists
    has_case_folder = source_folder.endswith("/cases")
    if has_case_folder:
        source_path = source_path.replace("cases/", "")

    # Get source folder string without last folder
    to_replace = source_folder.split("/")
    to_replace = to_replace[:-1]
    to_replace = "/".join(to_replace)

    return source_path.replace(f"{to_replace}/", ""), has_case_folder


def upload_to_batch(source_folder, batch_uuid, reupload):
    """Uploads each data file to generate a case.
    For each case, find the depndencies and upload them as well.
    Finally, find and upload any pending batch dependencies

    Args:
        source_folder (string): the folder that holds all batch cases
        batch_uuid (string): the UUID for this batch
        reupload (bool): flag to know if we should reupload all files
    """
    batch, batch_url = get_batch(batch_uuid)
    datafiles_progress = tqdm(find_files(source_folder, ".DATA"))
    for source_path in datafiles_progress:
        # Upload the .DATA file
        filepath, has_case_folder = parse_path(source_folder, source_path)
        datafiles_progress.set_description(f"uploading DATA {filepath}")
        case = upload_file_to_batch(batch_url, source_path, filepath)

        # Solve all dependencies
        if "dependencies" in case:
            dependencies = case.get("dependencies")
            number = case.get("number")
            dependencySolver = DependencySolver(
                batch_url,
                dependencies,
                number,
                source_folder,
                has_case_folder,
                reupload,
            )
            dependencySolver.solve_dependencies()

    # Upload any pending dependency
    batch, _ = get_batch(batch_uuid)
    report_batch_status(batch)
