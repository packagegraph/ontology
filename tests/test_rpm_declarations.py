"""Executable RPM declaration profile: structural failures must not pass vacuously."""
import re
import unittest
from pathlib import Path
from urllib.parse import quote

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL, PROV, SH, XSD

ROOT = Path(__file__).resolve().parents[1]
PKG = Namespace("https://purl.org/packagegraph/ontology/core#")
RPM = Namespace("https://purl.org/packagegraph/ontology/rpm#")
EX = Namespace("https://example.org/rpm/")
DATA = "https://packagegraph.github.io/d/"
DECL = URIRef(DATA + "rpm-declaration/" + "a" * 64)
CAP = URIRef(DATA + "capability/rpm/foo")


def fixture():
    return Graph().parse(ROOT / "tests/fixtures/rpm-declarations/contract.ttl")


class DeclarationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "core/core.ttl")
        cls.ontology.parse(ROOT / "ecosystems/rpm/rpm.ttl")
        cls.shapes = Graph().parse(ROOT / "ecosystems/rpm/rpm.shacl.ttl")

    def check(self, graph, expected, focus=None, inference="none"):
        conforms, report, detail = validate(
            graph, shacl_graph=self.shapes, ont_graph=self.ontology,
            inference=inference, allow_warnings=False, allow_infos=False)
        self.assertEqual(conforms, expected, detail)
        if not expected:
            self.assertIn(focus or DECL, set(report.objects(None, SH.focusNode)), detail)

    def kind(self, graph, kind, token="foo"):
        graph.set((DECL, RPM.declarationKind, kind))
        graph.set((DECL, RPM.declaredToken, Literal(token)))
        graph.remove((EX.package, PKG.requiresCapability, None))
        graph.remove((EX.package, PKG.providesCapability, None))
        graph.remove((DECL, RPM.declaredCapability, None))
        if kind != RPM.Obsoletes and not token.startswith("("):
            cap = URIRef(DATA + "capability/rpm/" + quote(token, safe=""))
            graph.add((DECL, RPM.declaredCapability, cap))
            graph.add((cap, RDF.type, PKG.Capability))
            graph.add((cap, PKG.capabilityName, Literal(token)))
            graph.add((cap, RDFS.label, Literal(token)))
            if kind in (RPM.Provides, RPM.Requires):
                predicate = PKG.providesCapability if kind == RPM.Provides else PKG.requiresCapability
                graph.add((EX.package, predicate, cap))

    def test_all_new_terms_are_defined(self):
        classes = (RPM.DependencyDeclaration, RPM.DeclarationKind)
        objects = (RPM.hasDeclaration, RPM.declaringPackage, RPM.declarationKind, RPM.declaredCapability)
        literals = (RPM.declaredToken, RPM.declarationFlags, RPM.declarationEpoch,
                    RPM.declarationVersion, RPM.declarationRelease, RPM.declarationPre)
        for kind, terms in ((OWL.Class, classes), (OWL.ObjectProperty, objects),
                            (OWL.DatatypeProperty, literals)):
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn((term, RDF.type, kind), self.ontology)
        for kind in (RPM.Provides, RPM.Requires, RPM.Conflicts, RPM.Obsoletes):
            self.assertIn((kind, RDF.type, RPM.DeclarationKind), self.ontology)

    def test_positive_fixture_has_focus_and_conforms_in_both_regimes(self):
        self.assertEqual(set(fixture().subjects(RDF.type, RPM.DependencyDeclaration)), {DECL})
        self.assertIn((RPM.DependencyDeclarationShape, SH.targetObjectsOf, RPM.hasDeclaration), self.shapes)
        for regime in ("none", "rdfs"):
            with self.subTest(regime=regime):
                self.check(fixture(), True, inference=regime)

    def test_all_four_kinds_and_opaque_expression(self):
        for kind, token in ((RPM.Provides, "example"), (RPM.Requires, "foo"),
                            (RPM.Conflicts, "foo"), (RPM.Obsoletes, "old-name"),
                            (RPM.Requires, "(foo >= 2 or bar)")):
            with self.subTest(kind=kind, token=token):
                graph = fixture()
                self.kind(graph, kind, token)
                self.check(graph, True)

    def test_prefix_tokens_require_capabilities_without_exceptions(self):
        for token in ("config(foo)", "rtld(GNU_HASH)", "rpmlib(CompressedFileNames)"):
            for kind in (RPM.Provides, RPM.Requires, RPM.Conflicts):
                with self.subTest(token=token, kind=kind):
                    graph = fixture()
                    self.kind(graph, kind, token)
                    self.check(graph, True)
                    graph.remove((DECL, RPM.declaredCapability, None))
                    self.check(graph, False)

    def test_obsoletes_and_expression_reject_capability_links(self):
        for kind, token in ((RPM.Obsoletes, "foo"), (RPM.Requires, "(foo or bar)")):
            graph = fixture()
            self.kind(graph, kind, token)
            graph.add((DECL, RPM.declaredCapability, CAP))
            self.check(graph, False)

    def test_required_fields_cannot_disappear(self):
        for predicate in (RPM.declaredToken, RPM.declarationKind, RPM.declaringPackage,
                          RDFS.label, PROV.wasDerivedFrom, RDF.type):
            with self.subTest(predicate=predicate):
                graph = fixture()
                graph.remove((DECL, predicate, None))
                self.check(graph, False)

    def test_orphaned_optional_fields_cannot_hide_beside_a_valid_declaration(self):
        orphan = URIRef(DATA + "rpm-declaration/" + "c" * 64)
        for predicate, value in (
            (RPM.declarationFlags, Literal("GTE")),
            (RPM.declarationEpoch, Literal(1)),
            (RPM.declarationVersion, Literal(1)),
            (RPM.declarationRelease, Literal(1)),
            (RPM.declarationPre, Literal(1)),
            (RPM.declaredCapability, CAP),
        ):
            with self.subTest(predicate=predicate):
                graph = fixture()  # Nonzero valid focus count cannot conceal the orphan.
                graph.add((orphan, predicate, value))
                self.check(graph, False, orphan)

    def test_declaration_cannot_be_package_or_dependency(self):
        for kind in (PKG.Dependency, RPM.Dependency, PKG.Package, PKG.PackageIdentity, PKG.Capability):
            with self.subTest(kind=kind):
                graph = fixture()
                graph.add((DECL, RDF.type, kind))
                self.check(graph, False)

    def test_single_valued_fields_and_string_datatypes(self):
        for predicate in (RPM.declaredToken, RPM.declarationFlags, RPM.declarationEpoch,
                          RPM.declarationVersion, RPM.declarationRelease, RPM.declarationPre):
            graph = fixture()
            graph.add((DECL, predicate, Literal(1)))
            self.check(graph, False)
        for predicate, extra in ((RPM.declarationKind, RPM.Provides),
                                 (RPM.declaringPackage, EX.other),
                                 (RPM.declaredCapability, EX.other)):
            graph = fixture()
            graph.add((DECL, predicate, extra))
            self.check(graph, False)

    def test_version_attribute_combinations_exhaustively(self):
        fields = (RPM.declarationFlags, RPM.declarationVersion, RPM.declarationEpoch, RPM.declarationRelease)
        values = ("GE", "2", "0", "1")
        for mask in range(16):
            with self.subTest(mask=mask):
                graph = fixture()
                for index, (predicate, value) in enumerate(zip(fields, values)):
                    if mask & (1 << index):
                        graph.add((DECL, predicate, Literal(value)))
                self.check(graph, mask == 0 or mask & 3 == 3)

    def test_createrepo_flags_and_unsupported_ne(self):
        for flag in ("EQ", "GE", "GT", "LE", "LT", "NE", "", "GTE"):
            with self.subTest(flag=flag):
                graph = fixture()
                graph.add((DECL, RPM.declarationFlags, Literal(flag)))
                graph.add((DECL, RPM.declarationVersion, Literal("2")))
                self.check(graph, flag in ("EQ", "GE", "GT", "LE", "LT"))

    def test_empty_pre_is_not_absence_and_is_not_interpreted(self):
        for value in ("", "1", "future-ordering-value"):
            graph = fixture()
            graph.add((DECL, RPM.declarationPre, Literal(value)))
            self.check(graph, True)

    def test_capability_type_name_label_and_uri_are_checked(self):
        for predicate in (RDF.type, PKG.capabilityName, RDFS.label):
            graph = fixture()
            graph.remove((CAP, predicate, None))
            self.check(graph, False, CAP)
        graph = fixture()
        graph.set((CAP, PKG.capabilityName, Literal("different-token")))
        self.check(graph, False)
        graph = fixture()
        wrong = URIRef(DATA + "capability/foo")
        for s, p, o in list(graph):
            if s == CAP or o == CAP:
                graph.remove((s, p, o))
                graph.add((wrong if s == CAP else s, p, wrong if o == CAP else o))
        self.check(graph, False)

    def test_explicit_package_links_are_required_in_both_directions(self):
        graph = fixture()
        graph.remove((EX.package, RPM.hasDeclaration, DECL))
        self.check(graph, False)
        graph = fixture()
        graph.add((EX.other, RPM.hasDeclaration, DECL))
        self.check(graph, False)

    def test_shortcuts_require_the_right_supporting_declaration(self):
        graph = fixture()
        graph.remove((EX.package, PKG.requiresCapability, CAP))
        self.check(graph, False)
        for kind in (RPM.Conflicts, RPM.Obsoletes):
            graph = fixture()
            self.kind(graph, kind)
            graph.add((EX.package, PKG.requiresCapability, CAP))
            self.check(graph, False, EX.package)

    def test_conflict_and_requirement_on_same_capability_can_coexist(self):
        graph = fixture()
        other = URIRef(DATA + "rpm-declaration/" + "b" * 64)
        for _, predicate, value in list(graph.triples((DECL, None, None))):
            graph.add((other, predicate, RPM.Conflicts if predicate == RPM.declarationKind else value))
        graph.add((EX.package, RPM.hasDeclaration, other))
        self.check(graph, True)  # The Requires declaration, not Conflicts, supports the edge.

    def test_legacy_package_projection_is_rejected_for_profile_packages(self):
        for predicate in (PKG.directlyDependsOn, PKG.directlyProvides, PKG.hasDependency,
                          RPM.rpmRequires, RPM.rpmProvides, RPM.rpmConflicts, RPM.rpmObsoletes):
            graph = fixture()
            graph.add((EX.package, predicate, EX.phantom))
            self.check(graph, False, EX.package)

    def test_named_occurrences_not_blank_nodes_or_arbitrary_identifiers(self):
        graph = fixture()
        graph.remove((EX.package, RPM.hasDeclaration, DECL))
        for _, predicate, value in list(graph.triples((DECL, None, None))):
            graph.remove((DECL, predicate, value))
            graph.add((EX.bad, predicate, value))
        graph.add((EX.package, RPM.hasDeclaration, EX.bad))
        self.check(graph, False, EX.bad)

    def test_owl_rl_does_not_turn_references_into_packages_or_resolution(self):
        graph = fixture() + self.ontology
        graph.add((EX.provider, PKG.providesCapability, CAP))
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertNotIn((DECL, RDF.type, PKG.Dependency), graph)
        self.assertNotIn((CAP, RDF.type, PKG.Package), graph)
        self.assertNotIn((CAP, RDF.type, PKG.PackageIdentity), graph)
        self.assertNotIn((EX.package, PKG.directlyDependsOn, EX.provider), graph)
        self.assertIn((EX.package, RDF.type, PKG.Package), graph)

    def test_documented_queries_preserve_occurrences_and_distinguish_obsoletes(self):
        graph = Graph().parse(ROOT / "ecosystems/rpm/rpm.examples.ttl")
        declarations = set(graph.subjects(RDF.type, RPM.DependencyDeclaration))
        self.assertEqual(len(declarations), 9)
        self.check(graph, True)
        self.check(graph, True, inference="rdfs")
        queries = re.findall(r"```sparql\n(.*?)```", (ROOT / "docs/rpm-declaration-contract.md").read_text(), re.S)
        self.assertEqual(len(queries), 2)
        requirements = list(graph.query(queries[0]))
        self.assertEqual(len(requirements), 4)
        constraints = sorted((str(row.flags), str(row.version)) for row in requirements
                             if str(row.capability).endswith("/foo"))
        self.assertEqual(constraints, [("GE", "1"), ("GE", "1"), ("LT", "2")])
        expressions = list(graph.query(queries[1]))
        self.assertEqual(len(expressions), 1)
        self.assertEqual(str(expressions[0].token), "(foo >= 2 or bar)")
        self.assertEqual(expressions[0].kind, RPM.Requires)


if __name__ == "__main__":
    unittest.main()
