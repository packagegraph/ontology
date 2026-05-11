# Ontology Issues Blocking OpenWrt Full Collector + SLSA Attestation

Date: 2026-04-27
Context: Plan review for `docs/plans/2026-04-27-openwrt-full-attestation.md`
Status: Blocking — cannot proceed to implementation without ontology team input

## Executive Summary

During plan review for the OpenWrt full collector (multi-feed collection + opkg index enrichment + upstream source tracking + GitHub SLSA attestation), we discovered seven ontology-level issues across `core.ttl`, `opkg.ttl`, and `slsa.ttl`. The most impactful is a class hierarchy misclassification: `opkg:OpkgPackage` is placed under `pkg:BinaryPackage`, but OpenWrt Makefile-defined packages are source-level build recipes — the same domain pattern as Yocto (`bitbake:BitBakeRecipe → pkg:SourcePackage`) and Gentoo (`portage:Ebuild → pkg:SourcePackage`). This blocks upstream project linking (`pkg:hasUpstreamProject`, domain: `pkg:SourcePackage`) for all OpenWrt packages.

---

## Issue 1: `opkg:OpkgPackage` Class Hierarchy Misclassification

**Severity:** Blocking
**Files:** `opkg.ttl:249-254`, `core.ttl:1264-1269`, `core.ttl:1308-1313`

### Current State

```turtle
# opkg.ttl:249-254
opkg:OpkgPackage a owl:Class ;
    rdfs:label "OpenWRT Package"@en ;
    IAO:0000115 "A package defined in an OpenWRT feed repository via a Makefile,
                 compiled as an opkg (.ipk) binary for router/IoT targets." ;
    rdfs:subClassOf pkg:BinaryPackage .
```

### Problem

OpenWrt packages are defined by Makefiles in feed repositories (`packages`, `luci`, `routing`, `telephony`). These Makefiles are **source-level build recipes** that specify:
- `PKG_SOURCE_URL` — upstream source location
- `PKG_VERSION`, `PKG_RELEASE` — version metadata
- `PKG_HASH` / `PKG_MIRROR_HASH` — source archive integrity
- `define Package/<name>` blocks — sub-package definitions

This is functionally identical to:
- **Yocto/BitBake:** `bitbake:BitBakeRecipe → pkg:SourcePackage` (`bitbake.ttl:279`)
- **Gentoo:** `portage:Ebuild → pkg:SourcePackage` (`portage.ttl:172`)
- **Arch Linux:** `pacman:PKGBUILD → pkg:SourcePackage` (`pacman.ttl:487`)
- **Buildroot:** `buildroot:BuildrootPackage → pkg:SourcePackage` (`buildroot.ttl:189`)
- **BSD Ports:** `bsdpkg:Port → pkg:SourcePackage` (`bsdpkg.ttl:512`)

All of these source-defined-package ecosystems correctly subclass `pkg:SourcePackage`. OpenWrt is the only one placed under `pkg:BinaryPackage`.

The `opkg:OpkgPackage` description even says "defined in an OpenWRT feed repository via a Makefile" — acknowledging the source-level nature — while classifying it as binary.

### Impact

1. **`pkg:hasUpstreamProject`** (domain: `pkg:SourcePackage`, `core.ttl:449-455`) cannot be used on `opkg:OpkgPackage` nodes without violating the domain constraint. This blocks the entire upstream source tracking feature planned for the OpenWrt full collector.

2. **`pkg:buildDependsOn`** (domain: `pkg:SourcePackage`, `core.ttl:163-168`) cannot be used on OpenWrt packages, even though OpenWrt Makefiles explicitly declare build dependencies.

3. **`pkg:checkDependsOn`** (domain: `pkg:SourcePackage`, `core.ttl:191-196`) is similarly blocked.

4. **`pkg:builtFromSource`** (domain: `pkg:BinaryPackage`, range: `pkg:SourcePackage`, `core.ttl:170-179`) becomes reflexive if OpenWrt packages are both source and binary — a Makefile package would need `builtFromSource` pointing to itself.

### Note on Disjointness

`pkg:BinaryPackage` and `pkg:SourcePackage` are NOT declared `owl:disjointWith` each other. The only `owl:disjointWith` in `core.ttl` is `Bot disjointWith Person` (line 1306). Dual typing is OWL-valid but semantically incoherent — a node typed as both would satisfy `builtFromSource`'s domain AND range, creating self-referential build provenance.

### Proposed Resolution Options

