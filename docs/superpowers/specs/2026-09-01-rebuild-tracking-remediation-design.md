# Rebuild Tracking Vocabulary — Remediation Design (v0.13.0)

**Date:** 2026-09-01
**Branch:** `feat/rebuild-tracking-vocabulary`
**Status:** Draft for review (rev 2 — incorporates maintainer spec review)
**Supersedes:** the direct-triple `rebuildTrackingStatus` model added in commit `19b0028`

## 1. Motivation

A three-reviewer audit plus the maintainer's own review found the v0.13.0 rebuild
tracking vocabulary formally valid (all `make` checks pass) but short of the
project's own rigor bar in concrete ways:

- **B1 (factual):** `track-exact` claims the NVR is "byte-identical" and
  `track-vendor-patched` claims a "provable rebuild". NVR equality is *string*
  identity; suffix-strip matching is strong evidence, not proof.
- **B2 (methodology):** no competency question was added, though the repo treats
  CQs as "the specification" and every prior feature shipped them.
- **B3 (expressiveness):** `sh:maxCount 1` on a single status property cannot
  express a package that is **vendor-patched *and* behind** upstream — the
  highest-value supply-chain signal. The two facts have *different baselines*.
- **B4 (hygiene):** `core.ttl` `dcterms:modified` still reads `2026-08-22`.
- **I1 (temporal):** `ahead`/`behind` are snapshot-relative but stored as timeless
  triples.
- **I2 (constraint):** the lineage-vs-comparison split is prose-only; nothing stops
  a `behind` package from also asserting `rebuildOf` (a false provenance claim).
- **I3 (documentation):** no `design-decisions.md` entry.
- **I4 (provenance):** a heuristic classification ships as a bare triple with no
  method, version, or confidence — unlike `PackageRelationship` (DD-REL) and EPSS
  (DD-EPSS), which the project reified for exactly this reason.

The project has faced the "computed, uncertain, time-sensitive attribute" problem
twice and reified both times (DD-REL, DD-EPSS). This design applies that precedent.

## 2. Finalized decisions (maintainer-confirmed — not open)

1. `pkg:rebuildOf` is **`owl:AsymmetricProperty` and `owl:IrreflexiveProperty`.**
2. Vocabulary stays in **`core/`** with **genericized labels** (RHEL is the running
   example, not hardcoded into labels/definitions).
3. Confidence uses a **dedicated `pkg:assessmentConfidence`** (the released
   `matchConfidence` is left untouched).
4. A **negative-fixture harness** is added **and wired into the standard validation
   gate** (`make validate` / CI depend on it).

## 3. Core design idea: three baselines, cleanly separated

Three distinct questions were conflated in the original seven statuses. This design
gives each its own property, and — critically — puts every **baseline on the
assessment** so results are self-describing and joinable:

| Question | Axis property | Baseline (on the assessment) |
|----------|---------------|------------------------------|
| Does an upstream counterpart exist at all? | `pkg:hasUpstreamCounterpart` (boolean) | the searched `DataSnapshot` |
| What specific upstream build was this rebuilt from, how faithfully? | `pkg:rebuildFidelity` | `pkg:fidelityBaseline` |
| Where does it sit vs upstream's current newest? | `pkg:rebuildDrift` | `pkg:comparedAgainst` |

Separating fidelity from drift is what makes "vendor-patched **and** behind"
expressible: `rebuildFidelity = vendor-patched` (vs the SRPM it rebuilt,
`fidelityBaseline`) while `rebuildDrift = behind` (vs RHEL's newest,
`comparedAgainst`). These are two different upstream builds, so both must be
recorded on the assessment.

## 4. Model

### 4.1 Reified class `pkg:RebuildAssessment`

Mirrors `pkg:PackageRelationship`. A single classification *observation*, produced
at a point in time by a specific, versioned method.

