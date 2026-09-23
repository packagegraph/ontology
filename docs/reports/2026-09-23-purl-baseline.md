# Fresh graph-scoped PURL baseline — 2026-09-23

This read-only capture is the current baseline for ontology issue #10. It does not
reuse the September 15 issue measurements and does not claim a production data
repair. Changing the ontology, validation rules, or a collector's version-removal
logic does not populate the missing PURLs measured here.

## Capture and reproduction

- Endpoint: <https://packagegraph.di.riseproject.dev/>
- Started: `2026-09-23T18:45:55.396560+00:00`; finished: `2026-09-23T18:46:39.256785+00:00` (UTC).
- Result: all 45 discovered named graphs measured successfully;
  zero failed graph queries. One discovery query followed by one count query per
  graph, sequentially, with a 30-second limit per request.
- Query source: [`scripts/measure_purls.py`](../../scripts/measure_purls.py).
- Evidence: [`2026-09-23-purl-measurements.json`](2026-09-23-purl-measurements.json)
  includes the exact discovery and per-graph SELECT text, original SPARQL JSON
  responses, decoded counts, endpoint and individual query timestamps.

```sh
python3 scripts/measure_purls.py --timeout 30 \
  --output docs/reports/2026-09-23-purl-measurements.json
```

The CLI requires Python 3.12+ and `curl`. Use repeated `--graph GRAPH_IRI` options
to measure selected graphs. Failed requests, invalid JSON, and responses reporting
truncation retain `status: "error"` and `counts: null`; the CLI exits nonzero.
They are unknown measurements, never zero observations. A successful count query
with no rows for one population establishes zero explicitly selected subjects in
that graph.

## Populations and counts

Every count is a **subject within a named graph**, not a PURL value or a globally
unique subject. The same subject in two graphs counts twice in the totals. Both
the explicit `rdf:type` and the optional `pkg:purl` are matched within the same
`GRAPH ?graph` block. A PURL in another graph cannot fill local missing coverage.

- **Identity:** subjects explicitly matching `rdf:type pkg:PackageIdentity`.
- **Concrete package:** subjects explicitly matching any of `pkg:Package`,
  `pkg:BinaryPackage`, or `pkg:SourcePackage`. A subject with several of those
  types counts once in the package population. This explicit type list covers
  the registry and distribution patterns observed in this capture.
- **Missing:** no `pkg:purl` value in the subject's graph.
- **Multiple:** more than one distinct RDF term as a `pkg:purl` value. Counts are
  per subject; these can overlap with either marker category.
- **With version marker:** at least one value whose lexical form contains an
  unescaped `@` in the final package-name path segment, before `?` qualifiers or
  `#` subpath. **Without version marker:** at least one present value without
  that marker. Scoped namespaces, qualifier URLs, subpaths and `%40` do not
  count as version delimiters. The exact regex is in every saved count query.

A subject with both marker-bearing and marker-free values counts in both marker
columns. Missing subjects count in neither. Marker detection is a screening
metric: malformed values may fall in either category. It does not establish
valid PURL syntax, nonempty versions, registered types, canonical serialization,
qualifier validity, datatype validity, or semantic identity/version correctness.
Full syntax validation requires the PURL parser, separately from these endpoint
counts.

No ontology or RDFS/OWL closure is loaded or requested. These measurements match
explicit query-visible types; they exclude subjects typed only with other
subclasses, untyped PURL subjects, and default-graph-only data. The endpoint's
prior stored/materialized type provenance is not established by a SELECT.
Discovery includes only named graphs with at least one selected explicit type.
The 46 sequential queries are a time-window observation, not an atomic snapshot.

## Overall results

| Population | Denominator | With PURL | Missing | Multiple PURLs | With version marker | Without version marker |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Identity | 5,910,698 | 667,263 | 5,243,435 | 10,276 | 665,339 | 1,924 |
| Concrete package | 2,038,196 | 0 | 2,038,196 | 0 | 0 | 0 |

Identity missing coverage is **5,243,435/5,910,698
(88.71%)**. The 665,339 identities
with a version marker expose the placement problem independently of that missing
coverage. All 1,924 marker-free identities are in `maven`.
There are 10,276 identities with multiple PURL RDF terms.

All 2,038,196 selected concrete packages are missing graph-local PURLs.
The zero versionless-on-package screening count therefore has a denominator of
**zero packages with PURLs**. It is not evidence of a completed or conforming
package-PURL migration. Missing-value backfill is separate work from correcting
version placement and cardinality.

## Per-graph identity results

Graph names below abbreviate the prefix
`https://packagegraph.github.io/graph/`. Denominators are selected subjects, and
all numbers come from successful queries in the linked evidence.

