# Justification: Ontology Changes for OpenWrt + SLSA Attestation

**Date:** 2026-04-27
**Companion to:** `2026-04-27-ontology-issues-openwrt-attestation.md`
**Scope:** `opkg.ttl`, `opkg.shacl.ttl`, `slsa.ttl`, `core.ttl`
**Status:** Applied (v0.9.0)

---

## Summary of Changes

Six ontology-level changes applied. The table shows the dependency ordering — each change is independent of those below it, but depends on those above it.

| # | File | Change | Severity |
|---|------|--------|----------|
| 1 | `opkg.ttl` | Reclassify `opkg:OpkgPackage` from `pkg:BinaryPackage` to `pkg:SourcePackage` | Blocking |
| 2 | `opkg.ttl` | Introduce `opkg:BinaryIPK rdfs:subClassOf pkg:BinaryPackage` (pre-24.10 .ipk output) | Medium |
| 2b | `opkg.ttl` | Introduce `opkg:BinaryAPK rdfs:subClassOf pkg:BinaryPackage` (24.10+ .apk output) | Medium |
| 3 | `opkg.ttl` + `opkg.shacl.ttl` | Add OWL definitions for `opkg:installedSize` and `opkg:opkgFilename`; relocate SHACL constraints to `BinaryIPKShape` and `BinaryAPKShape` | Medium |
| 4 | `slsa.ttl` | Remove `rdfs:domain` from `slsa:hasSourceVcsRepository` | Medium |
| 5 | `core.ttl` | Widen `pkg:isVersionOf` domain and `pkg:hasPackage` range from `BinaryPackage` to `Package` | Medium |

Four issues from the companion report require no ontology change:

| Issue | Reason |
|-------|--------|
| `opkg:parentPackage` range mismatch | Collector bug — ontology range (`OpkgPackage`) is correct |
| `slsa:sourceRepository` deprecated | Resolved as a consequence of Change 4 |
| `slsa:verificationStatus` | Already correct; use as defined |
| `pkg:UpstreamProject` identity strategy | Design question; deferred — `upstreamRepository` serves as cross-distro anchor |

---

## Change 1: Reclassify `opkg:OpkgPackage` → `pkg:SourcePackage`

### What changes

```turtle
# FROM (opkg.ttl):
opkg:OpkgPackage a owl:Class ;
    rdfs:label "OpenWRT Package"@en ;
    IAO:0000115 "A package defined in an OpenWRT feed repository via a Makefile,
                 compiled as an opkg (.ipk) binary for router/IoT targets. ..." ;
    rdfs:subClassOf pkg:BinaryPackage .

# TO:
opkg:OpkgPackage a owl:Class ;
    rdfs:label "OpenWRT Package"@en ;
    IAO:0000115 "A source-level build recipe defined in an OpenWRT feed repository
                 via a Makefile, specifying upstream source, build dependencies, and
                 sub-package definitions. Analogous to bitbake:BitBakeRecipe,
                 portage:Ebuild, and pacman:PKGBUILD." ;
    rdfs:subClassOf pkg:SourcePackage .
```

### Why this change is needed

**1. The current classification is factually wrong.**

OpenWrt packages are defined by Makefiles in feed repositories (`packages`, `luci`, `routing`, `telephony`). These Makefiles are source-level build recipes that declare:

- `PKG_SOURCE_URL` — upstream source location
- `PKG_VERSION`, `PKG_RELEASE` — version metadata
- `PKG_HASH` / `PKG_MIRROR_HASH` — source archive integrity verification
- `define Package/<name>` blocks — sub-package definitions
- `define Build/Compile` — build instructions

This is the definition of a source package: a build recipe that takes upstream source code and produces binary artifacts. The current IAO annotation even acknowledges this — "defined in an OpenWRT feed repository via a Makefile" — while contradicting itself by classifying the result as binary.

A `pkg:BinaryPackage` in the ontology is defined as "a binary package containing compiled executables, libraries, or architecture-independent files, ready for installation on a target system" (`core.ttl:1264-1269`). OpenWrt Makefiles are not compiled executables. They are not installable on a target system. They are build recipes that produce `.ipk` binaries.

**2. Every analogous ecosystem is classified correctly. OpenWrt is the sole exception.**

The ontology contains eight ecosystems where the collector parses source-level build definitions rather than binary package indexes:

