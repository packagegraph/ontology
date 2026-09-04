#!/usr/bin/env python3
"""Assert that each negative fixture FAILS SHACL with the expected validation result.

Each fixture declares the exact focus node, sh:sourceShape, sh:sourceConstraintComponent
and sh:resultMessage it must produce. This harness requires all of those to occur on a
SINGLE sh:ValidationResult node -- not merely somewhere in the report. Matching them
as independent sets would let a fixture pass when the expected message and component
come from two unrelated violations, which is precisely the failure mode a negative
test is supposed to exclude.

`--emit-focus` re-derives the focus node of the matching result for each fixture and
prints it as JSON, for regenerating expectations after a fixture is edited.
"""

import json
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import BNode, Graph, Namespace
from rdflib.namespace import SH

FIX_DIR = Path("tests/shacl-negative")
CORE = Path("core/core.ttl")
CORE_SHACL = Path("core/core.shacl.ttl")
PKG = Namespace("https://purl.org/packagegraph/ontology/core#")


def local(term):
    """Local name of an IRI (after '#' or the last '/')."""
    s = str(term)
    return s.split("#")[-1] if "#" in s else s.rsplit("/", 1)[-1]


def shape_id(shacl_g, term):
    """Stable identifier for a sh:sourceShape.

    Named shapes are identified by local name. Property shapes are blank nodes with
    no stable label, so they are identified by their sh:path as ``path:<localname>``
    -- which is what actually distinguishes one property constraint from another.
    """
    if term is None:
        return None
    if not isinstance(term, BNode):
        return local(term)
    path = next(shacl_g.objects(term, SH.path), None)
    return f"path:{local(path)}" if path is not None else "bnode:unknown"


def results(shacl_g, report_g):
    """Yield (focus, component_local, message, shape_id) per validation result."""
    for r in report_g.subjects(SH.resultMessage, None):
        focus = next(report_g.objects(r, SH.focusNode), None)
        comp = next(report_g.objects(r, SH.sourceConstraintComponent), None)
        shape = next(report_g.objects(r, SH.sourceShape), None)
        for msg in report_g.objects(r, SH.resultMessage):
            yield (focus, (local(comp) if comp else None), str(msg),
                   shape_id(shacl_g, shape))


def run(emit_focus=False):
    expectations = json.loads((FIX_DIR / "expectations.json").read_text())
    shacl_g = Graph()
    shacl_g.parse(str(CORE_SHACL), format="turtle")
    ok = True
    derived = {}
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

        want_msg = exp["resultMessage"]
        want_comp = exp["sourceConstraintComponent"]
        want_focus = exp.get("focusNode")
        want_shape = exp.get("sourceShape")

        # Require ONE result carrying every expected field.
        matches = [
            (f, c, m, s) for (f, c, m, s) in results(shacl_g, report_g)
            if m == want_msg and c == want_comp
            and (want_focus is None or local(f) == want_focus)
            and (want_shape is None or s == want_shape)
        ]
        if emit_focus:
            allm = [(f, c, m, s) for (f, c, m, s) in results(shacl_g, report_g)
                    if m == want_msg and c == want_comp]
            derived[fname] = {"focusNode": local(allm[0][0]) if allm else None,
                              "sourceShape": allm[0][3] if allm else None}
            continue

        if matches:
            print(f"  ✓ {fname}: fails as expected "
                  f"({want_comp} on {local(matches[0][0])} via {matches[0][3]})")
        else:
            ok = False
            got = sorted({(local(f), c, s, m[:50]) for (f, c, m, s) in results(shacl_g, report_g)})
            print(f"  ✗ {fname}: no single result with focus={want_focus} "
                  f"component={want_comp} shape={want_shape} message={want_msg!r}")
            for g_ in got:
                print(f"      report has: focus={g_[0]} component={g_[1]} shape={g_[2]} msg={g_[3]!r}...")

    if emit_focus:
        print(json.dumps(derived, indent=2))
        return
    if not ok:
        sys.exit(1)
    print(f"All {len(expectations)} negative fixtures fail as expected.")


if __name__ == "__main__":
    run(emit_focus="--emit-focus" in sys.argv)
