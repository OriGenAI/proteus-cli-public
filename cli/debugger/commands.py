import click
from cli.config import config
from api import runs_authentified
from api.decorators import may_fail_on_http_error


@click.group()
def debugger():
    """
    Commands to manage debugger
    """


@debugger.command()
@click.option("--workers", prompt=config.PROMPT, default=config.WORKERS_COUNT)
@click.option("--iterations", prompt=config.PROMPT, default=config.STRESS_ITERATIONS)
@click.argument("bucket")
@may_fail_on_http_error(exit_code=1)
@runs_authentified
def init_stress_test(bucket, workers=config.WORKERS_COUNT, iterations=config.STRESS_ITERATIONS):
    """This stress tests init file downloading and download integrity, simulating the preprocessing done by model runner"""
    from .init_keyword_check import keyword_check as init_keyword_check

    click.echo(init_keyword_check(bucket, workers=workers, iterations=iterations))

@debugger.command()
@click.option("--workers", prompt=config.PROMPT, default=config.WORKERS_COUNT)
@click.option("--iterations", prompt=config.PROMPT, default=config.STRESS_ITERATIONS)
@click.argument("bucket")
@click.argument("dataset_uuid")
@may_fail_on_http_error(exit_code=1)
@runs_authentified
def restart_stress_test(bucket, dataset_uuid, workers=config.WORKERS_COUNT, iterations=config.STRESS_ITERATIONS):
    """This stress tests restart file downloading and download itegrity, simulating the model runner training process"""
    from .restart_keyword_check import keyword_check as restart_keyword_check
    
    click.echo(restart_keyword_check(bucket, dataset_uuid, workers=workers, iterations=iterations))