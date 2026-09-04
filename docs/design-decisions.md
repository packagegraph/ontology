# PackageGraph Ontology Design Decisions

**Date:** 2026-04-20
**Context:** Academic peer review audit responses
**Purpose:** Document design choices where audit recommendations were rejected or deferred with technical justification

---

## Core Design Patterns

### CD-1: OntoClean Person/Role Separation

**Pattern:** Rigid identity (Person) separated from anti-rigid role assignments (Contributor, Maintainer).

**Implementation:**

```
pkg:Person  a owl:Class ;
    owl:equivalentClass foaf:Person ;
    rdfs:subClassOf prov:Agent .
    # Rigid: a person exists independently of any role

pkg:Contributor  a owl:Class ;
    rdfs:subClassOf owl:Thing .
    # Anti-rigid: a person can start/stop contributing without ceasing to exist

pkg:Maintainer  a owl:Class ;
    rdfs:subClassOf pkg:Contributor .
    # Anti-rigid: a maintenance role that can be assigned and revoked

pkg:heldBy  a owl:ObjectProperty ;
    rdfs:domain pkg:Contributor ;
    rdfs:range prov:Agent .
    # Links the role assignment to the agent (Person or SoftwareAgent) holding it
```

**Why not make Maintainer a subclass of foaf:Person?** In OntoClean methodology, a class that is anti-rigid (instances can lose membership without ceasing to exist) cannot subsume a class that is rigid (instances cannot lose membership). A person can stop being a maintainer — the maintenance role ends, but the person continues to exist. Making Maintainer a subclass of Person would violate this constraint and cause a reasoner to infer that every Maintainer IS a Person, which conflates identity with role.

**Non-human contributors:** The `heldBy` range was widened from `pkg:Person` to `prov:Agent` (v0.6.0) to support automated bot maintainers (Renovate, Dependabot, CI/CD pipelines). `pkg:SoftwareAgent rdfs:subClassOf prov:SoftwareAgent` is declared `owl:disjointWith :Person`, preserving OntoClean rigidity.

**Traversal patterns:**

- **Convenience (Agent → Package):** `pkg:maintainedBy` — direct link from Package to the agent (Person or SoftwareAgent) maintaining it
- **Detail (Agent → Role → Package):** `pkg:hasMaintenanceRole` → Maintainer → `pkg:heldBy` → Agent — captures role metadata (start date, role type)
- **FOAF integration:** Only `pkg:Person` is `owl:equivalentClass foaf:Person`. Contributor and Maintainer are pure role assignments with no FOAF alignment.

**Historical note:** An early version of `references/alignments.ttl` incorrectly declared `pkg:Maintainer rdfs:subClassOf schema:Person`. This was identified as an OntoClean violation in the v0.6.0 audit and corrected to `pkg:Person rdfs:subClassOf schema:Person`.

---

### CD-2: Two-Tier PURL Addressing

**Pattern:** Separate URLs for machine consumption (PURLs → Turtle) and human consumption (GitHub Pages → HTML documentation).

**Implementation:**

| Audience | URL | Resolves to |
|----------|-----|-------------|
| **Tools** (owl:imports, Protégé, rdflib) | `https://purl.org/packagegraph/ontology/{module}` | Raw Turtle file |
| **Humans** (browsers, citation) | `https://packagegraph.github.io/ontology/` | Landing page with Widoco/WebVOWL |

**Why two tiers?** GitHub Pages serves static files — no server-side content negotiation is possible. `owl:imports` requires the PURL to resolve to parseable RDF, so module PURLs must redirect to `.ttl` files. Humans need HTML with visualization, served from the documentation site.

**Discoverability:** The core ontology header includes `foaf:homepage <https://packagegraph.github.io/ontology/>` so that tools like Protégé can display a link to human-readable documentation.

**Note:** When opening an ontology in Protégé, use `https://purl.org/packagegraph/ontology/core` (no `.ttl` extension). The PURL redirects to the Turtle file automatically.

---

## Adopted Recommendations

### AR-1: Properties-as-Taxonomy for dependencyType

**Audit Recommendation:** Convert dependencyType from opaque string enumeration to formal class hierarchy or SKOS concept scheme.

**Decision:** ADOPTED with modification — use property URIs as taxonomy terms instead of classes.

**Implementation:** Changed `dependencyType` from `owl:DatatypeProperty` (range xsd:string) to `owl:ObjectProperty` (no declared range). Values are property URIs (`pkg:dependsOn`, `pkg:buildDependsOn`, `pkg:recommends`, etc.) using OWL 2 punning. Declared 6 missing shortcut properties (recommends, suggests, enhances, supplements, checkRequires, preDepends) to complete the property hierarchy.

**Rationale:** This harmonizes the dual-model (reified Dependency + shortcut properties) without introducing new classes. The reified node now references the exact shortcut predicate it represents. Query elegance: the dependencyType value IS the SPARQL predicate you use for shortcut queries. SHACL enforcement via `sh:in` on property URIs provides the same constraint strength as a class hierarchy would.

