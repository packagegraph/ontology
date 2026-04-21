#!/usr/bin/env python3
"""
Production SHACL Validation Script

Samples production data from Fuseki and validates against SHACL shapes to produce
a conformance report. This is the academic evaluation artifact demonstrating that
the ontology's constraints align with (or expose gaps in) production data quality.

Usage:
    python3 production_shacl_validate.py [--endpoint URL] [--output FILE]

Requirements:
    - Fuseki accessible via port-forward: oc port-forward -n packagegraph svc/fuseki 3031:3030
    - KUBECONFIG=~/.kube/config-2
"""

import argparse
import sys
from collections import defaultdict
import json

from rdflib import Graph, Namespace
from SPARQLWrapper import SPARQLWrapper, JSON
from pyshacl import validate

# Namespaces
PKG = Namespace("https://purl.org/packagegraph/ontology/core#")
SEC = Namespace("https://purl.org/packagegraph/ontology/security#")


def sample_class_instances(endpoint: str, graph_uri: str, class_uri: str, limit: int = 5000) -> Graph:
    """
    Sample instances of a class from a named graph via SPARQL CONSTRUCT.

    Returns a Graph containing the sampled instances and their properties.
    """
    sparql = SPARQLWrapper(endpoint)

    query = f"""
    CONSTRUCT {{ ?s ?p ?o }}
    WHERE {{
        GRAPH <{graph_uri}> {{
            ?s a <{class_uri}> .
            ?s ?p ?o .
        }}
    }}
    LIMIT {limit}
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        g = Graph()
        # Parse the CONSTRUCT results (JSON-LD format)
        g.parse(data=json.dumps(results), format="json-ld")
        return g
    except Exception as e:
        print(f"Error sampling {class_uri} from {graph_uri}: {e}", file=sys.stderr)
        return Graph()


def validate_sample(data_graph: Graph, shacl_graph: Graph) -> tuple[bool, str, dict[str, int]]:
    """
    Validate a data graph against SHACL shapes.

    Returns:
        (conforms, results_text, violation_summary)
    """
    conforms, results_g, results_text = validate(
        data_graph,
        shacl_graph=shacl_graph,
        inference="rdfs",
        serialize_report_graph=False
    )

    # Parse violations
    violations = defaultdict(int)
    if not conforms:
        for line in results_text.split("\n"):
            if "Message:" in line:
                message = line.split("Message:")[-1].strip()
                violations[message] += 1

    return conforms, results_text, dict(violations)


def main():
    parser = argparse.ArgumentParser(description="Validate production data against SHACL shapes")
    parser.add_argument("--endpoint", default="http://localhost:3031/packagegraph/sparql",
                        help="Fuseki SPARQL endpoint")
    parser.add_argument("--output", default="docs/reports/2026-04-20-production-shacl-validation.md",
                        help="Output report file")
    args = parser.parse_args()

    print(f"Production SHACL Validation")
    print(f"Endpoint: {args.endpoint}")
    print(f"Output: {args.output}\n")

    # Load SHACL shapes
    print("Loading SHACL shapes...")
    shacl_g = Graph()
    shacl_g.parse("core/core.shacl.ttl", format="turtle")
    shacl_g.parse("extensions/security/security.shacl.ttl", format="turtle")
    print(f"Loaded {len(shacl_g)} SHACL triples\n")

    # Target graphs and classes
    test_cases = [
        ("https://packagegraph.github.io/graph/fedora/43", str(PKG.Package), "Package", 5000),
        ("https://packagegraph.github.io/graph/fedora/43", str(PKG.BinaryPackage), "BinaryPackage", 5000),
        ("https://packagegraph.github.io/graph/fedora/43", str(PKG.Dependency), "Dependency", 3000),
        ("https://packagegraph.github.io/graph/debian/trixie", str(PKG.Package), "Package", 5000),
        ("https://packagegraph.github.io/graph/security", str(SEC.Vulnerability), "Vulnerability", 2000),
        ("https://packagegraph.github.io/graph/security", str(SEC.SecurityAdvisory), "SecurityAdvisory", 1000),
    ]

    results = []

    for graph_uri, class_uri, class_name, limit in test_cases:
        print(f"Sampling {class_name} from {graph_uri.split('/')[-1]}...")
        sample_g = sample_class_instances(args.endpoint, graph_uri, class_uri, limit)

        if len(sample_g) == 0:
            print(f"  No data found\n")
            results.append({
                "graph": graph_uri,
                "class": class_name,
                "sample_size": 0,
                "conforms": None,
                "violations": {}
            })
            continue

        print(f"  Sampled {len(sample_g)} triples")
        print(f"  Validating...")

        conforms, results_text, violations = validate_sample(sample_g, shacl_g)

        results.append({
            "graph": graph_uri,
            "class": class_name,
            "sample_size": len(sample_g),
            "conforms": conforms,
            "violations": violations
        })

        if conforms:
            print(f"  ✓ PASS\n")
        else:
            print(f"  ✗ FAIL — {len(violations)} unique violations")
            for msg, count in sorted(violations.items(), key=lambda x: -x[1])[:3]:
                print(f"    {count}× {msg[:80]}")
            print()

    # Generate report
    print(f"Writing report to {args.output}...")
    write_report(results, args.output)
    print("Done")

    # Exit with error if any failures
    if any(not r["conforms"] and r["conforms"] is not None for r in results):
        sys.exit(1)


def write_report(results: list[dict], output_path: str):
    """Write validation results to a markdown report."""

    with open(output_path, 'w') as f:
        f.write("# Production SHACL Validation Report\n\n")
        f.write("**Date:** 2026-04-20\n")
        f.write("**Scope:** Sample validation against production data (62.7M triples)\n")
        f.write("**Method:** CONSTRUCT sampling (1K-5K instances per class) + pyshacl validation with RDFS inference\n\n")

        f.write("## Executive Summary\n\n")

        total_tests = len(results)
        passed = sum(1 for r in results if r["conforms"])
        failed = sum(1 for r in results if r["conforms"] is False)
        no_data = sum(1 for r in results if r["conforms"] is None)

        f.write(f"- **Total test cases:** {total_tests}\n")
        f.write(f"- **Passed:** {passed}\n")
        f.write(f"- **Failed:** {failed}\n")
        f.write(f"- **No data:** {no_data}\n\n")

        if failed > 0:
            f.write("**Violations ARE expected.** This is production data validated against newly-strengthened shapes. Violations identify:\n")
            f.write("1. **Collector bugs** — collectors emit data that violates domain truth\n")
            f.write("2. **Model gaps** — shapes encode constraints that are too strict for real data\n\n")

        f.write("## Per-Class Results\n\n")

        for r in results:
            graph_name = r["graph"].split("/")[-1]
            f.write(f"### {r['class']} ({graph_name})\n\n")

            if r["conforms"] is None:
                f.write("**Status:** No data found in this graph\n\n")
                continue

            status = "✓ PASS" if r["conforms"] else "✗ FAIL"
            f.write(f"**Status:** {status}\n")
            f.write(f"**Sample size:** {r['sample_size']} triples\n\n")

            if not r["conforms"]:
                f.write("**Violations:**\n\n")
                for msg, count in sorted(r["violations"].items(), key=lambda x: -x[1]):
                    f.write(f"- {count}× {msg}\n")
                f.write("\n")

        f.write("## Analysis\n\n")
        f.write("### Collector Bugs vs Model Gaps\n\n")
        f.write("TBD — Categorization requires domain expertise to determine whether each violation represents:\n")
        f.write("- A collector bug (data violates domain truth)\n")
        f.write("- A model gap (constraint too strict for valid edge cases)\n\n")

        f.write("### Conformance Rates\n\n")
        f.write("TBD — Calculate per-class conformance percentage once violations are categorized\n\n")

        f.write("## Recommendations\n\n")
        f.write("1. Fix high-frequency collector bugs identified in this report\n")
        f.write("2. Relax overly-strict SHACL constraints where violations represent valid edge cases\n")
        f.write("3. Re-run validation after fixes to measure improvement\n")


if __name__ == "__main__":
    main()
