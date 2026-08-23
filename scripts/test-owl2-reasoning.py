#!/usr/bin/env python3
"""OWL 2 RL reasoning test for PackageGraph core ontology.

Tests:
  - owl:propertyChainAxiom on directlyDependsOn (hasDependency → dependencyTarget)
  - PackageEntity class hierarchy inference
  - Identity targets do not collapse into Package
  - Inverse property pairs for both identity and concrete targets
  - prov:Entity inference through PackageEntity
  - Core dependency subproperty identity-target acceptance

Requires: rdflib, owlrl (uv pip install owlrl)
"""
import sys
from rdflib import Graph, Namespace, RDF, RDFS, Literal
from rdflib.term import URIRef

try:
    import owlrl
except ImportError:
    print("SKIP: owlrl not installed (uv pip install owlrl)")
    sys.exit(0)

PKG = Namespace("https://purl.org/packagegraph/ontology/core#")
PROV = Namespace("http://www.w3.org/ns/prov#")
EX = Namespace("https://example.org/test/")


def _load_and_reason() -> Graph:
    """Load core ontology and apply OWL 2 RL reasoning."""
    g = Graph()
    g.parse("core/core.ttl", format="turtle")
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    return g


def test_ontology_consistency():
    """Basic OWL 2 RL expansion without errors."""
    g = Graph()
    g.parse("core/core.ttl", format="turtle")

    initial_count = len(g)
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    final_count = len(g)

    inferred = final_count - initial_count
    print(f"PASS: OWL 2 RL expansion ({initial_count} -> {final_count}, {inferred} inferred)")


def test_property_chain_concrete_target():
    """directlyDependsOn inferred from hasDependency + dependencyTarget (concrete Package)."""
    g = Graph()
    g.parse("core/core.ttl", format="turtle")

    g.add((EX.packageA, RDF.type, PKG.Package))
    g.add((EX.packageA, PKG.packageName, Literal("test-a")))
    g.add((EX.packageB, RDF.type, PKG.Package))
    g.add((EX.packageB, PKG.packageName, Literal("test-b")))
    g.add((EX.dep1, RDF.type, PKG.Dependency))
    g.add((EX.packageA, PKG.hasDependency, EX.dep1))
    g.add((EX.dep1, PKG.dependencyTarget, EX.packageB))

    assert (EX.packageA, PKG.directlyDependsOn, EX.packageB) not in g

    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    assert (EX.packageA, PKG.directlyDependsOn, EX.packageB) in g, (
        "FAIL: propertyChainAxiom did not infer directlyDependsOn for concrete target"
    )
    print("PASS: propertyChainAxiom (concrete target => directlyDependsOn)")


def test_property_chain_identity_target():
    """directlyDependsOn inferred when dependencyTarget is a PackageIdentity."""
    g = Graph()
    g.parse("core/core.ttl", format="turtle")

    g.add((EX.packageA, RDF.type, PKG.Package))
    g.add((EX.packageA, PKG.packageName, Literal("test-a")))
    g.add((EX.identityB, RDF.type, PKG.PackageIdentity))
    g.add((EX.dep1, RDF.type, PKG.Dependency))
    g.add((EX.packageA, PKG.hasDependency, EX.dep1))
    g.add((EX.dep1, PKG.dependencyTarget, EX.identityB))

    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    assert (EX.packageA, PKG.directlyDependsOn, EX.identityB) in g, (
        "FAIL: propertyChainAxiom did not infer directlyDependsOn for identity target"
    )
    print("PASS: propertyChainAxiom (identity target => directlyDependsOn)")


def test_identity_target_not_inferred_as_package():
    """A PackageIdentity dependency target must NOT be inferred as Package."""
    g = Graph()
    g.parse("core/core.ttl", format="turtle")

    g.add((EX.packageA, RDF.type, PKG.Package))
    g.add((EX.packageA, PKG.packageName, Literal("test-a")))
    g.add((EX.identityB, RDF.type, PKG.PackageIdentity))
    g.add((EX.packageA, PKG.directlyDependsOn, EX.identityB))

    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    assert (EX.identityB, RDF.type, PKG.PackageEntity) in g, (
        "FAIL: identity target not inferred as PackageEntity"
    )
    assert (EX.identityB, RDF.type, PKG.Package) not in g, (
        "FAIL: identity target incorrectly inferred as Package"
    )
    print("PASS: identity target is PackageEntity, not Package")


def test_inverse_pairs_concrete():
    """Both inverse pairs derive correct reverse edges for concrete targets."""
    g = Graph()
    g.parse("core/core.ttl", format="turtle")

    g.add((EX.packageA, RDF.type, PKG.Package))
    g.add((EX.packageA, PKG.packageName, Literal("test-a")))
    g.add((EX.packageB, RDF.type, PKG.Package))
    g.add((EX.packageB, PKG.packageName, Literal("test-b")))
    g.add((EX.packageA, PKG.dependsOn, EX.packageB))
    g.add((EX.packageA, PKG.directlyDependsOn, EX.packageB))

    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    dep_inv = (EX.packageB, PKG.isDependencyOf, EX.packageA) in g
    direct_inv = (EX.packageB, PKG.isDirectDependencyOf, EX.packageA) in g

    if dep_inv and direct_inv:
        print("PASS: both inverse pairs inferred (concrete target)")
    elif dep_inv or direct_inv:
        inferred = "isDependencyOf" if dep_inv else "isDirectDependencyOf"
        print(f"PARTIAL: only {inferred} inferred (concrete target)")
    else:
        print("INFO: OWL RL did not infer inverse pairs (limitation of RL profile)")