**Why better than class hierarchy:** Zero new classes to maintain, perfect alignment between reified and shortcut representations, property hierarchy already exists via `rdfs:subPropertyOf`.

**Why better than SKOS:** Properties ARE the taxonomy. No parallel vocabulary needed.

**Trade-off:** Requires OWL 2 punning (using property URIs as individuals). This is explicitly legal in OWL 2 but not in OWL 1.

---

### AR-2: Remove contributesTo/hasContributor Inverse Axiom

**Audit Recommendation:** The `owl:inverseOf` between `:contributesTo` (domain: Contributor, range: Repository) and `:hasContributor` (domain: Repository, range: prov:Agent) causes OntoClean role/identity collapse. OWL inverse semantics infer that if X contributesTo Y, then Y hasContributor X — but hasContributor ranges over prov:Agent, so X is inferred as both Contributor AND Agent.

**Decision:** ADOPTED — removed `owl:inverseOf :hasContributor` from `:contributesTo`.

**Rationale:** The two properties have deliberately different ranges (Contributor vs prov:Agent, which encompasses both Person and SoftwareAgent) reflecting the OntoClean separation. Making them formal inverses forces OWL to collapse the distinction. Both properties are retained as independent convenience shortcuts.

**Additional fix:** Removed `:Contributor` from `:hasAccount` domain (kept only `:Person`). In OntoClean, accounts belong to persons, not roles. Multiple rdfs:domain in OWL means the subject is inferred as ALL listed types (intersection), so listing both Contributor and Person as domains caused the same role/identity collapse.

---

## Rejected Recommendations

### RR-1: dependsOn as owl:TransitiveProperty

**Audit Recommendation:** Mark `:dependsOn` (or create `transitivelyDependsOn` super-property) as `owl:TransitiveProperty` to enable transitive dependency closure queries via reasoner inference rather than SPARQL property paths.

**Decision:** REJECTED

**Rationale:**

1. **SROIQ decidability violation:** Phase 0 (2026-04-19) removed `owl:TransitiveProperty` from `dependsOn` because it caused SROIQ violations when combined with `owl:IrreflexiveProperty` on its subproperties (`directlyDependsOn`, which was itself Irreflexive before the recent fix). While `directlyDependsOn` is no longer Irreflexive (SROIQ fix in audit round 1), making `dependsOn` transitive would still conflict with ANY characteristic on subproperties due to property hierarchy propagation rules in OWL 2.

2. **Materialization cost:** For 4.0M Dependency instances across 15 named graphs in production, materializing the transitive closure would add **billions of inferred triples**. Example: a package with 50 direct dependencies → each with 50 transitive → 2,500 closure triples per package. Across 413K packages = 1B+ triples. This exceeds Fuseki's practical reasoning limits.

3. **SPARQL property paths are the correct tool:** Queries use `?pkg pkg:directlyDependsOn+ ?dep` for transitive traversal. This computes transitivity at query time without storing the closure. Standard SPARQL 1.1 feature, no reasoner needed.

**Alternative considered:** A separate `transitivelyDependsOn` super-property marked Transitive. Rejected for the same materialization cost reason — the transitive closure would still be computed and stored.

**Supporting evidence:** OWL 2 Profiles specification explicitly notes that TransitiveProperty reasoning can lead to performance degradation on large graphs. SPARQL property paths are the recommended approach for on-demand transitivity.

---

### RR-2: QUDT Ontology for Physical Units

**Audit Recommendation:** Map `installSize` and `packageSize` properties to QUDT (Quantities, Units, Dimensions, Types) ontology to formally specify the unit of measurement (bytes) as machine-readable semantics.

**Decision:** REJECTED

**Rationale:**

1. **Disproportionate dependency:** QUDT is a comprehensive ontology for scientific dimensional analysis (mass, length, temperature, pressure with unit conversions). Adding it as a dependency for two properties whose units are unambiguous from domain context is over-engineering.

2. **No dimensional confusion possible:** Package sizes are ALWAYS in bytes. There is no ambiguity requiring unit conversion or dimensional analysis. The domain (software packaging) does not use megabytes, kilobytes, or bits as alternative units in any standard package format (RPM, Debian, npm all report bytes as the canonical unit).

3. **IAO:0000115 is formal documentation:** Both properties already state "measured in bytes" in their definitions. This is the formal specification — it appears in the published ontology and is machine-readable via the IAO annotation.

4. **Precedent:** Major software ontologies (DOAP, SPDX, Schema.org SoftwareApplication) model sizes as plain integers/longs without QUDT. The software packaging domain has established precedent that byte counts are self-documenting.

**Alternative considered:** Adding `qudt:unit qudt:Byte` as an annotation on the properties. Rejected because it still requires importing QUDT and provides no query benefit (the units are never ambiguous enough to require filtering or conversion).

---

## Deferred Enhancements

### DE-1: accountPlatform Elevation to Object Property

