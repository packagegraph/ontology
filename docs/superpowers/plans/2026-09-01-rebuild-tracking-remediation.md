# Rebuild Tracking Vocabulary Remediation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat `rebuildTrackingStatus` triple with a reified
`RebuildAssessment` model (presence / fidelity / drift axes, evidence-gated
lineage, snapshot-scoped provenance), plus SHACL, examples, a negative-fixture
harness, competency questions, a design-decision record, and release hygiene.

**Architecture:** A reified qualifier class `pkg:RebuildAssessment` (mirroring
`pkg:PackageRelationship`) carries three classification axes, each with its own
baseline on the assessment. Committed `prov` lineage (`rebuildOf`) is gated behind
an evidence flag (`lineageConfirmed`). All coupling/integrity rules are SHACL
(SPARQL-based, per the DD-REL precedent). Validation stays per-module via
`scripts/validate_module.py` (pyshacl, `inference="rdfs"`); a new negative-fixture
harness asserts that malformed graphs fail.

**Tech Stack:** RDF/Turtle, OWL 2, SKOS, SHACL (pyshacl), Python 3, rdflib,
GNU Make. Run Python via `$(PYTHON)` = `uv run python` locally.

**Spec:** `docs/superpowers/specs/2026-09-01-rebuild-tracking-remediation-design.md`
(read it alongside this plan — it carries the full definitions, the normative
`rebuild-norm/v1` algorithm, and the finding-by-finding rationale).

## Global Constraints

- Namespace: core terms use prefix `:` / `pkg:` = `https://purl.org/packagegraph/ontology/core#`.
- Every property carries `rdfs:label`@en, `IAO:0000115` (definition), `rdfs:comment`,
  and `rdfs:isDefinedBy :` — matching existing core properties.
- SKOS concepts use `skos:inScheme`, `skos:prefLabel`, `skos:definition` (no `@en`
  tag — matches sibling schemes like `FreshnessStatusScheme`); schemes use
  `rdfs:label`@en + `dcterms:description` + `skos:hasTopConcept`.
- Labels/definitions must be **vendor-generic** (RHEL is an example, never hardcoded).
- Wording rule: exact match = "canonical EVR equality"; never claim "byte-identical"
  or "provable"; the defensible claim is "NVR equality does not establish byte identity."
- Version stays **0.13.0** (unreleased on this branch); do not touch `owl:versionInfo`
  / `owl:versionIRI` / `owl:priorVersion` — they are already 0.13.0.
- pyshacl uses `inference="rdfs"`; `owl:inverseOf` is NOT materialized — validation
  keys only on the asserted `pkg:assessmentOf` direction.
- `core/` validation loads `core.ttl` + `core.examples.ttl` but NOT `skos-schemes.ttl`;
  therefore SHACL uses `sh:in` (value enumeration), never `sh:class skos:Concept`.
- Test each task with the repo's own gates: `make lint`, `make validate-all`
  (or `$(PYTHON) scripts/validate_module.py core`), `make validate-negative` (new),
  `make check-version`, `$(PYTHON) scripts/test-owl2-reasoning.py`.

---

## File Structure

| File | Responsibility | Action |
|------|----------------|--------|
| `core/skos-schemes.ttl` | `RebuildFidelityScheme` (4 concepts) + `RebuildDriftScheme` (4 concepts); remove old `track-*` + `RebuildTrackingScheme` | Modify |
| `core/core.ttl` | `RebuildAssessment` class + 13 new properties; retype/annotate `rebuildOf`, `comparedAgainst`; remove `rebuildTrackingStatus`; bump `dcterms:modified` | Modify |
| `core/core.shacl.ttl` | `RebuildAssessmentShape` (property + SPARQL constraints) + lineage guard; remove old `RebuildTrackingStatusShape` | Modify |
| `core/core.examples.ttl` | Positive examples per outcome incl. Alma/Rocky cross-distro; fix `#v` IRIs | Modify |
| `scripts/validate_negative.py` | Harness asserting fixtures FAIL with the expected shape/message | Create |
| `tests/shacl-negative/*.ttl` | One malformed graph per constraint | Create |
| `tests/shacl-negative/expectations.json` | Expected `sourceShape` + `resultMessage` + `sourceConstraintComponent` per fixture | Create |
| `Makefile` | `validate-negative` target; `validate` depends on it | Modify |
| `docs/competency-questions.md` | `## Domain: Rebuild Tracking (RB)` CQ-RB-01..09 + coverage/stats | Modify |
| `docs/design-decisions.md` | `### DD-RB` entry | Modify |
| `CHANGELOG.md`, `README.md` | Keep-a-Changelog entry; What's-New + CQ count | Modify |

---

## Task 1: SKOS schemes — fidelity & drift concepts

**Files:**
- Modify: `core/skos-schemes.ttl` (append two schemes; delete the seven `pkg:track-*`
  concepts and `pkg:RebuildTrackingScheme` added in commit `19b0028`, near end of file)

**Interfaces:**
- Produces concept IRIs consumed by Tasks 2/3/4: `pkg:fidelity-exact`,
  `pkg:fidelity-vendor-patched`, `pkg:fidelity-modular-equivalent`,
  `pkg:fidelity-unknown`; `pkg:drift-even`, `pkg:drift-ahead`, `pkg:drift-behind`,
  `pkg:drift-version-equivalent`; schemes `pkg:RebuildFidelityScheme`,
  `pkg:RebuildDriftScheme`.

- [ ] **Step 1: Delete the old vocabulary.** Remove every `pkg:track-*` concept block
  and the `pkg:RebuildTrackingScheme` block from `core/skos-schemes.ttl`.

- [ ] **Step 2: Append the two new schemes** to `core/skos-schemes.ttl`:

