# Changelog

All notable changes to the PackageGraph ontology are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.12.0] - 2026-08-22

Maven dependency exclusion vocabulary.

### Added
- **`maven:DependencyExclusion`** (Class) — represents a Maven POM `<exclusion>` element attached to a specific dependency declaration, not globally to the declaring artifact.
- **`maven:hasExclusion`** (ObjectProperty, domain: `pkg:Dependency`, range: `maven:DependencyExclusion`) — links a reified dependency to its exclusions.
- **`maven:excludedGroupId`** / **`maven:excludedArtifactId`** (DatatypeProperty) — the Maven coordinates of the excluded transitive dependency. Wildcard `*` values are representable.
- **`maven:DependencyExclusionShape`** (SHACL) — validates exactly one `excludedGroupId` and one `excludedArtifactId` per exclusion.
- **Exclusion example** in `maven.examples.ttl` — `spring-beans → spring-core` with `commons-logging` excluded.
- **CQ-MVN-06** — "Which transitive dependencies does an artifact exclude, and through which direct dependency?"
- **CQ-MVN-07** — "Which artifacts exclude a specific coordinate?" (reverse lookup by excluded groupId:artifactId)
- **CQ-MVN-08** — "Which dependencies use wildcard exclusions?" (exercises `*` representability) (CQ total: 68)

Resolves: #1. Related: `packagegraph/platform#3`.

## [0.11.0] - 2026-08-22

Corrective semantic revision: dependency properties now target `PackageEntity` instead of `Package`, stopping incorrect type inference on identity targets.

Discovered during platform collector testing by @luhenry (Ludovic Henry) and filed as ontology issue #2 by @brianredbeard.

### Added
- **`pkg:PackageEntity`** (Class, subClassOf `prov:Entity`) — common superclass of `Package` and `PackageIdentity`. Dependency properties target this class so that both version-specific packages and version-independent identities are valid targets without collapsing types under RDFS/OWL reasoning.
- **Identity-target dependency example** in `core/core.examples.ttl` — `wget → libssl3` exercises a dependency whose target is a `PackageIdentity` with a `VersionConstraint`, complementing the existing concrete-target `wget → glibc` example.
- **8 OWL 2 RL reasoning tests** — property chain for identity and concrete targets, negative assertion (identity not inferred as `Package`), both inverse pairs for identity and concrete targets, `prov:Entity` inference through `PackageEntity`, core subproperty identity-target acceptance.
- **DD-PE-1** design decision — documents `PackageEntity` rationale, alternatives rejected, inference behavior, and migration handling.

### Changed
- **`pkg:dependsOn`** range — `pkg:Package` → `pkg:PackageEntity`
- **`pkg:directlyDependsOn`** range — `pkg:Package` → `pkg:PackageEntity`
- **`pkg:dependencyTarget`** range — `pkg:Package` → `pkg:PackageEntity`
- **`pkg:isDependencyOf`** domain — `pkg:Package` → `pkg:PackageEntity`
- **`pkg:isDirectDependencyOf`** domain — `pkg:Package` → `pkg:PackageEntity`
- **7 core dependency subproperty ranges** (`buildDependsOn`, `checkRequires`, `enhances`, `preDepends`, `recommends`, `suggests`, `supplements`) — `pkg:Package` → `pkg:PackageEntity`
- **`pkg:Package`** superclass — removed redundant direct `owl:Thing` and `prov:Entity`; now `rdfs:subClassOf pkg:PackageEntity` (reaches both through `PackageEntity`)
- **`pkg:PackageIdentity`** superclass — `owl:Thing` → `pkg:PackageEntity` (intentionally promotes to `prov:Entity`)
- **`pkg:DependencyShape`** — `sh:class` on `dependencyTarget` changed from `pkg:Package` to `pkg:PackageEntity`; diagnostic message updated

### Migration
- **Entailment change:** Prior ranges/domains on dependency properties incorrectly inferred `rdf:type pkg:Package` on `PackageIdentity` targets. This inference is removed. Previously materialized stale type triples must be cleared or graphs reloaded.
- **Query impact:** SPARQL queries filtering dependency targets by `rdf:type pkg:Package` must be reviewed — use `pkg:PackageEntity` to match both target types. Queries matching `prov:Entity` will now also match `PackageIdentity` instances.
- **No triple rewriting:** Existing asserted dependency triples remain valid. Property IRIs are unchanged.