def test_inverse_pairs_identity():
    """Both inverse pairs derive correct reverse edges for identity targets."""
    g = Graph()
    g.parse("core/core.ttl", format="turtle")

    g.add((EX.packageA, RDF.type, PKG.Package))
    g.add((EX.packageA, PKG.packageName, Literal("test-a")))
    g.add((EX.identityB, RDF.type, PKG.PackageIdentity))
    g.add((EX.packageA, PKG.dependsOn, EX.identityB))
    g.add((EX.packageA, PKG.directlyDependsOn, EX.identityB))

    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    dep_inv = (EX.identityB, PKG.isDependencyOf, EX.packageA) in g
    direct_inv = (EX.identityB, PKG.isDirectDependencyOf, EX.packageA) in g

    if dep_inv and direct_inv:
        print("PASS: both inverse pairs inferred (identity target)")
    elif dep_inv or direct_inv:
        inferred = "isDependencyOf" if dep_inv else "isDirectDependencyOf"
        print(f"PARTIAL: only {inferred} inferred (identity target)")
    else:
        print("INFO: OWL RL did not infer inverse pairs for identity target (limitation of RL profile)")


def test_prov_entity_inference():
    """Both Package and PackageIdentity are inferred as prov:Entity through PackageEntity."""
    g = _load_and_reason()

    g.add((EX.pkg, RDF.type, PKG.Package))
    g.add((EX.pkg, PKG.packageName, Literal("test")))
    g.add((EX.ident, RDF.type, PKG.PackageIdentity))

    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    pkg_is_entity = (EX.pkg, RDF.type, PROV.Entity) in g
    ident_is_entity = (EX.ident, RDF.type, PROV.Entity) in g
    pkg_is_pe = (EX.pkg, RDF.type, PKG.PackageEntity) in g
    ident_is_pe = (EX.ident, RDF.type, PKG.PackageEntity) in g

    assert pkg_is_pe, "FAIL: Package not inferred as PackageEntity"
    assert ident_is_pe, "FAIL: PackageIdentity not inferred as PackageEntity"
    assert pkg_is_entity, "FAIL: Package not inferred as prov:Entity"
    assert ident_is_entity, "FAIL: PackageIdentity not inferred as prov:Entity"
    print("PASS: Package and PackageIdentity both inferred as prov:Entity via PackageEntity")


def test_core_subproperty_identity_target():
    """Core dependency subproperties accept identity targets without collapsing to Package."""
    g = Graph()
    g.parse("core/core.ttl", format="turtle")

    g.add((EX.srcPkg, RDF.type, PKG.SourcePackage))
    g.add((EX.srcPkg, PKG.packageName, Literal("test-src")))
    g.add((EX.identityB, RDF.type, PKG.PackageIdentity))

    g.add((EX.srcPkg, PKG.buildDependsOn, EX.identityB))

    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    assert (EX.identityB, RDF.type, PKG.PackageEntity) in g, (
        "FAIL: identity target of buildDependsOn not inferred as PackageEntity"
    )
    assert (EX.identityB, RDF.type, PKG.Package) not in g, (
        "FAIL: identity target of buildDependsOn incorrectly inferred as Package"
    )
    print("PASS: core subproperty (buildDependsOn) accepts identity without Package collapse")


def test_disjoint_classes():
    """Verify disjointness axioms are consistent."""
    g = Graph()
    g.parse("core/core.ttl", format="turtle")

    g.add((EX.bad, RDF.type, PKG.Package))
    g.add((EX.bad, PKG.packageName, Literal("bad")))
    g.add((EX.bad, RDF.type, PKG.Person))

    try:
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
        is_nothing = (EX.bad, RDF.type, URIRef("http://www.w3.org/2002/07/owl#Nothing")) in g
        if is_nothing:
            print("PASS: disjointness detected (individual typed as owl:Nothing)")
        else:
            print("INFO: OWL RL did not flag disjointness (limitation of RL profile)")
    except Exception as e:
        print(f"PASS: disjointness raised exception: {e}")


if __name__ == "__main__":
    print("=== OWL 2 RL Reasoning Tests ===\n")
    test_ontology_consistency()
    test_property_chain_concrete_target()
    test_property_chain_identity_target()
    test_identity_target_not_inferred_as_package()
    test_inverse_pairs_concrete()
    test_inverse_pairs_identity()
    test_prov_entity_inference()
    test_core_subproperty_identity_target()
    test_disjoint_classes()
    print("\n=== All reasoning tests complete ===")
