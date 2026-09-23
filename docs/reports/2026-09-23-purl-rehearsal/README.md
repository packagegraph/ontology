# Bounded production migration rehearsal

The local migration **passed on genuine production input**: two versioned PURLs
were moved from one identity onto their corresponding packages, and the identity
received one versionless PURL. All 106 non-PURL triples, including four snapshot
triples, were preserved exactly. No production data was changed. This is a bounded
sample, not a complete graph regeneration or replacement artifact.

## Source and scope

- Endpoint: <https://packagegraph.di.riseproject.dev/>.
- Named graph: `https://packagegraph.github.io/graph/almalinux/10`.
- Selected identity: `https://packagegraph.github.io/d/pkg/almalinux/10/aarch64/acl`.
- Identity selection completed: `2026-09-23T18:50:21.665670+00:00`.
- Sample request: `2026-09-23T18:51:00.815269+00:00` to
  `2026-09-23T18:51:01.933784+00:00` (UTC).
- [selection.rq](selection.rq) selects one identity with multiple PURLs containing
  a version delimiter. [selection.json](selection.json) records the actual
  identity and a count of two values.
- [query.rq](query.rq) selects all outgoing triples for that identity, its two
  `pkg:isVersionOf` packages, their version nodes, and every explicitly typed
  `pkg:DataSnapshot` in the same named graph. It returned 108 rows, safely below
  the 10,001-row refusal threshold, with no server-reported truncation.
- [response.json](response.json) retains the original SPARQL JSON;
  [before.nt](before.nt) contains the 108 RDF triples (22,226 bytes).
  [capture.json](capture.json) records timestamps, counts, graph identity, and the
  input SHA-256 digest.

This sample includes one identity, two packages, two version nodes and one
DataSnapshot with four outgoing triples. References to source packages,
dependency blank nodes, maintainers and other resources are retained, but their
outgoing triples were not recursively sampled. N-Triples does not encode the
named-graph IRI; that IRI is preserved separately in `capture.json`.

The JSON-to-RDF conversion uses `Literal(..., normalize=False)` to preserve
literal lexical forms exactly, including the snapshot timestamp
`2026-09-15T04:04:21Z`. RDFLib's default normalization can otherwise rewrite that
literal to `2026-09-15T04:04:21+00:00`.

## Verified migration

This production graph stores architecture in `pkg:hasVersion/pkg:versionString`,
whereas its PURLs store architecture only as a qualifier:

| Recorded versionString | Existing identity PURL |
| --- | --- |
| `2.3.2-4.el10.aarch64` | `pkg:rpm/almalinux/acl@2.3.2-4.el10?arch=aarch64` |
| `2.4.0-1.el10_2.aarch64` | `pkg:rpm/almalinux/acl@2.4.0-1.el10_2?arch=aarch64` |

The migrator uses the recorded RPM release and architecture qualifier to
corroborate removal of the architecture suffix for the PURL version. The
original versionString triples remain unchanged. Both old versioned PURLs match
the corresponding concrete package evidence; none is discarded unmatched.

[verification.json](verification.json) records the verification timestamp,
migration source hash, before/after hashes, exact preservation checks, parser
validation result and final PURLs.

| Measurement | Before | After |
| --- | ---: | ---: |
| RDF triples | 108 | 109 |
| PURL triples | 2 | 3 |
| Non-PURL triples | 106 | 106 |
| DataSnapshot triples | 4 | 4 |
| N-Triples bytes | 22,226 | 22,467 |

The identity now has `pkg:rpm/almalinux/acl?arch=aarch64`; each concrete package
has its matching versioned PURL from the table above. All values are
`xsd:anyURI` literals. The in-memory migration leaves its input unchanged and
preserves the exact RDF-term set of every non-PURL triple. The CLI result was
also checked isomorphic to the API result. [after.nt](after.nt) retains the input
blank-node labels, so its textual diff changes only PURL triples.

General parser-backed graph validation returns **zero errors**. The stricter RPM
collection profile reports **two missing source-package PURLs**: the package
triples reference `.../src/almalinux/10/acl/2.3.2-4.el10` and
`.../src/almalinux/10/acl/2.4.0-1.el10_2`, whose outgoing facts were not part of this
sample. This is expected for the bounded sample and is not a successful complete
collector-profile validation. Full source/package coverage requires collector
recollection and validation of a complete graph.

## Reproduce locally

Run from the repository root with its Python dependencies installed:

```python
from pathlib import Path
import rdflib
from rdflib import Graph, URIRef
from packagegraph.purl_migration import migrate_graph
from packagegraph.purls import PKG, validate_graph

rdflib.NORMALIZE_LITERALS = False
sample = Path("docs/reports/2026-09-23-purl-rehearsal/before.nt")
graph = Graph(identifier=URIRef(
    "https://packagegraph.github.io/graph/almalinux/10"
)).parse(sample, format="nt")
original = set(graph)
migrated = migrate_graph(graph)
assert set(graph) == original
assert {t for t in graph if t[1] != PKG.purl} == {
    t for t in migrated if t[1] != PKG.purl
}
assert len(graph) == 108 and len(migrated) == 109
assert not validate_graph(migrated)
```

The two source queries were read-only SELECT requests, each bounded by a
30-second curl timeout. All migration work runs locally; no SPARQL UPDATE,
graph replacement, or collector regeneration was performed against production.
