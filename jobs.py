from api import api
import requests


def get_status(uuid):
    response = api.get(f"/api/v1/jobs/{uuid}/status")
    response.raise_for_status()
    return response.json()