| Ecosystem | Class | `rdfs:subClassOf` | Build definition format |
|-----------|-------|--------------------|------------------------|
| Yocto/BitBake | `bitbake:BitBakeRecipe` | `pkg:SourcePackage` | `.bb` recipe files |
| Gentoo | `portage:Ebuild` | `pkg:SourcePackage` | `.ebuild` files |
| Arch Linux | `pacman:PKGBUILD` | `pkg:SourcePackage` | `PKGBUILD` files |
| BSD Ports | `bsdpkg:Port` | `pkg:SourcePackage` | `Makefile` + `pkg-plist` |
| Buildroot | `buildroot:BuildrootPackage` | `pkg:SourcePackage` | `.mk` files |
| Homebrew | `homebrew:Formula` | `pkg:SourcePackage` | Ruby formula files |
| Cargo | `cargo:CargoCrate` | `pkg:SourcePackage` | `Cargo.toml` |
| **OpenWrt** | **`opkg:OpkgPackage`** | **`pkg:BinaryPackage`** | **`Makefile`** |

OpenWrt Makefiles are structurally closest to BSD Ports Makefiles and Buildroot `.mk` files — all three use Make-based build systems with upstream source declarations. BSD Ports and Buildroot are correctly classified as source packages. OpenWrt uses the identical pattern but is misclassified as binary.

The consistency argument alone would justify the change, but it is also the factually correct classification.

**3. The misclassification blocks three `core.ttl` properties via domain constraints.**

OWL `rdfs:domain` is not a suggestion — it is an axiomatic entailment. Using a property on a subject that is not a member of the domain class causes an OWL reasoner to infer that the subject IS a member of the domain class, creating unintended type assertions. In SHACL validation, it produces domain violations.

The following properties have `rdfs:domain pkg:SourcePackage` and cannot be used on `opkg:OpkgPackage` instances while OpkgPackage remains a subclass of BinaryPackage:

| Property | Purpose | Blocked for OpenWrt? |
|----------|---------|---------------------|
| `pkg:hasUpstreamProject` | Links source packages to upstream projects | Yes — blocks entire upstream source tracking feature |
| `pkg:buildDependsOn` | Build-time dependencies | Yes — even though OpenWrt Makefiles explicitly declare `DEPENDS` |
| `pkg:checkRequires` | Test-time dependencies | Yes |
| `pkg:supportedArchitecture` | Architectures the source can build for | Yes |
| `pkg:producedBinary` | Links source to binary packages it produces | Yes — blocks source→binary provenance chain |

The first property (`hasUpstreamProject`) is the direct blocker for the OpenWrt full collector plan. The collector needs to link OpenWrt packages to their upstream projects via `PKG_SOURCE_URL`. Without reclassification, every `hasUpstreamProject` triple emitted by the collector is a domain violation.

**4. `pkg:builtFromSource` becomes semantically incoherent without the change.**

`pkg:builtFromSource` (`core.ttl:170-179`) has domain `pkg:BinaryPackage` and range `pkg:SourcePackage`, and is declared `owl:AsymmetricProperty`. Its purpose is linking a binary artifact to the source recipe it was compiled from.

If OpkgPackage remains a BinaryPackage, and we also need to represent the source-level nature of OpenWrt Makefiles, we face three untenable options:

- **Dual typing** (`OpkgPackage rdfs:subClassOf BinaryPackage, SourcePackage`): Formally prohibited — `core.ttl` declares `owl:AllDisjointClasses` between `BinaryPackage` and `SourcePackage`. Even without this constraint, a node typed as both would satisfy `builtFromSource`'s domain AND range, enabling self-referential build provenance that violates the `owl:AsymmetricProperty` axiom.

- **Overriding the domain**: Changing `builtFromSource`'s domain from `BinaryPackage` to `Package` weakens a well-defined constraint for the sake of one misclassified ecosystem. The property should remain restricted to binary packages — it is conceptually about the compilation relationship.

- **Reclassification**: The correct option. OpkgPackage becomes SourcePackage. Binary outputs are represented by two new classes — `BinaryIPK` for pre-24.10 `.ipk` packages and `BinaryAPK` for 24.10+ `.apk` packages (Change 2). The `builtFromSource` chain works correctly: `BinaryIPK --builtFromSource--> OpkgPackage` and `BinaryAPK --builtFromSource--> OpkgPackage`.

