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
