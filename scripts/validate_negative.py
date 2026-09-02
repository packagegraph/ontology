#!/usr/bin/env python3
"""Assert that each negative fixture FAILS SHACL with the expected message and component.

Each fixture declares the exact sh:resultMessage and sh:sourceConstraintComponent it must
produce; this harness checks the validation report graph for that specific result.
Message and component (by local name) together uniquely identify each rule violation.
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
        components = {str(c) for _, _, c in report_g.triples((None, SH.sourceConstraintComponent, None))}
        want_msg = exp["resultMessage"]
        want_component_local = exp["sourceConstraintComponent"]
        # Extract local name (part after #) from components.
        # Note: resultMessage and sourceConstraintComponent are matched as independent sets over the report,
        # which is safe because every constraint's sh:message string is distinct.
        component_local_names = {c.split("#")[-1] for c in components}
        if want_msg not in messages:
            print(f"  ✗ {fname}: expected message not in report: {want_msg!r}")
            ok = False
        elif want_component_local not in component_local_names:
            print(f"  ✗ {fname}: expected component {want_component_local} not in report")
            ok = False
        else:
            print(f"  ✓ {fname}: fails as expected")
    if not ok:
        sys.exit(1)
    print(f"All {len(expectations)} negative fixtures fail as expected.")


if __name__ == "__main__":
    run()
