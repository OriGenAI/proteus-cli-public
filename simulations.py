import boto3
import os
import re
from api import api
from config import config
import requests
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper
from common.logger import logger
from datetime import datetime, timezone
from dateutil import tz
import os


def create_batch(model_uuid, name=None):
    simulations_url = "api/v1/simulations/batches"
    new_simulation = dict(model_uuid=model_uuid, name=name)
    response = api.post(simulations_url, new_simulation)
    assert response.status_code == 201, f"Expectend batch to be created but got {response.content}"
    simulation = response.json().get("batch")
    return simulation.get('uuid')


def upload_file_to_batch(url, source_path, filepath):
    modification_ts = os.path.getmtime(source_path)
    modified = datetime.fromtimestamp(modification_ts, tz.tzlocal())
    with open(source_path) as source:
        response = api.post_file(url, filepath, content=source, modified=modified)
        response_json = response.json()
        print('upload', source_path, 'as', filepath, response_json)
        assert 'case' in response_json
        return response_json.get('case')


def upload_to_batch(source_folder, batch_uuid):
    simulations_batch_url = f"api/v1/simulations/{batch_uuid}"
    response = api.get(simulations_batch_url)
    assert response.status_code == 200, f"Expectend batch to be created but got {response.content}"
    assert 'simulation_batch' in response.json()
    batch = response.json().get("simulation_batch")
    for root, dirs, files in os.walk(source_folder):
        print('root', root, 'dirs', dirs)
        for file_ in files:
            if file_.endswith(".DATA"):
                source_path = os.path.join(root, file_)
                filepath = source_path.replace(source_folder + '/', '')
                case = upload_file_to_batch(simulations_batch_url, source_path, filepath)
                assert 'dependencies' in case
                dependencies = case.get('dependencies')
                print(f"{filepath} has {len(dependencies)} pending dependencies")
                for dependency_item in dependencies:
                    filepath = dependency_item.get('path')
                    source_path = f"{source_folder}/{filepath}"
                    upload_file_to_batch(simulations_batch_url, source_path, filepath)
