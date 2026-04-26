# Changelog

All notable changes to the PackageGraph ontology are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2026-04-25

Attestation signing infrastructure and forge modeling — new extension module for cryptographic signing across GPG, SSH, X.509, Sigstore, and OpenPubkey; four-level forge model for supply chain concentration and vulnerability analysis.

### Added
- **`extensions/attestation/` module** (`att:` namespace) — cryptographic signing infrastructure
  - 7 classes: `DigitalSignature`, `SignatureMethod`, `SigningCertificate`, `TransparencyLog`, `TransparencyLogEntry`, `CertificateAuthority`, `OIDCProvider`
  - 41 properties (7 object + 34 datatype) covering signatures, certificates, OIDC identity, transparency logs, Fulcio extensions
  - 11 named individuals: 5 signature methods (`GPG`, `SSH`, `X509`, `SigstoreKeyless`, `OpenPubkey`), 6 infrastructure (`SigstorePublicGood`, `SigstoreFulcio`, `GitHubActionsOIDC`, `GoogleAccountsOIDC`, `MicrosoftEntraOIDC`, `InTotoArchivista`)
  - 9 SHACL shapes with `sh:or` method profiles (core SHACL only, no `sh:sparql`)
  - 7 examples: Sigstore npm provenance, gitsign commit, GPG commit, SSH commit, OpenPubkey, GitHub Artifact Attestation, Witness/Archivista
- **Four-level forge model** for supply chain concentration and vulnerability analysis:
  - `vcs:ForgeSoftware` — product family (GitHub, GitLab, Forgejo, etc.)
  - `vcs:ForgeSoftwareVersion` — versioned release with capability surface (VCS support is version-dependent)
  - `vcs:Forge` — deployed instance at a URL (github.com, gitlab.gnome.org)
  - `vcs:ForgeVersionObservation` — timestamped observation that an instance was running a specific version
- **Forge properties:** `vcs:hostedOn` (Repository→Forge), `vcs:forgeSoftware` (Forge→ForgeSoftware), `vcs:forgeUrl`, `vcs:hasVersionObservation`, `vcs:observedSoftwareVersion` (Observation→ForgeSoftwareVersion), `vcs:observedAt`, `vcs:versionOfSoftware` (ForgeSoftwareVersion→ForgeSoftware), `vcs:supportedVcs` (ForgeSoftwareVersion→VCS), `vcs:versionString`
- **`vcs:VersionControlSystem`** — class for VCS types, enabling typed `vcs:supportedVcs` range and SHACL constraints
- New forge software individuals: `vcs:Forgejo`, `vcs:Gitea`, `vcs:cgit`
- 5 SHACL shapes: `ForgeShape`, `ForgeSoftwareShape`, `ForgeSoftwareVersionShape`, `ForgeVersionObservationShape`, `VersionControlSystemShape`
- `att#` registered in `NAMESPACES.md`

### Changed
- **Existing forge individuals retyped** — `vcs:GitHub`, `vcs:GitLab`, `vcs:Savannah`, `vcs:SourceHut` changed from bare `owl:NamedIndividual` to `vcs:ForgeSoftware`
- **`vcs:Bitbucket` split** — replaced by `vcs:BitbucketCloud` (SaaS) and `vcs:BitbucketDataCenter` (self-hosted) as separate `vcs:ForgeSoftware` individuals (distinct codebases with independent version lines)
- **VCS system individuals retyped** — `vcs:Git`, `vcs:Subversion`, `vcs:Mercurial`, `vcs:Bazaar`, `vcs:CVS`, `vcs:Fossil` changed from bare `owl:NamedIndividual` to `vcs:VersionControlSystem`
- **`vcs:Codeberg` removed** — Codeberg is a forge instance (codeberg.org running Forgejo), not a forge software product; replaced by `vcs:Forgejo` as the software individual
- **`slsa:verificationStatus`** — added `rdfs:seeAlso att:signatureStatus` cross-reference and documentation noting it as a flat shortcut with the same value vocabulary (verified/unverified/failed)

### Fixed
- **`scripts/validate_module.py`** — `resolve_imports` rewritten from regex to rdflib-based parsing. The regex never matched prefixed `owl:imports` (e.g., `owl:imports pkg:, vcs:`) so import resolution was silently broken for all modules since inception. All modules now properly load their imports during SHACL validation.

---

## [0.7.0] - 2026-04-21

Peer review remediation and academic hardening — resolves all findings from two independent ontological reviews.

