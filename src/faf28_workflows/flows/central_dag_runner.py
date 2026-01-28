import os
from typing import Any

from prefect import get_run_logger, flow

from faf28_workflows.flows.default_dag import create_default_dag
from faf28_workflows.flows.dag_class import DAG
from faf28_workflows.tasks.wrapper import FafStepResult, wrap_faf_analysis_step_as_task


class CentralDagRunner:
    """
    Runner for DAG-based pipelines.
    """

    def __init__(
            self,
            log_level: str = "INFO",
            dag: DAG | None = None,
    ) -> None:
        """
        Initialize the DAG runner.

        Args:
            log_level: Logging level
            dag: Custom DAG definition (uses default if None)
        """
        self.log_level = log_level
        self._dag = dag or create_default_dag()

    @property
    def available_nodes(self) -> list[str]:
        """Get list of available node names."""
        return self._dag.node_names

    def run(
            self,
            logger,
            input_data: Any,
            start_from: str | None = None,
            skip_existing: bool = False
    ) -> FafStepResult[Any] | None:
        """
        Run the DAG starting from a specific node.

        Args:
            start_from: Node name to start from. If None, it typically requires 
                        finding root nodes, but for simplicity we might enforce 
                        specifying a start node or defaulting to the first one 
                        added or a known root. 
                        For this specific implementation context (linear-ish default),
                        we'll default to the first node if None, or maybe "FafDenoising".
            input_data: The input argument (usually file path).
        """
        
        # Determine start node. 
        # CAUTION: 'start_from=None' is ambiguous in a general DAG with multiple roots.
        # But for our default DAG, we know "FafDenoising" is the root.
        # Let's check if start_from is provided, else try to find "FafDenoising" or fail.
        entry_node = start_from
        if entry_node is None:
             # Heuristic: try finding "FafDenoising"
             if "FafDenoising" in self._dag.node_names:
                 entry_node = "FafDenoising"
             else:
                 # Fallback: Just take the first node added? Or raise error?
                 # Raising error is safer.
                 # But to be user friendly like the pipeline:
                 if self._dag.node_names:
                     entry_node = self._dag.node_names[0]
                 else:
                     logger.warning("DAG is empty")
                     return None

        # Get the sub-graph execution order (topologically sorted)
        try:
            nodes_to_run = self._dag.get_descendants(entry_node)
        except ValueError as e:
            logger.error(str(e))
            return None

        node_names = [n.name for n in nodes_to_run]

        logger.info(f"Input data: {input_data}")
        logger.info(f"DAG '{self._dag.name}' executing nodes path: {node_names}")

        if not nodes_to_run:
            logger.warning("No nodes to run")
            return None

        # Execute nodes sequentially (as per topo sort)
        result: FafStepResult[Any] | None = None

        for i, node_spec in enumerate(nodes_to_run):
            
            logger.info(f"Step {i + 1}/{len(nodes_to_run)}: {node_spec.name}")
            
            # Create and run the task
            pipeline_args =  {"i": str(input_data)}
            if skip_existing: pipeline_args["x"] = True
            
            job_kwargs = node_spec.config_factory() | pipeline_args
            
            job_task = wrap_faf_analysis_step_as_task(
                node_spec.job_class, 
                task_name=node_spec.name
            )
            
            result = job_task(job_kwargs=job_kwargs)

            if not result.success:
                logger.error(f"DAG errored out at node '{node_spec.name}': {result.error}")
                result.metadata["input_data"] = str(input_data)
                return result

        logger.info(f"DAG execution completed successfully")

        if result:
            result.metadata["input_data"] = str(input_data)

        return result


@flow(name="central-dag-runner")
def central_dag_flow(input_data: str, start_from: str | None = None, skip_existing: bool = False):
    runner = CentralDagRunner()
    logger = get_run_logger()

    return runner.run(
        logger,
        input_data=input_data,
        start_from=start_from,
        skip_existing=skip_existing
    )
