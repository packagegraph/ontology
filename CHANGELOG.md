# Changelog

All notable changes to the PackageGraph ontology are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-04-20

Academic readiness release — comprehensive semantic audit and remediation across all 34 modules.

### Added
- **Competency questions:** 33 CQs formalized as SPARQL queries across 7 domains
- **OSV vulnerability model:** AffectedRange, RangeEvent, CVSSScore classes with full OSV schema alignment
- **Properties-as-taxonomy:** dependencyType uses property URIs (OWL 2 punning) instead of magic strings
- **6 new dependency shortcut properties:** recommends, suggests, enhances, supplements, checkRequires, preDepends
- **New properties:** satisfiesCapability (InstalledFile → Capability), applicableArchitecture (Dependency → Architecture)
- **Upper ontology alignment:** PROV-O, FOAF, SPDX, DOAP rdfs:seeAlso + subclass mappings
- **owl:propertyChainAxiom** on directlyDependsOn (hasDependency → dependencyTarget)
- **11 new SHACL shapes:** PackageIdentity, Distribution, DistributionRelease, Dependency, Architecture, License, VersionConstraint, AffectedRange, RangeEvent, CVSSScore, CVE
- **SHACL SPARQL constraint:** IrreflexiveDependsOnShape (replaces OWL characteristic for SROIQ compliance)
- **SKOS enforcement:** sh:in constraints on advisorySeverity, advisoryType, dependencyType
- **Schema annotations:** @en language tags (3,568) and rdfs:isDefinedBy (1,161) across all modules
- **Design decisions document** with adopted patterns, rejections, and deferrals
- **Evaluation comparison:** PackageGraph vs SPDX 3.0 vs CycloneDX 1.6 vs OSV schema
- **Production validation framework:** SHACL validation script for Fuseki data

### Changed
- **Package definition:** weakened from "can be installed" to "represented in repository metadata" (OntoClean fix)
- **conflicts:** now owl:SymmetricProperty; isConflictWith removed (redundant)
- **replaces:** added owl:AsymmetricProperty
- **directlyDependsOn:** removed owl:IrreflexiveProperty (SROIQ violation with propertyChainAxiom)
- **upstreamEcosystem:** DatatypeProperty → ObjectProperty (range :Ecosystem)
- **VersionConstraint properties:** domain corrected from Dependency to VersionConstraint
- **17 ecosystem subclass corrections:** source packages (cargo, npm, pypi, rubygems, gomod, hex, cpan, cran, hackage, portage) and binary packages (maven, nuget, conda, flatpak, snap, opkg, chocolatey)
- **9 ecosystem sub-property remappings:** dev/test → buildDependsOn, optional → suggests/recommends
- **metrics.ttl IAO precision:** linesOfCode, languageProportion, complexity metrics clarified

### Deprecated
- cvssScore, cvssVector → CVSSScore reification
- licenseName → hasLicense ObjectProperty
- deb/brew/npm/maven dependency type strings → pkg:dependencyType with property URIs
- slsa:sourceRepository → slsa:hasSourceVcsRepository

### Removed
- isConflictWith property, maven:DependencyScope class

### Fixed
- OntoClean: Maintainer subClassOf schema:Person → Person subClassOf schema:Person
- SROIQ decidability: IrreflexiveProperty + propertyChainAxiom conflict resolved
- Stale alignment: pkg:checksum → pkg:hasChecksum in SPDX mapping
- Example conformance: all examples pass pyshacl with RDFS inference
- 6 ecosystem author/maintainer properties annotated with PROV-O/FOAF links

## [0.5.1] - 2026-04-18

### Added
- SKOS concept schemes for dependency types, severity levels, advisory types
- OWL property characteristics: IrreflexiveProperty, AsymmetricProperty, SymmetricProperty
- Data quality module (dq.ttl)
- External alignment declarations (references/alignments.ttl)

## [0.5.0] - 2026-04-14

### Added
- Source/BinaryPackage class split
- UpstreamProject class for cross-distribution upstream tracking
- dcterms:abstract metadata on all modules
- 18 new ecosystem modules (npm, pypi, cargo, gomod, maven, nuget, rubygems, cpan, cran, hackage, hex, conda, flatpak, snap, portage, opkg, bitbake, buildroot)

## [0.3.0] - 2025-12-15

### Added
- security.ttl with Vulnerability, SecurityAdvisory, CVE classes
- metrics.ttl with ProgrammingLanguage and CodeMetrics
- redhat.ttl vendor extension
- PackageSet class, Patch class (RPM), VCS activity metrics
- SHACL shapes for security and metrics entities

## [0.2.0] - 2025-10-01

### Changed
- CI/CD deployment pipeline improvements
- Ontology version metadata standardization

## [0.1.1] - 2025-09-15

### Fixed
- Example and documentation updates

## [0.1.0] - 2025-09-05

### Added
- Initial ontology release with core classes (Package, Version, Dependency, Distribution)
- Ecosystem modules: RPM, Debian, Arch/Pacman, BSD, Homebrew, Nix, Alpine, Chocolatey
- VCS and SLSA extension modules
- SHACL validation shapes and example instances

[0.6.0]: https://github.com/packagegraph/ontology/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/packagegraph/ontology/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/packagegraph/ontology/compare/v0.3.0...v0.5.0
[0.3.0]: https://github.com/packagegraph/ontology/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/packagegraph/ontology/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/packagegraph/ontology/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/packagegraph/ontology/releases/tag/v0.1.0
