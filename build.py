import click
from config import config
import os
from common.safe import generate_aes_cipher, Safely, protect_path
from common.vault import Vault

PROMPT = config.PROMPT


@click.group()
def main():
    """
    Simple CLI for PROTEUS Worker building utils
    """
    pass


def arrange_keys(vault, image_ref, generate):
    safely = Safely()
    previous_config = vault.get_config(image_ref).get("data")
    if generate is True:
        if previous_config is not None:
            print(f"replacing existing key for {image_ref}")
        new_config = dict(cipher=generate_aes_cipher())
        print("created a config:")
        print(new_config)
        safely.set_config(new_config)
        vault.save_config(image_ref, new_config)
    else:
        if previous_config is None:
            raise Exception(
                "No key found on vault set generate "
                "arguement to create a new one"
            )
        print("using found config", previous_config)
        safely.set_config(previous_config)
    return safely


@main.command()
@click.option("--path", prompt=PROMPT, default="private")
@click.option("--target", prompt=PROMPT, default="private-secured")
@click.option("--generate", prompt=PROMPT, default=False)
def protect(path, target, generate):
    """Will create a secured copy of the folder's modules and upload
    the config to vault"""
    assert (
        "VAULT_TOKEN" in os.environ
    ), "VAULT_TOKEN env var should be set before continue"
    token = os.getenv("VAULT_TOKEN")
    assert (
        "CURRENT_IMAGE" in os.environ
    ), "CURRENT_IMAGE env var should be set before continue"
    image_ref = os.getenv("CURRENT_IMAGE")
    vault = Vault().set_token(token)
    safely = arrange_keys(vault, image_ref, generate)
    protect_path(safely, path, target)


if __name__ == "__main__":
    main()