**5. The Debian precedent validates the split.**

Debian is the only ecosystem in the ontology that has both source and binary package classes:

```
deb:DebianSourcePackage  rdfs:subClassOf  pkg:SourcePackage
deb:DebianBinaryPackage  rdfs:subClassOf  pkg:BinaryPackage
```

This is the exact pattern being applied to OpenWrt: source recipes (OpkgPackage) and binary outputs (BinaryIPK, BinaryAPK) as separate classes, connected via `builtFromSource`. The Debian model has been in production since the ontology's initial design and is well-tested against 68K+ Debian packages.

**6. The opkg-to-apk transition proves the source/binary separation is necessary.**

OpenWrt 24.10 switched from opkg (`.ipk`) to apk-tools (`.apk`) as the default package manager. The Makefile source layer is unchanged — the same feed repos, the same `PKG_SOURCE_URL` declarations, the same build system. Only the binary output format changed. If `OpkgPackage` remained classified as `BinaryPackage`, the class would be tied to a format that's being phased out. The source/binary split correctly models this:

```
opkg:OpkgPackage (SourcePackage)           ← Makefile recipe (stable across transition)
    ├── pkg:producedBinary → opkg:BinaryIPK    ← .ipk output (pre-24.10)
    └── pkg:producedBinary → opkg:BinaryAPK    ← .apk output (24.10+)
```

`opkg:BinaryAPK` is deliberately a separate class from `apk:AlpinePackage` — although the binary format is identical, the provenance chains differ (OpenWrt Makefiles vs Alpine APKBUILDs).

### What this change enables

After reclassification, the following become valid without domain violations:

```turtle
# Upstream project linking (currently blocked)
<pkg/openwrt/24.10/any/openssl> pkg:hasUpstreamProject <upstream/openssl> .

# Build dependency declaration (currently blocked)
<pkg/openwrt/24.10/any/luci-app-firewall> pkg:buildDependsOn <pkg/openwrt/24.10/any/luci-base> .

# Source-to-binary provenance (requires Change 2)
<ipk/openwrt/24.10/mips_24kc/openssl/3.0.14-1> pkg:builtFromSource <pkg/openwrt/24.10/any/openssl> .
```

### Backwards compatibility

This is a **breaking change** for existing OpenWrt data in the graph. Any SPARQL queries that match `?x a pkg:BinaryPackage` expecting to find OpenWrt packages will stop matching. Mitigation:

1. No OpenWrt data exists in the production graph yet — the OpenWrt collector is planned but not deployed. The class change costs nothing against existing data.
2. The ontology version bumps from `0.8.0` to `0.9.0`, tracked via `owl:priorVersion`.

---

## Change 2: Introduce `opkg:BinaryIPK` and `opkg:BinaryAPK` Classes

### What changes

Add to `opkg.ttl`:

```turtle
opkg:BinaryIPK a owl:Class ;
    rdfs:label "Binary IPK Package"@en ;
    IAO:0000115 "A compiled .ipk binary package produced from an OpenWRT Makefile
                 recipe, as indexed in an opkg Packages.gz feed. Used in OpenWRT
                 releases prior to 24.10."@en ;
    rdfs:isDefinedBy opkg: ;
    rdfs:subClassOf pkg:BinaryPackage .

opkg:BinaryAPK a owl:Class ;
    rdfs:label "Binary APK Package"@en ;
    IAO:0000115 "A compiled .apk binary package produced from an OpenWRT Makefile
                 recipe, as indexed in an apk APKINDEX feed. OpenWRT 24.10+ switched
                 from opkg (.ipk) to apk-tools (.apk) as the default package manager.
                 Separate from apk:AlpinePackage because the provenance chain differs
                 (OpenWRT Makefiles vs Alpine APKBUILDs)."@en ;
    rdfs:isDefinedBy opkg: ;
    rdfs:subClassOf pkg:BinaryPackage .
```

### Why this change is needed

**1. The OpenWrt full collector has two distinct data sources that map to two distinct ontological concepts.**

The planned collector has two stages:

| Stage | Data source | Ontological concept | Data emitted |
|-------|-------------|---------------------|--------------|
| Stage 1 | Feed repository Makefiles | Source-level build recipe | `PKG_SOURCE_URL`, `PKG_VERSION`, `DEPENDS`, `define Package` blocks |
| Stage 2a | opkg `Packages.gz` index (pre-24.10) | Binary .ipk metadata | `Installed-Size`, `Filename`, `SHA256sum`, `Architecture` |
| Stage 2b | apk `APKINDEX` (24.10+) | Binary .apk metadata | `S:` (size), `A:` (arch), `C:` (checksum) |

