"""
DAG (Directed Acyclic Graph) definitions for job workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Self

from faf_classes.faf_analysis import FafAnalysis


@dataclass
class NodeSpec:
    """Specification for a single node (job) in the DAG."""

    name: str
    job_class: type[FafAnalysis]
    config_factory: Callable[[], dict[str, Any]] = field(
        default_factory=lambda: lambda: {}
    )
    description: str = ""

    def create_instance(self) -> FafAnalysis:
        """Create a job instance with configuration."""
        config = self.config_factory()
        return self.job_class(**config)


class DAG:
    """
    Defines a Directed Acyclic Graph of jobs.

    Allows for branching workflows and execution of downstream
    dependencies from a given start node.
    """

    def __init__(self, name: str = "dag") -> None:
        self.name = name
        self._nodes: dict[str, NodeSpec] = {}
        # Adjacency list: parent -> list of children
        self._edges: dict[str, list[str]] = {}
        # Reverse adjacency: child -> list of parents (for validation/traversal if needed)
        self._reverse_edges: dict[str, list[str]] = {}

    def add_node(
        self,
        name: str,
        job_class: type[FafAnalysis],
        config_factory: Callable[[], dict[str, Any]] | None = None,
        description: str = "",
    ) -> Self:
        """
        Add a node to the DAG.

        Args:
            name: Unique identifier for the job
            job_class: The job class to instantiate
            config_factory: Callable that returns kwargs for job constructor
            description: Human-readable description
        """
        if name in self._nodes:
            raise ValueError(f"Node '{name}' already exists in DAG")

        spec = NodeSpec(
            name=name,
            job_class=job_class,
            config_factory=config_factory or (lambda: {}),
            description=description,
        )

        self._nodes[name] = spec
        self._edges[name] = []
        self._reverse_edges[name] = []
        return self

    def add_edge(self, distinct_parent: str, distinct_child: str) -> Self:
        """
        Add a directional dependency: parent -> child.
        """
        if distinct_parent not in self._nodes:
            raise ValueError(f"Parent node '{distinct_parent}' not found in DAG")
        if distinct_child not in self._nodes:
            raise ValueError(f"Child node '{distinct_child}' not found in DAG")
        
        if distinct_child in self._edges[distinct_parent]:
             # Edge already exists
             return self

        # Basic cycle detection could go here, but omitted for simplicity
        # assuming the user builds a valid DAG.
        
        self._edges[distinct_parent].append(distinct_child)
        self._reverse_edges[distinct_child].append(distinct_parent)
        return self

    def get_node(self, name: str) -> NodeSpec:
        """Get a node specification by name."""
        if name not in self._nodes:
            raise ValueError(f"Unknown node: '{name}'")
        return self._nodes[name]
    
    @property
    def node_names(self) -> list[str]:
        return list(self._nodes.keys())

    def get_descendants(self, start_node: str) -> list[NodeSpec]:
        """
        Get the list of nodes to execute starting from start_node.
        
        Returns a topologically sorted list containing the start_node
        and all its downstream descendants. Siblings of start_node
        or nodes on parallel branches not reachable from start_node
        are NOT included.
        """
        if start_node not in self._nodes:
            raise ValueError(f"Start node '{start_node}' not found in DAG")

        # BFS to find all reachable nodes
        visited = set()
        queue = [start_node]
        reachable_nodes = set()
        
        while queue:
            current = queue.pop(0)
            if current in visited: continue
            visited.add(current)
            reachable_nodes.add(current)
            # Add children to queue
            children = self._edges.get(current, [])
            queue.extend(children)
        
        # Now we need to topologically sort 'reachable_nodes'.
        # We can extract the subgraph induced by reachable_nodes and topo sort it.
        # Or simply use a standard topo sort algorithm restricted to this set.
        
        # Kahn's algorithm for subgraph
        in_degree = {node: 0 for node in reachable_nodes}
        for u in reachable_nodes:
            for v in self._edges.get(u, []):
                if v  not in reachable_nodes:  continue
                in_degree[v] += 1

        topo_queue = [n for n in reachable_nodes if in_degree[n] == 0]
        sorted_nodes = []
        
        while topo_queue:
            u = topo_queue.pop(0)
            sorted_nodes.append(self._nodes[u])
            
            for v in self._edges.get(u, []):
                if v in reachable_nodes:
                    in_degree[v] -= 1
                    if in_degree[v] == 0:
                        topo_queue.append(v)
                        
        return sorted_nodes

    def extract_subgraph(self, start_node: str, end_node: str) -> DAG:
        """
        Extract a subgraph containing all nodes and edges on paths from start_node to end_node.
        
        Args:
            start_node: The starting node of the subgraph.
            end_node: The ending node of the subgraph.
            
        Returns:
            A new DAG instance containing only the nodes and edges on paths 
            between start_node and end_node.
        """
        if start_node not in self._nodes:
            raise ValueError(f"Start node '{start_node}' not found in DAG")
        if end_node not in self._nodes:
            raise ValueError(f"End node '{end_node}' not found in DAG")

        # 1. Forward reachability from start_node
        forward_visited = set()
        queue = [start_node]
        while queue:
            curr = queue.pop(0)
            if curr not in forward_visited:
                forward_visited.add(curr)
                queue.extend(self._edges.get(curr, []))
                
        # 2. Backward reachability from end_node
        backward_visited = set()
        queue = [end_node]
        while queue:
            curr = queue.pop(0)
            if curr not in backward_visited:
                backward_visited.add(curr)
                queue.extend(self._reverse_edges.get(curr, []))
                
        # The subgraph consists of nodes that are reachable from start_node 
        # AND can reach end_node
        subgraph_nodes = forward_visited.intersection(backward_visited)
        
        new_dag = DAG(name=f"{self.name}_subgraph")
        
        # Add the nodes to the new DAG
        for node_name in subgraph_nodes:
            spec = self._nodes[node_name]
            new_dag.add_node(
                name=spec.name,
                job_class=spec.job_class,
                config_factory=spec.config_factory,
                description=spec.description,
            )
            
        # Add edges between nodes in the subgraph
        for node_name in subgraph_nodes:
            for child in self._edges.get(node_name, []):
                if child in subgraph_nodes:
                    new_dag.add_edge(node_name, child)
                    
        return new_dag
