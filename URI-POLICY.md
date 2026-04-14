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

### Package Identity vs Versioned Package

Every package has two URIs:

- **Identity URI** (`d/pkg/{distro}/{release}/{arch}/{name}`) — version-agnostic, stable. Used as dependency targets.
- **Versioned URI** (`d/pkg/{distro}/{release}/{arch}/{name}/{version}`) — specific build. Linked to identity via `pkg:isVersionOf`.

Dependencies always point to the **identity URI**. This enables:
- Direct name-based joins without URI parsing
- Transitive dependency traversal across versions
- Temporal queries ("all versions of bash in Debian trixie")

## Term Stability Levels

### Stable

These terms will not change meaning or be removed. Breaking changes require a new namespace version (which we commit to avoiding).

**Classes:** `Package`, `BinaryPackage`, `SourcePackage`, `PackageIdentity`, `Version`, `VersionConstraint`, `Dependency`, `Distribution`, `DistributionRelease`, `Architecture`, `Maintainer`, `Repository`, `InstalledFile`

**Properties:** `packageName`, `hasVersion`, `versionString`, `directlyDependsOn`, `directlyConflictsWith`, `builtFromSource`, `maintainedBy`, `partOfDistribution`, `partOfRelease`, `targetArchitecture`, `isVersionOf`, `description`, `homepage`, `installSize`, `packageSize`, `checksum`, `hasDependency`, `dependencyTarget`, `dependencyType`, `hasVersionConstraint`

### Provisional

Semantics locked. Name may change before 1.0 with a deprecation period (the old name will be kept as `owl:deprecated` for at least one release).

**Classes:** `DataSnapshot`, `PackageSet`, `UpstreamProject`, `BuildActivity`, `MetaPackage`, `VirtualPackage`

**Properties:** `snapshotSource`, `snapshotTimestamp`, `snapshotGraph`, `isCurrent`, `hasUpstreamProject`, `equivalentInDistribution`

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
