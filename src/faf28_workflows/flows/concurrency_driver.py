from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable

import click
from prefect import flow, get_run_logger
from prefect.futures import wait
from prefect.task_runners import ConcurrentTaskRunner
from prefect import tags
from prefect.deployments import  run_deployment

from faf28_workflows.flows.run_params_class import RunParams
from faf28_workflows.flows.central_pipe_runner import CentralPipeRunner
from faf28_workflows.tasks.wrapper import FafStepResult


def get_all_image_paths() -> Iterable[str]:
    retlist = []
    path1 = "/media/ivana/portable/abca4/faf/all/Confused_Cloud/OS/CC_OS_12_1.tiff"
    path2 = "/media/ivana/portable/abca4/faf/all/Confused_Cloud/OD/CC_OD_12_1.tiff"
    retlist = [path1, path2]
    return retlist


from prefect import task

'''
It looks like tasks and flows can be nested
Prefect 3 intentionally separates concerns:
Concept	Purpose
Flow	Orchestration
Task	Execution + concurrency
Subflow	Tracking & reuse
Runner	Scheduling tasks
'''


@task
def run_subflow(
    image_path: str,
    rp: RunParams,
) -> FafStepResult:
    return CentralPipeRunner().run(
        image_path,
        start_from=rp.start_from,
        stop_after=rp.stop_after,
        skip_existing=rp.skip_existing,
    )

@flow(
    name="process-all-images",
    task_runner=ConcurrentTaskRunner(),  # Enables concurrent subflow execution
    description="Process all images using CentralPipeRunner"
)
def process_all_images(
    rp: RunParams,
) -> list[FafStepResult]:
    """
    Using map for parallel execution of subflows
    """
    logger = get_run_logger()
    image_paths = list(get_all_image_paths())

    if not image_paths: return []

    futures = [run_subflow.submit(p, rp) for p in image_paths]

    results = []
    for future in futures:
        try:
            results.append(future.result())
        except Exception as exc:
            logger.error(f"Subflow failed: {exc}")

    logger.info(f"Successfully processed {len(results)}/{len(image_paths)} images")
    return results


def deploy_multiple_flows(rp: RunParams):
    click.echo(f"From CLI: Running the pipeline over all images in the database.")
    # touching the deployment, in the expectation that something has changed
    # it would not be necessary if we were always running the same code

    process_all_images.from_source(
        # Points to the current directory where this file lives
        source=str(Path(__file__).parent.absolute()),
        entrypoint="concurrency_driver.py:process_all_images"
    ).deploy(
        name="process-images-deployment",
        parameters= {"rp": rp},
        tags=["image-processing"],
        work_pool_name="concurrency-limited-pool",
    )
    flow_run = run_deployment(name="process-all-images/process-images-deployment")