**Audit Recommendation:** Convert `accountPlatform` from `owl:DatatypeProperty` (xsd:string) to `owl:ObjectProperty` with a new `IdentityPlatform` class. This would enable queries like "list all contributors on GitHub" via traversable entities rather than string matching.

**Decision:** DEFERRED

**Rationale:**

1. **Low current utilization:** The ContributorAccount class and accountPlatform property have minimal usage in the current dataset. Collectors emit platform names as strings ("github.com", "salsa.debian.org") but do not emit rich per-platform metadata.

2. **Useful future enrichment:** When contributor identity tracking becomes a primary analysis focus (tracking the same human across GitHub, GitLab, Fedora accounts), this elevation would enable cross-platform linking. But it requires:
   - Defining the IdentityPlatform class with properties (platformName, baseURL, authentication model)
   - Collector updates to emit platform entities instead of strings
   - Enricher to populate platform metadata

3. **Not blocking for current publication:** The journal paper focuses on cross-distribution package analysis, not contributor identity analysis. This enhancement supports a future research direction (contributor network analysis across forges) but is not required for the current academic contribution.

**Trigger for revisiting:** When we add contributor activity enrichment (commit counts, PR authorship, issue reporting) or build a contributor identity resolution system.

---

### DE-2: Advanced Property Chain (isVersionOf o directlyDependsOn)

**Audit Recommendation:** Add property chain axiom enabling direct traversal from versioned package instance to required package identity: `pkg:identityDependsOn owl:propertyChainAxiom ( pkg:isVersionOf pkg:directlyDependsOn )`.

**Decision:** DEFERRED

**Rationale:**

1. **SROIQ complexity:** `directlyDependsOn` already has a property chain axiom (`hasDependency → dependencyTarget`). Stacking a NEW property chain that USES directlyDependsOn as a component creates nested chain reasoning. The OWL 2 specification allows this but warns that decidability guarantees may be lost depending on the specific combination of axioms.

2. **Requires formal decidability analysis:** Before introducing chain-on-chain patterns, we need to verify that the combination of:
   - `directlyDependsOn owl:propertyChainAxiom ( :hasDependency :dependencyTarget )`
   - `identityDependsOn owl:propertyChainAxiom ( :isVersionOf :directlyDependsOn )`

   ...does not create a reasoning cycle or complexity class elevation beyond SROIQ. This requires tableaux algorithm analysis or submission to an OWL 2 reasoner complexity checker.

3. **SPARQL achieves the same result:** The query `?pkg pkg:isVersionOf/pkg:directlyDependsOn ?identity` computes the path in one hop using SPARQL property path syntax. No axiom needed.

**Trigger for revisiting:** If we introduce an OWL reasoner into the deployment stack (e.g., upgrading from Fuseki TDB2 to Jena with inference), AND we run formal decidability verification, AND the analysis confirms the chain composition is safe.

---

### DE-3: Formal dependencyType Class Taxonomy

**Audit Recommendation:** Create a formal class hierarchy for dependency types (with classes like BuildTimeDependency, RuntimeDependency, TestDependency) rather than using string literals.

**Decision:** SUPERSEDED by AR-1 (properties-as-taxonomy)

**Original deferral rationale (before AR-1):** SKOS `sh:in` enforcement on strings is stronger than raw strings but weaker than a class hierarchy. A formal taxonomy would be cleaner from a DL perspective but over-engineers an enumerated type. The existing `buildDependsOn` sub-property provides the most common query shortcut.

**Current status after AR-1:** The properties-as-taxonomy approach (adopted above) resolves this concern entirely. The property hierarchy (`dependsOn` with subproperties `buildDependsOn`, `recommends`, `suggests`, etc.) IS the taxonomy. No parallel class hierarchy needed. The dependencyType value is the property URI itself, providing both the classification and the query predicate in one.

---

## Notes on Multi-Lingual Metadata

**Design Principle:** The ontology distinguishes between **schema elements** (ontology definitions) and **data literals** (package metadata).

**Schema elements** (class names, property labels, IAO definitions in the ontology .ttl files): Now carry `@en` language tags per audit recommendation. This supports internationalization of the ontology itself — future translation efforts can add `@fr`, `@de`, etc. labels alongside the English definitions.

**Data literals** (package names, version strings, architecture names in instance data): Do NOT carry language tags. These are technical identifiers, not translatable text. Package names like "glibc", "openssl", "python3" are not English words — they are ecosystem-wide identifiers. Adding `@en` to 62.7M such literals would:
- Add 186MB of storage overhead (3 bytes × 62.7M)
- Break existing SPARQL queries (`?pkg rdfs:label "openssl"` would no longer match `"openssl"@en`)
- Provide zero information value (the literals are not ambiguous)

