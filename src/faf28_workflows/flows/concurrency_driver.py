#! /usr/bin/env python3
from __future__ import annotations

from typing import Iterable
from pathlib import Path
from prefect import flow, task, get_run_logger
from prefect.deployments import run_deployment
from prefect.task_runners import ConcurrentTaskRunner

from faf00_settings import global_db_proxy
from faf28_workflows.flows.run_params_class import RunParams
from models.abca4_faf_models import FafImage
from utils.db_utils import db_connect


def get_all_image_paths() -> Iterable[str]:
    # retlist = []
    # path1 = "/media/ivana/portable/abca4/faf/all/Confused_Cloud/OS/CC_OS_12_1.tiff"
    # path2 = "/media/ivana/portable/abca4/faf/all/Confused_Cloud/OD/CC_OD_12_1.tiff"
    # retlist = [path1, path2]
    if global_db_proxy.obj is None:
         db = db_connect()
    else:
         db = global_db_proxy
         db.connect(reuse_if_open=True)

    query   = FafImage.select(FafImage.image_path).where(FafImage.usable == True)
    retlist = [img.image_path for img in query.execute()]
    return retlist


'''
It looks like tasks and flows can be nested
Prefect 3 intentionally separates concerns:
Concept	Purpose
Flow	Orchestration
Task	Execution + concurrency
Subflow	Tracking & reuse
Runner	Scheduling tasks
'''


# --- 1. The "Child" Flow Deployment ---
# This needs to be deployed so the parent can trigger it by name.
def deploy_child_flow():
    # Assuming CentralPipeRunner().run is the flow you want to limit
    # We'll refer to this deployment name in the parent flow.
    from faf28_workflows.flows.central_pipe_runner import central_pipe_flow
    flow.from_source(
        source=str(Path(__file__).parent.absolute()),
        entrypoint="central_pipe_runner.py:central_pipe_flow"
    ).deploy(
        name="pipe-run-child",
        work_pool_name="concurrency-limited-pool",
    )

# --- 2. The Refactored Task ---
@task
def trigger_subflow_deployment(image_path: str, rp: RunParams):
    """
    Triggers the child deployment.
    By setting timeout=0, this task finishes as soon as the run is submitted.
    If you want the task to wait for the result, remove timeout=0.
    """
    logger = get_run_logger()
    logger.info(f"Submitting deployment run for {image_path}")

    # This call tells the Prefect API to put a job in the 'concurrency-limited-pool'
    flow_run = run_deployment(
        name="central-pipe-runner/pipe-run-child",  # Format: "flow-name/deployment-name"
        parameters={
            "input_data": image_path,
            "start_from": rp.start_from,
            "stop_after": rp.stop_after,
            "skip_existing": rp.skip_existing,
        },
        timeout=0  # Fire and forget so the parent can loop quickly
    )
    return flow_run.id


# --- 3. The Parent Flow ---
@flow(
    name="process-all-images",
    task_runner=ConcurrentTaskRunner(),
    description="Orchestrates child flow deployments"
)
def process_all_images(rp: RunParams):
    image_paths = list(get_all_image_paths())
    if not image_paths: return []

    # This will quickly submit 10 'requests' to the Work Pool.
    # The Work Pool will only let 5 start at a time.
    futures = [trigger_subflow_deployment.submit(p, rp) for p in image_paths]

    flow_run_ids = [f.result() for f in futures]
    return flow_run_ids


# --- 4. The Entry Point ---
def deploy_multiple_flows(rp: RunParams):
    # FIRST: Ensure the child exists in the Prefect API
    deploy_child_flow()

    # SECOND: Deploy and run the parent
    process_all_images.from_source(
        source=str(Path(__file__).parent.absolute()),
        entrypoint="concurrency_driver.py:process_all_images"
    ).deploy(
        name="process-images-deployment",
        parameters={"rp": rp},
        work_pool_name="concurrency-limited-pool",
    )

    run_deployment(name="process-all-images/process-images-deployment")

if __name__ == "__main__":
    image_paths = list(get_all_image_paths())
    for im in image_paths[:5]:
        print(im, type(im))