```turtle
pkg:fidelity-exact a skos:Concept ;
    skos:definition "Canonical EVR equality with the fidelity baseline build (the candidate set already fixes the package name; an absent epoch is treated as 0). NVR/EVR equality does not establish byte identity of artifacts." ;
    skos:inScheme pkg:RebuildFidelityScheme ;
    skos:prefLabel "exact" .

pkg:fidelity-vendor-patched a skos:Concept ;
    skos:definition "EVR equal to a baseline build after stripping an anchored vendor suffix enumerated by the assessment method ruleset (e.g. an AlmaLinux '.alma.N' tag). Strong evidence of rebuilding that source package with a vendor tag — not cryptographic proof." ;
    skos:inScheme pkg:RebuildFidelityScheme ;
    skos:prefLabel "vendor-patched" .

pkg:fidelity-modular-equivalent a skos:Concept ;
    skos:definition "Modular package whose base EVR (before the module build-context marker) matches the baseline within the same module stream; only the module build-context differs. Applies to distributions using RPM modularity (a RHEL-8-era AppStream construct)." ;
    skos:inScheme pkg:RebuildFidelityScheme ;
    skos:prefLabel "modular-equivalent" .

pkg:fidelity-unknown a skos:Concept ;
    skos:definition "An upstream counterpart exists but no baseline matched under normalization (including ambiguous multi-match cases); fidelity cannot be established. No fidelity baseline is recorded." ;
    skos:inScheme pkg:RebuildFidelityScheme ;
    skos:prefLabel "unknown" .

pkg:RebuildFidelityScheme a skos:ConceptScheme ;
    rdfs:label "Rebuild Fidelity"@en ;
    dcterms:description "How faithfully a downstream rebuild source package reproduces the specific upstream build it derives from (the fidelity baseline). Distinct from RebuildDriftScheme, which compares against upstream's current newest build." ;
    skos:hasTopConcept pkg:fidelity-exact,
        pkg:fidelity-vendor-patched,
        pkg:fidelity-modular-equivalent,
        pkg:fidelity-unknown .

pkg:drift-even a skos:Concept ;
    skos:definition "Canonical EVR strings are equal to the compared-against upstream newest build." ;
    skos:inScheme pkg:RebuildDriftScheme ;
    skos:prefLabel "even" .

pkg:drift-ahead a skos:Concept ;
    skos:definition "rpmvercmp ranks the rebuild's EVR higher than the upstream newest build (the rebuild leads the collected snapshot)." ;
    skos:inScheme pkg:RebuildDriftScheme ;
    skos:prefLabel "ahead" .

pkg:drift-behind a skos:Concept ;
    skos:definition "rpmvercmp ranks the rebuild's EVR lower than the upstream newest build (the rebuild lags upstream — investigate)." ;
    skos:inScheme pkg:RebuildDriftScheme ;
    skos:prefLabel "behind" .

pkg:drift-version-equivalent a skos:Concept ;
    skos:definition "Canonical EVR strings differ but rpmvercmp returns equality (e.g. ignored separators or leading zeros). Disjoint from 'even' by construction; a comparison result, not a lineage claim." ;
    skos:inScheme pkg:RebuildDriftScheme ;
    skos:prefLabel "version-equivalent" .

pkg:RebuildDriftScheme a skos:ConceptScheme ;
    rdfs:label "Rebuild Drift"@en ;
    dcterms:description "Where a downstream rebuild source package's build sits relative to upstream's current newest build, by epoch-aware rpmvercmp. Snapshot-relative — always recorded with the compared-against build and the assessment snapshot. Distinct from FreshnessStatusScheme (cross-repository currency)." ;
    skos:hasTopConcept pkg:drift-even,
        pkg:drift-ahead,
        pkg:drift-behind,
        pkg:drift-version-equivalent .
```

- [ ] **Step 3: Verify it parses.** Run: `make lint`
  Expected: PASS — `core/skos-schemes.ttl` listed with a triple count, "All … files valid".

- [ ] **Step 4: Confirm the old vocabulary is gone.** Run:
  `grep -c "track-\|RebuildTrackingScheme" core/skos-schemes.ttl`
  Expected: `0`.

- [ ] **Step 5: Commit.**

```bash
git add core/skos-schemes.ttl
git commit -m "feat(core): add rebuild fidelity + drift SKOS schemes (replace track-*)"
```

---

## Task 2: Core vocabulary — RebuildAssessment class + properties

**Files:**
- Modify: `core/core.ttl` (properties near the existing `:rebuildOf` block ~line 282;
  class near `:PackageRelationship` ~line 1507; remove `:rebuildTrackingStatus`)

**Interfaces:**
- Consumes concept IRIs from Task 1.
- Produces, for Tasks 3/4: class `:RebuildAssessment`; object properties
  `:hasRebuildAssessment`, `:assessmentOf`, `:rebuildFidelity`, `:rebuildDrift`,
  `:fidelityBaseline`, `:comparedAgainst`, `:assessedAgainstSnapshot`,
  `:ambiguousCandidate`, `:rebuildOf`; datatype properties `:hasUpstreamCounterpart`,
  `:assessedAt`, `:assessmentMethod`, `:assessmentConfidence`, `:lineageConfirmed`,
  `:lineageEvidence`.

- [ ] **Step 1: Remove the old status property.** Delete the `:rebuildTrackingStatus`
  block from `core/core.ttl`.

- [ ] **Step 2: Replace the `:rebuildOf` block and the old `:comparedAgainst` block**
  with the retyped/genericized versions:

```turtle
:rebuildOf a owl:ObjectProperty, owl:IrreflexiveProperty, owl:AsymmetricProperty ;
    rdfs:label "rebuild of"@en ;
    IAO:0000115 "Committed build-lineage: links a source package in a downstream rebuild distribution to the specific upstream source package it was rebuilt from. Asserted ONLY when a RebuildAssessment has promoted a candidate baseline to committed lineage (lineageConfirmed = true) on the strength of independent provenance evidence — never inferred from NVR/EVR normalization alone."@en ;
    rdfs:comment "This source package is a rebuild of a specific upstream source package (evidence-confirmed lineage)"@en ;
    rdfs:domain :SourcePackage ;
    rdfs:range :SourcePackage ;
    rdfs:subPropertyOf prov:wasDerivedFrom ;
    rdfs:isDefinedBy : .

:comparedAgainst a owl:ObjectProperty ;
    rdfs:label "compared against"@en ;
    IAO:0000115 "The upstream newest source package build used as the drift baseline for a RebuildAssessment. A comparison reference, NOT a provenance/lineage claim."@en ;
    rdfs:comment "Upstream newest build used as the drift baseline; not a lineage claim"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range :SourcePackage ;
    rdfs:isDefinedBy : .
```

- [ ] **Step 3: Add the assessment class and remaining properties** to `core/core.ttl`:

```turtle
:RebuildAssessment a owl:Class ;
    rdfs:label "rebuild assessment"@en ;
    IAO:0000115 "A reified, timestamped observation classifying how a downstream rebuild source package tracks upstream, produced by a specific versioned method against a specific data snapshot. Carries the presence, fidelity, and drift axes and their baselines."@en ;
    rdfs:comment "One point-in-time classification of a rebuild source package's relationship to upstream"@en ;
    rdfs:isDefinedBy : .

:hasRebuildAssessment a owl:ObjectProperty ;
    rdfs:label "has rebuild assessment"@en ;
    IAO:0000115 "Links a source package to a RebuildAssessment about it. Optional convenience inverse of assessmentOf; validation keys on the asserted assessmentOf direction (owl:inverseOf is not materialized under RDFS inference)."@en ;
    rdfs:comment "A rebuild assessment about this source package"@en ;
    rdfs:domain :SourcePackage ;
    rdfs:range :RebuildAssessment ;
    owl:inverseOf :assessmentOf ;
    rdfs:isDefinedBy : .

:assessmentOf a owl:ObjectProperty ;
    rdfs:label "assessment of"@en ;
    IAO:0000115 "The source package this RebuildAssessment classifies. Canonical asserted link direction."@en ;
    rdfs:comment "The source package this assessment is about"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range :SourcePackage ;
    rdfs:isDefinedBy : .

:rebuildFidelity a owl:ObjectProperty ;
    rdfs:label "rebuild fidelity"@en ;
    IAO:0000115 "How faithfully the assessed build reproduces its fidelity baseline, as a SKOS concept from RebuildFidelityScheme. Computed per the versioned assessment method (see assessmentMethod)."@en ;
    rdfs:comment "Fidelity classification for this assessment"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range skos:Concept ;
    rdfs:isDefinedBy : .

:rebuildDrift a owl:ObjectProperty ;
    rdfs:label "rebuild drift"@en ;
    IAO:0000115 "Where the assessed build sits relative to upstream's newest build (the comparedAgainst baseline), as a SKOS concept from RebuildDriftScheme. Epoch-aware rpmvercmp against the assessment snapshot."@en ;
    rdfs:comment "Drift classification for this assessment"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range skos:Concept ;
    rdfs:isDefinedBy : .

:fidelityBaseline a owl:ObjectProperty ;
    rdfs:label "fidelity baseline"@en ;
    IAO:0000115 "The specific upstream source package build the fidelity result was measured against. A comparison baseline, NOT a prov:wasDerivedFrom claim."@en ;
    rdfs:comment "Upstream build used as the fidelity baseline; not a lineage claim"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range :SourcePackage ;
    rdfs:isDefinedBy : .

:ambiguousCandidate a owl:ObjectProperty ;
    rdfs:label "ambiguous candidate"@en ;
    IAO:0000115 "An upstream build that tied with others when normalization matched more than one candidate. Present only with rebuildFidelity = fidelity-unknown; at least two are recorded."@en ;
    rdfs:comment "A tied upstream candidate for an ambiguous fidelity match"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range :SourcePackage ;
    rdfs:isDefinedBy : .

:assessedAgainstSnapshot a owl:ObjectProperty ;
    rdfs:label "assessed against snapshot"@en ;
    IAO:0000115 "The upstream data snapshot from which candidates, presence, and the newest build were determined. Required on every assessment so results (including closed-world absence) are reproducible."@en ;
    rdfs:comment "The upstream snapshot this assessment was computed against"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range :DataSnapshot ;
    rdfs:isDefinedBy : .

:hasUpstreamCounterpart a owl:DatatypeProperty ;
    rdfs:label "has upstream counterpart"@en ;
    IAO:0000115 "Whether the assessed source package name is present in the searched upstream snapshot. False indicates a distribution-exclusive package (branding or extras); when false, fidelity, drift, and baselines are omitted."@en ;
    rdfs:comment "Whether an upstream counterpart exists in the assessed snapshot"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range xsd:boolean ;
    rdfs:isDefinedBy : .

:assessedAt a owl:DatatypeProperty ;
    rdfs:label "assessed at"@en ;
    IAO:0000115 "The date and time this rebuild assessment was computed."@en ;
    rdfs:comment "When this assessment was computed"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range xsd:dateTime ;
    rdfs:isDefinedBy : .

:assessmentMethod a owl:DatatypeProperty ;
    rdfs:label "assessment method"@en ;
    IAO:0000115 "A versioned identifier of the tool and ruleset that produced this assessment (e.g. 'rebuild-norm/v1'). The identifier pins the exact normalization and comparison rules documented in the design decisions."@en ;
    rdfs:comment "Versioned method/ruleset identifier for this assessment"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range xsd:string ;
    rdfs:isDefinedBy : .

:assessmentConfidence a owl:DatatypeProperty ;
    rdfs:label "assessment confidence"@en ;
    IAO:0000115 "A confidence score (0.0 to 1.0) for this assessment's classification. Ambiguous multi-match outcomes take the deterministic value fixed by the method (0.5 for rebuild-norm/v1)."@en ;
    rdfs:comment "Confidence score for this assessment (0.0-1.0)"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range xsd:decimal ;
    rdfs:isDefinedBy : .

:lineageConfirmed a owl:DatatypeProperty ;
    rdfs:label "lineage confirmed"@en ;
    IAO:0000115 "Whether the promotion policy was satisfied by independent provenance evidence, licensing a committed rebuildOf triple to this assessment's fidelityBaseline. Normalized-only matches remain candidates (false)."@en ;
    rdfs:comment "Whether committed rebuildOf lineage is licensed by evidence"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range xsd:boolean ;
    rdfs:isDefinedBy : .

:lineageEvidence a owl:DatatypeProperty ;
    rdfs:label "lineage evidence"@en ;
    IAO:0000115 "A description of the independent provenance evidence that satisfied the promotion policy (e.g. 'srpm-sha256-match', 'vendor-build-provenance', 'operator:jdoe'). Present only when lineageConfirmed is true."@en ;
    rdfs:comment "Independent evidence supporting committed lineage"@en ;
    rdfs:domain :RebuildAssessment ;
    rdfs:range xsd:string ;
    rdfs:isDefinedBy : .
```

- [ ] **Step 3b: Update the AllDisjointClasses guard is NOT needed** — do not add
  `:RebuildAssessment` to the `owl:AllDisjointClasses` lists (it is a qualifier, like
  `:PackageRelationship`, which is also not disjoint with packages beyond its existing
  membership). Leave those lists unchanged.

- [ ] **Step 4: Verify it parses.** Run: `make lint`
  Expected: PASS — `core/core.ttl` valid.

- [ ] **Step 5: Verify OWL 2 reasoning still holds.** Run:
  `$(PYTHON) scripts/test-owl2-reasoning.py`
  Expected: all PASS (SourcePackage remains a prov:Entity; no new inconsistency).

- [ ] **Step 6: Commit.**

```bash
git add core/core.ttl
git commit -m "feat(core): reified RebuildAssessment vocabulary; gate rebuildOf on evidence"
```

---

## Task 3: SHACL — RebuildAssessmentShape + guards

**Files:**
- Modify: `core/core.shacl.ttl` (remove `pkg:RebuildTrackingStatusShape`; add the
  shapes below)

**Interfaces:**
- Consumes vocabulary from Tasks 1–2.
- Produces named shapes used by Task 4 (positive) and Task 6 (negative) fixtures:
  `pkg:RebuildAssessmentShape`, `pkg:RebuildAssessmentPromotionShape`,
  `pkg:RebuildAssessmentSelfBaselineShape`, `pkg:RebuildAssessmentResultsShape`,
  `pkg:RebuildAssessmentAmbiguityShape`, `pkg:RebuildLineageGuardShape`. Each SPARQL
  constraint carries a distinct `sh:message` (asserted by the negative harness).

- [ ] **Step 1: Delete** `pkg:RebuildTrackingStatusShape` from `core/core.shacl.ttl`.

- [ ] **Step 2: Add the property shape** (required fields + enumerations):

