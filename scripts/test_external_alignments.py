"""Semantic regressions for the supported core/security/alignment bundle."""

import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL
from rdflib.namespace import XSD

from reasoning_support import expand_checked

ROOT = Path(__file__).resolve().parents[1]
PKG = Namespace("https://purl.org/packagegraph/ontology/core#")
SEC = Namespace("https://purl.org/packagegraph/ontology/security#")
PROV = Namespace("http://www.w3.org/ns/prov#")
SCHEMA = Namespace("https://schema.org/")
EX = Namespace("https://example.org/alignment-tests/")
MAPPINGS = (
    (PKG.builtFromSource, PROV.wasDerivedFrom, EX.source),
    (PKG.performedBy, PROV.wasAssociatedWith, EX.agent),
    (PKG.description, SCHEMA.description, Literal("description")),
    (PKG.homepage, SCHEMA.url, Literal("https://example.org/", datatype=XSD.anyURI)),
    (PKG.packageName, SCHEMA.name, Literal("package-name")),
    (PKG.versionString, SCHEMA.version, Literal("1.0")),
)


def load_bundle():
    graph = Graph()
    for relative in (
        "core/core.ttl", "extensions/security/security.ttl", "references/alignments.ttl"
    ):
        graph.parse(ROOT / relative, format="turtle")
    return graph


class ExternalAlignmentTests(unittest.TestCase):
    def test_only_forward_subproperty_axioms(self):
        graph = load_bundle()
        for local, external, _ in MAPPINGS:
            with self.subTest(local=local):
                self.assertIn((local, RDFS.subPropertyOf, external), graph)
                self.assertNotIn((local, OWL.equivalentProperty, external), graph)
                self.assertNotIn((external, OWL.equivalentProperty, local), graph)
                self.assertNotIn((external, RDFS.subPropertyOf, local), graph)

    def test_every_local_mapping_still_exports(self):
        for local, external, value in MAPPINGS:
            with self.subTest(local=local):
                graph = load_bundle()
                graph.add((EX.localSubject, local, value))
                expand_checked(graph)
                self.assertIn((EX.localSubject, external, value), graph)

    def test_external_statements_do_not_acquire_local_semantics(self):
        for local, external, value in MAPPINGS:
            with self.subTest(external=external):
                graph = load_bundle()
                graph.add((EX.externalSubject, external, value))
                expand_checked(graph)
                self.assertNotIn((EX.externalSubject, local, value), graph)
                for kind in (PKG.Package, PKG.BinaryPackage, PKG.SourcePackage,
                             PKG.Version, PKG.PackagingActivity):
                    self.assertNotIn((EX.externalSubject, RDF.type, kind), graph)

    def test_person_can_have_multiple_external_names(self):
        graph = load_bundle()
        graph.add((EX.person, RDF.type, PKG.Person))
        graph.add((EX.person, SCHEMA.name, Literal("Alice")))
        graph.add((EX.person, SCHEMA.name, Literal("Alicia")))
        expand_checked(graph)
        self.assertNotIn((EX.person, RDF.type, PKG.Package), graph)
        self.assertEqual(list(graph.objects(EX.person, PKG.packageName)), [])

    def test_source_rebuild_preserves_provenance_without_binary_typing(self):
        graph = load_bundle()
        graph.add((EX.downstream, PKG.rebuildOf, EX.upstream))
        expand_checked(graph)
        self.assertIn((EX.downstream, PROV.wasDerivedFrom, EX.upstream), graph)
        self.assertIn((EX.downstream, RDF.type, PKG.SourcePackage), graph)
        self.assertNotIn((EX.downstream, RDF.type, PKG.BinaryPackage), graph)

    def test_successive_patch_versions_do_not_become_packages(self):
        graph = load_bundle()
        graph.add((EX.v3, SEC.patchedFrom, EX.v2))
        graph.add((EX.v2, SEC.patchedFrom, EX.v1))
        expand_checked(graph)
        self.assertIn((EX.v3, PROV.wasDerivedFrom, EX.v2), graph)
        self.assertIn((EX.v2, PROV.wasDerivedFrom, EX.v1), graph)
        for version in (EX.v1, EX.v2, EX.v3):
            self.assertIn((version, RDF.type, PKG.Version), graph)
            self.assertNotIn((version, RDF.type, PKG.Package), graph)


if __name__ == "__main__":
    unittest.main()