| Option | Change | Pros | Cons |
|--------|--------|------|------|
| **A. Reclassify** | `opkg:OpkgPackage rdfs:subClassOf pkg:SourcePackage` | Matches Yocto/Gentoo/Arch pattern. Enables `hasUpstreamProject`, `buildDependsOn`. | Breaks existing data that assumes OpkgPackage is binary. Properties with `domain pkg:BinaryPackage` (e.g., `hasInstalledFile`, `hasPackageIdentity`) would need domain changes or a separate binary class. |
| **B. Split** | Keep `opkg:OpkgPackage → BinaryPackage`. Add `opkg:OpkgMakefile → SourcePackage`. | Clean separation. Both source and binary facts have correct homes. | Requires two nodes per package in the graph, linked via `builtFromSource`. More triples, more complex queries. Collector must emit both. |
| **C. Dual subclass** | `opkg:OpkgPackage rdfs:subClassOf pkg:SourcePackage, pkg:BinaryPackage` | Minimal change. All properties work. | Semantically muddy. `builtFromSource` becomes self-referential. Reasoners may infer unexpected things. |
| **D. Broaden hasUpstreamProject domain** | Change `pkg:hasUpstreamProject` domain from `SourcePackage` to `Package` | No class hierarchy change needed. | Weakens the ontology's source/binary distinction. Any package could claim an upstream project. |

**Recommendation:** Option A for OpenWrt Makefile packages (matching the Yocto/Gentoo precedent), with a new `opkg:BinaryIPK` class for Stage 2 opkg Packages.gz data if separate binary-package representation is needed later.

---

## Issue 2: `opkg:parentPackage` Range Mismatch

**Severity:** High
**Files:** `opkg.ttl:109-114`, `openwrt.rs:311`

### Current State

```turtle
# opkg.ttl:109-114
opkg:parentPackage a owl:ObjectProperty ;
    rdfs:domain opkg:OpkgPackage ;
    rdfs:range opkg:OpkgPackage .
```

### Problem

The collector (`openwrt.rs:311`) emits `opkg:parentPackage` pointing to a `pkg:PackageIdentity` URI (constructed via `package_identity_uri()`), not to an `opkg:OpkgPackage` URI:

```rust
// openwrt.rs:311
let parent_uri = package_identity_uri(&self.distro_name, &self.release_name, "any", parent);
writer.write_triple(&pkg_uri, &format!("{OPENWRT}parentPackage"), &parent_uri)?;
```

The range violation means SHACL validation would flag every sub-package's `parentPackage` triple.

### Proposed Resolution

Either:
- **Fix the collector** to emit `parentPackage` pointing to the parent's package URI (not identity URI)
- **Change the range** to `pkg:PackageIdentity` if the intent is version-agnostic parent linking
- **Change the range** to `pkg:Package` for maximum flexibility

---

## Issue 3: Missing Binary Package Properties in `opkg.ttl`

**Severity:** Medium
**Files:** `opkg.ttl`, `core.ttl:401-407`, `core.ttl:832-838`

### Problem

The OpenWrt full collector's Stage 2 (opkg Packages.gz parser) needs to emit binary package metadata. The following properties are needed but not defined in `opkg.ttl`:

| Property | Type | Description | Status |
|----------|------|-------------|--------|
| `opkg:installedSize` | DatatypeProperty (xsd:integer) | Installed size in bytes from Packages.gz `Installed-Size` field | **Missing** |
| `opkg:opkgFilename` | DatatypeProperty (xsd:string) | Binary .ipk filename from Packages.gz `Filename` field | **Missing** |

The following `core.ttl` properties exist and should be used:
- `pkg:targetArchitecture` (ObjectProperty → `pkg:Architecture`, `core.ttl:832-838`) — for the `Architecture` field
- `pkg:hasChecksum` (ObjectProperty → `pkg:Checksum`, `core.ttl:401-407`) — for the `SHA256sum` field
- `pkg:packageSize` — for the `Size` field (download size)

### Proposed Resolution

Add to `opkg.ttl`:

```turtle
opkg:installedSize a owl:DatatypeProperty ;
    rdfs:label "installed size"@en ;
    IAO:0000115 "The installed size in bytes of the binary .ipk package on the target filesystem." ;
    rdfs:domain opkg:OpkgPackage ;
    rdfs:range xsd:integer .

opkg:opkgFilename a owl:DatatypeProperty ;
    rdfs:label "opkg filename"@en ;
    IAO:0000115 "The filename of the binary .ipk package as listed in the opkg Packages index." ;
    rdfs:domain opkg:OpkgPackage ;
    rdfs:range xsd:string .
```

---

## Issue 4: `slsa:hasSourceVcsRepository` Domain Restricts Usage

**Severity:** Medium
**Files:** `slsa.ttl:134-140`, `slsa.ttl:119-125`, `slsa.ttl:127-132`

### Current State

```turtle
# slsa.ttl:134-140
slsa:hasSourceVcsRepository a owl:ObjectProperty ;
    rdfs:domain slsa:SourceAttestation ;
    rdfs:range vcs:Repository .

# slsa.ttl:127-132
slsa:hasSourceCommit a owl:ObjectProperty ;
    # Domain is intentionally open (no rdfs:domain declared)
    rdfs:range vcs:Commit .
```