```turtle
pkg:RebuildAssessmentShape a sh:NodeShape ;
    sh:targetClass pkg:RebuildAssessment ;
    sh:property [ sh:path pkg:assessmentOf ; sh:class pkg:SourcePackage ; sh:minCount 1 ; sh:maxCount 1 ;
            sh:message "A RebuildAssessment must have exactly one assessmentOf SourcePackage."@en ] ;
    sh:property [ sh:path pkg:assessedAt ; sh:datatype xsd:dateTime ; sh:minCount 1 ; sh:maxCount 1 ;
            sh:message "A RebuildAssessment must have exactly one assessedAt dateTime."@en ] ;
    sh:property [ sh:path pkg:assessmentMethod ; sh:datatype xsd:string ; sh:minCount 1 ; sh:maxCount 1 ;
            sh:message "A RebuildAssessment must have exactly one assessmentMethod."@en ] ;
    sh:property [ sh:path pkg:assessedAgainstSnapshot ; sh:class pkg:DataSnapshot ; sh:minCount 1 ; sh:maxCount 1 ;
            sh:message "A RebuildAssessment must reference exactly one assessedAgainstSnapshot."@en ] ;
    sh:property [ sh:path pkg:hasUpstreamCounterpart ; sh:datatype xsd:boolean ; sh:minCount 1 ; sh:maxCount 1 ;
            sh:message "A RebuildAssessment must have exactly one hasUpstreamCounterpart boolean."@en ] ;
    sh:property [ sh:path pkg:lineageConfirmed ; sh:datatype xsd:boolean ; sh:minCount 1 ; sh:maxCount 1 ;
            sh:message "A RebuildAssessment must have exactly one lineageConfirmed boolean."@en ] ;
    sh:property [ sh:path pkg:assessmentConfidence ; sh:datatype xsd:decimal ; sh:maxCount 1 ;
            sh:minInclusive 0.0 ; sh:maxInclusive 1.0 ;
            sh:message "assessmentConfidence must be between 0.0 and 1.0."@en ] ;
    sh:property [ sh:path pkg:rebuildFidelity ; sh:maxCount 1 ;
            sh:in ( pkg:fidelity-exact pkg:fidelity-vendor-patched pkg:fidelity-modular-equivalent pkg:fidelity-unknown ) ;
            sh:message "rebuildFidelity must be a concept from RebuildFidelityScheme."@en ] ;
    sh:property [ sh:path pkg:rebuildDrift ; sh:maxCount 1 ;
            sh:in ( pkg:drift-even pkg:drift-ahead pkg:drift-behind pkg:drift-version-equivalent ) ;
            sh:message "rebuildDrift must be a concept from RebuildDriftScheme."@en ] .
```

- [ ] **Step 3: Add the SPARQL constraint shapes** (coupling, conditionals, ambiguity,
  self-baseline, promotion). All target `pkg:RebuildAssessment` except the lineage
  guard:

```turtle
pkg:RebuildAssessmentResultsShape a sh:NodeShape ;
    sh:targetClass pkg:RebuildAssessment ;
    sh:sparql [ sh:message "hasUpstreamCounterpart=false forbids fidelity, drift, baselines, and ambiguous candidates."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:hasUpstreamCounterpart false .
                        { $this pkg:rebuildFidelity ?x } UNION { $this pkg:rebuildDrift ?x }
                        UNION { $this pkg:fidelityBaseline ?x } UNION { $this pkg:comparedAgainst ?x }
                        UNION { $this pkg:ambiguousCandidate ?x }
                    }
                """ ] ,
        [ sh:message "hasUpstreamCounterpart=true requires exactly one rebuildFidelity and one rebuildDrift."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:hasUpstreamCounterpart true .
                        FILTER ( NOT EXISTS { $this pkg:rebuildFidelity ?f } || NOT EXISTS { $this pkg:rebuildDrift ?d } )
                    }
                """ ] ,
        [ sh:message "rebuildDrift present requires a comparedAgainst baseline."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:rebuildDrift ?d .
                        FILTER NOT EXISTS { $this pkg:comparedAgainst ?c }
                    }
                """ ] ,
        [ sh:message "A matched fidelity (exact/vendor-patched/modular-equivalent) requires a fidelityBaseline."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:rebuildFidelity ?f .
                        FILTER ( ?f IN ( pkg:fidelity-exact, pkg:fidelity-vendor-patched, pkg:fidelity-modular-equivalent ) )
                        FILTER NOT EXISTS { $this pkg:fidelityBaseline ?b }
                    }
                """ ] ,
        [ sh:message "fidelity-unknown forbids a fidelityBaseline."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:rebuildFidelity pkg:fidelity-unknown ; pkg:fidelityBaseline ?b .
                    }
                """ ] .

pkg:RebuildAssessmentSelfBaselineShape a sh:NodeShape ;
    sh:targetClass pkg:RebuildAssessment ;
    sh:sparql [ sh:message "A package must not be its own fidelity or drift baseline."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:assessmentOf ?p .
                        { $this pkg:fidelityBaseline ?p } UNION { $this pkg:comparedAgainst ?p }
                    }
                """ ] .

pkg:RebuildAssessmentAmbiguityShape a sh:NodeShape ;
    sh:targetClass pkg:RebuildAssessment ;
    sh:sparql [ sh:message "ambiguousCandidate requires rebuildFidelity = fidelity-unknown."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:ambiguousCandidate ?c .
                        FILTER NOT EXISTS { $this pkg:rebuildFidelity pkg:fidelity-unknown }
                    }
                """ ] ,
        [ sh:message "ambiguousCandidate requires at least two distinct candidates."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:ambiguousCandidate ?c .
                        FILTER NOT EXISTS { $this pkg:ambiguousCandidate ?c2 . FILTER ( ?c2 != ?c ) }
                    }
                """ ] ,
        [ sh:message "An ambiguous assessment must have assessmentConfidence 0.5 and lineageConfirmed=false."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:ambiguousCandidate ?c .
                        FILTER ( NOT EXISTS { $this pkg:assessmentConfidence ?v . FILTER ( ?v = 0.5 ) }
                                 || EXISTS { $this pkg:lineageConfirmed true } )
                    }
                """ ] .

pkg:RebuildAssessmentPromotionShape a sh:NodeShape ;
    sh:targetClass pkg:RebuildAssessment ;
    sh:sparql [ sh:message "lineageConfirmed=true requires a matched fidelity, a fidelityBaseline, and non-empty lineageEvidence."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:lineageConfirmed true .
                        FILTER ( NOT EXISTS { $this pkg:fidelityBaseline ?b }
                                 || NOT EXISTS { $this pkg:lineageEvidence ?e . FILTER ( STRLEN( STR(?e) ) > 0 ) }
                                 || NOT EXISTS { $this pkg:rebuildFidelity ?f .
                                        FILTER ( ?f IN ( pkg:fidelity-exact, pkg:fidelity-vendor-patched, pkg:fidelity-modular-equivalent ) ) } )
                    }
                """ ] ,
        [ sh:message "lineageConfirmed=false forbids lineageEvidence."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:lineageConfirmed false ; pkg:lineageEvidence ?e .
                    }
                """ ] .

pkg:RebuildLineageGuardShape a sh:NodeShape ;
    sh:targetSubjectsOf pkg:rebuildOf ;
    sh:sparql [ sh:message "rebuildOf requires an assessment of the same package with the same fidelityBaseline and lineageConfirmed=true."@en ;
            sh:select """
                    PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
                    SELECT $this WHERE {
                        $this pkg:rebuildOf ?target .
                        FILTER NOT EXISTS {
                            ?a pkg:assessmentOf $this ;
                               pkg:fidelityBaseline ?target ;
                               pkg:lineageConfirmed true .
                        }
                    }
                """ ] .
```

- [ ] **Step 4: Verify it parses.** Run: `make lint`
  Expected: PASS — `core/core.shacl.ttl` valid.