| Graph | Identities | With PURL | Missing | Multiple PURLs | With version marker | Without version marker |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| almalinux/10 | 83,683 | 1,760 | 81,923 | 844 | 1,760 | 0 |
| almalinux/9 | 85,280 | 1,980 | 83,300 | 840 | 1,980 | 0 |
| alpine/edge/riscv64 | 27,028 | 0 | 27,028 | 0 | 0 | 0 |
| alpine/v3.20 | 24,161 | 0 | 24,161 | 0 | 0 | 0 |
| alpine/v3.20/aarch64 | 24,040 | 0 | 24,040 | 0 | 0 | 0 |
| arch | 134,844 | 0 | 134,844 | 0 | 0 | 0 |
| archarm/aarch64 | 13,220 | 0 | 13,220 | 0 | 0 | 0 |
| cargo | 3,585 | 0 | 3,585 | 0 | 0 | 0 |
| centos-stream/10 | 86,927 | 1,908 | 85,019 | 1,840 | 1,908 | 0 |
| centos-stream/9 | 88,048 | 2,061 | 85,987 | 1,785 | 2,061 | 0 |
| chocolatey | 9,590 | 0 | 9,590 | 0 | 0 | 0 |
| conda-forge | 14,000 | 0 | 14,000 | 0 | 0 | 0 |
| cran | 25,023 | 0 | 25,023 | 0 | 0 | 0 |
| debian/sid/riscv64 | 169,918 | 72,255 | 97,663 | 223 | 72,255 | 0 |
| debian/trixie | 278,051 | 103,205 | 174,846 | 5 | 103,205 | 0 |
| debian/trixie/arm64 | 144,232 | 68,191 | 76,041 | 5 | 68,191 | 0 |
| debian/trixie/riscv64 | 141,739 | 66,159 | 75,580 | 5 | 66,159 | 0 |
| fedora/42 | 440,264 | 0 | 440,264 | 0 | 0 | 0 |
| fedora/42/aarch64 | 396,675 | 0 | 396,675 | 0 | 0 | 0 |
| fedora/43 | 621,535 | 102,755 | 518,780 | 4 | 102,755 | 0 |
| fedora/44 | 571,631 | 101,379 | 470,252 | 3 | 101,379 | 0 |
| fedora/44/aarch64 | 348,624 | 0 | 348,624 | 0 | 0 | 0 |
| fedora/44/riscv64 | 481,246 | 65,757 | 415,489 | 28 | 65,757 | 0 |
| fedora/rawhide | 511,603 | 0 | 511,603 | 0 | 0 | 0 |
| flatpak | 3,326 | 0 | 3,326 | 0 | 0 | 0 |
| freebsd/14 | 38,115 | 0 | 38,115 | 0 | 0 | 0 |
| gentoo | 19,528 | 0 | 19,528 | 0 | 0 | 0 |
| gomod | 3,218 | 0 | 3,218 | 0 | 0 | 0 |
| hackage | 1,141 | 0 | 1,141 | 0 | 0 | 0 |
| homebrew | 16,325 | 0 | 16,325 | 0 | 0 | 0 |
| maven | 1,924 | 1,924 | 0 | 0 | 0 | 1,924 |
| nix/nixpkgs | 108,313 | 0 | 108,313 | 0 | 0 | 0 |
| npm | 1,805 | 0 | 1,805 | 0 | 0 | 0 |
| opensuse/tumbleweed | 598,895 | 52,677 | 546,218 | 0 | 52,677 | 0 |
| pypi | 3,962 | 0 | 3,962 | 0 | 0 | 0 |
| rhel/10 | 85,266 | 1,760 | 83,506 | 1,310 | 1,760 | 0 |
| rhel/9 | 94,374 | 2,021 | 92,353 | 1,727 | 2,021 | 0 |
| rocky/10 | 83,165 | 1,749 | 81,416 | 827 | 1,749 | 0 |
| rocky/9 | 85,146 | 1,972 | 83,174 | 830 | 1,972 | 0 |
| rubygems | 1,425 | 0 | 1,425 | 0 | 0 | 0 |
| snap | 237 | 0 | 237 | 0 | 0 | 0 |
| ubuntu/noble | 10,354 | 6,099 | 4,255 | 0 | 6,099 | 0 |
| ubuntu/noble/arm64 | 9,975 | 5,977 | 3,998 | 0 | 5,977 | 0 |
| ubuntu/noble/riscv64 | 9,579 | 5,674 | 3,905 | 0 | 5,674 | 0 |
| void | 9,678 | 0 | 9,678 | 0 | 0 | 0 |

## Per-graph concrete-package results

