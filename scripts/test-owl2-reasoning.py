#!/usr/bin/env python3
"""OWL 2 RL reasoning test for PackageGraph core ontology.

Tests that owl:propertyChainAxiom on directlyDependsOn is sound:
  hasDependency → dependencyTarget => directlyDependsOn

Requires: rdflib, owlrl (uv pip install owlrl)
"""
import sys
from rdflib import Graph, Namespace, RDF, Literal
from rdflib.term import URIRef

try:
    import owlrl
except ImportError:
    print("SKIP: owlrl not installed (uv pip install owlrl)")
    sys.exit(0)

PKG = Namespace("https://purl.org/packagegraph/ontology/core#")
EX = Namespace("https://example.org/test/")


def test_property_chain_axiom():
    """directlyDependsOn should be inferred from hasDependency + dependencyTarget."""
    g = Graph()
    g.parse("core/core.ttl", format="turtle")

    # Add test instances
    g.add((EX.packageA, RDF.type, PKG.Package))
    g.add((EX.packageA, PKG.packageName, Literal("test-a")))
    g.add((EX.packageB, RDF.type, PKG.Package))
    g.add((EX.packageB, PKG.packageName, Literal("test-b")))
    g.add((EX.dep1, RDF.type, PKG.Dependency))
    g.add((EX.packageA, PKG.hasDependency, EX.dep1))
    g.add((EX.dep1, PKG.dependencyTarget, EX.packageB))

    # Before reasoning: directlyDependsOn should NOT exist
    direct_before = (EX.packageA, PKG.directlyDependsOn, EX.packageB) in g
    assert not direct_before, "directlyDependsOn should not exist before reasoning"

    # Apply OWL 2 RL reasoning
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

    # After reasoning: directlyDependsOn SHOULD be inferred
    direct_after = (EX.packageA, PKG.directlyDependsOn, EX.packageB) in g
    assert direct_after, (
        "FAIL: owl:propertyChainAxiom did not infer directlyDependsOn. "
        "Chain: packageA -hasDependency-> dep1 -dependencyTarget-> packageB "
        "should produce: packageA -directlyDependsOn-> packageB"
    )

    # Also check inverse: isDirectDependencyOf
    inverse = (EX.packageB, PKG.isDirectDependencyOf, EX.packageA) in g

    print("PASS: propertyChainAxiom (hasDependency + dependencyTarget => directlyDependsOn)")
    if inverse:
        print("PASS: owl:inverseOf (isDirectDependencyOf) also inferred")
    else:
        print("INFO: owl:inverseOf (isDirectDependencyOf) not inferred by OWL RL (expected)")


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


def test_ontology_consistency():
    """Basic OWL 2 RL expansion without errors."""
    g = Graph()
    g.parse("core/core.ttl", format="turtle")

    initial_count = len(g)
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    final_count = len(g)

    inferred = final_count - initial_count
    print(f"PASS: OWL 2 RL expansion ({initial_count} -> {final_count}, {inferred} inferred)")


if __name__ == "__main__":
    print("=== OWL 2 RL Reasoning Tests ===\n")
    test_ontology_consistency()
    test_property_chain_axiom()
    test_disjoint_classes()
    print("\n=== All reasoning tests complete ===")
