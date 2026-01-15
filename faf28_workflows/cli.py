"""Command-line interface for the pipeline."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from faf28_workflows.flows.pipeline_runner import PipelineRunner


def configure_logging(log_level: str) -> None:
    """Configure logging based on the specified level."""
    if log_level == "OFF":
        logging.disable(logging.CRITICAL)
        logging.getLogger("prefect").setLevel(logging.CRITICAL + 10)
    else:
        logging.disable(logging.NOTSET)
        numeric_level = getattr(logging, log_level)
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        logging.getLogger("prefect").setLevel(numeric_level)


@click.group()
@click.option(
    "--log-level", "-l",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"]),
    default="INFO",
    help="Set logging level. Use 'OFF' to disable logging entirely.",
)
@click.pass_context
def main(
        ctx: click.Context,
        log_level: str,
) -> None:
    """
    Prefect Pipeline CLI.

    Run data processing pipelines with configurable logging and storage.
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

    actual_start = start_from or runner.available_jobs[0]

    if actual_start == "C":
        try:
            parsed_input: Path | int = int(input_data)
        except ValueError:
            txt = f"Error: Job C requires a batch ID (integer), got: {input_data}"
            click.echo(click.style(txt, fg="red"))
            sys.exit(1)
    else:
        parsed_input = Path(input_data)
        if not parsed_input.exists():
            click.echo(
                click.style(f"Error: File not found: {parsed_input}", fg="red")
            )
            sys.exit(1)

    click.echo(f"Running pipeline...")
    if start_from:
        click.echo(f"  Starting from: {start_from}")
    if stop_after:
        click.echo(f"  Stopping after: {stop_after}")

    result = runner.run(
        input_data=parsed_input,
        start_from=start_from,
        stop_after=stop_after,
    )

    if result.success:
        click.echo(click.style("Pipeline completed successfully!", fg="green"))
        click.echo(f"Result: {result.output}")
    else:
        click.echo(click.style(f"Pipeline failed: {result.error}", fg="red"))
        sys.exit(1)




if __name__ == "__main__":
    main()