## [0.10.0] - 2026-05-12

Maven security & VCS integration, academic hardening, and full ecosystem example coverage.

### Added
- **`vcs:Diff` properties** — 7 new properties on the previously empty `Diff` class: `diffFrom`, `diffTo` (→ Commit), `diffUrl` (→ anyURI), `linesAdded`, `linesDeleted`, `filesChanged` (→ xsd:int). Enables source-diff-between-versions queries.
- **`vcs:hasDiff`** (ObjectProperty, domain: Release, range: Diff) — links a release to the diff from its previous release
- **`vcs:DiffShape`** SHACL shape — requires `diffFrom` and `diffTo` (exactly one Commit each)
- **`sec:eventCommit`** (ObjectProperty, domain: RangeEvent, range: vcs:Commit) — links GIT-range vulnerability fix events to VCS commit entities. Optional — only populated when `rangeType` is GIT.
- **`maven:MavenEcosystem`** (NamedIndividual, pkg:Ecosystem) — Maven Central ecosystem entity for `sec:affectsEcosystem` targeting
- **Maven example data** (`ecosystems/maven/maven.examples.ttl`) — Spring4Shell (CVE-2022-22965) test corpus exercising all 5 Maven CQs: vulnerability lookup, version ranges, fix commits, source location, source diffs. Cross-coordinate equivalence (javax→Jakarta) also demonstrated.
- **Maven equivalence seed** (`ecosystems/maven/maven-equivalences.ttl`) — 17 `pkg:upstreamEquivalent` pairs: 15 javax→Jakarta EE 9+ API migrations, 2 high-profile coordinate renames (mysql-connector, commons-io). Loaded as named graph `<graph/maven/equivalences>`.
- **5 Maven competency questions** (CQ-MVN-01 through CQ-MVN-05) — CVEs for artifact, vulnerable versions, fix commit, source location, source diff. All formalized as SPARQL with expected result schemas. CQ total: 53 (was 48).
- **20 new ecosystem example files** — all 28 ecosystem modules now have `.examples.ttl` files. Generated from ontology class/property definitions with correct superclass typing (`BinaryPackage` vs `SourcePackage`). All pass `scripts/validate_module.py` SHACL validation.
- **OWL 2 RL reasoning test** (`scripts/test-owl2-reasoning.py`) — validates `owl:propertyChainAxiom` on `directlyDependsOn` (hasDependency → dependencyTarget chain), disjointness axioms, and basic OWL RL expansion consistency. 1,666 triples inferred from core ontology.
- **DD-UO-1** design decision — documents upper ontology non-alignment rationale (BFO/DOLCE evaluated but not adopted)
- **VersionConstraint example** in `core/core.examples.ttl` — `wget → libc6 >= 2.17` exercises the `hasDependency → hasVersionConstraint → VersionConstraint` reification pattern (CQ-DEP-03)
- **Graph model requirement** documented in `competency-questions.md` — all CQs assume `tdb2:unionDefaultGraph true`; named graphs are for lifecycle management, not query scoping

### Changed
- **`sec:RangeEventShape`** — updated to allow optional `sec:eventCommit` (vcs:Commit)
- **`dcterms:references`** to BFO/DOLCE — replaced with `rdfs:comment` attribution. The `dcterms:references` assertion implied formal alignment that doesn't exist. Upper ontology positioning rationale moved to dedicated comment and DD-UO-1.
- **CQ-MVN-02 SPARQL** — filters to ECOSYSTEM/SEMVER range types only (GIT ranges contain commit hashes, not version strings)
- **CQ summary statistics** — 53 CQs total, 48 PASS, 4 ADVISORY-SIDE, 1 BLOCKED
- **CQ Coverage Map** — 29 classes exercised (added Diff), 70+ properties exercised (added eventCommit, diffFrom/To/Url, linesAdded/Deleted, filesChanged, hasDiff, correspondingPackageVersion, previousRelease, packagedFromTag, cloneUrl)

### Fixed
- **BFO/DOLCE overclaim** — `dcterms:references` to `bfo.owl` and `DOLCEbasic` removed. These implied formal alignment that was explicitly rejected in the design. Replaced with `rdfs:comment` explaining the evaluation.
- **Maven example SHACL** — `rdfs:label` added to Vulnerability example (required by VulnerabilityShape); diff stats use `xsd:int` typed literals (bare integers default to `xsd:integer`, SHACL expects `xsd:int`)
- **Maven example GIT range** — linked to vulnerability via `sec:hasAffectedRange` (was orphaned)