### Added
- `pkg:identityName` — naming anchor for PackageIdentity (owl:FunctionalProperty)
- `pkg:derivedFromCommit` — links Package to vcs:Commit for build traceability
- `pkg:spdxId` — SPDX License List identifier on License class (was ghost property in SHACL)
- `pkg:SoftwareAgent` — non-human contributor class (subClassOf prov:SoftwareAgent, disjointWith Person)
- `ecosystems/redhat/redhat.shacl.ttl` — SHACL shapes for Red Hat module
- 3 SKOS schemes: `sec:AdvisoryCategoryScheme`, `sec:EventTypeScheme`, `sec:RangeTypeScheme`
- `sec:sev-none` concept added to existing SeverityScheme
- 6 new competency questions: CQ-LIC-01/02/03 (license analysis), CQ-TEMP-01/02/03 (temporal analysis)
- CQ-PM-03b — VirtualPackage UNION query demonstrating provides/providesCapability bifurcation
- `owl:versionIRI` on all 35 module headers
- `owl:priorVersion`, `dcterms:modified`, `rdfs:seeAlso` (SHACL shapes) on all headers
- `dcterms:creator` as FOAF Organization IRI (was opaque string)
- `<https://packagegraph.github.io/>` entity defined as foaf:Organization in core.ttl
- Design decisions: DD-VirtualPackage, DD-crossDistributionAlternative, AR-2

### Changed (BREAKING)
- **`equivalentInDistribution` → `crossDistributionAlternative`** — renamed to signal non-transitive correspondence
- **`heldBy`, `maintainedBy`, `hasContributor`, `maintains`, `holdsRole`** — range/domain widened from `pkg:Person` to `prov:Agent`
- **`partOfRelease`** — removed `rdfs:subPropertyOf partOfDistribution` (range inference trap)
- **`advisorySeverity`, `advisoryType`, `eventType`, `rangeType`** — DatatypeProperty → ObjectProperty with SKOS concept ranges
- **All 6 CVSS score properties** — `xsd:float` → `xsd:decimal` (IEEE 754 precision fix)
- **`deb:buildsFrom`, `pacman:builtFrom`** — `owl:equivalentProperty` downgraded to `rdfs:seeAlso`
- **`pkg:Package`** — removed `owl:minCardinality 1` on `hasVersion` (PhantomPackage compatibility)
- **`pkg:Repository`** — removed `owl:minCardinality 1` on `contains` (empty repo compatibility)
- **`pkg:Package rdfs:subClassOf schema:SoftwareApplication`** — weakened to `rdfs:seeAlso`
- **`contributesTo`/`hasContributor`** — removed `owl:inverseOf` (OntoClean role/identity collapse)
- **`hasAccount`** — domain narrowed from Person+Contributor to Person only
- **`cpan:CPANAuthor`** — subClassOf changed from Contributor to ContributorAccount
- SHACL: ContributorShape, MaintainerShape, PackageShape updated for prov:Agent
- SHACL: CPAN DistributionShape authorPAUSEID moved to new CPANAuthorShape
- CQ suite: all 39 queries rewritten to use actual vocabulary (zero non-existent predicates)
- CQ suite: 5 BLOCKED security CQs unblocked (schema now complete)
- CQ suite: graph paths unified to use `^pkg:hasRelease` inverse traversal

### Fixed
- Debian git package example using Fedora maintainer (copy-paste error since initial commit)
- CQ-PROV-01 wasBuiltBy self-referencing query
- SPARQL PREFIX rdfs: missing from 40 query blocks
- maintainedBy examples pointing at Maintainer role instead of Person

---

## [0.6.0] - 2026-04-20

Academic readiness release — comprehensive semantic audit and remediation across all 34 modules.

### Added
- **Competency questions:** CQs formalized as SPARQL queries across multiple domains
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
- **BREAKING: equivalentInDistribution → crossDistributionAlternative** — renamed to signal non-transitive correspondence assertion (symmetric but intentionally NOT transitive). The old name "equivalent" misleadingly implied transitivity.
- **BREAKING: heldBy, maintainedBy, hasContributor, maintains** — range/domain widened from pkg:Person to prov:Agent to support non-human contributors (bots, CI pipelines). pkg:SoftwareAgent class added (disjoint with Person).
- **BREAKING: partOfRelease** — removed rdfs:subPropertyOf partOfDistribution (range inference trap: DistributionRelease ≠ Distribution)
- **Package cardinality:** removed owl:minCardinality 1 on hasVersion from Package (PhantomPackage compatibility)
- **Repository cardinality:** removed owl:minCardinality 1 on contains (empty repository compatibility)
- **contributesTo/hasContributor:** removed owl:inverseOf (OntoClean role/identity collapse fix)
- **hasAccount:** domain narrowed from Person+Contributor to Person only
- **Security properties:** advisorySeverity, advisoryType, eventType, rangeType changed from DatatypeProperty (xsd:string) to ObjectProperty (skos:Concept)
- **CVSS scores:** all 6 score properties changed from xsd:float to xsd:decimal (IEEE 754 precision fix)
- **deb:buildsFrom, pacman:builtFrom:** owl:equivalentProperty downgraded to rdfs:seeAlso (incompatible ranges)
- **Package → SoftwareApplication:** rdfs:subClassOf weakened to rdfs:seeAlso in alignments.ttl
- **CPANAuthor:** subClassOf changed from Contributor to ContributorAccount
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