**Exception acknowledged:** Package descriptions ARE natural language text. Debian and Ubuntu maintain dedicated localisation teams (`debian-l10n-english`, `ubuntu-translators`) providing meticulously translated descriptions for packages like `apache2`, `nginx`, and `postgresql`. The RDF literal language tag mechanism (`pkg:description "..."@fr`, `pkg:description "..."@de`) remains **available** for collectors that ingest such translated metadata. The ontology does not prohibit language-tagged description literals — it simply does not mandate them for the monolingual English metadata that comprises 99%+ of current production data.

**Collector flexibility:** Collectors are free to emit `pkg:description "Le serveur web Apache"@fr` alongside `pkg:description "Apache web server"@en` when multilingual metadata is available. The ontology's schema does not constrain this — RDF's language tag mechanism is always available at the data layer.

---

## DD-VirtualPackage: provides vs providesCapability Bifurcation

**Pattern:** Two distinct property paths for dependency satisfaction — `provides` (Package→Package) for virtual packages, `providesCapability` (Package→Capability) for named capabilities.

**Why the split:**

`VirtualPackage` is modeled as `rdfs:subClassOf :Capability`, not `rdfs:subClassOf :Package`. The ontological rationale (OntoClean): virtual packages are abstract capability promises without installable artifacts (no size, no checksum, no files). Real packages (`pkg:Package`) are concrete installable units.

This creates a **query bifurcation**: dependency resolution queries must traverse both paths to catch all satisfaction mechanisms.

**When to use each:**

| Predicate | Domain | Range | Use Case |
|---|---|---|---|
| `provides` | Package | Package | Package X provides Package Y (e.g., `postfix` provides `mail-transport-agent` in Debian) — Y is a VirtualPackage that is ALSO typed as Capability |
| `providesCapability` | Package | Capability | Package X provides shared library capability (e.g., `openssl` provides `libssl.so.3`) — capability is a named library, not a package |

**SPARQL pattern for comprehensive dependency satisfaction:**

```sparql
SELECT DISTINCT ?provider
WHERE {
  {
    ?target pkg:packageName "mail-transport-agent" .
    ?provider pkg:provides ?target .
  }
  UNION
  {
    ?capability pkg:capabilityName "mail-transport-agent" .
    ?provider pkg:providesCapability ?capability .
  }
}
```

See CQ-PM-03b for a working example.

**Historical note:** An early version modeled VirtualPackage as a subclass of Package. This was rejected during the OntoClean audit because virtual packages lack the rigid properties (size, checksum) that define Package instances. Moving them to Capability eliminated the need for `owl:minCardinality 0` overrides on Package restrictions.

---

## DD-crossDistributionAlternative: Renamed from equivalentInDistribution

**Rationale for rename:** Academic peer review feedback flagged that a property named `equivalentInDistribution` which is documented as **not transitive** creates reviewer confusion. In OWL/RDF semantics, "equivalent" strongly implies transitivity (A≡B and B≡C → A≡C), yet cross-distribution package equivalence is context-dependent and should NOT be transitive.

**Why non-transitive:**

Cross-distribution package correspondence is an approximation, not formal equivalence:
- Debian `libssl-dev` ≈ Fedora `openssl-devel` (both provide OpenSSL development headers)
- Fedora `openssl-devel` ≈ Alpine `openssl-dev` (same upstream, different ABI)
- But Debian `libssl-dev` and Alpine `openssl-dev` may differ in ABI version, patch level, or enabled features

Transitive closure would incorrectly infer that Debian and Alpine packages are equivalent just because they both correspond to the Fedora package. The property is **symmetric** (if A~B then B~A) but intentionally **not transitive**.

**Property characteristics:**
- `owl:SymmetricProperty` — yes
- `owl:TransitiveProperty` — NO (intentionally omitted)

**Renamed:** `crossDistributionAlternative` signals correspondence/alternative rather than formal equivalence.

**Backward compatibility:** The rename is a breaking change from v0.5.x to v0.6.0, documented in CHANGELOG.md and tracked via `owl:priorVersion <.../0.5.0>` declarations.

---

### DD-SignatureStatusStrings: String Enums for Small Fixed Value Sets

**Decision:** `att:signatureStatus` and `slsa:verificationStatus` use `xsd:string` with `sh:in` SHACL constraints rather than SKOS concept schemes.

**Context:** v0.7.0 converted `sec:advisorySeverity` (5 values) and `sec:advisoryType` (3 values) from string literals to SKOS ObjectProperties. The attestation module (v0.8.0) introduces `att:signatureStatus` with 3 values (`verified`, `failed`, `unverified`) using the string-with-sh:in pattern.

**Rationale:**
- The v0.7.0 SKOS conversion was driven by security domain requirements — severity levels have ordering semantics (critical > high > medium > low) and advisory types have hierarchical relationships that benefit from concept scheme modeling.
- Signature verification status is a flat 3-value result with no ordering or hierarchy. The string-with-sh:in pattern is simpler for both producers and consumers.
- `slsa:verificationStatus` already uses the same string vocabulary and predates the SKOS direction. Alignment between the two properties was a design goal.
- The sh:in constraint catches value errors during SHACL validation. Query-time typos (e.g., "Verified" vs "verified") are a known trade-off — SKOS concepts prevent this class of bug but add 3 named individuals, a concept scheme, and an ObjectProperty change for a 3-value enum.

