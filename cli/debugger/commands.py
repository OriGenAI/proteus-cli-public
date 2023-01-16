import click

from cli.api.decorators import may_fail_on_http_error
from cli.config import config
from cli.runtime import proteus


@click.group()
def debugger():
    """
    Commands to manage debugger
    """


@debugger.command()
@click.option("--workers", prompt=config.PROMPT, default=config.WORKERS_COUNT)
@click.option("--iterations", prompt=config.PROMPT, default=config.STRESS_ITERATIONS)
@click.option("--user", prompt=config.USERNAME is None, default=config.USERNAME)
@click.option("--password", prompt=config.PASSWORD is None, default=config.PASSWORD, hide_input=True)
@click.argument("bucket")
@click.argument("parallel_method", default="threads")
@may_fail_on_http_error(exit_code=1)
@proteus.runs_authentified
def x_stress_test(
    bucket,
    parallel_method="threads",
    workers=config.WORKERS_COUNT,
    iterations=config.STRESS_ITERATIONS,
):
    """This stress tests init file downloading and download integrity,
    simulating the pre-training done by model runner"""
    from .init_keyword_check import keyword_check as init_keyword_check

    click.echo(
        init_keyword_check(
            bucket,
            ".X",
            parallel_method,
            workers=workers,
            iterations=iterations,
        )
    )


@debugger.command()
@click.option("--workers", prompt=config.PROMPT, default=config.WORKERS_COUNT)
@click.option("--iterations", prompt=config.PROMPT, default=config.STRESS_ITERATIONS)
@click.option("--user", prompt=True, default=config.USERNAME)
@click.option("--password", prompt=True, default=config.PASSWORD, hide_input=True)
@click.argument("bucket")
@click.argument("parallel_method", default="threads")
@may_fail_on_http_error(exit_code=1)
@proteus.runs_authentified
def init_stress_test(
    bucket,
    parallel_method="threads",
    workers=config.WORKERS_COUNT,
    iterations=config.STRESS_ITERATIONS,
):
    """This stress tests init file downloading and download integrity,
    simulating the training done by model runner"""
    from .init_keyword_check import keyword_check as init_keyword_check

    click.echo(
        init_keyword_check(
            bucket,
            ".INIT",
            parallel_method,
            workers=workers,
            iterations=iterations,
        )
    )
