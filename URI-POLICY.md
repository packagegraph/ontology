# PackageGraph URI Stability Policy

Version: 0.5.0
Date: 2026-04-14

## Ontology Namespace URIs

The ontology uses hash namespaces for term definitions:

```
https://purl.org/packagegraph/ontology/core#
https://purl.org/packagegraph/ontology/debian#
https://purl.org/packagegraph/ontology/rpm#
https://purl.org/packagegraph/ontology/security#
https://purl.org/packagegraph/ontology/vcs#
https://purl.org/packagegraph/ontology/metrics#
https://purl.org/packagegraph/ontology/slsa#
```

These namespace URIs are **permanent**. They will not change. The ontology version is tracked via `owl:versionInfo` and `owl:versionIRI`, not by changing the namespace.

## Data Instance URIs

Data URIs use a shortened base path with hierarchical structure:

```
https://purl.org/packagegraph/d/{type}/{path...}
```

### URI Patterns

| Type | Pattern | Example |
|------|---------|---------|
| Package Identity | `d/pkg/{distro}/{release}/{arch}/{name}` | `d/pkg/debian/trixie/amd64/bash` |
| Binary Package | `d/pkg/{distro}/{release}/{arch}/{name}/{version}` | `d/pkg/debian/trixie/amd64/bash/5.2.37-2+b8` |
| Source Package | `d/src/{distro}/{release}/{name}/{version}` | `d/src/debian/trixie/bash/5.2.37-2` |
| Version | `d/ver/{distro}/{release}/{name}/{version}` | `d/ver/debian/trixie/bash/5.2.37-2+b8` |
| Distribution | `d/distro/{name}` | `d/distro/debian` |
| Release | `d/release/{distro}/{codename}` | `d/release/debian/trixie` |
| Architecture | `d/arch/{name}` | `d/arch/amd64` |
| Maintainer | `d/maintainer/{email}` | `d/maintainer/doko@debian.org` |
| Vulnerability | `d/cve/{id}` | `d/cve/CVE-2022-0778` |
| Repository | `d/repo/{host/path}` | `d/repo/github.com%2Fcurl%2Fcurl` |
| Commit | `d/commit/{sha12}` | `d/commit/abc123def456` |
| Capability (RPM profile) | `d/capability/rpm/{encoded-token}` | `d/capability/rpm/libssl.so.3%28%29%2864bit%29` |
| RPM declaration occurrence | `d/rpm-declaration/{sha256}` | Hash of the source-occurrence key below |

### Package Identity vs Versioned Package

Every package has two URIs:

- **Identity URI** (`d/pkg/{distro}/{release}/{arch}/{name}`) — version-agnostic, stable. Can be used as a genuine package dependency target.
- **Versioned URI** (`d/pkg/{distro}/{release}/{arch}/{name}/{version}`) — specific build. Linked to identity via `pkg:isVersionOf`.

Package-oriented relationships may target an identity or a concrete version
where the property's range permits it. Identity targets enable:
- Direct name-based joins without URI parsing
- Transitive dependency traversal across versions
- Temporal queries ("all versions of bash in Debian trixie")

This does not authorize creating a PackageIdentity from every dependency token.
The bounded RPM profile records requirements as declarations; a token-name match
does not establish a package dependency or license transitive traversal.

### Bounded RPM primary.xml profile

The [RPM declaration contract](docs/rpm-declaration-contract.md) fixes the scope
and publication checks. The platform currently deploys the data base
`https://packagegraph.github.io/d/`; this policy also documents
`https://purl.org/packagegraph/d/`. The RPM reference implementation and shapes
support these two bases. A publication manifest must pin **one** data base;
changing base is an explicit identifier migration, not an implicit equivalence.
This release does not rename existing package identifiers or assert that IRIs
under different bases are identical.

**Capability identity:** exact XML-decoded token in the RPM naming system.
Percent-encode its UTF-8 bytes using uppercase hexadecimal escapes, preserving
only `A-Z a-z 0-9 - _ . ~`. Do not trim, lowercase, normalize Unicode, re-decode
entities or unescape existing percent sequences. `/bin/sh` becomes `%2Fbin%2Fsh`;
`foo%2Fbar` becomes `foo%252Fbar`. Matching names do not establish a compatible
provider. There is no global `owl:sameAs` mapping from legacy mixed-ecosystem
`d/capability/{token}` nodes to replacements.

**Declaration identity:** SHA-256 of the UTF-8 encoding of this compact JSON array:

```text
[1, packageIRI, uncompressedPrimarySha256, packageOrdinal, sectionKind, entryOrdinal]
```

- `packageIRI` is the full, unchanged IRI of the declaring collected package.
- `uncompressedPrimarySha256` is 64 lowercase hexadecimal digits over the exact
  uncompressed primary.xml bytes, not the compressed archive or reserialized XML.
- Ordinals are unsigned 64-bit integers, zero-based in document order.
  `packageOrdinal` counts all package elements, including unselected ones.
  `entryOrdinal` counts entries of that kind within the package across repeated
  sections, including entries rejected by validation.
- `sectionKind` is exactly `provides`, `requires`, `conflicts`, or `obsoletes`.
- Serialize without a BOM, whitespace between JSON tokens, or a trailing newline.
  Use decimal integers without leading zeros; emit non-ASCII characters as UTF-8.
  Escape quotes/backslashes and JSON control characters, using the standard short
  escapes where available and lowercase `\\u00xx` otherwise. Do not escape `/`.
  The reference expression is
  `json.dumps(key, ensure_ascii=False, separators=(",", ":")).encode("utf-8")`.
- Append the lowercase hexadecimal digest to `d/rpm-declaration/`.

Re-reading the same bytes/context and recompression preserve identity. Changed
XML bytes may change identity; no cross-snapshot occurrence identity is asserted.
Identical entries at distinct positions remain distinct. Source bytes and the
manifest are retained; the digest does not make discarded source recoverable.

Reference implementation: `packagegraph/rpm_contract.py`. Independently hashed
vectors are exercised by `tests/test_rpm_uris.py`; for source digest `a` repeated
64 times and package ordinal 0:

| Package IRI | Section | Entry | Result SHA-256 |
|---|---|---:|---|
| `https://example.org/package/1` | `requires` | 0 | `c8cc209329892ecabebe17fb3985a0d92de4ca52c73dbc64782355d7a0a48ea7` |
| `https://example.org/package/1` | `requires` | 1 | `52d63a2446c3c26bf54851157eff30499181c0f3eb3f9bdd0cea148b0a9c4394` |
| `https://example.org/é` | `provides` | 0 | `91a3e57f528d571bea4e4c7e4991ca23e3809cdcf6e6cb8da35ba80ec8d645e3` |

## Term Stability Levels

### Stable

These terms will not change meaning or be removed. Breaking changes require a new namespace version (which we commit to avoiding).

**Classes:** `Package`, `BinaryPackage`, `SourcePackage`, `PackageIdentity`, `Version`, `VersionConstraint`, `Dependency`, `Distribution`, `DistributionRelease`, `Architecture`, `Maintainer`, `Repository`, `InstalledFile`

**Properties:** `packageName`, `hasVersion`, `versionString`, `directlyDependsOn`, `directlyConflictsWith`, `builtFromSource`, `maintainedBy`, `partOfDistribution`, `partOfRelease`, `targetArchitecture`, `isVersionOf`, `description`, `homepage`, `installSize`, `packageSize`, `checksum`, `hasDependency`, `dependencyTarget`, `dependencyType`, `hasVersionConstraint`

### Provisional

Semantics locked. Name may change before 1.0 with a deprecation period (the old name will be kept as `owl:deprecated` for at least one release).

**Classes:** `DataSnapshot`, `PackageSet`, `UpstreamProject`, `BuildActivity`, `MetaPackage`, `VirtualPackage`

**Properties:** `snapshotSource`, `snapshotTimestamp`, `snapshotGraph`, `isCurrent`, `hasUpstreamProject`, `crossDistributionAlternative`

### Experimental

May change or be removed without notice. Not yet used in production data.

**Modules:** `slsa.ttl` (entire module), `metrics.ttl` (entire module)

## Encoding Rules

All URI path components are percent-encoded using the same rules as Python's `urllib.parse.quote(s, safe="")`:
- All characters except `A-Z a-z 0-9 - _ . ~` are encoded
- **Exception:** Maintainer URIs do NOT encode email addresses (@ and . are valid in URIs)

## Future Considerations

- **PURL registration** (`purl.org/packagegraph/`) is registered and active for hosting independence
- **Dereferenceable data URIs** (303 redirect to SPARQL DESCRIBE) planned for pre-1.0
- **Versioned SPARQL endpoint** (`/v1/packagegraph/sparql`) planned when external consumers exist
