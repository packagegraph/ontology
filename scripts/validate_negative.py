#!/usr/bin/env python3
"""Assert that each negative fixture FAILS SHACL with the expected shape/message.

Every SPARQL-based SHACL constraint reports the same sh:sourceConstraintComponent
(sh:SPARQLConstraintComponent), so a fixture that fails for an unrelated reason could
masquerade as a pass. To prevent that, each fixture declares the exact
sh:sourceShape and sh:resultMessage it must produce; this harness checks the
validation report graph for that specific result.
"""

import json
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace
from rdflib.namespace import SH

FIX_DIR = Path("tests/shacl-negative")
CORE = Path("core/core.ttl")
CORE_SHACL = Path("core/core.shacl.ttl")
PKG = Namespace("https://purl.org/packagegraph/ontology/core#")


def run():
    expectations = json.loads((FIX_DIR / "expectations.json").read_text())
    shacl_g = Graph(); shacl_g.parse(str(CORE_SHACL), format="turtle")
    ok = True
    for fname, exp in sorted(expectations.items()):
        data_g = Graph()
        data_g.parse(str(CORE), format="turtle")
        data_g.parse(str(FIX_DIR / fname), format="turtle")
        conforms, report_g, _ = validate(
            data_g, shacl_graph=shacl_g, inference="rdfs",
            serialize_report_graph=False,
        )
        if conforms:
            print(f"  ✗ {fname}: expected violation but graph CONFORMS")
            ok = False
            continue
        messages = {str(m) for _, _, m in report_g.triples((None, SH.resultMessage, None))}
        shapes = {str(s) for _, _, s in report_g.triples((None, SH.sourceShape, None))}
        want_shape = str(PKG[exp["sourceShape"]])
        want_msg = exp["resultMessage"]
        if want_shape not in shapes:
            print(f"  ✗ {fname}: expected sourceShape {exp['sourceShape']} not in report")
            ok = False
        elif want_msg not in messages:
            print(f"  ✗ {fname}: expected message not in report: {want_msg!r}")
            ok = False
        else:
            print(f"  ✓ {fname}: fails as expected ({exp['sourceShape']})")
    if not ok:
        sys.exit(1)
    print(f"All {len(expectations)} negative fixtures fail as expected.")


if __name__ == "__main__":
    run()
