import re
import sys

import click
from cli.api.decorators import may_fail_on_http_error  # noqa: E402
from cli.buckets.commands import buckets as buckets_commands
from cli.config import config
from cli.datasets.commands import datasets as datasets_commands
from cli.debugger.commands import debugger as debugger_commands
from cli.jobs.commands import jobs as jobs_commands
from cli.runtime import proteus
from cli.simulations.commands import simulations as simulations_commands
from cli.utils import sssh  # noqa: F401

ENTITY_INFO = next(
    (
        x.groupdict()
        for x in re.finditer(
            r"^/api/v[12]/(?P<entity_name>[^/]+)/(?P<entity_id>[a-fA-F0-9\-]+)/?$", config.ENTITY_URL or ""
        )
    ),
    {},
)

if ENTITY_INFO.get("entity_name") == "datasets" and ENTITY_INFO.get("entity_id"):
    proteus.logger.info(
        f"Obtaining {ENTITY_INFO['entity_name'].rstrip('s')} info for {ENTITY_INFO['entity_id']} from API"
    )
    with proteus.runs_authentified(user=config.USERNAME, password=config.PASSWORD):
        entity_info_from_server = proteus.api.get(config.ENTITY_URL).json()
        ENTITY_INFO["source_uri"] = entity_info_from_server["dataset"]["source_uri"]

        if not ENTITY_INFO["source_uri"]:
            proteus.logger.error(
                "The dataset specified in the ENTITY_URL is having no source_uri, or the source uri is incorrect"
            )
            exit(-1)

    sys.argv = sys.argv[:1]

    sys.argv.append(ENTITY_INFO.get("entity_name"))
    sys.argv.append("upload")
    sys.argv.append("--workers")
    sys.argv.append("1" if getattr(sys, "gettrace", lambda: None)() is not None else "8")  # One worker if CPU is
    sys.argv.append(ENTITY_INFO.get("source_uri"))
    sys.argv.append(ENTITY_INFO.get("entity_id"))

    log_command = "proteus-do " + " ".join(sys.argv[1:]).replace(
        ENTITY_INFO.get("source_uri"), ENTITY_INFO["source_uri"].split("?")[0] + "?CREDENTIALS=HIDDEN"
    )
    proteus.logger.info("Done, the cli will run the following command implicitly: \n  " + log_command)
    del log_command

    # FIXME: just necessary for the well model QA workflow. Remove when this can be passed from env variables
    for param in "-m SWL.GRDECL -m SWATINIT.GRDECL -m fipblk_05202014.grdecl".split(" "):
        sys.argv.append(param)


# Try to fill up args from env
@click.group()
@proteus.reporting.ensure_failed_is_reported
def main():
    """
    Simple CLI for PROTEUS auxiliary utils
    """
    pass


main.add_command(jobs_commands)
main.add_command(simulations_commands)
main.add_command(datasets_commands)
main.add_command(buckets_commands)
main.add_command(debugger_commands)


@main.command()
@click.option("--user", prompt=config.USERNAME is None, default=config.USERNAME)
@click.option("--password", prompt=config.PASSWORD is None, default=config.PASSWORD, hide_input=True)
@may_fail_on_http_error(exit_code=1)
def login(user, password):
    """Will perfom a login to test current credentials"""
    session = proteus.login(username=user, password=password, auto_update=False)
    click.echo(session.access_token_parsed)


if __name__ == "__main__":
    main()

__all__ = ["main"]
