#! /usr/bin/env python3
"""Command-line interface for the pipeline."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from faf28_workflows.flows.pipeline_flow import PipelineRunner
from utils.utils import shrug


def get_logging_level_names():
    return list(logging.getLevelNamesMapping().keys())

def configure_logging(log_level: str) -> None:
    """Configure logging based on the specified level."""
    logging.disable(logging.NOTSET)
    numeric_level = logging.getLevelNamesMapping().get(log_level.upper(), "unrecognized")
    if numeric_level == "unrecognized":
        shrug("Logging level {} not recognized, setting log level to ERROR")
        numeric_level = logging.ERROR

    logging.basicConfig(level=numeric_level,format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
    ctx.obj["runner"] = PipelineRunner(log_level=log_level)


@main.command()
@click.pass_context
def list_jobs(ctx: click.Context) -> None:
    """List all available jobs in the pipeline."""
    runner: PipelineRunner = ctx.obj["runner"]

    click.echo("Available jobs:")
    for i, name in enumerate(runner.available_jobs, 1):
        click.echo(f"  {i}. {name}")


@main.command()
@click.argument("input_data", type=str)
@click.option(
    "--start-from",
    type=str,
    default=None,
    help="Job name to start from.",
)
@click.option(
    "--stop-after",
    type=str,
    default=None,
    help="Job name to stop after.",
)
@click.pass_context
def run(
        ctx: click.Context,
        input_data: str,
        start_from: str | None,
        stop_after: str | None,
) -> None:
    """
    Run the pipeline with flexible start/stop points.

    INPUT_DATA: Input for the starting job (file path, batch ID, etc.)
    """
    runner: PipelineRunner = ctx.obj["runner"]

    available_jobs = runner.available_jobs
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

    parsed_input = Path(input_data)
    if not parsed_input.exists():
        click.echo(click.style(f"From CLI: Error: File not found: {parsed_input}", fg="red"))
        sys.exit(1)

    click.echo(f"From CLI: Running the pipeline for {parsed_input}")
    if start_from:
        click.echo(f"From CLI: Starting from: {start_from}")
    if stop_after:
        click.echo(f"From CLI: Stopping after: {stop_after}")

    result = runner.run(input_data=parsed_input, start_from=start_from, stop_after=stop_after)

    if result is None:
        click.echo(click.style("From CLI: Pipeline stopped!", fg="yellow"))
    elif result.success:
        click.echo(click.style("From CLI: Pipeline completed successfully!", fg="green"))
        click.echo(f"From CLI: Result: {result.output}")
    else:
        click.echo(click.style(f"From CLI: Pipeline failed: {result.error}", fg="red"))
        sys.exit(1)

####################################
if __name__ == "__main__":
    main()