- [ ] **Step 5: Confirm no examples exist yet to break.** Run:
  `$(PYTHON) scripts/validate_module.py core`
  Expected: `✓ core: … SHACL OK` (the current `core.examples.ttl` has no
  RebuildAssessment instances yet, so no shape fires). If it reports violations,
  they are from the pre-existing `#v` example — that is fixed in Task 4; proceed.

- [ ] **Step 6: Commit.**

```bash
git add core/core.shacl.ttl
git commit -m "feat(core): SHACL for RebuildAssessment (coupling, ambiguity, lineage guard)"
```

---

## Task 4: Positive examples

**Files:**
- Modify: `core/core.examples.ttl` (remove the `track-exact`/`#v` example added in
  `19b0028`; append the examples below; ensure the file ends with a trailing newline)

**Interfaces:**
- Consumes vocabulary + shapes from Tasks 1–3. Produces fixtures exercised by CQs
  (Task 7) and referenced in the coverage map.

- [ ] **Step 1: Remove** the old `almalinux/9/openssl … track-exact … #v` example block.

- [ ] **Step 2: Append the flagship + cross-distro + coverage examples.** Use
  URI-POLICY IRIs (`d/src/{distro}/{release}/{name}/{version}`,
  `d/ver/{distro}/{release}/{name}/{version}`). Full block:

```turtle
# --- Rebuild tracking: shared upstream (RHEL) builds + snapshot ---
<https://packagegraph.github.io/d/snap/rhel/9/2026-08-30> a pkg:DataSnapshot ;
    pkg:snapshotTimestamp "2026-08-30T00:00:00Z"^^xsd:dateTime ;
    pkg:snapshotSource "pg-collect rhel-9" .

<https://packagegraph.github.io/d/src/rhel/9/openssl/3.5.5-6.el9_8> a pkg:SourcePackage ;
    pkg:packageName "openssl" ;
    pkg:hasVersion <https://packagegraph.github.io/d/ver/rhel/9/openssl/3.5.5-6.el9_8> ;
    rdfs:label "openssl (RHEL 9 source, build -6)" .
<https://packagegraph.github.io/d/ver/rhel/9/openssl/3.5.5-6.el9_8> a pkg:Version ;
    pkg:versionString "3.5.5-6.el9_8" .

<https://packagegraph.github.io/d/src/rhel/9/openssl/3.5.5-7.el9_8> a pkg:SourcePackage ;
    pkg:packageName "openssl" ;
    pkg:hasVersion <https://packagegraph.github.io/d/ver/rhel/9/openssl/3.5.5-7.el9_8> ;
    rdfs:label "openssl (RHEL 9 source, build -7, newest)" .
<https://packagegraph.github.io/d/ver/rhel/9/openssl/3.5.5-7.el9_8> a pkg:Version ;
    pkg:versionString "3.5.5-7.el9_8" .

# FLAGSHIP: AlmaLinux openssl is vendor-patched vs the -6 SRPM it rebuilt,
# yet behind RHEL's newer -7 build (patched but lagging a security update).
<https://packagegraph.github.io/d/src/almalinux/9/openssl/3.5.5-6.el9_8.alma.1> a pkg:SourcePackage ;
    pkg:packageName "openssl" ;
    pkg:hasVersion <https://packagegraph.github.io/d/ver/almalinux/9/openssl/3.5.5-6.el9_8.alma.1> ;
    pkg:hasRebuildAssessment <https://packagegraph.github.io/d/rba/almalinux/9/openssl/2026-08-31> ;
    rdfs:label "openssl (AlmaLinux 9 source)" .
<https://packagegraph.github.io/d/ver/almalinux/9/openssl/3.5.5-6.el9_8.alma.1> a pkg:Version ;
    pkg:versionString "3.5.5-6.el9_8.alma.1" .
<https://packagegraph.github.io/d/rba/almalinux/9/openssl/2026-08-31> a pkg:RebuildAssessment ;
    pkg:assessmentOf <https://packagegraph.github.io/d/src/almalinux/9/openssl/3.5.5-6.el9_8.alma.1> ;
    pkg:hasUpstreamCounterpart true ;
    pkg:rebuildFidelity pkg:fidelity-vendor-patched ;
    pkg:fidelityBaseline <https://packagegraph.github.io/d/src/rhel/9/openssl/3.5.5-6.el9_8> ;
    pkg:rebuildDrift pkg:drift-behind ;
    pkg:comparedAgainst <https://packagegraph.github.io/d/src/rhel/9/openssl/3.5.5-7.el9_8> ;
    pkg:assessedAt "2026-08-31T12:00:00Z"^^xsd:dateTime ;
    pkg:assessmentMethod "rebuild-norm/v1" ;
    pkg:assessmentConfidence "0.95"^^xsd:decimal ;
    pkg:assessedAgainstSnapshot <https://packagegraph.github.io/d/snap/rhel/9/2026-08-30> ;
    pkg:lineageConfirmed false .

# CROSS-DISTRO: Rocky openssl is an exact rebuild of the same -6 RHEL build,
# and even with newest at the time of its snapshot; lineage confirmed by digest.
<https://packagegraph.github.io/d/src/rocky/9/openssl/3.5.5-6.el9_8> a pkg:SourcePackage ;
    pkg:packageName "openssl" ;
    pkg:hasVersion <https://packagegraph.github.io/d/ver/rocky/9/openssl/3.5.5-6.el9_8> ;
    pkg:hasRebuildAssessment <https://packagegraph.github.io/d/rba/rocky/9/openssl/2026-08-31> ;
    pkg:rebuildOf <https://packagegraph.github.io/d/src/rhel/9/openssl/3.5.5-6.el9_8> ;
    rdfs:label "openssl (Rocky 9 source)" .
<https://packagegraph.github.io/d/ver/rocky/9/openssl/3.5.5-6.el9_8> a pkg:Version ;
    pkg:versionString "3.5.5-6.el9_8" .
<https://packagegraph.github.io/d/rba/rocky/9/openssl/2026-08-31> a pkg:RebuildAssessment ;
    pkg:assessmentOf <https://packagegraph.github.io/d/src/rocky/9/openssl/3.5.5-6.el9_8> ;
    pkg:hasUpstreamCounterpart true ;
    pkg:rebuildFidelity pkg:fidelity-exact ;
    pkg:fidelityBaseline <https://packagegraph.github.io/d/src/rhel/9/openssl/3.5.5-6.el9_8> ;
    pkg:rebuildDrift pkg:drift-even ;
    pkg:comparedAgainst <https://packagegraph.github.io/d/src/rhel/9/openssl/3.5.5-6.el9_8> ;
    pkg:assessedAt "2026-08-31T12:00:00Z"^^xsd:dateTime ;
    pkg:assessmentMethod "rebuild-norm/v1" ;
    pkg:assessmentConfidence "1.0"^^xsd:decimal ;
    pkg:assessedAgainstSnapshot <https://packagegraph.github.io/d/snap/rhel/9/2026-08-30> ;
    pkg:lineageConfirmed true ;
    pkg:lineageEvidence "srpm-sha256-match" .

# EXCLUSIVE: distro-only branding package, absent upstream.
<https://packagegraph.github.io/d/src/almalinux/9/almalinux-release/9.4-1.el9> a pkg:SourcePackage ;
    pkg:packageName "almalinux-release" ;
    pkg:hasRebuildAssessment <https://packagegraph.github.io/d/rba/almalinux/9/almalinux-release/2026-08-31> ;
    rdfs:label "almalinux-release (AlmaLinux 9 source)" .
<https://packagegraph.github.io/d/rba/almalinux/9/almalinux-release/2026-08-31> a pkg:RebuildAssessment ;
    pkg:assessmentOf <https://packagegraph.github.io/d/src/almalinux/9/almalinux-release/9.4-1.el9> ;
    pkg:hasUpstreamCounterpart false ;
    pkg:assessedAt "2026-08-31T12:00:00Z"^^xsd:dateTime ;
    pkg:assessmentMethod "rebuild-norm/v1" ;
    pkg:assessedAgainstSnapshot <https://packagegraph.github.io/d/snap/rhel/9/2026-08-30> ;
    pkg:lineageConfirmed false .

# AMBIGUOUS: two upstream builds tied under normalization.
<https://packagegraph.github.io/d/src/rhel/9/examplelib/1.0-1.el9> a pkg:SourcePackage ;
    pkg:packageName "examplelib" ; rdfs:label "examplelib (RHEL 9, build A)" .
<https://packagegraph.github.io/d/src/rhel/9/examplelib/1.0-1.0.el9> a pkg:SourcePackage ;
    pkg:packageName "examplelib" ; rdfs:label "examplelib (RHEL 9, build B)" .
<https://packagegraph.github.io/d/src/almalinux/9/examplelib/1.0-1.el9.alma.1> a pkg:SourcePackage ;
    pkg:packageName "examplelib" ;
    pkg:hasRebuildAssessment <https://packagegraph.github.io/d/rba/almalinux/9/examplelib/2026-08-31> ;
    rdfs:label "examplelib (AlmaLinux 9 source)" .
<https://packagegraph.github.io/d/rba/almalinux/9/examplelib/2026-08-31> a pkg:RebuildAssessment ;
    pkg:assessmentOf <https://packagegraph.github.io/d/src/almalinux/9/examplelib/1.0-1.el9.alma.1> ;
    pkg:hasUpstreamCounterpart true ;
    pkg:rebuildFidelity pkg:fidelity-unknown ;
    pkg:rebuildDrift pkg:drift-even ;
    pkg:comparedAgainst <https://packagegraph.github.io/d/src/rhel/9/examplelib/1.0-1.el9> ;
    pkg:ambiguousCandidate <https://packagegraph.github.io/d/src/rhel/9/examplelib/1.0-1.el9> ,
        <https://packagegraph.github.io/d/src/rhel/9/examplelib/1.0-1.0.el9> ;
    pkg:assessedAt "2026-08-31T12:00:00Z"^^xsd:dateTime ;
    pkg:assessmentMethod "rebuild-norm/v1" ;
    pkg:assessmentConfidence "0.5"^^xsd:decimal ;
    pkg:assessedAgainstSnapshot <https://packagegraph.github.io/d/snap/rhel/9/2026-08-30> ;
    pkg:lineageConfirmed false .
```