These are not the same thing. A single Makefile (one source package) can produce multiple binary files (multiple binary packages). The `define Package/<name>` blocks in the Makefile define sub-packages, each producing a separate binary. The source→binary relationship is one-to-many.

Without binary classes, Stage 2 data has no home. The properties needed for Stage 2 (installed size, binary filename, SHA256 checksum) are binary-package attributes that do not belong on a source-level build recipe.

**2. The split enables the `builtFromSource` provenance chain.**

With all three classes defined, the `builtFromSource` property works as designed:

```
opkg:BinaryIPK  --pkg:builtFromSource-->  opkg:OpkgPackage   (pre-24.10)
opkg:BinaryAPK  --pkg:builtFromSource-->  opkg:OpkgPackage   (24.10+)
     (binary)                                (source recipe)
```

This mirrors the Debian model:

```
deb:DebianBinaryPackage  --pkg:builtFromSource-->  deb:DebianSourcePackage
```

And the Gentoo model:

```
portage:PortagePackage   --pkg:builtFromSource-->  portage:Ebuild
```

**4. Two binary classes are needed because the output format changed.**

OpenWrt 24.10 switched from opkg (`.ipk`) to apk-tools (`.apk`). The Makefile source layer is identical — the same feed repos, build system, and upstream source declarations. Only the binary output changes. A single source class (`OpkgPackage`) naturally produces two binary formats depending on release version.

`opkg:BinaryAPK` is deliberately separate from `apk:AlpinePackage` because the provenance chains differ. Alpine packages are built from APKBUILDs in the `aports` repository. OpenWrt `.apk` packages are built from OpenWrt Makefiles in feed repositories. The binary format may be identical, but the build recipe, dependency model, and upstream tracking are completely different.

**3. The SHACL shapes already assume this class exists (in effect).**

The existing `opkg.shacl.ttl` validates `opkg:installedSize` and `opkg:opkgFilename` on `opkg:OpkgPackageShape`. After Change 1 reclassifies OpkgPackage as SourcePackage, these binary-level constraints are semantically wrong on a source package shape. They belong on the binary class shape (Change 3).

### Why not defer this to "later"?

The companion issues report suggests BinaryIPK "if separate binary-package representation is needed later." However:

1. The SHACL shapes already reference binary properties on OpkgPackageShape. Reclassifying OpkgPackage without creating BinaryIPK leaves the SHACL shapes validating binary constraints on a source class — semantically incoherent.
2. Introducing BinaryIPK now avoids a second round of SHACL churn when Stage 2 is implemented.
3. The class definition is minimal (5 lines) and carries no maintenance burden.

---

## Change 3: Add OWL Definitions for SHACL-Referenced Properties

### What changes

Add to `opkg.ttl`:

```turtle
opkg:installedSize a owl:DatatypeProperty ;
    rdfs:label "installed size"@en ;
    IAO:0000115 "The installed size in bytes of the binary package on the target
                 filesystem. Distinct from archive/download size (pkg:packageSize).
                 Currently sourced from the opkg Packages.gz Installed-Size field
                 for BinaryIPK packages."@en ;
    rdfs:domain pkg:BinaryPackage ;
    rdfs:isDefinedBy opkg: ;
    rdfs:range xsd:integer .

opkg:opkgFilename a owl:DatatypeProperty ;
    rdfs:label "opkg filename"@en ;
    IAO:0000115 "The filename of the binary .ipk package as listed in the opkg
                 Packages index, from the Packages.gz Filename field."@en ;
    rdfs:domain opkg:BinaryIPK ;
    rdfs:isDefinedBy opkg: ;
    rdfs:range xsd:string .
```

Note: `installedSize` has domain `pkg:BinaryPackage` (not `BinaryIPK`) so both `BinaryIPK` and `BinaryAPK` instances can use it without OWL inferring cross-class membership. `opkgFilename` retains domain `BinaryIPK` because it is specific to the `.ipk` format.

Move SHACL constraints from `OpkgPackageShape` to new `BinaryIPKShape` and `BinaryAPKShape` in `opkg.shacl.ttl`.

