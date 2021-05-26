import boto3
import os
import re
from api import api
from config import config
import requests
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper
from common.logger import logger


def get_status(uuid):
    # ceba91e4-53ab-4dbb-8488-34ee655f2ce0
    response = api.get( f"/api/v1/jobs/{uuid}/status")
    response.raise_for_status()
    return response.json()
