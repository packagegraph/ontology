"""Execute documented competency queries against regression fixtures."""

import re
import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace

ROOT = Path(__file__).resolve().parents[1]
EX = Namespace("https://example.org/cq-xd-04/")


def documented_query(cq_id):
    """Read the executable query from its CQ section, without a test copy."""
    document = (ROOT / "docs/competency-questions.md").read_text()
    section = re.search(
        rf"^### {re.escape(cq_id)}:.*?(?=^### |\Z)",
        document,
        re.MULTILINE | re.DOTALL,
    )
    if section is None:
        raise ValueError(f"Missing competency question: {cq_id}")
    query = re.search(r"```sparql\n(.*?)\n```", section.group(), re.DOTALL)
    if query is None:
        raise ValueError(f"Missing SPARQL query: {cq_id}")
    return query.group(1)


class SharedUpstreamProjectsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        graph = Graph().parse(ROOT / "tests/competency-questions/cq-xd-04.ttl")
        cls.rows = [row.asdict() for row in graph.query(documented_query("CQ-XD-04"))]

    def test_same_name_projects_do_not_combine_distribution_counts(self):
        # GitHub covers Fedora + Debian; unrelated GitLab covers Arch only.
        self.assertEqual(
            [row for row in self.rows if row["projectName"] == Literal("acme/widget")],
            [],
        )

    def test_project_in_three_distributions_returns_its_identity(self):
        rows = [
            {**row, "distros": set(str(row["distros"]).split(", "))}
            for row in self.rows
            if row["projectName"] == Literal("acme/shared")
        ]
        self.assertEqual(rows, [{
            "upstream": EX.sharedProject,
            "projectName": Literal("acme/shared"),
            "distroCount": Literal(3),
            "distros": {"Fedora", "Debian", "Arch Linux"},
        }])

    def test_multiple_versions_and_releases_in_one_distribution_do_not_qualify(self):
        self.assertEqual(
            [row for row in self.rows if row["projectName"] == Literal("acme/single")],
            [],
        )


if __name__ == "__main__":
    unittest.main()
