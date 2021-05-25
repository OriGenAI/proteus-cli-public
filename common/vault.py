import requests
from config import config


VAULT_HOST = config.VAULT_HOST


class Vault:
    def __init__(self):
        self._vault_token = None

    def authenticate_with_jwt(self, auth):
        headers = {
            "Content-Type": "application/json",
        }
        url = "v1/auth/jwt-origen-workers/login"
        data = {"jwt": auth.access_token, "role": "worker"}
        response = requests.post(
            f"{VAULT_HOST}/{url}", headers=headers, json=data
        )
        response.raise_for_status()
        self._vault_token = response.json().get("auth").get("client_token")
        return self

    def set_token(self, token):
        self._vault_token = token
        return self

    def get_config(self, image_ref):
        assert (
            self._vault_token is not None
        ), "Should run authenticate_with_jwt() before"
        headers = {
            "X-Vault-Token": self._vault_token,
            "Content-Type": "application/json",
        }
        url = f"v1/secret/data/epyc-keys/{image_ref}"
        response = requests.get(f"{VAULT_HOST}/{url}", headers=headers)
        response.raise_for_status()
        return response.json().get("data")

    def save_config(self, image_ref, config):
        vault_token = self._vault_token
        headers = {
            "X-Vault-Token": vault_token,
            "Content-Type": "application/json",
        }
        url = f"v1/secret/data/epyc-keys/{image_ref}"
        response = requests.post(
            f"{VAULT_HOST}/{url}", headers=headers, json=dict(data=config)
        )
        print(response, response.json())
        response.raise_for_status()
        assert (
            response.status_code == 201
        ), "Cant confirm key assigment on vault"
        return response.json().get("data")