### Problem

`slsa:hasSourceVcsRepository` has domain `slsa:SourceAttestation`, but the OpenWrt attestation enricher (and npm provenance enricher) emit provenance data from `slsa:ProvenanceAttestation` nodes. The SLSA ontology provides a chain:

```
ProvenanceAttestation → hasSourceAttestation → SourceAttestation → hasSourceVcsRepository → Repository
```

But creating a separate `SourceAttestation` intermediary node is only justified when a distinct source attestation document exists. When source information is embedded directly in the provenance predicate (as in GitHub Attestations API responses), the intermediary is artificial overhead.

`slsa:hasSourceCommit` avoids this problem — its domain is intentionally open (per its IAO annotation: "usable on both SourceAttestation and ProvenanceAttestation"). But `hasSourceVcsRepository` was not given the same treatment.

### Current Workaround

The npm provenance enricher (`enrich_npm_provenance.rs:273`) uses the deprecated `slsa:sourceRepository` (DatatypeProperty, domain: `SourceAttestation`) directly on the attestation node, which violates the domain constraint. Both properties (`sourceRepository` and `hasSourceVcsRepository`) have `SourceAttestation` as domain.

### Proposed Resolution Options

| Option | Change |
|--------|--------|
| **A. Open the domain** | Remove `rdfs:domain` from `hasSourceVcsRepository` (matching `hasSourceCommit` pattern) |
| **B. Add a ProvenanceAttestation property** | New `slsa:provenanceSourceRepository` with domain `ProvenanceAttestation` |
| **C. Document the intermediary** | Keep as-is; document that enrichers should create a `SourceAttestation` node when source info is available |

**Recommendation:** Option A — mirror the `hasSourceCommit` approach. The IAO annotation for `hasSourceCommit` already explains why open domain is appropriate; the same reasoning applies to `hasSourceVcsRepository`.

---

## Issue 5: `slsa:sourceRepository` Deprecated Without Migration Path

**Severity:** Low-Medium
**Files:** `slsa.ttl:191-198`, `enrich_npm_provenance.rs:273`

### Current State

```turtle
# slsa.ttl:191-198
slsa:sourceRepository a owl:DatatypeProperty ;
    owl:deprecated true ;
    IAO:0000115 "DEPRECATED: Use slsa:hasSourceVcsRepository for graph-traversable links." ;
    rdfs:domain slsa:SourceAttestation ;
    rdfs:range xsd:anyURI .
```

### Problem

`slsa:sourceRepository` is deprecated in favor of `slsa:hasSourceVcsRepository`, but:

1. The replacement has `rdfs:domain slsa:SourceAttestation` (Issue 4), making it unusable in the same contexts the deprecated property was used
2. The npm provenance enricher still uses the deprecated property
3. No migration plan exists for existing triples in the graph

### Proposed Resolution

Resolve Issue 4 first, then provide a migration query (SPARQL UPDATE) to convert `slsa:sourceRepository` literals to `slsa:hasSourceVcsRepository` ObjectProperty links.

---

## Issue 6: `slsa:verificationStatus` vs DQ Annotation Mechanism

**Severity:** Low
**Files:** `slsa.ttl:217-224`

### Current State

```turtle
# slsa.ttl:217-224
slsa:verificationStatus a owl:DatatypeProperty ;
    rdfs:label "verification status"@en ;
    rdfs:domain slsa:ProvenanceAttestation ;
    rdfs:range xsd:string .
```

### Clarification Needed

The OpenWrt attestation enricher plans to record that attestation signatures are **not cryptographically verified** (the enricher ingests but does not verify). The question is whether to use:

- `slsa:verificationStatus "unverified"` — a first-class SLSA property (correct mechanism)
- A DQ annotation — the `dq:DataQualityIssue` pattern used elsewhere in the codebase

These are different mechanisms. `slsa:verificationStatus` is the correct one per the ontology, but the plan should be explicit about which to use.

**Recommendation:** Use `slsa:verificationStatus "unverified"` as defined. It is purpose-built for this.

---

## Issue 7: `pkg:UpstreamProject` Cross-Ecosystem Identity Strategy

**Severity:** Medium
**Files:** `core.ttl:669+` (UpstreamProject class), `core.ttl:329-333` (`ecosystemIdentity`), `uris.rs:211`

### Problem

`pkg:UpstreamProject` is designed as a **cross-ecosystem identity hub** — the IAO annotation for `ecosystemIdentity` says "enables queries like 'what packages from different ecosystems come from the same project.'" This requires that the same upstream project (e.g., OpenSSL) shares one `UpstreamProject` URI across distributions.