**Alternative considered:** SKOS concepts for all enums. Rejected for signature status due to disproportionate modeling overhead relative to the enum size and lack of ordering/hierarchy semantics.

**Revisit trigger:** If `att:signatureStatus` grows beyond 5 values, or if ordering semantics are needed (e.g., "verified > partially_verified > unverified"), convert to SKOS at that point.

---

### DD-ForgeSoftwareVsVCS: ForgeSoftware and VersionControlSystem Are Independent

**Decision:** `vcs:ForgeSoftware` and `vcs:VersionControlSystem` are independent classes with no subclass or equivalence relationship.

**Context:** Both classes live in the `vcs:` namespace and their individuals appear near each other in `vcs.ttl`. Downstream code may conflate them because platforms like GitHub are strongly associated with Git. But "GitHub" and "Git" are different things — one is a hosting platform, the other is a version control system.

**Class responsibilities:**

| Class | What it represents | Examples | Used by |
|-------|-------------------|----------|---------|
| `vcs:VersionControlSystem` | A VCS type (the tool) | Git, Subversion, Mercurial, Bazaar, CVS, Fossil | `vcs:supportedVcs` range (on ForgeSoftwareVersion), future `vcs:vcsType` replacement |
| `vcs:ForgeSoftware` | A forge product family (the hosting platform) | GitHub, GitLab, Forgejo, Gitea, SourceHut, cgit | `vcs:forgeSoftware` range (on Forge instance) |

**Connection between them:** `vcs:ForgeSoftwareVersion → supportedVcs → VersionControlSystem`. A forge software version supports one or more VCS types. This is a has-a relationship (capability), not an is-a relationship (inheritance).

**Why no inheritance:** GitHub is not a kind of Git. GitLab is not a kind of Git. Savannah supports Git AND Subversion AND Mercurial — it cannot be a subclass of any single VCS. The relationship is version-dependent capability, not type hierarchy.

**Downstream guidance:** If your code checks `?x a vcs:ForgeSoftware`, you get forge platforms. If your code checks `?x a vcs:VersionControlSystem`, you get VCS types. These will never overlap. To find what VCS a forge supports: `?version vcs:versionOfSoftware ?forge ; vcs:supportedVcs ?vcs`.

---

### DD-REL: Reified Package Relationships with Epistemic Qualifiers

**Decision:** Add `PackageRelationship` as a reified cross-ecosystem identity link with `matchMethod` and `matchConfidence`, complementing the existing `crossDistributionAlternative` and `upstreamEquivalent` shortcut properties.

**Rationale:** The shortcut properties assert clean equivalence but provide no evidence for how the equivalence was established or how reliable it is. ecosyste.ms/advisories tracks `match_kind` (repo_fork, likely_fork, repackage, name_match) because identity matching across ecosystems is inherently uncertain. A `crossDistributionAlternative` link established by Repology project mapping (confidence ~0.95) is qualitatively different from one established by name heuristic (confidence ~0.6). The reification makes this distinction queryable without breaking existing shortcut-based queries.

**Relationship to existing properties:** `crossDistributionAlternative` and `upstreamEquivalent` remain as unqualified convenience shortcuts. `PackageRelationship` provides the qualified version when evidence matters. The two models coexist — parallel to the `directlyDependsOn` / `hasDependency` dual pattern.

**Source-side enforcement:** SHACL includes a SPARQL constraint requiring every `PackageRelationship` to be linked from at least one `PackageIdentity` via `hasPackageRelationship`, preventing orphaned relationship nodes.

---

### DD-TAX: Taxonomy as SKOS, Not OWL Classes

**Decision:** Model the OSS Taxonomy as a SKOS concept scheme with `skos:Collection` per facet, not as OWL class hierarchies.

**Rationale:** Taxonomy terms are classification labels, not ontological types. A package classified as `role:framework` does not become a member of a `Framework` class — it carries a tag. SKOS is the W3C standard for exactly this use case: controlled vocabularies, thesauri, and classification systems. Using SKOS keeps the taxonomy editable (add/remove terms without OWL reasoning impact), aligns with the CodeMeta community direction (ecosyste.ms is working with CodeMeta on structured taxonomy support), and allows multiple classifications per facet without multiple inheritance problems.

**Alternative rejected:** OWL subclasses of `Package` (e.g., `FrameworkPackage`, `LibraryPackage`). This would force single-class assignment (or use multiple inheritance), create a combinatorial explosion of classes, and conflate classification with identity.

---

### DD-EPSS: EPSS as Reified Assessment

**Decision:** Model EPSS as a reified `EPSSAssessment` class with timestamp, rather than flat properties on `Vulnerability`.