- [ ] **Step 3: Validate the examples against the shapes.** Run:
  `$(PYTHON) scripts/validate_module.py core`
  Expected: `✓ core: … triples, SHACL OK`.

- [ ] **Step 4: Ensure the file ends with a newline** (fixes the missing-newline nit):
  `tail -c1 core/core.examples.ttl | od -An -c` → expected `\n`.

- [ ] **Step 5: Commit.**

```bash
git add core/core.examples.ttl
git commit -m "docs(core): rebuild assessment examples (Alma/Rocky cross-distro, exclusive, ambiguous)"
```

---

## Task 5: Negative-fixture harness

**Files:**
- Create: `scripts/validate_negative.py`, `tests/shacl-negative/expectations.json`
- Modify: `Makefile` (add `validate-negative`; make `validate` depend on it)

**Interfaces:**
- Produces `make validate-negative`, consumed by CI (via `make validate` →
  `make deploy`). The harness loads `core/core.ttl` + each fixture, runs pyshacl with
  the core SHACL graph and `inference="rdfs"`, and asserts (a) `conforms == False` and
  (b) each expected `(sourceShape, message, constraintComponent)` from
  `expectations.json` appears in the results graph.

- [ ] **Step 1: Write `scripts/validate_negative.py`:**

```python
#!/usr/bin/env python3
"""Assert that each negative fixture FAILS SHACL with the expected shape/message.

Every SPARQL-based SHACL constraint reports the same sh:sourceConstraintComponent
(sh:SPARQLConstraintComponent), so a fixture that fails for an unrelated reason could
masquerade as a pass. To prevent that, each fixture declares the exact
sh:sourceShape and sh:resultMessage it must produce; this harness checks the
validation report graph for that specific result.
"""

import json
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace
from rdflib.namespace import SH

FIX_DIR = Path("tests/shacl-negative")
CORE = Path("core/core.ttl")
CORE_SHACL = Path("core/core.shacl.ttl")
PKG = Namespace("https://purl.org/packagegraph/ontology/core#")


def run():
    expectations = json.loads((FIX_DIR / "expectations.json").read_text())
    shacl_g = Graph(); shacl_g.parse(str(CORE_SHACL), format="turtle")
    ok = True
    for fname, exp in sorted(expectations.items()):
        data_g = Graph()
        data_g.parse(str(CORE), format="turtle")
        data_g.parse(str(FIX_DIR / fname), format="turtle")
        conforms, report_g, _ = validate(
            data_g, shacl_graph=shacl_g, inference="rdfs",
            serialize_report_graph=False,
        )
        if conforms:
            print(f"  ✗ {fname}: expected violation but graph CONFORMS")
            ok = False
            continue
        messages = {str(m) for _, _, m in report_g.triples((None, SH.resultMessage, None))}
        shapes = {str(s) for _, _, s in report_g.triples((None, SH.sourceShape, None))}
        want_shape = str(PKG[exp["sourceShape"]])
        want_msg = exp["resultMessage"]
        if want_shape not in shapes:
            print(f"  ✗ {fname}: expected sourceShape {exp['sourceShape']} not in report")
            ok = False
        elif want_msg not in messages:
            print(f"  ✗ {fname}: expected message not in report: {want_msg!r}")
            ok = False
        else:
            print(f"  ✓ {fname}: fails as expected ({exp['sourceShape']})")
    if not ok:
        sys.exit(1)
    print(f"All {len(expectations)} negative fixtures fail as expected.")


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Add the Makefile target** (near `validate-integration`, ~line 64) and
  wire it into `validate`:

```make
validate: validate-all validate-integration validate-negative

.PHONY: validate-negative
validate-negative:
	@echo "Negative SHACL fixtures (must fail)..."
	@$(PYTHON) scripts/validate_negative.py
