"""PURL placement, completeness and forbidden-inference regressions."""
import unittest
from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS
from rdflib.namespace import XSD

ROOT = Path(__file__).resolve().parents[1]
PKG = Namespace("https://purl.org/packagegraph/ontology/core#")
EX = Namespace("https://example.org/purl/")


def fixture():
    return Graph().parse(ROOT / "tests/fixtures/purls/two-versions.ttl")


class ContractTests(unittest.TestCase):
    def conforms(self, graph):
        return validate(graph, shacl_graph=str(ROOT / "core/core.shacl.ttl"),
                        ont_graph=str(ROOT / "core/core.ttl"), inference="rdfs",
                        allow_warnings=True, allow_infos=True)[0]

    def test_two_versions_share_one_versionless_identity(self):
        self.assertTrue(self.conforms(fixture()))

    def test_incomplete_identity_has_no_global_purl_requirement(self):
        graph = Graph()
        graph.add((EX.incomplete, RDF.type, PKG.PackageIdentity))
        graph.add((EX.incomplete, PKG.identityName, Literal("virtual-capability")))
        graph.add((EX.incomplete, RDFS.label, Literal("virtual-capability")))
        self.assertTrue(self.conforms(graph))

    def test_identity_rejects_versioned_purl(self):
        graph = fixture()
        graph.set((EX.identity, PKG.purl, Literal("pkg:rpm/almalinux/acl@2.0", datatype=XSD.anyURI)))
        self.assertFalse(self.conforms(graph))

    def test_package_rejects_versionless_purl(self):
        graph = fixture()
        graph.set((EX.old, PKG.purl, Literal("pkg:rpm/almalinux/acl", datatype=XSD.anyURI)))
        self.assertFalse(self.conforms(graph))

    def test_purl_does_not_collapse_package_and_identity_types(self):
        graph = fixture().parse(ROOT / "core/core.ttl")
        graph.add((EX.untyped, PKG.purl, Literal("pkg:generic/example", datatype=XSD.anyURI)))
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        for subject in (EX.identity, EX.old, EX.new, EX.untyped):
            self.assertIn((subject, RDF.type, PKG.PackageEntity), graph)
        for package in (EX.old, EX.new):
            self.assertNotIn((package, RDF.type, PKG.PackageIdentity), graph)
        for subject in (EX.identity, EX.untyped):
            self.assertNotIn((subject, RDF.type, PKG.Package), graph)
        self.assertNotIn((EX.untyped, RDF.type, PKG.PackageIdentity), graph)


if __name__ == "__main__":
    unittest.main()