**Rationale:** EPSS scores are temporal predictions that change daily as FIRST.org updates their model with new exploit activity data. A flat `epssScore` property would imply a static value. The reification pattern mirrors `CVSSScore` and allows storing historical EPSS assessments to track how exploit probability evolves over a vulnerability's lifetime. ecosyste.ms/advisories stores only the latest score; our model supports the full timeline.

**Alternative rejected:** Flat properties (`sec:epssScore`, `sec:epssPercentile` directly on `Vulnerability`). Simpler but loses temporal dimension. If the pipeline only ever stores the latest score, the reification degrades gracefully to a single assessment per vulnerability.

---

### DD-RB: Reified Rebuild Assessment with Presence / Fidelity / Drift Axes

**Decision:** Model rebuild tracking as a reified `RebuildAssessment` class with temporal scope, versioned method, and three independent axes (presence, fidelity, drift), each with its own baseline.

**Why reified:** Rebuild determinations are computed results: uncertain heuristics (vendor-suffix stripping, version normalization), time-sensitive snapshot-relative comparisons, and multi-valued (a package can be both vendor-patched and behind upstream simultaneously). This mirrors the reification precedents `PackageRelationship` (DD-REL: epistemic qualifiers on cross-ecosystem matches) and `EPSSAssessment` (DD-EPSS: temporal predictions). A flat triple `rebuildTrackingStatus` on the package cannot express all three axes independently, cannot carry versioned methodology, and provides no evidence trail for promotion to committed `rebuildOf` lineage.

**Three axes, cleanly separated:**

| Question | Property | Baseline | Notes |
|----------|----------|----------|-------|
| Does an upstream counterpart exist? | `pkg:hasUpstreamCounterpart` (boolean) | assessed `DataSnapshot` | Absence means source name not found in upstream dataset (distro exclusives, e.g., `almalinux-release`) |
| What upstream build was this rebuilt from, how faithfully? | `pkg:rebuildFidelity` | `pkg:fidelityBaseline` | Four tiers: exact EVR match, vendor-patched suffix strip, modular-equivalent, unknown |
| How does it sit vs upstream's current newest? | `pkg:rebuildDrift` | `pkg:comparedAgainst` | Four outcomes: even, ahead, behind, version-equivalent |

Separating fidelity from drift enables the highest-value supply-chain signal: vendor-patched **and** behind — locally modified but lagging upstream security updates — expressible as `rebuildFidelity = vendor-patched` (baseline: the specific upstream build rebuilt) and `rebuildDrift = behind` (baseline: upstream's newest, e.g. the SRPM rebuilt vs. RHEL's newest). These reference *different* upstream builds, both recorded on the assessment. The class and property model (`RebuildAssessment`, the three axes, evidence-gated `rebuildOf`) is ecosystem-neutral; RPM/RHEL is the motivating and most fully worked example, not a scope boundary — see the method-id discussion below.

**The versioned executable algorithm `rebuild-norm/v1`:**

Normalized candidate matching is deterministic and versioned. `pkg:assessmentMethod` is a free-form versioned identifier precisely so each ecosystem can define its own ruleset — `rebuild-norm/v1` below is the RPM-family instantiation (RHEL/AlmaLinux/Rocky), not the only one a conformant assessment may cite. A Debian-derivative rebuild would define its own id (e.g. `debian-norm/v1`) over `dpkg --compare-versions`; a language-ecosystem rebuild (Maven, npm, Cargo) would define one over semantic versioning. The method id pins the ruleset:

- **Candidate scope:** upstream builds with same source `packageName` within the release (and, for modular packages, same `module:stream`) recorded in `assessedAgainstSnapshot`.
- **Version comparison:** epoch-aware `rpmvercmp` over full EVR. Missing epoch treated as `0` (RPM semantics).
- **Exact match:** canonical EVR equality — string equality of `E:V-R` after epoch normalization.
- **Vendor-suffix normalization:** strip anchored suffixes recognized by the method ruleset (e.g., AlmaLinux `\.alma\.\d+$`). Re-match → `fidelity-vendor-patched`.
- **Modular normalization:** strip module build-context marker (`\.module[+_]el\d+.*$`), match base NVR within same stream → `fidelity-modular-equivalent`.
- **Ambiguity handling:** if multiple upstream builds match at the chosen fidelity tier, record all via `pkg:ambiguousCandidate` (domain `RebuildAssessment`, range `SourcePackage`, `minCount 2`), set `rebuildFidelity = fidelity-unknown`, set `assessmentConfidence = 0.5` (deterministic, not vague), and set `lineageConfirmed = false` (never promote from ambiguous match). This explicit ambiguity representation (not merely low confidence) supports investigation and cross-distro comparison.

**Candidate-vs-committed lineage split:**

