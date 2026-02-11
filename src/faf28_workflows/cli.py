#! /usr/bin/env python3
"""Command-line interface for the pipeline."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from faf28_workflows.flows.central_dag_runner import CentralDagRunner, central_dag_flow
from faf28_workflows.flows.dag_visualization import print_dag_diagram, print_dag_mermaid, dag_to_string
from faf28_workflows.flows.run_params_class import RunParams
from utils.utils import shrug


def get_logging_level_names():
    return list(logging.getLevelNamesMapping().keys())

def configure_logging(log_level: str) -> None:
    """Configure logging based on the specified level."""
    logging.disable(logging.NOTSET)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    numeric_level = logging.getLevelNamesMapping().get(log_level.upper(), "unrecognized")
    if numeric_level == "unrecognized":
        shrug("Logging level {} not recognized, setting log level to ERROR")
        numeric_level = logging.ERROR

    # Remove all existing handlers to ensure basicConfig takes effect
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    logging.basicConfig(level=numeric_level,format="%(asctime)s - [%(filename)s:%(lineno)d] - %(name)s - %(levelname)s - %(message)s", force=True)
    logging.getLogger("prefect").setLevel(numeric_level)


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option(
    "--log-level", "-l",
    type=click.Choice(get_logging_level_names()),
    default="INFO",
    help="Set logging level.",
)
@click.pass_context
def main(
        ctx: click.Context,
        log_level: str,
) -> None:
    """
    FAF analysis pipeline  CLI.
    """
    configure_logging(log_level)

    ctx.ensure_object(dict)
    ctx.obj["log_level"] = log_level
    ctx.obj["runner"] = CentralDagRunner(log_level=log_level)

@main.command()
@click.pass_context
def list_jobs(ctx: click.Context) -> None:
    """List all available jobs in the pipeline."""
    runner: CentralDagRunner = ctx.obj["runner"]

    click.echo("Available jobs:")
    for i, name in enumerate(runner.available_nodes, 1):
        click.echo(f"  {i}. {name}")


@main.command()
@click.pass_context
def draw_dag(ctx: click.Context) -> None:
    """Draw DAG for the whole pipeline"""
    runner: CentralDagRunner = ctx.obj["runner"]

    click.echo("DAG for the whole pipeline:")
    dag_str = dag_to_string(runner.dag, "mermaid" )
    print(dag_str)


def run_single_flow(runner, rp: RunParams) -> None:
    input_image_path = Path(rp.input_data)
    if not input_image_path.exists():
        click.echo(click.style(f"From CLI: Error: File not found: {input_image_path}", fg="red"))
        sys.exit(1)
    click.echo(f"From CLI: Running the pipeline for {input_image_path}")

    result = central_dag_flow(input_data=str(input_image_path), start_from=rp.start_from,
                      stop_after=rp.stop_after, skip_existing=rp.skip_existing)

    if result is None:
        click.echo(click.style("From CLI: Pipeline stopped!", fg="yellow"))
    elif result.success:
        click.echo(click.style("From CLI: Pipeline completed successfully!", fg="green"))
        click.echo(f"From CLI: Result: {result.output}")
    else:
        click.echo(click.style(f"From CLI: Pipeline failed: {result.error}", fg="red"))
        sys.exit(1)


@main.command()
@click.argument("input_data", type=str)
@click.option(
    "--start-from",
    type=str,
    default=None,
    help="Job name to start from. Default: None.",
)
@click.option(
    "--stop-after",
    type=str,
    default=None,
    help="Job name to stop after. Default: None.",
)
@click.option(
    "--skip-existing", "-x",
    is_flag=True,
    default=False,
    help="Skip existing intermediate results or images. Default: False",
)
@click.pass_context
def run(
        ctx: click.Context,
        input_data: str,
        start_from: str | None,
        stop_after: str | None,
        skip_existing: bool,
) -> None:
    """
    Run the pipeline with flexible start/stop points.

    INPUT_DATA: Input for the starting job (file path, batch ID, etc).
    If 'all' the pipeline runs over all images in the database.
    """
    runner: CentralDagRunner = ctx.obj["runner"]

    available_jobs = runner.available_nodes
    if start_from and start_from not in available_jobs:
        click.echo(click.style(f"From CLI: Error: Start job '{start_from}' not found.", fg="red"))
        click.echo("Available jobs:")
        for job in available_jobs:
            click.echo(f"  - {job}")
        sys.exit(1)

    if stop_after and stop_after not in available_jobs:
        click.echo(click.style(f"From CLI: Error: Stop job '{stop_after}' not found.", fg="red"))
        click.echo("Available jobs:")
        for job in available_jobs:
            click.echo(f"  - {job}")
        sys.exit(1)

    if start_from:
        click.echo(f"From CLI: Starting from: {start_from}")
    if stop_after:
        click.echo(f"From CLI: Stopping after: {stop_after}")

    params = RunParams(input_data=input_data, start_from=start_from,
                       stop_after=stop_after, skip_existing=skip_existing)

    if input_data=='all':
        from faf28_workflows.flows.concurrency_driver import deploy_multiple_flows
        deploy_multiple_flows(params)
    else:
        run_single_flow(runner,params)

####################################
if __name__ == "__main__":
    main()
