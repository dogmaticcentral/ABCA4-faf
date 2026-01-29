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


def print_dag_diagram(dag: DAG, output: TextIO = sys.stdout) -> None:
    """
    Print a visual ASCII diagram of the DAG with boxes and arrows.
    Nodes are arranged in levels based on their depth from root nodes.

    Args:
        dag: The DAG instance to visualize
        output: Output stream (defaults to stdout)
    """
    if not dag._nodes:
        output.write("(empty DAG)\n")
        return

    # Find levels (topological layers)
    levels = _compute_levels(dag)

    # Calculate box widths
    box_width = max(len(name) for name in dag._nodes) + 4  # padding

    output.write(f"DAG: {dag.name}\n")
    output.write("=" * 40 + "\n\n")

    for level_idx, level_nodes in enumerate(levels):
        # Print boxes for this level
        _print_level_boxes(level_nodes, box_width, output)

        # Print arrows to next level (if not last level)
        if level_idx < len(levels) - 1:
            _print_arrows(dag, level_nodes, levels[level_idx + 1], box_width, output)


def print_dag_edges(dag: DAG, output: TextIO = sys.stdout) -> None:
    """
    Print a simple edge list representation of the DAG.

    Args:
        dag: The DAG instance to visualize
        output: Output stream (defaults to stdout)
    """
    output.write(f"DAG: {dag.name}\n")
    output.write("=" * 40 + "\n")
    output.write("Nodes:\n")

    for name, spec in dag._nodes.items():
        parents = dag._reverse_edges.get(name, [])
        children = dag._edges.get(name, [])
        desc = f" - {spec.description}" if spec.description else ""
        output.write(f"  • {name}{desc}\n")
        if parents:
            output.write(f"      ← depends on: {', '.join(parents)}\n")
        if children:
            output.write(f"      → leads to: {', '.join(children)}\n")

    output.write("\nEdges:\n")
    for parent, children in dag._edges.items():
        for child in children:
            output.write(f"  {parent} ──→ {child}\n")


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
        style: One of "tree", "diagram", "edges", "mermaid"

    Returns:
        String representation of the DAG
    """
    buffer = StringIO()

    printers = {
        "tree": print_dag_tree,
        "diagram": print_dag_diagram,
        "edges": print_dag_edges,
        "mermaid": print_dag_mermaid,
    }

    if style not in printers:
        raise ValueError(
            f"Unknown style: '{style}'. Use one of: {', '.join(printers.keys())}"
        )

    printers[style](dag, buffer)
    return buffer.getvalue()


# =============================================================================
# Private helper functions
# =============================================================================

def _compute_levels(dag: DAG) -> list[list[str]]:
    """Compute topological levels (layers) of the DAG."""
    depths: dict[str, int] = {}

    def compute_depth(node: str, visited: set) -> int:
        if node in depths:
            return depths[node]
        if node in visited:
            return 0  # Cycle protection
        visited.add(node)

        parents = dag._reverse_edges.get(node, [])
        if not parents:
            depths[node] = 0
        else:
            depths[node] = max(compute_depth(p, visited) for p in parents) + 1
        return depths[node]

    for node in dag._nodes:
        compute_depth(node, set())

    # Group nodes by depth
    max_depth = max(depths.values()) if depths else 0
    levels: list[list[str]] = [[] for _ in range(max_depth + 1)]
    for node, depth in depths.items():
        levels[depth].append(node)

    return levels


def _print_level_boxes(
        nodes: list[str],
        box_width: int,
        output: TextIO
) -> None:
    """Print boxes for a level of nodes."""
    if not nodes:
        return

    # Top border
    for _ in nodes:
        output.write("┌" + "─" * box_width + "┐  ")
    output.write("\n")

    # Node name (centered)
    for node in nodes:
        padded = node.center(box_width)
        output.write(f"│{padded}│  ")
    output.write("\n")

    # Bottom border
    for _ in nodes:
        output.write("└" + "─" * box_width + "┘  ")
    output.write("\n")


def _print_arrows(
        dag: DAG,
        current_level: list[str],
        next_level: list[str],
        box_width: int,
        output: TextIO
) -> None:
    """Print arrows between levels."""
    cell_width = box_width + 4  # box + spacing

    # First line: vertical bars from parents
    line1 = ""
    for node in current_level:
        children_in_next = [c for c in dag._edges.get(node, []) if c in next_level]
        if children_in_next:
            center_pos = box_width // 2
            line1 += " " * center_pos + "│" + " " * (cell_width - center_pos - 1)
        else:
            line1 += " " * cell_width
    output.write(line1.rstrip() + "\n")

    # Arrow line
    line2 = ""
    for node in current_level:
        children_in_next = [c for c in dag._edges.get(node, []) if c in next_level]
        if children_in_next:
            center_pos = box_width // 2
            line2 += " " * center_pos + "▼" + " " * (cell_width - center_pos - 1)
        else:
            line2 += " " * cell_width
    output.write(line2.rstrip() + "\n")

    output.write("\n")