The algorithm produces a *candidate* baseline on the assessment (`fidelityBaseline` + versioned method + confidence). The committed `rebuildOf` triple is **not auto-created**. It is **promoted only** when an explicit evidence policy is satisfied — e.g., matching source-artifact digest, vendor-published build provenance, or operator confirmation — never from normalization alone. The assessment carries:
- `pkg:lineageConfirmed` — `xsd:boolean`, exactly one value (boolean, not optional). Promotes *only* when independent evidence supports the baseline.
- `pkg:lineageEvidence` — `xsd:string`, what evidence type (e.g., `"srpm-sha256-match"`, `"vendor-build-provenance"`, `"operator:jdoe"`). Required when `lineageConfirmed = true`; must be absent when `false` (prohibit misleading residual evidence).

A normalized vendor/modular match — fidelity result alone — does **not** pass the lineage guard (SHACL SPARQL constraint: for every `rebuildOf` link, there must exist an assessment pointing to the same `fidelityBaseline` with `lineageConfirmed = true`).

**Canonical link direction and RDFS validation:**

The assessment points to its package via `pkg:assessmentOf` (asserted, canonical). **All SHACL, competency questions, and the lineage guard use the asserted direction `assessmentOf`.** The inverse `pkg:hasRebuildAssessment` remains optional (`owl:inverseOf`) for authoring convenience, but **nothing in validation depends on inverse inference** — the project validates with RDFS only, which does not materialize `owl:inverseOf`. This prevents silent validation failures when inverse rules are not applied.

**Property characteristics:**

`pkg:rebuildOf` is declared `owl:AsymmetricProperty` and `owl:IrreflexiveProperty`. Asymmetry forbids only mutual `rebuildOf` (A→B→A); chains A→B→C remain legal. Irreflexivity forbids self-derivation (A→A), preventing circular lineage. **Baselines are NOT declared irreflexive** — `fidelityBaseline` and `comparedAgainst` have disjoint node kinds (domain `RebuildAssessment`, range `SourcePackage`), so `owl:IrreflexiveProperty` would be vacuous. The real constraint — *assessed package ≠ baseline package* — is enforced in SHACL via comparison logic.

**Wording discipline:** NVR equality does not establish byte identity. Vendor-suffix stripping and version normalization are strong evidence, not cryptographic proof. Reproducible builds *may* yield byte-identical artifacts, but NVR matching alone cannot verify that claim.

**Freshness distinction:**

**Validation limits under RDFS inference.** The project validates with pyshacl
`inference="rdfs"`, which materialises each property's `rdfs:range`. A `sh:class` check on
`fidelityBaseline`, `comparedAgainst`, or `ambiguousCandidate` consequently cannot reject an
IRI that was typed as another class — range inference retypes it first — though it still
rejects literals. Cardinality (`sh:maxCount 1` on both baselines) and the `lineageEvidence`
`sh:datatype`/`sh:minLength` checks are fully enforceable and are what the negative fixtures
pin. This is recorded so future readers do not mistake the `sh:class` clauses for stronger
guarantees than they provide.

