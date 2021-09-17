import os
from api import api
from tqdm import tqdm
from datetime import datetime
from dateutil import tz


def create_batch(model_uuid, name=None):
    simulations_url = "api/v1/simulations/batches"
    new_simulation = dict(model_uuid=model_uuid, name=name)
    response = api.post(simulations_url, new_simulation)
    assert (
        response.status_code == 201
    ), f"Expectend batch to be created but got {response.content}"
    simulation = response.json().get("batch")
    return simulation.get("uuid")


def get_batch(batch_uuid, name=None):
    simulations_batch_url = f"api/v1/simulations/{batch_uuid}"
    response = api.get(simulations_batch_url)
    assert "simulation_batch" in response.json()
    return response.json().get("simulation_batch"), simulations_batch_url


def upload_file_to_batch(url, source_path, filepath):
    try:
        modification_ts = os.path.getmtime(source_path)
        modified = datetime.fromtimestamp(modification_ts, tz.tzlocal())
        with open(source_path, "rb") as source:
            response = api.post_file(
                url, filepath, content=source, modified=modified
            )
            response_json = response.json()
            # print('upload', source_path, 'as', filepath, response_json)
            # from pprint import pprint
            # print('uploaded', pprint(response_json))
            assert "case" in response_json
            return response_json.get("case")
    except FileNotFoundError:
        print(f"File not found: {source_path}")
        return False


def find_files(source_folder, extension):
    for root, dirs, files in os.walk(source_folder):
        for file_ in files:
            if file_.endswith(extension):
                yield os.path.join(root, file_)


def provide_case_dependencies(
    simulations_batch_url, dependencies, source_folder
):
    dependencies_progress = tqdm(dependencies, leave=False)
    for dependency_item in dependencies_progress:
        if dependency_item.get("status") == "solved":
            continue
        filepath = dependency_item.get("path")
        source_path = f"{source_folder}/{filepath}"
        dependencies_progress.set_description(
            f"uploading dependency {filepath}"
        )
        upload_file_to_batch(simulations_batch_url, source_path, filepath)


def provide_batch_initial_state(batch_url, missing_expression, source_folder):
    extension = missing_expression.replace("*", "")
    for source_path in find_files(source_folder, extension):
        filepath = source_path.replace(f"{source_folder}/", "")
        upload_file_to_batch(batch_url, source_path, filepath)
    else:
        return False
    return True


def provide_batch_dependencies(batch_url, dependencies, source_folder):
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
    print(f"name: {batch['name']}")
    print(f"uuid: {batch['uuid']}")
    print(f"status: {batch['status']}")
    dependencies = batch.get("pending_dependencies")
    if len(dependencies) > 0:
        print("missing dependencies:")
        for dependency in dependencies:
            print("*", dependency)


def upload_to_batch(source_folder, batch_uuid):
    batch, batch_url = get_batch(batch_uuid)
    datafiles_progress = tqdm(find_files(source_folder, ".DATA"))
    for source_path in datafiles_progress:
        filepath = source_path.replace(f"{source_folder}/", "")
        datafiles_progress.set_description(f"uploading DATA {filepath}")
        case = upload_file_to_batch(batch_url, source_path, filepath)
        assert "dependencies" in case
        dependencies = case.get("dependencies")
        provide_case_dependencies(batch_url, dependencies, source_folder)
    batch, batch_url = get_batch(batch_uuid)
    dependencies = batch.get("pending_dependencies", [])
    provide_batch_dependencies(batch_url, dependencies, source_folder)
    batch, _ = get_batch(batch_uuid)
    report_batch_status(batch)
