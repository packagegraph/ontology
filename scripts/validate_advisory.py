#!/usr/bin/env python3
"""Assert that each advisory fixture CONFORMS while still producing the expected
sh:Warning/sh:Info result.

This is the complement of validate_negative.py: some SHACL constraints (e.g. the
rebuild-vs-fork contradiction guard) are deliberately advisory (sh:Warning) rather
than a hard sh:Violation, because the two pieces of data they cross-check are
populated by different curatorial processes and may legitimately not both be
present. Advisory severities must not block conformance (pyshacl's allow_infos /
allow_warnings flags), but that non-blocking behavior, and the specific result it
still produces, both need a test -- a shape that regressed to sh:Violation, or that
silently stopped firing, would otherwise go unnoticed.

Each fixture declares the exact focus node, sh:sourceShape, sh:sourceConstraintComponent
and sh:resultMessage it must produce, all required on a SINGLE sh:ValidationResult, and
the graph must otherwise conform (conforms == True with allow_infos/allow_warnings set).
"""

import json
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import BNode, Graph, Namespace
from rdflib.namespace import SH

FIX_DIR = Path("tests/shacl-advisory")
CORE = Path("core/core.ttl")
CORE_SHACL = Path("core/core.shacl.ttl")
PKG = Namespace("https://purl.org/packagegraph/ontology/core#")


def local(term):
    """Local name of an IRI (after '#' or the last '/')."""
    s = str(term)
    return s.split("#")[-1] if "#" in s else s.rsplit("/", 1)[-1]


def shape_id(shacl_g, term):
    """Stable identifier for a sh:sourceShape (see validate_negative.py)."""
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


def run():
    expectations = json.loads((FIX_DIR / "expectations.json").read_text())
    shacl_g = Graph()
    shacl_g.parse(str(CORE_SHACL), format="turtle")
    ok = True
    for fname, exp in sorted(expectations.items()):
        data_g = Graph()
        data_g.parse(str(CORE), format="turtle")
        data_g.parse(str(FIX_DIR / fname), format="turtle")
        conforms, report_g, _ = validate(
            data_g, shacl_graph=shacl_g, inference="rdfs",
            serialize_report_graph=False,
            allow_infos=True, allow_warnings=True,
        )
        if not conforms:
            print(f"  ✗ {fname}: expected CONFORMS but graph does not "
                  f"(a sh:Violation is present alongside the intended advisory result)")
            ok = False
            continue

        want_msg = exp["resultMessage"]
        want_comp = exp["sourceConstraintComponent"]
        want_focus = exp.get("focusNode")
        want_shape = exp.get("sourceShape")

        matches = [
            (f, c, m, s) for (f, c, m, s) in results(shacl_g, report_g)
            if m == want_msg and c == want_comp
            and (want_focus is None or local(f) == want_focus)
            and (want_shape is None or s == want_shape)
        ]
        if matches:
            print(f"  ✓ {fname}: conforms with expected advisory result "
                  f"({want_comp} on {local(matches[0][0])} via {matches[0][3]})")
        else:
            ok = False
            got = sorted({(local(f), c, s, m[:50]) for (f, c, m, s) in results(shacl_g, report_g)})
            print(f"  ✗ {fname}: conforms, but no result matches focus={want_focus} "
                  f"component={want_comp} shape={want_shape} message={want_msg!r}")
            for g_ in got:
                print(f"      report has: focus={g_[0]} component={g_[1]} shape={g_[2]} msg={g_[3]!r}...")

    if not ok:
        sys.exit(1)
    print(f"All {len(expectations)} advisory fixtures conform with their expected result.")


if __name__ == "__main__":
    run()