The OpenWrt collector's planned URI strategy (`upstream_uri("openwrt/openssl")`) namespaces by distribution, which defeats the cross-ecosystem purpose. But using global names (`upstream_uri("openssl")`) risks conflating unrelated projects that happen to share a package name.

### Current Approaches

The `upstreamRepository` property (`core.ttl:873-880`, domain: `PackageIdentity`) provides a simpler cross-distribution anchor: packages sharing the same upstream git repository are the same software. This already works without `UpstreamProject` entities.

### Question for Ontology Team

What is the intended identity strategy for `UpstreamProject` URIs? Options:

1. **Forge-derived:** `upstream_uri` based on normalized forge URL (e.g., `github.com/openssl/openssl`) — unique, cross-ecosystem, but only works for forge-hosted projects
2. **Name-based global:** `upstream_uri("openssl")` — simple but collision-prone
3. **Repology-derived:** Use Repology project names as the canonical cross-distribution identity (we already have a Repology enricher)
4. **Deferred:** Skip `UpstreamProject` entities for now; rely on `upstreamRepository` for cross-distribution linking

---

## Cross-Cutting Concern: Source-Defined Ecosystems

Issues 1 and 7 are not specific to OpenWrt. Any ecosystem where the collector parses **source-level build definitions** (rather than binary package indexes) faces the same class hierarchy question. Currently affected:

| Ecosystem | Class | Subclass Of | Correct? |
|-----------|-------|-------------|----------|
| OpenWrt | `opkg:OpkgPackage` | `pkg:BinaryPackage` | **Wrong** — Makefile build recipe |
| Yocto | `bitbake:BitBakeRecipe` | `pkg:SourcePackage` | Correct |
| Gentoo (ebuild) | `portage:Ebuild` | `pkg:SourcePackage` | Correct |
| Gentoo (installed) | `portage:PortagePackage` | `pkg:BinaryPackage` | Correct |
| Arch (PKGBUILD) | `pacman:PKGBUILD` | `pkg:SourcePackage` | Correct |
| BSD Ports | `bsdpkg:Port` | `pkg:SourcePackage` | Correct |
| Buildroot | `buildroot:BuildrootPackage` | `pkg:SourcePackage` | Correct |
| Homebrew | `homebrew:Formula` | `pkg:SourcePackage` | Correct |

OpenWrt is the only source-defined ecosystem misclassified as binary. The fix should align it with the established pattern.

---

## Appendix: File References

| File | Lines | Content |
|------|-------|---------|
| `etl/ontology/core.ttl` | 1264-1269 | `pkg:BinaryPackage` class definition |
| `etl/ontology/core.ttl` | 1308-1313 | `pkg:SourcePackage` class definition |
| `etl/ontology/core.ttl` | 449-455 | `pkg:hasUpstreamProject` (domain: SourcePackage) |
| `etl/ontology/core.ttl` | 170-179 | `pkg:builtFromSource` (domain: BinaryPackage, range: SourcePackage) |
| `etl/ontology/core.ttl` | 873-880 | `pkg:upstreamRepository` (domain: PackageIdentity) |
| `etl/ontology/core.ttl` | 1306 | Only `owl:disjointWith` in core.ttl (Bot/Person) |
| `etl/ontology/opkg.ttl` | 249-254 | `opkg:OpkgPackage rdfs:subClassOf pkg:BinaryPackage` |
| `etl/ontology/opkg.ttl` | 109-114 | `opkg:parentPackage` (range: OpkgPackage) |
| `etl/ontology/slsa.ttl` | 134-140 | `slsa:hasSourceVcsRepository` (domain: SourceAttestation) |
| `etl/ontology/slsa.ttl` | 127-132 | `slsa:hasSourceCommit` (open domain) |
| `etl/ontology/slsa.ttl` | 191-198 | `slsa:sourceRepository` (deprecated) |
| `etl/ontology/slsa.ttl` | 217-224 | `slsa:verificationStatus` |
| `etl/ontology/slsa.ttl` | 111-117 | `slsa:hasProvenance` (domain: pkg:Package) |
| `etl/ontology/bitbake.ttl` | 279 | `bitbake:BitBakeRecipe rdfs:subClassOf pkg:SourcePackage` (correct pattern) |
| `etl/ontology/portage.ttl` | 172 | `portage:Ebuild rdfs:subClassOf pkg:SourcePackage` (correct pattern) |
| `etl/pg-collect/src/openwrt.rs` | 211 | URI construction (hardcodes arch="any") |
| `etl/pg-collect/src/openwrt.rs` | 220-222 | Dual typing (Package + OpkgPackage) |
| `etl/pg-collect/src/openwrt.rs` | 311 | `parentPackage` emitted with PackageIdentity URI |
| `etl/pg-collect/src/enrich_npm_provenance.rs` | 273 | Uses deprecated `slsa:sourceRepository` |
