"""Regression tests for the fail-closed OWL-RL diagnostic boundary."""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from rdflib import BNode, Graph, Literal, Namespace, RDF

from reasoning_support import OWL_RL_ERROR, expand_checked, owlrl_errors

ROOT = Path(__file__).resolve().parents[1]
PKG = Namespace("https://purl.org/packagegraph/ontology/core#")
EX = Namespace("https://example.org/reasoning-gate/")


class ReasoningSupportTests(unittest.TestCase):
    def test_extracts_only_error_predicate(self):
        graph = Graph()
        graph.add((BNode(), OWL_RL_ERROR, Literal("second")))
        graph.add((BNode(), OWL_RL_ERROR, Literal("first")))
        graph.add((EX.subject, EX.errorDescription, Literal("not a report")))
        self.assertEqual(owlrl_errors(graph), ("first", "second"))

    def test_valid_core_returns_same_graph_without_errors(self):
        graph = Graph().parse(ROOT / "core/core.ttl")
        self.assertIs(expand_checked(graph), graph)
        self.assertEqual(owlrl_errors(graph), ())

    def test_disjoint_individual_is_rejected(self):
        graph = Graph().parse(ROOT / "core/core.ttl")
        graph.add((EX.bad, RDF.type, PKG.Person))
        graph.add((EX.bad, RDF.type, PKG.Package))
        with self.assertRaisesRegex(AssertionError, "Disjoint classes"):
            expand_checked(graph)

    def test_library_failure_is_not_success(self):
        with patch("reasoning_support.DeductiveClosure") as closure:
            closure.return_value.expand.side_effect = RuntimeError("probe failure")
            with self.assertRaisesRegex(RuntimeError, "probe failure"):
                expand_checked(Graph())

    def test_cli_fails_when_owlrl_is_missing(self):
        code = (
            "import runpy, sys; sys.modules['owlrl'] = None; "
            "runpy.run_path('scripts/test-owl2-reasoning.py', run_name='__main__')"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT,
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("owlrl not installed", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