### Validation
- **Maven CQs Fuseki-validated** — 5 Maven CQs (CQ-MVN-01..05) executed against local Fuseki with real OSV data from the live pipeline (12 Spring/Struts components, 23K security triples, 1.2K diff triples). Report: `docs/reports/2026-05-12-maven-cq-validation.md`
- **All 53 CQs structurally valid** — all SPARQL queries executed against local Fuseki without errors. 12 returned data (example data + Maven pipeline output); remainder returned NO DATA (require production cluster's 37.5M triples). Report: `docs/reports/2026-05-12-cq-local-validation.md`
- **OWL 2 RL reasoning** — `propertyChainAxiom` on `directlyDependsOn` verified sound (1,666 inferred triples)
- **SHACL** — all 33 example files conform to their module shapes

---

## [0.9.0] - 2026-04-27

OpenWrt class hierarchy correction and SLSA/core domain widenings — reclassifies source-defined packages, introduces binary IPK and APK classes for the opkg-to-apk transition, and removes domain constraints that blocked legitimate property usage.

### Changed (BREAKING)
- **`opkg:OpkgPackage`** — `rdfs:subClassOf` changed from `pkg:BinaryPackage` to `pkg:SourcePackage`. OpenWrt Makefile-defined packages are source-level build recipes (upstream URL, build deps, sub-package definitions), not compiled binaries. This was the only source-defined ecosystem misclassified as binary — all seven analogues (BitBake, Gentoo, Arch, BSD Ports, Buildroot, Homebrew, Cargo) correctly subclass `SourcePackage`. The reclassification unblocks `pkg:hasUpstreamProject`, `pkg:buildDependsOn`, `pkg:checkRequires`, `pkg:supportedArchitecture`, and `pkg:producedBinary` (all domain: `SourcePackage`) for OpenWrt packages. **No production data affected** — no OpenWrt data exists in the graph yet. See `docs/reports/2026-04-27-ontology-changes-justification.md` for full rationale.
- **`pkg:isVersionOf`** — domain widened from `pkg:BinaryPackage` to `pkg:Package`. The version-to-identity mapping applies equally to source and binary packages. The `BinaryPackage` restriction was an oversight from early versions that modeled only binary package indexes. Affects all 10 `SourcePackage` ecosystems, not only OpenWrt. Strictly backwards compatible (superclass replaces subclass).
- **`pkg:hasPackage`** — range widened from `pkg:BinaryPackage` to `pkg:Package` (inverse of `isVersionOf`; range follows domain change).
- **`slsa:hasSourceVcsRepository`** — `rdfs:domain` removed (was `slsa:SourceAttestation`, now open). Mirrors the `slsa:hasSourceCommit` pattern established in v0.8.0. Both properties serve the same purpose (linking attestations to source origins) and should have the same domain treatment. The restricted domain forced artificial `SourceAttestation` intermediary nodes when source info is embedded directly in provenance predicates (GitHub Attestations API, npm registry). Resolves existing domain violation in the npm provenance enricher and completes the `slsa:sourceRepository` → `slsa:hasSourceVcsRepository` migration path.

### Added
- **`opkg:BinaryIPK`** class (`rdfs:subClassOf pkg:BinaryPackage`) — compiled `.ipk` binary packages from opkg Packages.gz indexes (pre-24.10). Mirrors the Debian model (`DebianSourcePackage` / `DebianBinaryPackage`). Connected to source recipes via `pkg:builtFromSource`: `BinaryIPK --builtFromSource--> OpkgPackage`.
- **`opkg:BinaryAPK`** class (`rdfs:subClassOf pkg:BinaryPackage`) — compiled `.apk` binary packages from apk-tools APKINDEX feeds (24.10+). OpenWrt 24.10 switched from opkg to apk-tools as the default package manager. The Makefile source layer (`OpkgPackage`) is unchanged — only the binary output format changed. `BinaryAPK` is a separate class from `apk:AlpinePackage` because the provenance chain differs (OpenWrt Makefiles vs Alpine APKBUILDs).
- **`opkg:installedSize`** (DatatypeProperty, domain: `pkg:BinaryPackage`, range: `xsd:integer`) — installed size in bytes on target filesystem, currently sourced from Packages.gz `Installed-Size` for BinaryIPK. Domain is `pkg:BinaryPackage` (not `BinaryIPK`) so both binary classes can use it without domain violation. Distinct from `pkg:packageSize` (archive/download size).
- **`opkg:opkgFilename`** (DatatypeProperty, domain: `BinaryIPK`, range: `xsd:string`) — binary `.ipk` filename from Packages.gz `Filename` field.
- **`opkg:BinaryIPKShape`** SHACL shape — validates `installedSize`, `opkgFilename`, `packageName` on `BinaryIPK` instances.
- **`opkg:BinaryAPKShape`** SHACL shape — validates `installedSize`, `packageName` on `BinaryAPK` instances.

### Fixed
- **`opkg.shacl.ttl`** — `OpkgPackageShape` was validating `opkg:installedSize` and `opkg:opkgFilename`, but neither property had an OWL definition in `opkg.ttl` (SHACL referenced undefined properties). Properties now defined with correct domain (`BinaryIPK`); SHACL constraints relocated from `OpkgPackageShape` to new `BinaryIPKShape`.

### Migration Guide

**OpkgPackage reclassification:** No data migration needed — no OpenWrt triples exist in the production graph. Consumers with SPARQL queries matching `?x a pkg:BinaryPackage` that expect OpenWrt packages must update to `?x a pkg:SourcePackage` or `?x a opkg:OpkgPackage`.

**isVersionOf / hasPackage widening:** No data migration needed. Existing `BinaryPackage` instances remain valid (`BinaryPackage` is a subclass of `Package`). Source packages can now use `isVersionOf` without domain violations.

**hasSourceVcsRepository domain removal:** No data migration needed. Existing triples on `SourceAttestation` subjects remain valid. `ProvenanceAttestation` subjects can now use `hasSourceVcsRepository` directly instead of routing through an artificial `SourceAttestation` intermediary. The deprecated `slsa:sourceRepository` can be migrated with:

```sparql
# Migrate deprecated sourceRepository (DatatypeProperty) to
# hasSourceVcsRepository (ObjectProperty → vcs:Repository)
DELETE { ?att slsa:sourceRepository ?repoUri }
INSERT { ?att slsa:hasSourceVcsRepository ?repo }
WHERE {
  ?att slsa:sourceRepository ?repoUri .
  ?repo a vcs:Repository ;
        vcs:repositoryUrl ?repoUri .
}
```

---

## [0.8.0] - 2026-04-26

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
- **`vcs:Codeberg` removed** — Codeberg is a forge instance (codeberg.org running Forgejo), not a forge software product; replaced by `vcs:Forgejo` as the software individual. **Migration:** see Migration Guide below — `hostedOn` triples must point to a new Forge instance entity, not directly to `vcs:Forgejo`
- **`slsa:verificationStatus`** — added `rdfs:seeAlso att:signatureStatus` cross-reference and documentation noting it as a flat shortcut with the same value vocabulary (verified/unverified/failed)
- **`slsa:hasSourceCommit`** — domain restriction removed (was `slsa:SourceAttestation`, now open). Usable on both `SourceAttestation` and `ProvenanceAttestation` to avoid OWL open-world type inference. See definition for rationale.
- **`slsa:attestationTimestamp`** — cardinality relaxed from `owl:cardinality 1` to `owl:maxCardinality 1`. Attestations without extractable timestamps are incomplete but valid.

### Fixed
- **`scripts/validate_module.py`** — `resolve_imports` rewritten from regex to rdflib-based parsing. The regex never matched prefixed `owl:imports` (e.g., `owl:imports pkg:, vcs:`) so import resolution was silently broken for all modules since inception. All modules now properly load their imports during SHACL validation.

### CQ Readiness (v0.8.0)

CQ statuses now distinguish three layers: ontology-complete (vocabulary exists), pipeline-complete (producer emits data), and query-complete (SPARQL uses correct predicates). See `docs/competency-questions.md` for the full legend.

| CQ | Ontology | Pipeline | Query | Notes |
|----|----------|----------|-------|-------|
| VCS-01 | Yes | Yes | **Fixed in v0.8.0** | Rewritten from ghost `hasUpstreamProject` chain to `isVersionOf/upstreamRepository` |
| VCS-02 | Partial | No | Broken | `derivedFromCommit` exists but `vcs:onBranch` undefined; no producer |
| PROV-02 | Yes | Partial | **Fixed in v0.8.0** | Rewritten from phantom `slsa:slsaLevel` to `attestsBuildLevel`. npm enricher emits L2 attestations for 6 packages; Koji emits Builder+builtBy chains. CQ queries for L3 specifically — no L3 data exists yet. |
| SCR-03 | Yes | No | OK | Blocked on `maintainerSince` / `lastReleaseDate` producer |
| SCR-10 | Partial | No | OK | New CQ — requires `sec:affectsForgeSoftwareVersion` property |
| XD-01 | Yes | No | OK | Blocked on Repology cross-distro equivalence data |

### Migration Guide

Producers and consumers using v0.7.0 individuals should update references:

| v0.7.0 | v0.8.0 | Action |
|--------|--------|--------|
| `vcs:Bitbucket` | `vcs:BitbucketCloud` or `vcs:BitbucketDataCenter` | Replace based on target instance. SaaS (bitbucket.org) → `BitbucketCloud`. Self-hosted → `BitbucketDataCenter`. |
| `vcs:Codeberg` | `vcs:Forgejo` | Codeberg is an instance running Forgejo, not a software product. Replace the software individual; model codeberg.org as a `vcs:Forge` instance with `vcs:forgeSoftware vcs:Forgejo`. |

SPARQL migration for existing graph data:
```sparql
# Bitbucket: in the old model, vcs:Bitbucket was used as a hosting
# platform individual. In the new model, Bitbucket Cloud and Data Center
# are separate ForgeSoftware products, and hostedOn must point to a
# vcs:Forge instance.
#
# Step 1: Create the Bitbucket Cloud forge instance (run once)
# (Adjust for Data Center instances as needed)
INSERT DATA {
  <https://packagegraph.github.io/d/forge/bitbucket.org> a vcs:Forge ;
    vcs:forgeUrl "https://bitbucket.org"^^xsd:anyURI ;
    vcs:forgeSoftware vcs:BitbucketCloud ;
    rdfs:label "Bitbucket Cloud" .
} ;
# Step 2: Repoint hostedOn triples from old individual to new instance
DELETE { ?s vcs:hostedOn vcs:Bitbucket }
INSERT { ?s vcs:hostedOn <https://packagegraph.github.io/d/forge/bitbucket.org> }
WHERE  { ?s vcs:hostedOn vcs:Bitbucket } ;
# Step 3: Repoint any forgeSoftware triples
DELETE { ?s vcs:forgeSoftware vcs:Bitbucket }
INSERT { ?s vcs:forgeSoftware vcs:BitbucketCloud }
WHERE  { ?s vcs:forgeSoftware vcs:Bitbucket } ;

# Codeberg: in the old model, vcs:Codeberg was used as a hosting platform
# individual. In the new model, Codeberg is a forge INSTANCE running
# Forgejo SOFTWARE. The migration must create a Forge instance entity,
# not blindly replace Codeberg with Forgejo.
#
# Step 1: Create the Codeberg forge instance (run once)
INSERT DATA {
  <https://packagegraph.github.io/d/forge/codeberg.org> a vcs:Forge ;
    vcs:forgeUrl "https://codeberg.org"^^xsd:anyURI ;
    vcs:forgeSoftware vcs:Forgejo ;
    rdfs:label "Codeberg" .
} ;
# Step 2: Repoint hostedOn triples from the old individual to the new instance
DELETE { ?s vcs:hostedOn vcs:Codeberg }
INSERT { ?s vcs:hostedOn <https://packagegraph.github.io/d/forge/codeberg.org> }
WHERE  { ?s vcs:hostedOn vcs:Codeberg } ;
# Step 3: Repoint any forgeSoftware triples (if Codeberg was used as software)
DELETE { ?s vcs:forgeSoftware vcs:Codeberg }
INSERT { ?s vcs:forgeSoftware vcs:Forgejo }
WHERE  { ?s vcs:forgeSoftware vcs:Codeberg }
```

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

[0.10.0]: https://github.com/packagegraph/ontology/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/packagegraph/ontology/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/packagegraph/ontology/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/packagegraph/ontology/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/packagegraph/ontology/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/packagegraph/ontology/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/packagegraph/ontology/compare/v0.3.0...v0.5.0
[0.3.0]: https://github.com/packagegraph/ontology/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/packagegraph/ontology/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/packagegraph/ontology/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/packagegraph/ontology/releases/tag/v0.1.0