```

- [ ] **Step 3: Create an empty expectations file** to start:
  `tests/shacl-negative/expectations.json` containing `{}`.

- [ ] **Step 4: Verify the harness runs** (no fixtures yet):
  `make validate-negative`
  Expected: "All 0 negative fixtures fail as expected."

- [ ] **Step 5: Commit.**

```bash
git add scripts/validate_negative.py tests/shacl-negative/expectations.json Makefile
git commit -m "test(core): negative-fixture harness wired into make validate"
```

---

## Task 6: Negative fixtures (one per constraint)

**Files:**
- Create: `tests/shacl-negative/<name>.ttl` (one per row below)
- Modify: `tests/shacl-negative/expectations.json`

**Interfaces:** Consumes shapes from Task 3 and the harness from Task 5.

Each fixture is a minimal RebuildAssessment that is valid Turtle but violates exactly
one rule. Give each a `@prefix pkg:` / `@prefix xsd:` header, an `assessmentOf` a
`pkg:SourcePackage`, and only the fields needed to trigger the target rule (add the
always-required fields so unrelated required-field rules don't also fire, EXCEPT for
the required-field fixtures themselves). Populate `expectations.json` with, per file,
`{"sourceShape": "<ShapeName>", "resultMessage": "<exact sh:message>",
"sourceConstraintComponent": "SPARQLConstraintComponent|InConstraintComponent|..."}`.

- [ ] **Step 1: Create the fixtures.**

| File | Triggers | sourceShape | Expected message (verbatim) |
|------|----------|-------------|------------------------------|
| `missing-snapshot.ttl` | assessment w/o `assessedAgainstSnapshot` | `RebuildAssessmentShape` | "A RebuildAssessment must reference exactly one assessedAgainstSnapshot." |
| `two-fidelity.ttl` | two `rebuildFidelity` values | `RebuildAssessmentShape` | "rebuildFidelity must be a concept from RebuildFidelityScheme." |
| `bad-confidence.ttl` | `assessmentConfidence 1.5` | `RebuildAssessmentShape` | "assessmentConfidence must be between 0.0 and 1.0." |
| `lineage-confirmed-twice.ttl` | `lineageConfirmed true, false` | `RebuildAssessmentShape` | "A RebuildAssessment must have exactly one lineageConfirmed boolean." |
| `drift-without-baseline.ttl` | `rebuildDrift` w/o `comparedAgainst` | `RebuildAssessmentResultsShape` | "rebuildDrift present requires a comparedAgainst baseline." |
| `matched-without-baseline.ttl` | `fidelity-exact` w/o `fidelityBaseline` | `RebuildAssessmentResultsShape` | "A matched fidelity (exact/vendor-patched/modular-equivalent) requires a fidelityBaseline." |
| `unknown-with-baseline.ttl` | `fidelity-unknown` + `fidelityBaseline` | `RebuildAssessmentResultsShape` | "fidelity-unknown forbids a fidelityBaseline." |
| `counterpart-false-with-fidelity.ttl` | `hasUpstreamCounterpart false` + fidelity | `RebuildAssessmentResultsShape` | "hasUpstreamCounterpart=false forbids fidelity, drift, baselines, and ambiguous candidates." |
| `counterpart-true-missing-results.ttl` | `hasUpstreamCounterpart true`, no fidelity/drift | `RebuildAssessmentResultsShape` | "hasUpstreamCounterpart=true requires exactly one rebuildFidelity and one rebuildDrift." |
| `self-baseline.ttl` | `fidelityBaseline` = `assessmentOf` | `RebuildAssessmentSelfBaselineShape` | "A package must not be its own fidelity or drift baseline." |
| `one-ambiguous.ttl` | single `ambiguousCandidate` | `RebuildAssessmentAmbiguityShape` | "ambiguousCandidate requires at least two distinct candidates." |
| `ambiguous-not-unknown.ttl` | `ambiguousCandidate` + `fidelity-exact` | `RebuildAssessmentAmbiguityShape` | "ambiguousCandidate requires rebuildFidelity = fidelity-unknown." |
| `ambiguous-bad-confidence.ttl` | ambiguous + confidence ≠ 0.5 | `RebuildAssessmentAmbiguityShape` | "An ambiguous assessment must have assessmentConfidence 0.5 and lineageConfirmed=false." |
| `confirmed-unknown.ttl` | `lineageConfirmed true` + `fidelity-unknown` | `RebuildAssessmentPromotionShape` | "lineageConfirmed=true requires a matched fidelity, a fidelityBaseline, and non-empty lineageEvidence." |
| `confirmed-no-evidence.ttl` | `lineageConfirmed true` + no `lineageEvidence` | `RebuildAssessmentPromotionShape` | "lineageConfirmed=true requires a matched fidelity, a fidelityBaseline, and non-empty lineageEvidence." |
| `unconfirmed-with-evidence.ttl` | `lineageConfirmed false` + `lineageEvidence "x"` | `RebuildAssessmentPromotionShape` | "lineageConfirmed=false forbids lineageEvidence." |
| `lineage-wrong-target.ttl` | `pkg SourcePackage` with `rebuildOf ?t` but the only confirmed assessment names a different baseline | `RebuildLineageGuardShape` | "rebuildOf requires an assessment of the same package with the same fidelityBaseline and lineageConfirmed=true." |
| `lineage-unconfirmed.ttl` | `rebuildOf ?t` with a matching assessment but `lineageConfirmed false` | `RebuildLineageGuardShape` | "rebuildOf requires an assessment of the same package with the same fidelityBaseline and lineageConfirmed=true." |

  Example — `tests/shacl-negative/drift-without-baseline.ttl`:

```turtle
@prefix pkg: <https://purl.org/packagegraph/ontology/core#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

pkg:_negSrc a pkg:SourcePackage ; pkg:packageName "x" .
pkg:_negSnap a pkg:DataSnapshot .
pkg:_neg a pkg:RebuildAssessment ;
    pkg:assessmentOf pkg:_negSrc ;
    pkg:hasUpstreamCounterpart true ;
    pkg:rebuildFidelity pkg:fidelity-exact ;
    pkg:fidelityBaseline pkg:_negSrc2 ;
    pkg:rebuildDrift pkg:drift-behind ;
    pkg:assessedAt "2026-08-31T00:00:00Z"^^xsd:dateTime ;
    pkg:assessmentMethod "rebuild-norm/v1" ;
    pkg:assessedAgainstSnapshot pkg:_negSnap ;
    pkg:lineageConfirmed false .
pkg:_negSrc2 a pkg:SourcePackage ; pkg:packageName "x" .
```

  (Write the other 17 analogously — minimal, one rule each. For guard fixtures put
  `rebuildOf` on the `SourcePackage`.)

- [ ] **Step 2: Populate `expectations.json`** with one entry per fixture using the
  table's sourceShape + verbatim message.

- [ ] **Step 3: Run the harness.** Run: `make validate-negative`
  Expected: "All 18 negative fixtures fail as expected."

- [ ] **Step 4: Confirm positives still pass** (fixtures must not pollute module
  validation — `tests/` is not a module dir): `make validate`
  Expected: all modules SHACL OK, integration OK, negatives OK.

- [ ] **Step 5: Commit.**

```bash
git add tests/shacl-negative/
git commit -m "test(core): negative fixtures for every RebuildAssessment constraint"
```

---

## Task 7: Competency questions

**Files:**
- Modify: `docs/competency-questions.md` (new `## Domain: Rebuild Tracking (RB)` after
  the ERA domain ~line 2272; update Summary Statistics, Classes/Properties Exercised,
  CQ Coverage Map)

