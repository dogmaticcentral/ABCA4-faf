from typing import Iterable
from prefect import flow
from prefect.concurrency.sync import concurrency    # sync context manager
from prefect.futures import wait

from faf28_workflows.flows.central_pipe_runner import CentralPipeRunner


# placeholder provider for image paths
def get_all_image_paths() -> Iterable[str]:
    # implement this to return your list of paths
    raise NotImplementedError

@flow
def process_all_images(
    runner: CentralPipeRunner,
    concurrency_name: str = "image_pipeline",
    start_from: str | None = None,
    stop_after: str | None = None,
    skip_existing: bool = False,
) -> None:
    """
    Driver flow: runs `runner.run` once per image, keeping at most N images in flight.
    Requires a Prefect concurrency limit with name == `concurrency_name` (create via CLI).
    """
    image_paths = list(get_all_image_paths())
    futures = []

    # iterate images and submit subflows once we've acquired a concurrency slot
    for p in image_paths:
        # Blocks until a slot is available. occupy=1 because every subflow
        # consumes one slot while running.
        with concurrency(concurrency_name, occupy=1):
            # submit the subflow; returns a PrefectFuture that runs concurrently
            fut = runner.run.submit(
                input_data=p,
                start_from=start_from,
                stop_after=stop_after,
                skip_existing=skip_existing,
            )
            futures.append(fut)

    # wait for all submitted subflow runs to finish
    wait(futures)
