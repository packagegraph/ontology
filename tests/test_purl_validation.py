"""Parser boundary regressions; expectations are independently spelled out."""
import unittest

from rdflib import Graph, Literal, Namespace, RDF
from rdflib.namespace import XSD

from test_purl_contract import EX, PKG, fixture
from packagegraph.purls import parse_canonical, validate_graph

RPM = Namespace("https://purl.org/packagegraph/ontology/rpm#")


class ParserTests(unittest.TestCase):
    def test_valid_encoding_qualifiers_and_ecosystems(self):
        for value, name, version in [
            ("pkg:npm/%40scope/widget", "widget", None),
            ("pkg:deb/debian/libc6@1:2.38-1?arch=amd64", "libc6", "1:2.38-1"),
            ("pkg:rpm/fedora/acl@2.0-1?arch=x86_64&epoch=1", "acl", "2.0-1"),
            ("pkg:maven/org.example/widget@1.0?classifier=sources&type=jar", "widget", "1.0"),
            ("pkg:pypi/my-project@1.0", "my-project", "1.0"),
            ("pkg:generic/team/a%2Bb@1%2B2?download_url=https://example.org/a%3Fb%3Dc#src/lib", "a+b", "1+2"),
        ]:
            with self.subTest(value=value):
                parsed = parse_canonical(value)
                self.assertEqual(parsed.name, name)
                self.assertEqual(parsed.version, version)

    def test_invalid_or_noncanonical_inputs_are_rejected(self):
        for value in ["pkg:/name", "pkg:maven/name", "pkg:pypi/My_Project", "pkg:npm/@scope/widget",
                      "pkg:generic/a%ZZ", "pkg:generic/a?x=1&x=2", "pkg:generic/a?z=1&a=2",
                      "pkg:generic/a@", "pkg:generic/a#../src", "pkg:rpm/fedora/a@1:2-3",
                      "pkg:rpm/Fedora/a@1", "pkg:deb/Debian/a@1"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_canonical(value)

    def test_supported_profile_requires_purls_on_collected_entities(self):
        graph = fixture()
        self.assertEqual(validate_graph(graph, profile="rpm"), [])
        graph.remove((EX.old, PKG.purl, None))
        graph.remove((EX.identity, PKG.purl, None))
        errors = validate_graph(graph, profile="rpm")
        self.assertEqual({error.subject for error in errors}, {EX.old, EX.identity})
        self.assertEqual(validate_graph(graph), [])

    def test_unmapped_dependency_identity_does_not_acquire_requirement(self):
        graph = fixture()
        graph.add((EX.capability, RDF.type, PKG.PackageIdentity))
        graph.add((EX.old, PKG.directlyDependsOn, EX.capability))
        self.assertEqual(validate_graph(graph, profile="rpm"), [])

    def test_wrong_roles_types_and_literal_datatypes_are_rejected(self):
        for subject, value in [(EX.identity, "pkg:rpm/almalinux/acl@1"),
                               (EX.old, "pkg:rpm/almalinux/acl"),
                               (EX.old, "pkg:deb/debian/acl@1")]:
            graph = fixture()
            graph.set((subject, PKG.purl, Literal(value, datatype=XSD.anyURI)))
            with self.subTest(value=value):
                self.assertTrue(validate_graph(graph, profile="rpm"))
        graph = fixture()
        graph.set((EX.identity, PKG.purl, Literal("pkg:rpm/almalinux/acl?arch=aarch64")))
        self.assertTrue(validate_graph(graph))

    def test_source_and_maven_dependencies_are_in_profile(self):
        graph = fixture()
        graph.add((EX.source, RDF.type, PKG.SourcePackage))
        graph.add((EX.old, PKG.builtFromSource, EX.source))
        errors = validate_graph(graph, profile="rpm")
        self.assertIn(EX.source, {error.subject for error in errors})
        graph = fixture()
        graph.add((EX.maven, RDF.type, Namespace("https://purl.org/packagegraph/ontology/maven#").MavenArtifact))
        graph.add((EX.maven, PKG.directlyDependsOn, EX.dep))
        graph.add((EX.dep, RDF.type, PKG.PackageIdentity))
        self.assertIn(EX.dep, {error.subject for error in validate_graph(graph, profile="maven")})

    def test_source_only_exports_require_purls(self):
        for profile, kind in (("rpm", RPM.SourceRPM), ("deb", PKG.SourcePackage)):
            graph = Graph()
            graph.add((EX.source, RDF.type, kind))
            with self.subTest(profile=profile):
                self.assertEqual({error.subject for error in validate_graph(graph, profile)}, {EX.source})
            graph.add((EX.source, PKG.purl, Literal(f"pkg:{profile}/vendor/source", datatype=XSD.anyURI)))
            self.assertTrue(validate_graph(graph, profile))


if __name__ == "__main__":
    unittest.main()
