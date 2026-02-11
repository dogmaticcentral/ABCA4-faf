"""
DAG visualization utilities.

Functions for rendering DAG structures as plain text diagrams.
"""

from __future__ import annotations

import sys
from io import StringIO
from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from faf28_workflows.flows.dag_class import DAG


# =============================================================================
# Private helper functions
# =============================================================================


def print_dag_tree(dag: DAG, output: TextIO = sys.stdout) -> None:
    """
    Print DAG as an indented tree structure with ASCII connectors.

    Args:
        dag: The DAG instance to visualize
        output: Output stream (defaults to stdout)
    """
    if not dag._nodes:
        output.write("(empty DAG)\n")
        return

    output.write(f"DAG: {dag.name}\n")
    output.write("=" * 40 + "\n")

    # Find root nodes (nodes with no parents)
    roots = [n for n in dag._nodes if not dag._reverse_edges.get(n)]

    if not roots:
        output.write("(no root nodes found - possible cycle)\n")
        return

    visited: set[str] = set()

    def print_subtree(node: str, prefix: str, is_last: bool, is_root: bool) -> None:
        # Connector characters
        if is_root:
            connector = ""
            child_prefix = ""
        else:
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

        # Mark if already visited (shows DAG convergence)
        suffix = " (→ merged)" if node in visited else ""
        output.write(f"{prefix}{connector}{node}{suffix}\n")

        if node in visited:
            return
        visited.add(node)

        # Print children
        children = dag._edges.get(node, [])
        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            print_subtree(child, prefix + child_prefix, is_last_child, False)

    for i, root in enumerate(roots):
        if i > 0:
            output.write("\n")
        print_subtree(root, "", True, True)


def print_dag_mermaid(dag: DAG, output: TextIO = sys.stdout) -> None:
    """
    Print DAG in Mermaid diagram format (for documentation/markdown).

    Args:
        dag: The DAG instance to visualize
        output: Output stream (defaults to stdout)
    """
    output.write("```mermaid\ngraph TD\n")

    for name, spec in dag._nodes.items():
        label = name
        output.write(f'    {name}["{label}"]\n')

    output.write("\n")

    for parent, children in dag._edges.items():
        for child in children:
            output.write(f"    {parent} --> {child}\n")

    output.write("```\n")


def dag_to_string(dag: DAG, style: str = "tree") -> str:
    """
    Return DAG visualization as a string.

    Args:
        dag: The DAG instance to visualize
        style: One of "tree", "mermaid"

    Returns:
        String representation of the DAG
    """
    buffer = StringIO()

    printers = {
        "tree": print_dag_tree,
        "mermaid": print_dag_mermaid,
    }

    if style not in printers:
        raise ValueError(
            f"Unknown style: '{style}'. Use one of: {', '.join(printers.keys())}"
        )

    printers[style](dag, buffer)
    return buffer.getvalue()

