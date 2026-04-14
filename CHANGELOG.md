# Changelog

## [0.5.0] - 2026-04-13

### Added

#### New Ontology File (slsa.ttl)
- **SLSA Supply Chain Security Ontology** — Models SLSA v1.0 provenance attestations, build levels (L0-L3), builder identity, and build environments
  - 5 classes: `ProvenanceAttestation`, `BuildLevel`, `Builder`, `SourceAttestation`, `BuildEnvironment`
  - 4 SLSA level individuals: `slsa:L0`, `slsa:L1`, `slsa:L2`, `slsa:L3`
  - 14 datatype properties (attestationDigest, builderVersion, buildImage, isEphemeral, isIsolated, etc.)
  - 8 object properties (hasProvenance, attestsBuildLevel, builtBy, usedBuildEnvironment, etc.)
  - **Namespace**: `https://packagegraph.github.io/ontology/slsa#`
  - Imports: core.ttl, security.ttl, vcs.ttl

#### PROV-O Grounding (core.ttl)
- **`pkg:Package` now subclasses `prov:Entity`** — Completes the PROV-O entity layer for packages
- **`pkg:Repository` now subclasses `prov:Entity`** — Repositories are provenance entities
- **`pkg:builtFromSource` as `prov:wasDerivedFrom`** — Formalizes binary-to-source derivation semantics
- **`pkg:maintainedBy` as `prov:wasAttributedTo`** — Package-to-maintainer attribution follows PROV-O
- **New property `pkg:performedBy`** (subproperty of `prov:wasAssociatedWith`) — Links packaging activities to the agents that performed them

#### PROV-O Grounding (vcs.ttl)
- **`vcs:parentCommit` as `prov:wasDerivedFrom`** — Commit lineage follows provenance derivation
- **`vcs:packagedFromTag` as `prov:wasDerivedFrom`** — VCS tag to package derivation
- **`vcs:packagedFromCommit` as `prov:wasDerivedFrom`** — VCS commit to package derivation
- **`vcs:previousRelease` as `prov:wasDerivedFrom`** — Release lineage as derivation chain
- **`vcs:releasedBy` as `prov:wasAttributedTo`** — Release attribution with explicit range

#### Supply Chain Security (security.ttl)
- **New class `sec:PatchActivity`** (subclass of `pkg:PackagingActivity`) — Models the act of applying security patches
- **New property `sec:patchedFrom`** (subproperty of `prov:wasDerivedFrom`) — Tracks version-to-version patch derivation
- **New property `sec:patchProducedVersion`** (subproperty of `prov:wasGeneratedBy`) — Links fixed versions to patch activities
- **New property `sec:patchAddresses`** — Links patch activities to vulnerabilities they fix
- **New property `sec:affectsPackage`** — Package-level vulnerability association

#### SHACL Validation Shapes (shacl.ttl)
- `BuildActivityShape` — Validates PROV-O grounding for build activities
- `ProvenanceAttestationShape` — Validates SLSA attestation level, timestamp, digest
- `BuilderShape` — Validates builder ID URI
- `BuildEnvironmentShape` — Validates ephemeral/isolated flags
- `CommitShape` — Validates commit hash, timestamp, authorship
- `PatchActivityShape` — Validates patch activities address vulnerabilities

#### Example Instances (examples.ttl)
- **PROV-O provenance chain** — Demonstrates upstream commit → VCS tag → source package → build activity → binary package for Debian openssl
- **SLSA L2 attestation** — Koji-built RPM with full provenance (builder, build environment, source attestation)
- **Security patch provenance** — Unpatched glibc → patch activity → patched glibc with CVE linkage

### Changed
- **slsa.ttl registered in build tooling** — Added to `ONTOLOGY_FILES` in Makefile for lint/concat/deploy
- **Documentation updated** — README.md now lists slsa.ttl as 10th ontology with full description

## [0.4.0] - 2026-04-09

### Breaking Changes

- **Removed `pkg:upstreamProject` DatatypeProperty** — Superseded by `pkg:hasUpstreamProject` ObjectProperty linking `SourcePackage` to the new `UpstreamProject` class. Enables richer upstream metadata (project name, URL) instead of a plain string.
- **Narrowed `pkg:buildDependsOn` domain** from `pkg:Package` to `pkg:SourcePackage`. Build dependencies are inherently a source-package concept.
- **Changed `vcs:Repository` superclass** from `pkg:Repository` to `owl:Thing`. VCS repositories are independent entities, not a subtype of package repositories.
- **Module class hierarchy aligned with core SourcePackage/BinaryPackage:**
  - `deb:SourcePackage` now also subclasses `pkg:SourcePackage`
  - `deb:BinaryPackage` now also subclasses `pkg:BinaryPackage`
  - `rpm:SourceRPM` now also subclasses `pkg:SourcePackage`
  - `rpm:BinaryRPM` now also subclasses `pkg:BinaryPackage`
  - `arch:PKGBUILD` now subclasses `pkg:SourcePackage` (was `owl:Thing`)
  - `bsd:Port` now subclasses `pkg:SourcePackage` (was `pkg:Package`)
  - `nix:Derivation` now subclasses `pkg:SourcePackage` (was `pkg:Package`)

### Added

#### New Classes (core.ttl)
- `pkg:SourcePackage` — Source package containing source code and build scripts
- `pkg:BinaryPackage` — Compiled, installable package produced from a source package (cardinality 1 on `builtFromSource`)
- `pkg:UpstreamProject` — Upstream open source project that distribution packages are based on
- `pkg:DistributionRelease` — A specific versioned release of a distribution (e.g., Debian 12, Fedora 41)
- `pkg:ContributorAccount` — A contributor's identity on a specific platform
- `pkg:InstalledFile` — A file installed on the target filesystem by a binary package

#### New Object Properties (core.ttl)
- `pkg:builtFromSource` / `pkg:producedBinary` — Inverse pair linking binary and source packages
- `pkg:hasUpstreamProject` — Links source packages to their upstream project
- `pkg:hasDependency` / `pkg:dependencyTarget` — Reified dependency with version constraints
- `pkg:hasRelease` — Links a distribution to its versioned releases
- `pkg:partOfRelease` — Links packages/repositories to a specific distribution release
- `pkg:hasAccount` — Links contributors to platform-specific accounts
- `pkg:installsFile` — Links binary packages to files they install
- `pkg:supportedArchitecture` — Architectures a source package can be built for

#### New Datatype Properties (core.ttl)
- `pkg:dependencyType` — Classifies dependency relationships (runtime, build, recommends, etc.)
- `pkg:accountPlatform`, `pkg:accountUsername`, `pkg:accountURL` — Contributor account metadata
- `pkg:installedFilePath` — Filesystem path where a file is installed
- `pkg:projectName`, `pkg:projectURL` — Upstream project metadata

#### SHACL Shapes (shacl.ttl)
- Added validation shapes for all 6 new classes

### Changed
- `vcs:hasUpstreamRepository` range refined from `vcs:Repository` to `owl:Thing` (aligns with VCS repository independence)
- All module ontologies bumped from 0.3.0 to 0.4.0

## [0.3.0] - Initial tracked version

First versioned release of the PackageGraph ontology suite.