### Why this change is needed

**1. SHACL references properties that have no OWL definition — a schema-level inconsistency.**

The SHACL shapes file (`opkg.shacl.ttl`) currently validates two properties on `OpkgPackageShape`:

```turtle
# opkg.shacl.ttl lines 51-54
[ sh:datatype xsd:integer ;
  sh:maxCount 1 ;
  sh:path opkg:installedSize ]

# opkg.shacl.ttl lines 59-62
[ sh:datatype xsd:string ;
  sh:maxCount 1 ;
  sh:path opkg:opkgFilename ]
```

Neither `opkg:installedSize` nor `opkg:opkgFilename` appears in `opkg.ttl`. SHACL validation itself still works — SHACL validates against property paths regardless of OWL definitions. But the ontology is incomplete: these properties have no `rdfs:domain`, no `rdfs:range`, no `IAO:0000115` annotation, and do not appear in ontology documentation (Widoco, WebVOWL).

This is not a theoretical concern — it means:
- OWL reasoners cannot infer domain/range constraints for these properties
- Ontology documentation generators will not list them
- The SHACL shapes make promises about a schema that does not exist

**2. The domains should reflect where each property applies.**

Installed size (the bytes consumed on the target filesystem after installation) and `.ipk` filename (the binary archive name in the package feed) are binary package attributes. They come from the `Packages.gz` index or APKINDEX, not from Makefiles. After Change 1 reclassifies OpkgPackage as SourcePackage, these properties must belong to binary classes.

- `opkg:installedSize` → domain `pkg:BinaryPackage` — installed size applies to both `.ipk` (BinaryIPK) and `.apk` (BinaryAPK) outputs. Using the superclass avoids OWL inferring cross-class membership when the property is used on BinaryAPK instances.
- `opkg:opkgFilename` → domain `opkg:BinaryIPK` — the `.ipk` filename is specific to the opkg format and does not apply to `.apk` packages.

The SHACL constraints follow: `BinaryIPKShape` validates both properties, `BinaryAPKShape` validates only `installedSize`.

---

## Change 4: Remove `rdfs:domain` from `slsa:hasSourceVcsRepository`

### What changes

```turtle
# FROM (slsa.ttl lines 134-140):
slsa:hasSourceVcsRepository a owl:ObjectProperty ;
    rdfs:label "has source VCS repository"@en ;
    IAO:0000115 "Associates a source attestation with the version control
                 repository from which the source was obtained."@en ;
    rdfs:domain slsa:SourceAttestation ;
    rdfs:isDefinedBy slsa: ;
    rdfs:range vcs:Repository .

# TO:
slsa:hasSourceVcsRepository a owl:ObjectProperty ;
    rdfs:label "has source VCS repository"@en ;
    IAO:0000115 "Associates an attestation with the version control repository
                 from which the source was obtained. Domain is intentionally
                 open — usable on both slsa:SourceAttestation (when a separate
                 source attestation document exists) and
                 slsa:ProvenanceAttestation (when source info is bundled
                 directly in the provenance predicate, as in GitHub
                 Attestations API responses or npm registry attestations)."@en ;
    rdfs:isDefinedBy slsa: ;
    rdfs:range vcs:Repository .
```

### Why this change is needed

**1. The SLSA ontology itself already established the open-domain pattern — and applied it inconsistently.**

`slsa:hasSourceCommit` (`slsa.ttl:127-132`) has no `rdfs:domain`:

```turtle
slsa:hasSourceCommit a owl:ObjectProperty ;
    # Domain is intentionally open (no rdfs:domain declared)
    rdfs:range vcs:Commit .
```

Its IAO annotation explains why: "Domain is intentionally open — usable on both slsa:SourceAttestation (when a separate source attestation document exists) and slsa:ProvenanceAttestation (when source info is bundled directly in the provenance predicate, as in npm registry attestations)."

`slsa:hasSourceVcsRepository` serves the same purpose (linking attestations to source origins) but was not given the same treatment. There is no semantic reason for the asymmetry — if `hasSourceCommit` needs open domain to support both attestation types, `hasSourceVcsRepository` does too. They appear together in attestation data (a source repository has commits; you need both to identify the source).

**2. The restricted domain forces artificial intermediary nodes.**

With domain `SourceAttestation`, the only compliant way to link a `ProvenanceAttestation` to a VCS repository is through the full chain:

```
ProvenanceAttestation → hasSourceAttestation → SourceAttestation → hasSourceVcsRepository → Repository
```

This requires creating a `SourceAttestation` intermediary node. But a `SourceAttestation` is a distinct attestation document — not a sub-structure of a provenance attestation. Creating one without an actual source attestation document existing is modeling fiction.

In GitHub Attestations API responses and npm registry provenance bundles, source information (repository, commit, ref) is embedded directly in the provenance predicate. There is no separate source attestation document. The intermediary node would be an empty shell whose only purpose is to satisfy the domain constraint.

**3. The existing npm provenance enricher already violates the domain.**

`enrich_npm_provenance.rs:273` uses the deprecated `slsa:sourceRepository` (DatatypeProperty, domain: `SourceAttestation`) directly on `ProvenanceAttestation` nodes. Both the deprecated property and its replacement (`hasSourceVcsRepository`) have `SourceAttestation` as domain. The enricher violates the domain constraint because the domain is wrong for the use case, not because the enricher is wrong.

Opening the domain fixes the existing violation and makes the replacement property usable where the deprecated property was used — completing the migration path (resolving Issue 5 from the companion report as a side effect).

**4. The change is backwards compatible.**

Removing an `rdfs:domain` axiom is a **domain widening** — it makes the property usable in strictly more contexts. All existing triples that use `hasSourceVcsRepository` on `SourceAttestation` subjects remain valid. No existing SPARQL queries break. No existing SHACL shapes reference this property's domain (the SLSA SHACL shapes validate `ProvenanceAttestationShape` and do not include `hasSourceVcsRepository` constraints).

---

## Change 5: Widen `pkg:isVersionOf` Domain and `pkg:hasPackage` Range

### What changes

```turtle
# isVersionOf (core.ttl lines 541-548):
# domain: BinaryPackage → Package

# hasPackage (core.ttl lines 989-995):
# range: BinaryPackage → Package
```

### Why this change is needed

**1. The version-to-identity mapping is not binary-specific.**

`pkg:isVersionOf` links a specific versioned package to its canonical `PackageIdentity`. `pkg:hasPackage` is its inverse. The concept of "this versioned entity belongs to that version-agnostic identity" applies equally to source and binary packages:

- A Debian source package `openssl_3.0.14-1` is a version of the identity `openssl` in Debian
- A Fedora SRPM `openssl-3.0.14-1.fc43.src.rpm` is a version of the identity `openssl` in Fedora
- An OpenWrt Makefile defining `openssl` version `3.0.14-1` is a version of the identity `openssl` in OpenWrt

The version→identity relationship is inherent to all packages, not just binary ones. The current domain restriction (`BinaryPackage`) is an oversight from a period when the ontology modeled only binary package indexes (RPM, Debian Packages.gz, Alpine APKINDEX).

**2. Without this change, reclassified `OpkgPackage` cannot link to `PackageIdentity`.**

After Change 1, `opkg:OpkgPackage` is a `pkg:SourcePackage`. Using `pkg:isVersionOf` on a SourcePackage instance violates the domain constraint:

```turtle
# DOMAIN VIOLATION after Change 1:
<pkg/openwrt/24.10/any/openssl> a opkg:OpkgPackage ;     # → SourcePackage
    pkg:isVersionOf <identity/openwrt/24.10/any/openssl> . # domain: BinaryPackage ✗
```

**3. The same gap exists for every SourcePackage ecosystem — OpenWrt exposes it first.**

Every ecosystem with `SourcePackage` subclasses has the same domain violation if it uses `isVersionOf`:

| Ecosystem | Source class | Can use `isVersionOf`? |
|-----------|-------------|----------------------|
| `bitbake:BitBakeRecipe` | SourcePackage | No — domain violation |
| `portage:Ebuild` | SourcePackage | No — domain violation |
| `pacman:PKGBUILD` | SourcePackage | No — domain violation |
| `bsdpkg:Port` | SourcePackage | No — domain violation |
| `buildroot:BuildrootPackage` | SourcePackage | No — domain violation |
| `homebrew:Formula` | SourcePackage | No — domain violation |
| `cargo:CargoCrate` | SourcePackage | No — domain violation |
| `cpan:CpanDistribution` | SourcePackage | No — domain violation |
| `cran:CranPackage` | SourcePackage | No — domain violation |
| `deb:DebianSourcePackage` | SourcePackage | No — domain violation |