`rebuildDrift` (pairwise comparison: rebuild vs a specific upstream build) is distinct from `FreshnessStatusScheme` (cross-repo currency: how old is the rebuild vs the upstream ecosystem's latest). Drift answers "is this rebuild stale relative to RHEL's latest?"; freshness answers "how old is RHEL itself compared to Fedora/upstream community?" They are different baselines (specific upstream vs ecosystem benchmark) and are not redundant.

**Rebuild vs. Fork.**

`RebuildAssessment` models an *ongoing* relationship: the downstream is expected to correspond to a specific current upstream release and to keep re-assessing as upstream ships new ones — that expectation is what makes `rebuildDrift` (ahead/behind/even) meaningful. A **fork** is the opposite: development has diverged into an independent trajectory, and there is no longer a "current upstream release" the downstream is expected to track. Asking whether MariaDB is "N versions behind" MySQL is not a well-formed question in the way asking it about AlmaLinux's openssl vs. RHEL's is — the two version schemes stopped corresponding to each other once the fork happened. The project already has vocabulary for the fork case: `PackageRelationship` with `matchMethod = pkg:match-fork-detected` (a diverged, independently-developed trajectory) or `pkg:match-repackage-detected` (republished under a new name, no assumption of continued correspondence).

Two things this is deliberately **not** a test of:

- **Not package-name identity.** A rebuild is commonly published under a different downstream name — Eclipse Temurin, Amazon Corretto, and Azul Zulu all rebuild the same upstream OpenJDK source under their own product names (`temurin-17-jdk`, `java-17-amazon-corretto`, `zulu17-jdk`), and none of that makes them forks. Conversely a repackage under an *unchanged* name is still not a rebuild if it stops tracking upstream's releases. Same-name is neither necessary nor sufficient.
- **Not product-level version comparison.** The unit of comparison is always the specific `SourcePackage`, never the enclosing product or distribution. OpenShift's own release numbering (4.15, 4.16, …) is on a completely different axis from the Kubernetes version it bundles (1.28, 1.29, …) — no version comparison between "OpenShift 4.15" and "Kubernetes 1.28" is meaningful, so `RebuildAssessment` must never be asserted between them at that level. What *does* have a genuine rebuild relationship is the specific vendored Kubernetes source tree inside OpenShift's build against the exact upstream Kubernetes tag it was cut from and patched — the same `SourcePackage`-to-`SourcePackage` discipline this ontology already applies everywhere (cf. Kubernetes distributions like k3s/k0s, whose own release tags make this explicit: `v1.28.5+k3s1` is the anchored-vendor-suffix pattern applied to a Kubernetes rebuild, exactly like `.el9_8.alma.1`).

The line itself is a curatorial judgment — like `crossDistributionAlternative`'s "correspondence, not equivalence" or `match-fork-detected` itself, no structural rule can determine from a single triple whether a project's development has diverged. What SHACL *can* catch is a **contradiction**: the same pair of packages should not simultaneously carry a committed `rebuildOf` lineage claim *and* be linked via `match-fork-detected`/`match-repackage-detected` — that would be classifying the same relationship both ways at once. `pkg:RebuildOfForkContradictionShape` (`sh:Warning` severity — advisory, not a hard violation, since the two links are populated by different curatorial processes and may legitimately not both be present) flags this when both are.

---

### DD-PE-1: PackageEntity as Dependency Target Superclass

**Decision:** Introduce `pkg:PackageEntity` as the common superclass of `pkg:Package` and `pkg:PackageIdentity`. Generic dependency properties (`dependsOn`, `directlyDependsOn`, `dependencyTarget`) target `PackageEntity`; their sources remain concrete `Package` instances. Inverse properties (`isDependencyOf`, `isDirectDependencyOf`) widen their domain to `PackageEntity`.

**Problem:** Platform collectors emit dependency targets as `PackageIdentity` resources (version-independent coordinates), but the dependency properties declared `rdfs:range pkg:Package`. Under RDFS/OWL reasoning, any `PackageIdentity` used as a dependency target was incorrectly inferred as `pkg:Package`, collapsing the intended distinction between identities and concrete releases.

**Why a named superclass, not an OWL union?** An anonymous union of `Package` and `PackageIdentity` expresses the allowed set in OWL but is less useful to RDFS-only consumers and more cumbersome in SHACL and SPARQL. A named superclass gives callers a stable query and validation target.

**Why not PackageIdentity-only targets?** Existing core examples and ecosystem properties (Maven, Nix, Conda) intentionally target concrete package subclasses. Making every dependency target exclusively a `PackageIdentity` would invalidate those models.

**prov:Entity promotion:** `PackageEntity rdfs:subClassOf prov:Entity` means `PackageIdentity` becomes a `prov:Entity` by transitivity. This is intentional — PROV-O defines Entity broadly enough to include conceptual things with fixed aspects. Queries targeting `prov:Entity` must be audited.

**Disjointness deferred:** `Package` and `PackageIdentity` are not declared `owl:disjointWith` in this change. Existing reasoned data may contain identity resources with stale `rdf:type pkg:Package` from the old ranges. The first release stops the invalid inference; explicit disjointness can be considered after production data audit.

**Core subproperties:** All seven generic `dependsOn` subproperties (`buildDependsOn`, `checkRequires`, `enhances`, `preDepends`, `recommends`, `suggests`, `supplements`) also widen their ranges to `PackageEntity`. The platform already emits `buildDependsOn` to identity targets; leaving a narrower `Package` range would reintroduce the inference collapse.

**Ecosystem subproperties:** Ecosystem-specific dependency subproperties (e.g., `nix:nixBuildInput` with range `nix:Derivation`) retain their narrower ranges. RDFS range is conjunctive — a target is inferred as both the ecosystem type and `PackageEntity`. These narrower ranges are intentional when the ecosystem always targets concrete packages.

**Version:** Released as ontology v0.11.0 (corrective semantic revision, not conservative extension).

---

### DD-UO-1: Upper Ontology Non-Alignment

**Decision:** PackageGraph does not align with BFO or DOLCE. It references them as evaluated alternatives, not as imports or formal alignments.

**Rationale:**
- BFO's `material-entity` / `process` / `disposition` hierarchy does not cleanly categorize software packages, which are informational artifacts with physical manifestations (installed files) and social roles (maintainers)
- DOLCE's cognitive/social focus treats roles as dependent on agents, but package maintenance roles are organizational constructs, not cognitive states
- Domain vocabularies (PROV-O for provenance, FOAF for people, SPDX for licensing, DOAP for projects) provide the interoperability that matters for this domain — foundational ontology categorization does not

**What we use instead:**
- `prov:Agent`, `prov:Entity`, `prov:Activity` for provenance chains
- `foaf:Person` equivalence for contributor identity
- `spdx:Vulnerability` cross-reference for security alignment
- `doap:Project` superclass for upstream projects

**Historical note:** Early versions (pre-v0.6.0) included `dcterms:references` to BFO and DOLCE OWL files, which was misinterpreted by reviewers as claiming formal alignment. Changed to `rdfs:comment` attribution in v0.9.0.
