
import sys
import unittest
from unittest.mock import MagicMock

# Mock faf_classes.faf_analysis BEFORE importing dag_class
sys.modules["faf_classes"] = MagicMock()
sys.modules["faf_classes.faf_analysis"] = MagicMock()

# Now we can safely import, but we need to ensure dag_class doesn't fail 
# when it tries to use FafAnalysis as a type hint or base class if it checks.
# dag_class imports FafAnalysis. 
# We need to make sure the mocked FafAnalysis is usable.
mock_faf_analysis = MagicMock()
sys.modules["faf_classes.faf_analysis"].FafAnalysis = mock_faf_analysis

from faf28_workflows.flows.dag_class import DAG, NodeSpec

class MockJob:
    def __init__(self, **kwargs):
        pass

class TestDAG(unittest.TestCase):
    def setUp(self):
        self.dag = DAG("test_dag")
        # Structure:
        # A -> B -> D
        # A -> C -> D
        # A -> E
        # F -> G
        
        self.dag.add_node("A", MockJob)
        self.dag.add_node("B", MockJob)
        self.dag.add_node("C", MockJob)
        self.dag.add_node("D", MockJob)
        self.dag.add_node("E", MockJob)
        self.dag.add_node("F", MockJob)
        self.dag.add_node("G", MockJob)
        
        self.dag.add_edge("A", "B")
        self.dag.add_edge("B", "D")
        self.dag.add_edge("A", "C")
        self.dag.add_edge("C", "D")
        self.dag.add_edge("A", "E")
        self.dag.add_edge("F", "G")

    def test_descendants_from_root(self):
        # From A, should get A, B, C, D, E. Order of B, C, E can vary but must be before D
        nodes = self.dag.get_descendants("A")
        names = [n.name for n in nodes]
        print(f"Descendants of A: {names}")
        
        self.assertIn("A", names)
        self.assertIn("B", names)
        self.assertIn("C", names)
        self.assertIn("D", names)
        self.assertIn("E", names)
        self.assertNotIn("F", names)
        self.assertNotIn("G", names)
        
        # Check topo order constraints
        self.assertLess(names.index("A"), names.index("B"))
        self.assertLess(names.index("A"), names.index("C"))
        self.assertLess(names.index("A"), names.index("E"))
        self.assertLess(names.index("B"), names.index("D"))
        self.assertLess(names.index("C"), names.index("D"))

    def test_descendants_from_branch(self):
        # From B -> [B, D]
        # Should NOT include A, C, E, F, G
        nodes = self.dag.get_descendants("B")
        names = [n.name for n in nodes]
        print(f"Descendants of B: {names}")
        
        self.assertEqual(names, ["B", "D"])

    def test_descendants_from_leaf(self):
        # From E -> [E]
        nodes = self.dag.get_descendants("E")
        names = [n.name for n in nodes]
        print(f"Descendants of E: {names}")
        self.assertEqual(names, ["E"])

    def test_descendants_disjoint(self):
        # From F -> [F, G]
        nodes = self.dag.get_descendants("F")
        names = [n.name for n in nodes]
        print(f"Descendants of F: {names}")
        self.assertEqual(names, ["F", "G"])

if __name__ == '__main__':
    unittest.main()