**Interfaces:** Consumes the examples from Task 4 (queries must return rows against
them). Follows the exact CQ format used by e.g. CQ-ERA-01 (heading, prose question,
fenced SPARQL, expected-result schema).

- [ ] **Step 1: Add CQ-RB-01..09** per §9 of the spec. Each as
  `### CQ-RB-0N: <title>` + question + SPARQL + expected schema. Full SPARQL for the
  killer query, CQ-RB-03 (the others follow the same shape against the Task-4 data):

```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
SELECT ?pkg ?distro ?baseline ?newest WHERE {
  ?a pkg:assessmentOf ?pkg ;
     pkg:rebuildFidelity pkg:fidelity-vendor-patched ;
     pkg:rebuildDrift pkg:drift-behind ;
     pkg:fidelityBaseline ?baseline ;
     pkg:comparedAgainst ?newest .
  ?pkg pkg:packageName ?name .
  BIND( REPLACE( STR(?pkg), "^.*/d/src/([^/]+)/.*$", "$1" ) AS ?distro )
}
```

  Expected result against Task-4 data: one row — the AlmaLinux `openssl` assessment
  (baseline `…-6.el9_8`, newest `…-7.el9_8`).

- [ ] **Step 2: Update counts.** In Summary Statistics and the README (Task 9), set the
  CQ total to the true prior total (68) + 9 = 77. Add at least CQ-RB-02, -03, -05, -07
  to the "Validation Against Examples" list. Add `RebuildAssessment` to Classes
  Exercised and the new properties to Properties Exercised.

- [ ] **Step 3: Structural check** — confirm each new SPARQL parses:

```bash
uv run python - <<'PY'
import re, pathlib, rdflib
text = pathlib.Path("docs/competency-questions.md").read_text()
blocks = re.findall(r"```sparql\n(.*?)```", text, re.S)
rb = [b for b in blocks if "RebuildAssessment" in b or "rebuildFidelity" in b or "assessmentOf" in b]
for i, q in enumerate(rb):
    rdflib.Graph().query(q)  # raises on parse error
print(f"OK: {len(rb)} rebuild CQs parse")
PY
```
  Expected: "OK: 9 rebuild CQs parse" (or the count you added).

- [ ] **Step 4: Commit.**

```bash
git add docs/competency-questions.md
git commit -m "docs: add CQ-RB-01..09 rebuild tracking competency questions"
```

---

## Task 8: Design decision record

**Files:**
- Modify: `docs/design-decisions.md` (add `### DD-RB` alongside DD-REL/DD-EPSS)

**Interfaces:** none (documentation).

- [ ] **Step 1: Write `### DD-RB: Reified Rebuild Assessment with Presence / Fidelity /
  Drift Axes`** covering, per spec §12: why reified (temporal + heuristic +
  multi-valued, citing DD-REL/DD-EPSS); the three axes/baselines; the canonical
  `assessmentOf` direction and why validation must not rely on `owl:inverseOf` under
  RDFS; the versioned `rebuild-norm/v1` algorithm (candidate scope, epoch=0, exact =
  canonical EVR, vendor/module normalization, ambiguity → `ambiguousCandidate` +
  confidence 0.5); the candidate-vs-committed lineage split, the `rebuildOf` promotion
  policy, and `lineageConfirmed`/`lineageEvidence`; the RebuildDrift-vs-FreshnessStatus
  distinction; and the asymmetric+irreflexive choice for `rebuildOf`.

- [ ] **Step 2: Verify the anchor renders** (matches sibling heading depth `###`):
  `grep -n "### DD-RB" docs/design-decisions.md` → one hit.

- [ ] **Step 3: Commit.**

```bash
git add docs/design-decisions.md
git commit -m "docs: DD-RB design decision for reified rebuild assessment"
```

---

## Task 9: Release hygiene + final verification

**Files:**
- Modify: `core/core.ttl` (`dcterms:modified`), `CHANGELOG.md`, `README.md`

**Interfaces:** none.

- [ ] **Step 1: Bump the modified date.** In `core/core.ttl` change
  `dcterms:modified "2026-08-22"^^xsd:date` → `"2026-09-01"^^xsd:date`. Leave all
  other modules' dates unchanged (their content did not change).

- [ ] **Step 2: Rewrite the CHANGELOG entry** to Keep-a-Changelog style, replacing the
  `## v0.13.0` block:

```markdown
## [0.13.0] - 2026-09-01

Reified rebuild-tracking vocabulary (presence / fidelity / drift) for downstream
RHEL rebuilds.

### Added
- `pkg:RebuildAssessment` reified class + `hasRebuildAssessment` / `assessmentOf`.
- Axes: `rebuildFidelity` (`RebuildFidelityScheme`: exact, vendor-patched,
  modular-equivalent, unknown) and `rebuildDrift` (`RebuildDriftScheme`: even, ahead,
  behind, version-equivalent).
- Baselines `fidelityBaseline`, `comparedAgainst`; presence `hasUpstreamCounterpart`.
- Provenance `assessedAt`, `assessmentMethod`, `assessmentConfidence`,
  `assessedAgainstSnapshot`; evidence-gated lineage `rebuildOf`
  (asymmetric + irreflexive), `lineageConfirmed`, `lineageEvidence`;
  `ambiguousCandidate`.
- `pkg:RebuildAssessmentShape` + SPARQL guards (coupling, ambiguity, self-baseline,
  promotion, lineage) and a negative-fixture harness (`make validate-negative`).
- 9 competency questions (CQ-RB-01..09) and DD-RB.

### Changed
- Replaced the flat `rebuildTrackingStatus` / `RebuildTrackingScheme` (never released)
  with the reified model above.
```

- [ ] **Step 3: Update the README** "What's New in v0.13.0" to describe the reified
  model, and correct the competency-question count (`53` → `77`).

- [ ] **Step 4: Full verification suite.** Run each and confirm green:

```bash
make lint
make validate            # validate-all + integration + negative
make check-version
uv run python scripts/test-owl2-reasoning.py
```
  Expected: all pass; `check-version` reports all modules consistent at v0.13.0.

- [ ] **Step 5: Commit.**

```bash
git add core/core.ttl CHANGELOG.md README.md
git commit -m "chore: release hygiene for v0.13.0 (modified date, changelog, README)"
```

---

## Self-Review notes (author)

- **Spec coverage:** every spec section maps to a task — §4 vocab → T1/T2; §5 algorithm
  → DD-RB (T8) + method string; §6 SHACL → T3; §7 negatives → T5/T6; §8 examples → T4;
  §9 CQs → T7; §11 hygiene → T9; §12 DD → T8. Finding #1–10 and the two rev-5 notes are
  all realized in T2/T3/T6.
- **Placeholders:** none — all TTL/SPARQL/Python is literal. The only "write the other
  17 analogously" is backed by an exact per-fixture table (file, trigger, shape,
  verbatim message) so each is fully specified.
- **Type consistency:** property/shape/concept names are identical across T1–T9
  (`assessmentOf`, `fidelityBaseline`, `rebuildFidelity`, `pkg:fidelity-*`,
  `pkg:drift-*`, shape names in T3 = expectations in T6).