None of these ecosystems have hit the issue yet because their collectors either (a) don't emit `isVersionOf` for source packages, or (b) the domain violation has gone unnoticed. The OpenWrt collector plan is the first to make it explicit.

**4. The change is strictly backwards compatible.**

Widening a domain from a subclass (`BinaryPackage`) to its superclass (`Package`) is a monotonic relaxation. Every existing triple remains valid — `BinaryPackage` is still a `Package`. No existing SPARQL queries break. The `BinaryPackageShape` in `core.shacl.ttl` does not include `isVersionOf` constraints. The `hasPackage` inverse range widens correspondingly.

The IAO annotations update to replace "binary package" with "package (source or binary)" — a factual correction, not a semantic change.

---

## Changes NOT Proposed

### `opkg:parentPackage` range (Issue 2)

The ontology is correct. `parentPackage` links an OpkgPackage sub-package to its parent OpkgPackage (the primary package defined in the same Makefile). The range `opkg:OpkgPackage` accurately describes this relationship.

The bug is in the collector (`openwrt.rs:311`), which emits `parentPackage` pointing to a `PackageIdentity` URI (constructed via `package_identity_uri()`) instead of the parent package's `OpkgPackage` URI. This is a collector-side fix, not an ontology change.

### `slsa:sourceRepository` deprecated status (Issue 5)

No ontology change needed. The deprecated property retains its deprecation notice. Change 4 (opening `hasSourceVcsRepository` domain) completes the migration path — the replacement property is now usable in all contexts where the deprecated property was used. Migration of existing triples from `sourceRepository` (DatatypeProperty, xsd:anyURI) to `hasSourceVcsRepository` (ObjectProperty, vcs:Repository) is a SPARQL UPDATE operation on the data layer, not a schema change.

### `slsa:verificationStatus` mechanism (Issue 6)

No change needed. The property is purpose-built for recording attestation verification status. The SHACL constraint (`sh:in ("verified" "unverified" "failed")`) already enforces the value vocabulary. Design decision DD-SignatureStatusStrings documents the rationale for string enums with `sh:in` over SKOS concepts for small fixed value sets.

### `pkg:UpstreamProject` identity strategy (Issue 7)

Deferred. The design question (how to construct cross-ecosystem `UpstreamProject` URIs) does not block any immediate work. The existing `pkg:upstreamRepository` property (`core.ttl:873-880`, domain: `PackageIdentity`) already provides a cross-distribution identity anchor: packages sharing the same upstream VCS repository are the same software. This works without `UpstreamProject` entities.

The Repology enricher (already deployed) maps packages to Repology project names, which are curated cross-distribution identities. When the ontology team decides to mint `UpstreamProject` entities, Repology-derived names are the strongest candidate for the identity strategy. This decision can wait until after the OpenWrt collector is operational and producing data.

### `owl:disjointWith` between `BinaryPackage` and `SourcePackage`

Already present. `core.ttl` declares `owl:AllDisjointClasses` between `BinaryPackage` and `SourcePackage`, formally prohibiting dual typing. This was discovered during verification and strengthens the case for Change 1 — reclassification is the only compliant option.

---

## Backwards Compatibility Summary

| Change | Compatibility | Justification |
|--------|--------------|---------------|
| 1. OpkgPackage → SourcePackage | Breaking (theory), safe (practice) | No OpenWrt data exists in production graph. Version bump 0.8.0 → 0.9.0. |
| 2. Add BinaryIPK + BinaryAPK classes | Additive | New classes — no existing data affected |
| 3. Add installedSize/opkgFilename OWL definitions | Additive | New property definitions — no existing data affected. SHACL shape reorganization does not affect data. |
| 4. Remove hasSourceVcsRepository domain | Widening | Strictly more permissive. All existing triples remain valid. |
| 5. Widen isVersionOf/hasPackage | Widening | Domain/range relaxed from subclass to superclass. All existing triples remain valid. |

No SPARQL queries against the production dataset (37.5M triples across 10 named graphs) are affected by any of these changes. The only ecosystem-specific changes (1, 2, 3) target OpenWrt, which has no production data yet. The cross-cutting changes (4, 5) are monotonic widenings that make properties usable in more contexts without invalidating existing usage.
