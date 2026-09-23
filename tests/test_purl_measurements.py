"""Execute the production PURL query on small, graph-isolated datasets."""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from rdflib import Dataset

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "measure_purls.py"


class PurlMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SCRIPT.exists():
            raise AssertionError("The reproducible measurement CLI has not been implemented")
        spec = importlib.util.spec_from_file_location("measure_purls", SCRIPT)
        cls.measure = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.measure)

    def query(self, trig, graph=None):
        dataset = Dataset()
        dataset.parse(data=trig, format="trig")
        result = dataset.query(self.measure.count_query(graph))
        return json.loads(result.serialize(format="json"))

    def test_counts_subjects_with_missing_multiple_and_mixed_version_markers(self):
        result = self.query("""
            @prefix pkg: <https://purl.org/packagegraph/ontology/core#> .
            @prefix ex: <https://example.test/> .
            ex:g {
                ex:i1 a pkg:PackageIdentity .
                ex:i2 a pkg:PackageIdentity; pkg:purl "pkg:pypi/a" .
                ex:i3 a pkg:PackageIdentity; pkg:purl "pkg:pypi/b@1" .
                ex:i4 a pkg:PackageIdentity;
                    pkg:purl "pkg:pypi/c", "pkg:pypi/c@2" .
                ex:p1 a pkg:Package .
                ex:p2 a pkg:Package, pkg:BinaryPackage;
                    pkg:purl "pkg:deb/a@1", "pkg:deb/a@2" .
                ex:p3 a pkg:SourcePackage; pkg:purl "pkg:deb/source" .
                ex:untyped pkg:purl "pkg:pypi/untyped@1" .
            }
        """)
        rows = self.measure.decode_counts(result, "https://example.test/g")
        self.assertEqual(rows["identity"], {
            "denominator": 4, "with_purl": 3, "missing_purl": 1,
            "multiple_purls": 1, "with_version_marker": 2,
            "without_version_marker": 2,
        })
        self.assertEqual(rows["package"], {
            "denominator": 3, "with_purl": 2, "missing_purl": 1,
            "multiple_purls": 1, "with_version_marker": 1,
            "without_version_marker": 1,
        })

    def test_purl_in_another_graph_cannot_fill_a_missing_value(self):
        trig = """
            @prefix pkg: <https://purl.org/packagegraph/ontology/core#> .
            @prefix ex: <https://example.test/> .
            ex:g1 { ex:i a pkg:PackageIdentity . }
            ex:g2 { ex:i a pkg:PackageIdentity; pkg:purl "pkg:pypi/a" . }
            ex:g3 { ex:i pkg:purl "pkg:pypi/a@1" . }
            ex:default a pkg:PackageIdentity; pkg:purl "pkg:pypi/default" .
        """
        rows = self.measure.decode_counts(self.query(trig, "https://example.test/g1"),
                                          "https://example.test/g1")
        self.assertEqual(rows["identity"]["denominator"], 1)
        self.assertEqual(rows["identity"]["missing_purl"], 1)
        self.assertEqual(rows["identity"]["with_purl"], 0)
        self.assertEqual(rows["package"]["denominator"], 0)
        rows = self.measure.decode_counts(self.query(trig, "https://example.test/g2"),
                                          "https://example.test/g2")
        self.assertEqual(rows["identity"]["multiple_purls"], 0)
        self.assertEqual(rows["identity"]["with_version_marker"], 0)

    def test_scope_qualifiers_subpaths_and_encoded_at_are_not_versions(self):
        result = self.query("""
            @prefix pkg: <https://purl.org/packagegraph/ontology/core#> .
            @prefix ex: <https://example.test/> .
            ex:g {
                ex:p1 a pkg:Package; pkg:purl "pkg:npm/@scope/name" .
                ex:p2 a pkg:Package; pkg:purl "pkg:generic/a?download_url=https://x/@1" .
                ex:p3 a pkg:Package; pkg:purl "pkg:generic/a#directory/@1" .
                ex:p4 a pkg:Package; pkg:purl "pkg:generic/a%40b" .
                ex:p5 a pkg:Package; pkg:purl "pkg:npm/%40scope/name@1?arch=x#lib" .
                ex:p6 a pkg:Package; pkg:purl "pkg:npm/@scope/name@1" .
            }
        """)
        rows = self.measure.decode_counts(result, "https://example.test/g")
        self.assertEqual(rows["package"]["denominator"], 6)
        self.assertEqual(rows["package"]["with_version_marker"], 2)
        self.assertEqual(rows["package"]["without_version_marker"], 4)

    def test_failed_query_is_unknown_and_does_not_prevent_other_graph_counts(self):
        success = self.query("""
            @prefix pkg: <https://purl.org/packagegraph/ontology/core#> .
            <https://example.test/good> { <urn:p> a pkg:Package . }
        """)
        with patch.object(self.measure, "query_endpoint", side_effect=[TimeoutError("timed out"), success]):
            report = self.measure.measure("https://example.test/sparql", 5,
                                          ["https://example.test/bad", "https://example.test/good"])
        self.assertFalse(report["complete"])
        self.assertEqual(report["graphs"][0]["status"], "error")
        self.assertIsNone(report["graphs"][0]["counts"])
        self.assertEqual(report["graphs"][1]["counts"]["package"]["denominator"], 1)

    def test_discovery_only_selects_named_graphs_with_explicit_target_types(self):
        dataset = Dataset()
        dataset.parse(data="""
            @prefix pkg: <https://purl.org/packagegraph/ontology/core#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix ex: <https://example.test/> .
            ex:included { ex:p a pkg:BinaryPackage . }
            ex:untyped { ex:i pkg:purl "pkg:pypi/a" . }
            ex:subclass {
                ex:SpecialPackage rdfs:subClassOf pkg:Package .
                ex:s a ex:SpecialPackage .
            }
            ex:default a pkg:PackageIdentity .
        """, format="trig")
        response = json.loads(dataset.query(self.measure.DISCOVERY_QUERY).serialize(format="json"))
        self.assertEqual([row["graph"]["value"] for row in response["results"]["bindings"]],
                         ["https://example.test/included"])

    def test_discovery_failure_is_incomplete_not_an_empty_success(self):
        with patch.object(self.measure, "query_endpoint", side_effect=TimeoutError("timed out")):
            report = self.measure.measure("https://example.test/sparql", 5)
        self.assertFalse(report["complete"])
        self.assertEqual(report["discovery"]["status"], "error")
        self.assertEqual(report["graphs"], [])

    def test_malformed_or_truncated_response_is_not_a_zero_count(self):
        for response in ({}, {"head": {"vars": []}, "results": {"bindings": []},
                              "meta": {"result-size-total": 2}}):
            with self.subTest(response=response), self.assertRaises(ValueError):
                self.measure.decode_counts(response, "https://example.test/g")

    def test_graph_iri_cannot_inject_a_second_query(self):
        with self.assertRaises(ValueError):
            self.measure.count_query("https://example.test/> } UNION { ?s ?p ?o")


if __name__ == "__main__":
    unittest.main()