**Canonical link direction (fixes finding #3):** the assessment points to its
package via `pkg:assessmentOf` (self-contained record). Because the project
validates with **RDFS inference only** — which does not materialize
`owl:inverseOf` — **all SHACL, CQs, and the lineage guard use `assessmentOf`, the
asserted direction.** `pkg:hasRebuildAssessment` remains as an OPTIONAL
`owl:inverseOf` convenience property for authoring/query, but nothing in validation
depends on inverse inference.

```
:RebuildAssessment --pkg:assessmentOf--> :SourcePackage   (asserted, canonical; exactly 1)
:SourcePackage --pkg:hasRebuildAssessment--> :RebuildAssessment  (optional convenience; owl:inverseOf)
```

Many assessments accumulate per package over time (fixes I1 — each is timestamped
and snapshot-scoped). `RebuildAssessment` is **not** in
`AllDisjointClasses(BinaryPackage, SourcePackage)`; it is a qualifier entity like
`PackageRelationship`.

### 4.2 Upstream-presence axis (fixes finding #5)

Source-name absence is **not a fidelity grade** — it says no fidelity baseline
exists. It is modelled separately:

- `pkg:hasUpstreamCounterpart` — `xsd:boolean`, on `RebuildAssessment`. `false`
  means the source name is absent from the searched upstream dataset (branding /
  distro-exclusive extras, e.g. `almalinux-release`). Modelled as a boolean per the
  `DD-SignatureStatusStrings` precedent ("string enums / small fixed value sets").
- When `false`: `rebuildFidelity`, `rebuildDrift`, `fidelityBaseline`, and
  `comparedAgainst` are **omitted**, but `pkg:assessedAgainstSnapshot` is
  **required** (absence is a closed-world conclusion — see finding #4 / §4.5).

### 4.3 Fidelity axis (on the assessment)

- `pkg:rebuildFidelity` → `skos:Concept` from `pkg:RebuildFidelityScheme`,
  `maxCount 1`. Baseline = `pkg:fidelityBaseline`.
  - `pkg:fidelity-exact` — **canonical EVR equality** with the `fidelityBaseline`
    build (the candidate set already fixes the name; absent epoch ⇒ `0:`).
  - `pkg:fidelity-vendor-patched` — NVR equal after stripping an anchored vendor
    suffix recognised by the method ruleset; strong evidence, not cryptographic
    proof.
  - `pkg:fidelity-modular-equivalent` — modular package whose base NVR (before the
    module build-context marker) matches, within the same module stream; only the
    module build-context differs. (RHEL-8-era AppStream modularity.)
  - `pkg:fidelity-unknown` — an upstream counterpart exists
    (`hasUpstreamCounterpart = true`) but no NVR match under normalization; fidelity
    cannot be established (drift may still be recorded).
- `pkg:fidelityBaseline` — domain `RebuildAssessment`, range `SourcePackage`. The
  specific upstream build the fidelity result was measured against. **A comparison
  baseline, NOT `prov:wasDerivedFrom`** (finding #1/#2). Required whenever
  `rebuildFidelity ∈ {exact, vendor-patched, modular-equivalent}`.
- `pkg:ambiguousCandidate` — domain `RebuildAssessment`, range `SourcePackage`. The
  tied upstream builds when normalization matched more than one (see §5.1); present
  only with `rebuildFidelity = fidelity-unknown`.

### 4.4 Drift axis (on the assessment)

- `pkg:rebuildDrift` → `skos:Concept` from `pkg:RebuildDriftScheme`, `maxCount 1`.
  Baseline = `pkg:comparedAgainst`.
  - `pkg:drift-even` — **canonical EVR strings are equal** to the `comparedAgainst`
    build.
  - `pkg:drift-ahead` — `rpmvercmp` ranks the rebuild higher than upstream newest.
  - `pkg:drift-behind` — `rpmvercmp` ranks the rebuild lower than upstream newest
    (investigate).
  - `pkg:drift-version-equivalent` — canonical EVR strings **differ** but `rpmvercmp`
    returns equality (e.g. ignored separators / leading zeros). Disjoint from
    `drift-even` by construction. A comparison result, not a lineage claim.
- `pkg:comparedAgainst` — **domain changes from `SourcePackage` to
  `RebuildAssessment`.** The upstream newest build used as the drift baseline.
  Explicitly **not** `prov:wasDerivedFrom`. Required whenever `rebuildDrift` present.

### 4.5 Assessment provenance (fixes I1, I4, finding #4)

| Property | Range | Required | Notes |
|----------|-------|----------|-------|
| `pkg:assessedAt` | `xsd:dateTime` | exactly 1 | when computed (I1) |
| `pkg:assessmentMethod` | `xsd:string` | exactly 1 | **versioned** method id, e.g. `"rebuild-norm/v1"` (styled after `snapshotSource`); the id pins the exact ruleset in DD-RB |
| `pkg:assessmentConfidence` | `xsd:decimal` | 0–1, ≤1 | styled after `matchConfidence` |
| `pkg:assessedAgainstSnapshot` | `pkg:DataSnapshot` | exactly 1 | the upstream dataset every candidate/presence/newest determination was drawn from (finding #4) |

`assessedAgainstSnapshot` is **required on every `RebuildAssessment` (exactly one)**
(fixes finding #2). §5 selects *all* candidates — for presence, fidelity, and drift
— from this snapshot, so a fidelity-only or presence-only assessment must still
identify the dataset its candidate came from. (No non-snapshot assessment method is
introduced; if one ever is, this cardinality is revisited.)

### 4.6 Committed lineage: `pkg:rebuildOf` (fixes finding #2, #7)

- `pkg:rebuildOf` — `SourcePackage → SourcePackage`,
  `rdfs:subPropertyOf prov:wasDerivedFrom`, `owl:AsymmetricProperty`,
  `owl:IrreflexiveProperty`. The **committed** derivation claim.
- It is **not** auto-created by the normalization algorithm. The algorithm records a
  *candidate* baseline on the assessment (`fidelityBaseline` + fidelity + method +
  confidence). `rebuildOf` is **promoted** from a candidate only when an explicit,
  documented policy is satisfied by **independent provenance evidence** (see §5.3) —
  e.g. matching source-artifact digest, vendor-published build provenance, or
  operator confirmation. Adding confidence to an assessment does **not** by itself
  license an unqualified `prov` triple.

**Promotion evidence, on the assessment (fixes finding #1):** a fidelity result is
not enough to license `rebuildOf`. The assessment carries:

- `pkg:lineageConfirmed` — `xsd:boolean`. `true` iff the §5.3 promotion policy was
  satisfied for this assessment's `fidelityBaseline`.
- `pkg:lineageEvidence` — `xsd:string`. What independent evidence satisfied the
  policy (e.g. `"srpm-sha256-match"`, `"vendor-build-provenance"`, `"operator:jdoe"`).

The lineage guard (§6) requires `lineageConfirmed = true` (not merely a qualifying
fidelity tier), so a normalized-only vendor/modular match — insufficient under §5.3 —
**cannot** pass SHACL as committed lineage.

### 4.7 Property characteristics (M5, finding #8)

`pkg:rebuildOf`: `owl:IrreflexiveProperty` **and** `owl:AsymmetricProperty`
(maintainer-confirmed; same class on both ends, so both are meaningful). Asymmetry
forbids only mutual `rebuildOf`; chains A→B→C remain legal.

**Baselines are NOT declared irreflexive (fixes finding #4).** `fidelityBaseline`
and `comparedAgainst` have domain `RebuildAssessment` and range `SourcePackage` —
disjoint node kinds — so `owl:IrreflexiveProperty` would be vacuous (it only forbids
an assessment targeting *itself*, which range typing already precludes). The real
constraint — *the assessed package must not be its own baseline* — is enforced in
SHACL by comparing `assessmentOf` against `fidelityBaseline` / `comparedAgainst`
(§6).

> The unreleased `pkg:track-*` concepts from commit `19b0028` are renamed to
> `fidelity-*` / `drift-*`. 0.13.0 is unmerged, so no `owl:deprecated` is needed.

## 5. Normative, executable decision procedure (fixes I2/I3, findings #3)

DD-RB carries the algorithm as **executable-style rules under a versioned method id
(`rebuild-norm/v1`)**, with boundary fixtures. Fidelity, drift, and presence are
computed independently. The prose below is the specification the DD entry pins
precisely.

### 5.1 Candidate scope and version comparison (finding #3)

- **Candidate set:** upstream builds with the same source `packageName`, within the
  release (and, for modular packages, the same `module:stream`) recorded in the
  referenced `assessedAgainstSnapshot`.
- **Version comparison:** epoch-aware `rpmvercmp` over full EVR. **Missing epoch is
  treated as `0`** (RPM semantics) for every comparison, including exact match.
- **Exact match:** the candidate set already fixes the name `N`, so the exact test is
  **canonical EVR equality** — string equality of `E:V-R` after epoch normalization
  (absent epoch ⇒ `0:`). (Minor terminology fix: this is EVR, not NVR.)
- **Multiple candidate matches → explicit ambiguity representation (fixes finding
  #6):** if more than one upstream build matches at the chosen fidelity tier:
  - `rebuildFidelity` = `fidelity-unknown`; no `fidelityBaseline` is set;
    `lineageConfirmed = false` (never promote from an ambiguous match);
  - each tied upstream build is linked via `pkg:ambiguousCandidate` (domain
    `RebuildAssessment`, range `SourcePackage`, `minCount 2` when present);
  - `assessmentConfidence` is set to the **deterministic** value defined by the
    method id — `rebuild-norm/v1` fixes it at `0.5` for any ambiguous outcome (a
    constant, not a vague "reduced"). DD-RB records the rule and its rationale.

### 5.2 Presence, fidelity, drift

- **Presence:** if no candidate shares the source name in the snapshot →
  `hasUpstreamCounterpart = false`, set `assessedAgainstSnapshot`, stop. Else
  `hasUpstreamCounterpart = true`.
- **Fidelity (ordered; first match wins), sets `fidelityBaseline` to the matched
  build:**
  1. Canonical EVR equality → `fidelity-exact`.
  2. Else strip the anchored vendor suffix enumerated by `rebuild-norm/v1` (canonical
     example: AlmaLinux `\.alma\.\d+$`; the ruleset enumerates the exact recognised
     set and is the authority — no distro suffix is hardcoded in the ontology) and
     re-match → `fidelity-vendor-patched`.
  3. Else strip the module build-context marker (`\.module[+_]el\d+.*$`) and match the
     base NVR within the same `module:stream` → `fidelity-modular-equivalent`.
  4. Else → `fidelity-unknown`.
- **Drift (independent; whenever `hasUpstreamCounterpart = true`):** compare the
  rebuild against the upstream newest build in the snapshot. `rpmvercmp` higher →
  `drift-ahead`; lower → `drift-behind`. If `rpmvercmp` equal: canonical EVR strings
  equal → `drift-even`; canonical EVR strings differ → `drift-version-equivalent`.
  Set `comparedAgainst` = upstream newest.

### 5.3 `rebuildOf` promotion policy (finding #2)

A `fidelityBaseline` candidate is promoted to a committed `rebuildOf` triple **only**
when the policy in DD-RB is met, e.g.: (a) `fidelity-exact` **and** matching
source-artifact digest, or (b) vendor-published build provenance linking the two, or
(c) explicit operator confirmation. Normalized-only matches
(`vendor-patched` / `modular-equivalent`) remain candidates on the assessment and are
**not** auto-promoted. The policy version travels in `assessmentMethod`.

## 6. SHACL (`pkg:RebuildAssessmentShape` + guards) — fixes finding #6, #7, #9

`sh:targetClass pkg:RebuildAssessment`, with **required** fields (no empty or
methodologically-incomplete assessment can conform). All rules `sh:Violation` unless
noted.

**Always required:**
- `assessmentOf`: exactly 1 `SourcePackage`.
- `assessedAt`: `xsd:dateTime`, exactly 1.
- `assessmentMethod`: `xsd:string`, exactly 1.
- `assessedAgainstSnapshot`: `pkg:DataSnapshot`, exactly 1 (finding #2).
- `hasUpstreamCounterpart`: `xsd:boolean`, exactly 1 (drives the conditionals below).
- `lineageConfirmed`: `xsd:boolean`, **exactly 1** (fixes finding #1 — a single
  boolean value; no assessment may carry both `true` and `false`).
- `assessmentConfidence`: `xsd:decimal`, `sh:minInclusive 0.0`,
  `sh:maxInclusive 1.0`, `maxCount 1`.
- `rebuildFidelity`: `sh:in (…4 concepts…)`, `maxCount 1`. **`sh:class skos:Concept`
  dropped** (M2).
- `rebuildDrift`: `sh:in (…4 concepts…)`, `maxCount 1`.

**Conditional result rules (SPARQL-based, mirror §5.2 — fixes finding #5):**
- `hasUpstreamCounterpart = false` ⇒ **no** `rebuildFidelity`, `rebuildDrift`,
  `fidelityBaseline`, or `comparedAgainst`.
- `hasUpstreamCounterpart = true` ⇒ **exactly one** `rebuildFidelity` **and exactly
  one** `rebuildDrift` (an upstream counterpart implies a comparable newest build).
- `rebuildDrift` present ⇒ `comparedAgainst` present.
- `rebuildFidelity ∈ {exact, vendor-patched, modular-equivalent}` ⇒ exactly one
  `fidelityBaseline`.
- `rebuildFidelity = fidelity-unknown` ⇒ **no** `fidelityBaseline`.

**Self-baseline guard (SPARQL, fixes finding #4):** `assessmentOf` must not equal
`fidelityBaseline` or `comparedAgainst` (a package is not its own baseline).

**Promotion / lineage guard (targets `SourcePackage`, SPARQL — fixes findings #1,
#7):** for every `?pkg rebuildOf ?target`, there must exist `?a` with
`?a assessmentOf ?pkg`, `?a fidelityBaseline ?target` (**same target**), **and
`?a lineageConfirmed true`**. Fidelity tier alone is insufficient — only an
evidence-confirmed promotion (§4.6/§5.3) licenses the committed `prov` triple. Uses
the canonical `assessmentOf` direction (finding #3), so validation never depends on
inverse inference.

**Promotion integrity (SPARQL):** `lineageConfirmed = true` ⇒ `rebuildFidelity ∈
{exact, vendor-patched, modular-equivalent}`, `fidelityBaseline` present, and
`lineageEvidence` present and non-empty (`sh:minLength 1`). Conversely,
`lineageConfirmed = false` ⇒ **no** `lineageEvidence` (prohibit misleading residual
evidence strings on unpromoted candidates).

**Ambiguity rules (SPARQL, mirror §5.1 — fixes finding #2):**
- `ambiguousCandidate` present ⇒ `rebuildFidelity = fidelity-unknown`.
- `ambiguousCandidate` present ⇒ **at least two** distinct values (`minCount 2`).
- `ambiguousCandidate` present ⇒ `assessmentConfidence = 0.5` **and**
  `lineageConfirmed = false`.
- `hasUpstreamCounterpart = false` ⇒ **no** `ambiguousCandidate`.

## 7. Negative SHACL fixtures, wired into the gate (findings #4, #6, #7, #9)

New `tests/shacl-negative/` + `scripts/validate_negative.py`, added as a
`Makefile` target `validate-negative` **that `make validate` (and the CI workflow)
depend on** (finding #9). Each fixture asserts the **expected focus node,
`sh:sourceConstraintComponent`, and — because every SPARQL-based constraint reports
the same `sh:SPARQLConstraintComponent` — the expected `sh:sourceShape` and
`sh:resultMessage`**, not merely `conforms=False`, so no unrelated failure can make a
fixture pass. (Each SPARQL constraint therefore carries a distinct, stable
`sh:message`.) Fixtures include:

- `rebuildOf` to a target that no assessment's `fidelityBaseline` matches → lineage
  guard.
- `rebuildOf` whose matching assessment has `lineageConfirmed = false` (a
  normalized-only vendor match) → lineage guard (finding #1).
- `rebuildOf` whose only `lineageConfirmed` assessment names a *different*
  `fidelityBaseline` target → lineage guard (finding #7).
- `lineageConfirmed = true` with `rebuildFidelity = fidelity-unknown`, or with empty
  `lineageEvidence` → promotion-integrity guard.
- `lineageConfirmed` carrying both `true` and `false` (or a non-boolean) → cardinality
  / datatype violation (finding #1).
- `lineageConfirmed = false` with a `lineageEvidence` string present → promotion-integrity
  guard (residual-evidence prohibition).
- `ambiguousCandidate` with a single value → `minCount 2` (finding #2).
- `ambiguousCandidate` alongside `rebuildFidelity = fidelity-exact` → ambiguity rule.
- `ambiguousCandidate` with `assessmentConfidence ≠ 0.5` or `lineageConfirmed = true`
  → ambiguity rule.
- `ambiguousCandidate` with `hasUpstreamCounterpart = false` → ambiguity rule.
- `assessmentOf` equal to `fidelityBaseline` → self-baseline guard (finding #4).
- Two `rebuildFidelity` values on one assessment → `maxCount`.
- `hasUpstreamCounterpart = true` with no `rebuildFidelity`/`rebuildDrift` →
  conditional-result violation (finding #5).
- `hasUpstreamCounterpart = false` with a `rebuildFidelity` set → conditional-result
  violation.
- `rebuildDrift` present, `comparedAgainst` absent → coupling violation.
- Assessment missing `assessedAgainstSnapshot` → required-field violation (finding #2).
- `assessmentConfidence = 1.5` → range violation.
- Empty `RebuildAssessment` → required-field violations.

## 8. Examples (`core/core.examples.ttl`)

One conforming example per fidelity value, per drift value, and the presence case,
including:

- **Flagship:** AlmaLinux `openssl` — `rebuildFidelity = vendor-patched` +
  `rebuildDrift = behind`, `fidelityBaseline` = the `-6.el9_8` build it rebuilt,
  `comparedAgainst` = RHEL's newer `-7.el9_8`, plus `assessedAt`,
  `assessmentMethod "rebuild-norm/v1"`, `assessmentConfidence`,
  `assessedAgainstSnapshot`. Demonstrates the case the old model could not express.
  Shows `rebuildOf` **only if** the promotion policy is met (else candidate stays on
  the assessment).
- **Cross-distro pair (for CQ-RB-07 / CQ-RB-09):** a **Rocky** `openssl` assessment
  against the **same** RHEL upstream build as the Alma flagship, with a *different*
  outcome (e.g. `fidelity-exact` + `drift-even`, promoted `rebuildOf`) — so Alma vs
  Rocky can be compared and shown to diverge on the same upstream.
- `fidelity-exact` + `drift-even` (with a promoted `rebuildOf`, `lineageConfirmed =
  true`, `lineageEvidence "srpm-sha256-match"`).
- `hasUpstreamCounterpart = false` (`almalinux-release` and a `rocky-release`,
  snapshot ref, no baselines) — for CQ-RB-05.
- A `fidelity-modular-equivalent` case, a `drift-ahead` case, a
  `drift-version-equivalent` case, and an **ambiguous** case (`fidelity-unknown` +
  two `ambiguousCandidate`s + `assessmentConfidence 0.5`) — for CQ-RB-06/08.

Version node IRIs use URI-POLICY `d/ver/{distro}/{release}/{name}/{version}` (M6 —
replaces the ad-hoc `#v` fragment).

## 9. Competency questions (fixes B2)

New `## Domain: Rebuild Tracking (RB)` in `docs/competency-questions.md`, each
formalized as SPARQL with an expected-result schema in the house style. The suite
deliberately spans **RHEL (upstream) vs AlmaLinux vs Rocky**, exercises every new
axis, and includes both **positive** (matches found) and **negative** (absence /
lag / ambiguity) searches. Every query keys on the *latest* assessment per package
(`ORDER BY DESC(?assessedAt)` / `MAX`), joins via the canonical `assessmentOf`
direction, and filters `assessedAgainstSnapshot` for reproducibility.

| CQ | Question | Axis / kind |
|----|----------|-------------|
| **CQ-RB-01** | Which AlmaLinux and Rocky source packages are `drift-behind` their RHEL upstream, as of the latest assessment? | drift · negative |
| **CQ-RB-02** | For a given rebuild package's latest assessment, what is the `fidelityBaseline`, `rebuildFidelity`, `assessmentMethod`, and `assessmentConfidence`? | fidelity provenance join · positive |
| **CQ-RB-03** *(killer)* | Which packages are `vendor-patched` **yet** `drift-behind` — locally patched but lagging upstream security updates — in Alma vs Rocky? | fidelity × drift compound · negative |
| **CQ-RB-04** | Which packages carry committed `rebuildOf` lineage (`lineageConfirmed = true`) versus only an unpromoted candidate `fidelityBaseline`? | lineage promotion · positive/negative |
| **CQ-RB-05** | Which source packages are **exclusive** (`hasUpstreamCounterpart = false`) to AlmaLinux or to Rocky — absent from RHEL? | presence · negative |
| **CQ-RB-06** | Which packages have an **ambiguous** upstream match (`ambiguousCandidate`), and what are the tied builds? | ambiguity · negative |
| **CQ-RB-07** | For a package present in all three, compare Alma's and Rocky's fidelity + drift **against the same RHEL upstream** side by side. | cross-distro three-way · positive/negative |
| **CQ-RB-08** | Which packages are `drift-ahead` of RHEL (a rebuild leads the upstream snapshot)? | drift · positive edge |
| **CQ-RB-09** | Where do Alma and Rocky **disagree** on tracking the same RHEL package (different fidelity or drift in their latest assessments)? | cross-distro divergence · negative |

At least CQ-RB-02, CQ-RB-03, CQ-RB-05, and CQ-RB-07 are added to the **CQ Coverage
Map → Validation Against Examples** list so they are exercised by the new
`core.examples.ttl` fixtures (§8). Update Summary Statistics, the Classes/Properties
Exercised counts, and the README CQ count (M7 — README says "53"; correct to the true
total including these).

## 10. Freshness disambiguation

DD-RB explicitly contrasts `rebuildDrift` (pairwise vs a *specific* upstream build)
with `FreshnessStatusScheme` (cross-repo currency) so the two are not read as
redundant.

## 11. Release hygiene (B4, M4, M6, M7, finding #10)

- `core/core.ttl` `dcterms:modified` → `2026-09-01` (only the changed module moves).
- `CHANGELOG.md`: `## [0.13.0] - 2026-09-01` Keep-a-Changelog style with typed
  bullets enumerating the class, properties, three schemes/axes, SHACL shape,
  examples, negative harness, and CQs.
- README "What's New" reworded to the model; fix CQ count.
- **Finding #10 wording:** motivation and definitions state "NVR equality does not
  establish byte identity" — **not** "a rebuild is never byte-identical" (reproducible
  builds can be byte-identical). Corrected in §1 above and to be carried into the
  definitions.
- Version stays **0.13.0** (unreleased on this branch).

## 12. Design-decisions entry

New `### DD-RB: Reified Rebuild Assessment with Presence / Fidelity / Drift Axes` in
`docs/design-decisions.md` (alongside DD-REL, DD-EPSS), recording: why reified;
presence/fidelity/drift separation and their three baselines; the canonical
`assessmentOf` link direction (and why validation must not rely on `owl:inverseOf`
under RDFS inference); the versioned executable algorithm (`rebuild-norm/v1`) with
candidate scope, epoch handling, ambiguity representation (`ambiguousCandidate` +
fixed `0.5` confidence), and mandatory snapshot scoping; the candidate-vs-committed
lineage split, the `rebuildOf` promotion policy, and its `lineageConfirmed` /
`lineageEvidence` witnesses; the freshness distinction; and the asymmetric/irreflexive
choice.

## 13. Verification (item 6)

Rerun and confirm green: `make lint`, `make validate` (now depending on
`validate-negative`), `make validate-integration`, `make check-version`,
`scripts/test-owl2-reasoning.py`, plus structural validation of the new CQs.

## 14. Out of scope (deferred, documented in DD-RB)

- Elevating `freshnessStatus` to a reified assessment (same latent issue, separate
  change).
- A SKOS scheme for upstream presence (a boolean suffices today; revisit if a third
  presence state, e.g. "retired-upstream", is needed).

*(All four decisions from rev 1's "open questions" are now finalized in §2.)*
