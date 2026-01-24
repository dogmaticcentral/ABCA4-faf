#! /usr/bin/env python3
import asyncio
import logging
import subprocess
from typing import Optional

from prefect.settings import PREFECT_API_URL

logger = logging.getLogger("bootstrap")

async def prefect_api_reachable(timeout_s: float = 2.0) -> bool:
    api_url = str(PREFECT_API_URL.value() or "").strip()
    if not api_url:
        logger.error("PREFECT_API_URL is not set; cannot check Prefect API.")
        return False

    health_url = api_url.rstrip("/") + "/health"
    logger.info("Checking Prefect API health endpoint: %s", health_url)

    try:
        import httpx

        timeout = httpx.Timeout(timeout_s, connect=timeout_s)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(health_url)

        if resp.status_code != 200:
            logger.error(
                "Prefect API responded but is not healthy: url=%s status=%s body=%r",
                health_url, resp.status_code, resp.text[:300],
            )
            return False

        logger.info("Prefect API reachable: %s", health_url)
        return True

    except (Exception,) as exc:
        # If httpx is installed, narrow to connection-ish exceptions with no traceback.
        try:
            import httpx
            conn_excs = (
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.RemoteProtocolError,
            )
        except Exception:
            conn_excs = ()

        if conn_excs and isinstance(exc, conn_excs):
            # No traceback (this is the common "server is down" case)
            logger.error("Prefect API NOT reachable at %s (%s: %s)", health_url, type(exc).__name__, exc)
            # Optional: keep details available at DEBUG only
            logger.debug("Prefect API connection failure details:", exc_info=True)
            return False

        # Unexpected error: keep traceback
        logger.exception("Unexpected error while probing Prefect API at %s", health_url)
        return False


def prefect_api_reachable_sync(timeout_s: float = 2.0) -> bool:
    """
    Sync wrapper that also avoids leaking the 'asyncio.run() cannot be called
    from a running event loop' error.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # no running loop -> safe to use asyncio.run
        try:
            return asyncio.run(prefect_api_reachable(timeout_s=timeout_s))
        except Exception as exc:
            logger.exception("Unexpected failure while running reachability check: %s: %s",
                             type(exc).__name__, exc)
            return False
    else:
        # already in an event loop -> require awaiting the async function
        logger.error(
            "prefect_api_reachable_sync() called while an event loop is running. "
            "Use: `await prefect_api_reachable(...)` instead."
        )
        return False

def ensure_work_pool_exists(pool_name: str, limit: int) -> bool:
    """
    Ensure a Prefect concurrency limit exists.

    Behavior:
    - If the server is unreachable -> exit
    - If the limit already exists -> log debug, continue
    - If created successfully -> info
    """

    if not prefect_api_reachable_sync():
        logger.error("Prefect server is not reachable.")
        return False

    try:
        # TODO - this hangs
        create = ["prefect", "work_pool", "create", pool_name, # this is the pool name we are choosing here
                "--type",  "process" ]
        set_limit = ["prefect", "work_pool", "set-concurrency-limit", pool_name,  str(limit)]
        start_workers = ["prefect", "worker", "start",  "--pool", pool_name,  "--name", "busybee"]
        for cmd in [create, set_limit, start_workers]:
            logger.info("Executing as subprocess: %s", " ".join(cmd))
            subprocess.run(cmd,  stdout=subprocess.DEVNULL,  stderr=subprocess.DEVNULL)
            logger.info("returned")
        logger.info(f"Prefect work pool with CPU limit created (max={limit}). Started worker: busybee")
        return True

    except subprocess.CalledProcessError:
        # at this point, failure almost certainly means "already exists"
        logger.info(f"Problem setting up the work pool: {pool_name}")
        return False

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

    logger.info("Bootstrapping Prefect environment")

    if not  ensure_work_pool_exists(pool_name="concurrency-limited-pool", limit=8):
        exit(1)

    # Hand off to the real CLI
    from faf28_workflows.cli import main as real_main
    real_main()

if __name__ == "__main__":
    main()
