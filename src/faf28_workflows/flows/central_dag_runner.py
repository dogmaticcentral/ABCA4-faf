import os
from typing import Any

from prefect import get_run_logger, flow
from prefect.futures import wait
from prefect.task_runners import ConcurrentTaskRunner  # or ThreadPoolTaskRunner

from faf28_workflows.flows.default_dag import create_default_dag
from faf28_workflows.flows.dag_class import DAG
from faf28_workflows.tasks.wrapper import FafStepResult, wrap_faf_analysis_step_as_task


class CentralDagRunner:
    """
    Runner for DAG-based pipelines with parallel execution support.
    """

    def __init__(
            self,
            log_level: str = "INFO",
            dag: DAG | None = None,
    ) -> None:
        self.log_level = log_level
        self._dag = dag or create_default_dag()

    @property
    def available_nodes(self) -> list[str]:
        return self._dag.node_names

    @property
    def dag(self) -> DAG:
        return self._dag

    def run(
            self,
            logger,
            input_data: Any,
            start_from: str | None = None,
            skip_existing: bool = False
    ) -> FafStepResult[Any] | None:
        """
        Run the DAG starting from a specific node.
        Sibling nodes (nodes without dependencies between them) run in parallel.
        """

        # Determine entry node
        entry_node = start_from
        if entry_node is None:
            if "FafDenoising" in self._dag.node_names:
                entry_node = "FafDenoising"
            elif self._dag.node_names:
                entry_node = self._dag.node_names[0]
            else:
                logger.warning("DAG is empty")
                return None

        # Get topologically sorted nodes to run
        try:
            nodes_to_run = self._dag.get_descendants(entry_node)
        except ValueError as e:
            logger.error(str(e))
            return None

        if not nodes_to_run:
            logger.warning("No nodes to run")
            return None

        node_names_set = {n.name for n in nodes_to_run}
        logger.info(f"Input data: {input_data}")
        logger.info(f"DAG '{self._dag.name}' executing nodes: {[n.name for n in nodes_to_run]}")

        # =====================================================================
        # PARALLEL EXECUTION: Submit all tasks with proper dependencies
        # =====================================================================

        # Track futures for each node
        node_futures: dict[str, Any] = {}  # node_name -> PrefectFuture

        for node_spec in nodes_to_run:
            # Find parent nodes that are part of this execution
            parent_names = [
                p for p in self._dag._reverse_edges.get(node_spec.name, [])
                if p in node_names_set
            ]

            # Collect parent futures for dependency specification
            parent_futures = [node_futures[p] for p in parent_names if p in node_futures]

            logger.info(
                f"Submitting '{node_spec.name}' "
                f"(waits for: {parent_names if parent_names else 'nothing'})"
            )

            # Prepare job kwargs
            pipeline_args = {"i": str(input_data)}
            if skip_existing:
                pipeline_args["x"] = True
            job_kwargs = node_spec.config_factory() | pipeline_args

            # Get the wrapped task
            job_task = wrap_faf_analysis_step_as_task(
                node_spec.job_class,
                task_name=node_spec.name
            )

            # Submit task with dependencies via wait_for
            # This allows Prefect to schedule parallel execution for independent nodes
            future = job_task.submit(
                job_kwargs=job_kwargs,
                wait_for=parent_futures  # Task won't start until these complete
            )
            node_futures[node_spec.name] = future

        # =====================================================================
        # Wait for all tasks to complete and collect results
        # =====================================================================

        all_futures = list(node_futures.values())
        wait(all_futures)  # Block until all complete

        # Check results for errors
        for node_name, future in node_futures.items():
            result = future.result()
            if not result.success:
                logger.error(f"DAG errored at node '{node_name}': {result.error}")
                result.metadata["input_data"] = str(input_data)
                return result

        logger.info("DAG execution completed successfully")

        # Return result from a terminal node (node with no children in execution set)
        terminal_nodes = [
            n.name for n in nodes_to_run
            if not any(child in node_names_set for child in self._dag._edges.get(n.name, []))
        ]

        final_node = terminal_nodes[-1] if terminal_nodes else nodes_to_run[-1].name
        result = node_futures[final_node].result()
        result.metadata["input_data"] = str(input_data)

        return result


# ================================================================================
# IMPORTANT: Use a concurrent task runner for actual parallelism
# ================================================================================

@flow(
    name="central-dag-runner",
    task_runner=ConcurrentTaskRunner()  # <-- This enables parallel execution!
)
def central_dag_flow(
        input_data: str,
        start_from: str | None = None,
        skip_existing: bool = False
):
    runner = CentralDagRunner()
    logger = get_run_logger()

    return runner.run(
        logger,
        input_data=input_data,
        start_from=start_from,
        skip_existing=skip_existing
    )
