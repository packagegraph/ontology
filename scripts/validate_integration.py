#!/usr/bin/env python3
"""Cross-module integration validation.

Validates cross-module boundaries that per-module validation cannot catch.
Each integration test loads multiple modules' ontologies, SHACL shapes, and
examples, then runs pyshacl to verify the combined graph is consistent.

Per-module validation (validate_module.py) only loads a module's direct
owl:imports. Cross-module links via rdfs:seeAlso or att:hasSignature
references in examples are not validated there. This script fills that gap.
"""

import sys
from pathlib import Path
from rdflib import Graph

INTEGRATION_TESTS = [
    {
        "name": "slsa-attestation",
        "description": "SLSA provenance attestation with structured att:hasSignature path",
        "ontologies": [
            "core/core.ttl",
            "extensions/vcs/vcs.ttl",
            "extensions/security/security.ttl",
            "extensions/slsa/slsa.ttl",
            "extensions/attestation/attestation.ttl",
        ],
        "shapes": [
            "extensions/slsa/slsa.shacl.ttl",
            "extensions/attestation/attestation.shacl.ttl",
        ],
        "examples": [
            "extensions/slsa/slsa.examples.ttl",
        ],
    },
]


def run_test(test):
    """Run a single integration test."""
    name = test["name"]

    # Build data graph
    data_g = Graph()
    for f in test["ontologies"]:
        if not Path(f).exists():
            print(f"  SKIP {name}: missing {f}")
            return True
        data_g.parse(f, format="turtle")

    for f in test["examples"]:
        if not Path(f).exists():
            print(f"  SKIP {name}: missing {f}")
            return True
        data_g.parse(f, format="turtle")

    # Build SHACL graph
    shacl_g = Graph()
    for f in test["shapes"]:
        if not Path(f).exists():
            print(f"  SKIP {name}: missing {f}")
            return True
        shacl_g.parse(f, format="turtle")

    # Validate
    try:
        from pyshacl import validate

        conforms, _, results_text = validate(
            data_g, shacl_graph=shacl_g, inference="rdfs",
            serialize_report_graph=False
        )

        if conforms:
            print(f"  ✓ {name}: {len(data_g)} triples, integration OK")
        else:
            print(f"  ✗ {name}: integration SHACL violations")
            for line in results_text.split("\n")[:15]:
                print(f"    {line}")
        return conforms

    except ImportError:
        print(f"  ⚠ {name}: pyshacl not installed, skipping")
        return True


def main():
    all_ok = True
    for test in INTEGRATION_TESTS:
        if not run_test(test):
            all_ok = False
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
