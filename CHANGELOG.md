# Changelog

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