All package `with_purl`, `multiple_purls`, `with_version_marker`, and
`without_version_marker` counts are zero; they are repeated below so that missing
coverage is not confused with a zero denominator. The JSON retains every metric.

| Graph | Packages | With PURL | Missing | Multiple PURLs | Versionless screening |
| --- | ---: | ---: | ---: | ---: | ---: |
| almalinux/10 | 5,233 | 0 | 5,233 | 0 | 0 |
| almalinux/9 | 5,764 | 0 | 5,764 | 0 | 0 |
| alpine/edge/riscv64 | 35,872 | 0 | 35,872 | 0 | 0 |
| alpine/v3.20 | 32,186 | 0 | 32,186 | 0 | 0 |
| alpine/v3.20/aarch64 | 32,008 | 0 | 32,008 | 0 | 0 |
| arch | 134,844 | 0 | 134,844 | 0 | 0 |
| archarm/aarch64 | 13,221 | 0 | 13,221 | 0 | 0 |
| cargo | 3,585 | 0 | 3,585 | 0 | 0 |
| centos-stream/10 | 9,079 | 0 | 9,079 | 0 | 0 |
| centos-stream/9 | 9,585 | 0 | 9,585 | 0 | 0 |
| chocolatey | 9,590 | 0 | 9,590 | 0 | 0 |
| conda-forge | 154,919 | 0 | 154,919 | 0 | 0 |
| cran | 25,023 | 0 | 25,023 | 0 | 0 |
| debian/sid/riscv64 | 113,370 | 0 | 113,370 | 0 | 0 |
| debian/trixie | 140,705 | 0 | 140,705 | 0 | 0 |
| debian/trixie/arm64 | 105,534 | 0 | 105,534 | 0 | 0 |
| debian/trixie/riscv64 | 103,294 | 0 | 103,294 | 0 | 0 |
| fedora/42 | 101,253 | 0 | 101,253 | 0 | 0 |
| fedora/42/aarch64 | 91,557 | 0 | 91,557 | 0 | 0 |
| fedora/43 | 126,758 | 0 | 126,758 | 0 | 0 |
| fedora/44 | 125,023 | 0 | 125,023 | 0 | 0 |
| fedora/44/aarch64 | 90,388 | 0 | 90,388 | 0 | 0 |
| fedora/44/riscv64 | 89,229 | 0 | 89,229 | 0 | 0 |
| fedora/rawhide | 99,163 | 0 | 99,163 | 0 | 0 |
| flatpak | 3,326 | 0 | 3,326 | 0 | 0 |
| freebsd/14 | 38,115 | 0 | 38,115 | 0 | 0 |
| gentoo | 33,583 | 0 | 33,583 | 0 | 0 |
| gomod | 3,218 | 0 | 3,218 | 0 | 0 |
| hackage | 1,141 | 0 | 1,141 | 0 | 0 |
| homebrew | 16,325 | 0 | 16,325 | 0 | 0 |
| maven | 4,360 | 0 | 4,360 | 0 | 0 |
| nix/nixpkgs | 112,584 | 0 | 112,584 | 0 | 0 |
| npm | 1,805 | 0 | 1,805 | 0 | 0 |
| opensuse/tumbleweed | 69,832 | 0 | 69,832 | 0 | 0 |
| pypi | 3,962 | 0 | 3,962 | 0 | 0 |
| rhel/10 | 14,046 | 0 | 14,046 | 0 | 0 |
| rhel/9 | 31,983 | 0 | 31,983 | 0 | 0 |
| rocky/10 | 4,999 | 0 | 4,999 | 0 | 0 |
| rocky/9 | 5,578 | 0 | 5,578 | 0 | 0 |
| rubygems | 1,425 | 0 | 1,425 | 0 | 0 |
| snap | 237 | 0 | 237 | 0 | 0 |
| ubuntu/noble | 8,470 | 0 | 8,470 | 0 | 0 |
| ubuntu/noble/arm64 | 8,337 | 0 | 8,337 | 0 | 0 |
| ubuntu/noble/riscv64 | 8,004 | 0 | 8,004 | 0 | 0 |
| void | 9,683 | 0 | 9,683 | 0 | 0 |

## Query verification

`tests/test_purl_measurements.py` executes the same SELECTs with RDFLib `Dataset`
fixtures. The eight tests check missing and multiple values, version-marker
categories, de-duplication across explicit concrete types, isolation between named
graphs, exclusion of default graph and inferred-only types, scoped namespaces,
qualifier/subpath delimiters, discovery failure, malformed/truncated results, and
query failures remaining unknown while later graphs are measured. No production
write or update query is used.

```sh
uv run python -m unittest discover -s tests -p test_purl_measurements.py -v
```
