# Bounded RPM Contract Resolution Implementation Plan

> **Status: a proposal, not an approved specification.** This plan depends on
> four amendments to [#19](https://github.com/packagegraph/ontology/issues/19)
> that have not been decided. Task 1 in particular describes ontology changes
> that nobody has agreed to; do not treat its term list, shapes or URI recipes
> as settled. Tasks 2 and 3's parser work have landed on the platform side
> because they need no new terms.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish faithful, auditable RPM declarations without representing
unresolved expressions or capability references as package dependencies.

**Architecture:** Preserve source observations as RPM-specific declaration
occurrences, reference naming-system-qualified capabilities where appropriate,
and treat capability shortcuts as explicitly lossy indexes. Keep provider
resolution and package-level necessity separate and unimplemented this release.

**Tech Stack:** Existing Rust/quick-xml collector, RDF/OWL, SHACL/pySHACL,
SPARQL/QLever, and generation/manifest publication machinery. No new solver.

**Spec:** Platform `docs/ontology-request-rpm-capability-contract.md` and
`docs/superpowers/specs/2026-09-25-rpm-capability-contract-design.md`, at
`0fa40b132f747fc3de10dd7038386f83b7b9a3ea`, **with the proposed amendments below**.
Evidence: [independent audit](../../reports/2026-09-27-rpm-contract-audit.md).

**Status:** Proposal for approval, not an instruction to deploy. Existing
ontology#19/platform#62 remain the coordination points. Platform#109 is merged;
#110 is the independently useful first slice, not the final contract.

## Global Constraints

- Preserve the four currently supported sections: Provides, Requires,
  Conflicts, Obsoletes. No dependency solver or weak-dependency interpretation.
- “A `rpm:DependencyDeclaration` is emitted for every `rpm:entry` in the four
  supported sections, with no exceptions.” Invalid input must block complete
  publication, not disappear while the run reports success.
- “The platform will not project `pkg:directlyDependsOn` on a name match.”
- “RPM package-level reverse-dependency metrics are withheld visibly.”
- G1 remains a publication gate on released vocabulary; G2 gates final
  identifiers/publication, not source acquisition. No destructive migration.
- Declarations remain outside pkg:Dependency in this bounded release; this is
  not a permanent disjointness axiom or an argument against later unification.
- Existing core domains/ranges are unchanged. All amendments below require
  ontology-team review; URI comments must not silently redefine core terms.

## Review Focus

- XML escaping, absent versus empty attributes, unknown flags/attributes, and
  `pre` must not silently alter or erase evidence (Tasks 1 and 3).
- Exact duplicates and repeated constraints must not contradict the declared
  occurrence identity; recollection must be deterministic (Tasks 1 and 3).
- Obsoletes package-name matching and RPM-process requirements must not become
  generic package-provider claims (Tasks 1, 3, and 4).
- Extraction must preserve shape targets and all fields for retained
  declarations; zero targets cannot certify a corpus (Tasks 2 and 4).
- Partial/legacy generations and stale metrics must not leak into the new
  publication, nor make missing resolution look like zero dependencies
  (Tasks 4 and 5).

## Recommended model and amendments to #19

### 1. Separate identity criteria

| Entity | What identifies it | What equality does not establish |
|---|---|---|
| Collected package | Existing versioned, distro/release/architecture-qualified package identity contract | That every token it provides names another package |
| RPM capability reference | RPM naming system plus exact XML-decoded token; `d/capability/rpm/{encoded-token}` | ABI compatibility, equal versions, a selected provider, or successful installation |
| Declaration occurrence | A supported entry at a specific location in an immutable primary.xml, interpreted for its declaring package | Equality with another occurrence having the same text |
| Future resolution result | A particular solver assessment against specified inputs and policy | A timeless boolean property of the declaration |

Use pkg:Capability as a **nominal, RPM-scoped feature abstraction**, as allowed
by its existing shared-library/virtual-name examples. Its URI is a feature key,
not a proof that all same-named implementations are interchangeable. The literal
token, the source occurrence, and the named feature are different objects.
If this interpretation is unacceptable to the ontology team, publish the
declarations without the convenience layer; do not change the core definition
through an ingestion comment.

Choose **occurrence identity**, matching #19's “one rpm:entry” definition.
Replace its seven-component content hash with:

```text
d/rpm-declaration/{sha256(UTF8(compact-JSON-array))}
array = [1, packageIRI, uncompressedPrimarySha256,
         packageOrdinal, sectionKind, entryOrdinal]
```

Ordinals are zero-based in document order; entryOrdinal counts entries of that
kind within the package, including repeated sections. `sectionKind` is one of
the four lowercase parser strings. Specify JSON serialization and UTF-8 test
vectors. Recompression alone preserves identity; changed XML bytes may change
it. Re-reading the same bytes in the same package context preserves it.
Two byte-identical entries at different positions remain different observations.
Do not claim cross-snapshot identity of declarations from these IRIs.

The cheaper alternative is a content-set model with a separate occurrence
ledger. Reject it for this release: it adds two identity mechanisms to maintain
and contradicts the current definition unless that definition is rewritten.
The observed duplicate count is small relative to all entries; nevertheless
benchmark total declaration volume before bulk rollout.

### 2. Preserve the received information, not an imagined spec string

Retain `name`, `flags`, `epoch`, `ver`, `rel`, and add
`rpm:declarationPre` (optional xsd:string, maximum one) for the raw XML-decoded
`pre` attribute. This increases the requested vocabulary from 15 to **16 terms**,
not counting existing PROV terms. Interpretation of ordering stays deferred.
Do not call pre="1" exclusively a pre-install requirement.

Decode XML entities exactly once; do not Unicode-normalize, lowercase, or trim
tokens. Preserve absent versus present-empty attributes. Keep immutable source
bytes for exact XML spelling and unmodeled metadata. The fidelity claim is
**the six represented attributes in four sections**, not all RPM header data.
Unknown attributes are retained in the source and reported as unsupported;
missing names, bad XML, or unsupported flag combinations cannot yield a graph
marked completely validated. A leading `(` identifies an opaque expression
candidate, not proof that its syntax is valid or its requirement satisfiable.

A declaration is an information record, not the package or functionality it
describes. Use `prov:wasDerivedFrom` to an immutable source entity with a digest
manifest. Reuse existing pkg:DataSnapshot for collection provenance; do not use
properties whose domains are RebuildAssessment. No new provenance ontology.

### 3. Make emission kind-specific

| Kind / syntax | declaredCapability | Convenience edge |
|---|---|---|
| Simple Provides | Required, including config/rtld | providesCapability |
| Simple Requires | Required, including observed config/rtld/rpmlib | requiresCapability, as a documented token-level projection |
| Simple Conflicts | Required | None |
| Obsoletes | Absent: retain package-name token and EVR fields | None |
| Opaque expression candidate | Absent | None; do not flatten operands |

**Amend #19's Obsoletes rule**: its plain-token requirement currently also
creates a capability reference for Obsoletes. Keep that target as the literal
package-name selector for now; no new placeholder PackageIdentity is needed.
Obsoletes matches Name/EVR, not arbitrary Provides. The four kinds therefore
share a declaration representation, not one matching relation.

Remove the config/rtld/rpmlib prefix exception from canonical reference
preservation. An observed rpmlib token can be referenced without inventing a
package provider; its native interpretation concerns the RPM process. Default
UI filters and bounded traversal may exclude classes of relationships, but
must identify their policy and omissions. Degree alone is not a correctness
criterion for the source graph.

Shortcuts are existential, unqualified projections: at least one appropriate
simple declaration mentions that feature. They erase constraints, ordering,
and occurrence multiplicity. They do not assert a compatible provider,
runtime-only dependency, selected wire, or transitive package dependency.
Require an explicit scope note for this use and **no property chain** from
shared capabilities into directlyDependsOn. Consumers needing constraints
must read declarations; consumers needing resolution must report unavailable.

### 4. Keep resolution outside this delivery

A later resolution record needs source/declaration references, repository and
installed-system snapshots, architecture/platform context, resolver/version,
policy, outcome, and selected provider evidence. An unknown/unattempted result
is not an unsatisfiable requirement. No `resolved=true` field on a shared
declaration, and no commit URI alone as a substitute for those inputs.

Keep expression ASTs, native solver integration, shared cross-ecosystem
declarations, a standalone capability ontology, weak dependencies, and implicit
file providers on the [deferred roadmap](../../reports/2026-09-25-dependency-declarations-roadmap.md).

## Delivery tasks

Paths beginning `O/` are in packagegraph/ontology; `P/` in packagegraph/platform.
Use separate, reviewable PRs for ontology, extraction, collector, and consumers.
Do not combine them with unrelated formatting or collector rewrites.

### Task 1: Settle and release the bounded ontology profile

**Files:** Modify `P/docs/ontology-request-rpm-capability-contract.md`,
`P/docs/superpowers/specs/2026-09-25-rpm-capability-contract-design.md`,
`O/ecosystems/rpm/rpm.ttl`, `O/ecosystems/rpm/rpm.shacl.ttl`,
`O/ecosystems/rpm/rpm.examples.ttl`, `O/URI-POLICY.md`,
`O/docs/design-decisions.md`, and scoped annotations in `O/core/core.ttl`.
Create `O/tests/test_rpm_declarations.py` and
`O/tests/fixtures/rpm-declarations/contract.ttl`; wire the tests into `O/Makefile`.

**Interfaces:** The #19 terms plus declarationPre; both package/declaration
directions are explicitly serialized for no-inference consumers. URI recipes
above are the producer contract. Neither new class inherits pkg:Dependency.

- [ ] Approve the four amendments: occurrence identity; decoded attributes plus
  pre; canonical prefix preservation; kind-specific Obsoletes handling.
- [ ] Add failing fixtures for all four kinds, rich expressions, repeated names,
  exact duplicates, token/name mismatch, URI mismatch, missing inverse link,
  and all prohibited flag/version combinations. Include EQ/NE/GE/GT/LE/LT
  mapping tests against the chosen native producer profile; do not rely on the
  current document's inconsistent five-value table versus six-value shape.
- [ ] Implement terms, shapes and URI/profile assertions. Check both typed
  declarations and objects of hasDeclaration so removing a type cannot hide
  them. Validate capabilityName against the declaration token and canonical
  identifier; do not require a capability for Obsoletes or opaque expressions.
- [ ] Add entailment probes: declaration does not become pkg:Dependency;
  capability does not become Package; matching token alone does not entail
  directlyDependsOn. Run OWL-RL checks with explicit prohibited-inference
  assertions; do not treat absence of owl:Nothing as full OWL-DL certification.
- [ ] Correct the complete DD-VirtualPackage example, relation table, and
  satisfaction query; qualify URI-POLICY's package-only dependency guidance.
- [ ] Run `make lint validate reason test-cq check-version` and
  `.venv/bin/python -m unittest discover -s tests -p test_rpm_declarations.py -v`.
  Require expected positive focus counts and all designated negatives failing.
- [ ] Review, commit the focused ontology change, and release a version before
  changed-vocabulary RDF publication. Do not amend core ranges to satisfy data.

### Task 2: Make extracted corpora honest

**Files:** `P/etl/pg-collect/src/extract.rs`; create
`P/etl/pg-collect/tests/extract_rpm_contract.rs` and
`P/etl/pg-collect/tests/fixtures/rpm-declaration-extract.nt`.

**Interfaces:** Keep `bfs_expand` and `extract_triples` callers stable. Treat
vocabulary objects separately from instance traversal; augment the existing
coverage report with target counts and truncation information.

- [ ] Add an end-to-end fixture asserting retained package type, capability
  edge/type/name/label. Add a malformed capability that fails the actual shape
  before and after extraction. First confirm these expose the current gap.
- [ ] Move object-policy filtering from the textual `rfind("> <")` heuristic
  into the CONSTRUCT query, using SPARQL's RDF-term operations (`isIRI`,
  predicate tests, and membership in the selected instance/vocabulary sets).
  Preserve rdf:type values and permitted vocabulary individuals without
  traversing the whole ontology or adding a new Rust RDF parser dependency.
- [ ] After Task 1 agreement, follow hasDeclaration, declaringPackage, and
  declaredCapability; retain declarationKind and provenance identifiers.
  Hydrate a retained declaration completely, including its type and fields.
  Do not rely on inverse-property inference in QLever.
- [ ] Test declarations at the depth boundary and a source with more neighbors
  than fan_out. Either include a complete selected declaration or report its
  omission; never label a partially hydrated record conforming. Make capped
  selection deterministic and report cuts. Blank-node descriptions must not
  silently appear complete; declare their support or report omission.
- [ ] Run `cargo test --locked extract::tests` and
  `cargo test --locked --test extract_rpm_contract`; retain the RDF-level
  validation result and nonzero target counts, not just mock query matching.
- [ ] Commit and review independently of RPM rollout. No fabricated identities
  may be restored to satisfy the extractor.

### Task 3: Implement faithful RPM collection

**Files:** `P/etl/pg-collect/src/rpm.rs`, `src/uris.rs`, `src/vocab.rs`,
`src/source_cache.rs` (only source-reference plumbing if needed),
`P/etl/ONTOLOGY_VERSION`; create `P/etl/pg-collect/tests/rpm_declarations.rs`
and `P/etl/pg-collect/tests/fixtures/rpm-declarations-primary.xml`.

**Interfaces:** Extend RpmDep with `pre: Option<String>` and source entry
ordinal; carry package ordinal/source digest to emission. Add
`rpm_declaration_uri(package_iri: &str, source_sha256: &str,
package_ordinal: usize, section_kind: &str, entry_ordinal: usize) -> String`
in uris.rs. Existing package identities are not redefined by this change.

- [ ] Write failing parser tests for `&gt;`, `&amp;`, numeric character entities,
  malformed XML/attributes, pre="1", absent/empty fields, exact duplicates,
  and repeated names with different operators/epochs/releases.
- [ ] Decode attributes with quick-xml's supported decoding/unescaping API;
  propagate attribute errors instead of `.flatten()` discarding them. Carry
  pre and occurrence location through parsing. Reject a malformed required
  source stage and retain its source artifact for diagnosis.
- [ ] Add identity test vectors: duplicate locations differ, same source/context
  rerun agrees, recompression agrees, changed primary bytes differ. Compute
  the uncompressed digest in a streaming pass before emission; reuse a verified
  repomd open-checksum only if content verification is actually performed.
- [ ] Emit one declaration per supported occurrence using Task 1's rules.
  Preserve all EVR fields for Provides, not just Requires. Emit labels and
  reciprocal links explicitly. Do not drop prefix tokens.
- [ ] Remove legacy requires/conflicts/obsoletes identity manufacture and the
  corresponding undeclared rpm:rpm* predicates. Keep identity creation from
  real package records. Retire stale KNOWN_BAD entries as the ratchet demands;
  rpm:RPMGroup is a separate issue, not proof this contract is incomplete.
- [ ] Test every projection kind and its prohibited edges. Mutating a kind,
  dropping an attribute, conflating duplicates, or restoring identity manufacture
  must fail a specific test. Test an unrelated package with Provides matching
  an Obsoletes token: that does not become an obsolete target automatically.
- [ ] Pin/sync the released ontology; run `cargo test --all-targets --locked`.
  Review and commit; deployment still waits for Tasks 4 and 5.

### Task 4: Gate consumers and prove source-to-graph fidelity

**Files:** `P/etl/pg-collect/src/enrich_revdeps.rs`, `src/enrich_blast_radius.rs`,
`src/stage_report.rs`; create `P/etl/scripts/audit-rpm-contract.py` and
`P/docs/reviews/rpm-contract/acceptance.md`. Wire the audit into the collector
CI workflow `.github/workflows/ci.yml` after checking its current job layout.

**Interfaces:** Audit CLI accepts `--primary`, `--rdf`, `--ontology-root`,
`--manifest`, and `--report`. Its JSON report records source/RDF digests,
per-kind source/declared/rejected counts, shape focus counts, violations,
prohibited edges, and coverage scope. Exit nonzero on a release-gate failure.

- [ ] Test that a migrated RPM graph cannot acquire reverseDependencyCount or
  blastRadius from removed edges, guessed name matches, or legacy mixed-graph
  inputs. Report unsupported RPM results explicitly, not a numeric zero.
- [ ] Independently parse source XML, then compare occurrence multisets and all
  six fields to RDF. Count emitted declarations by kind and source location;
  comparing two outputs produced by the same Rust parser is not independence.
  Stream source/RDF records into a disk-backed or sorted comparison; do not
  require the entire BaseOS RDF graph in Python memory.
- [ ] Validate with no inference first; separately check the declared RDFS/OWL
  regime. Require nonzero expected targets and coverage equality. Include a
  mutation deleting all Capability types: it must fail the coverage/type gate
  even if a class-targeted SHACL run alone reports conformance.
  Validate complete package/declaration/capability partitions plus corpus-wide
  uniqueness/coverage checks. Keep reasoning probes bounded; distinguish full
  structural coverage from any sampled semantic checks in the report.
- [ ] Run competency queries for requirements with constraints, versioned
  provides, opaque expressions, Obsoletes selectors, config/rtld references,
  and provenance. A missing candidate in this incomplete universe must not
  be reported as globally unsatisfiable.
- [ ] Canary in increasing size: retained Extras; pinned BaseOS; a Fedora
  snapshot with rich/conditional expressions and at least two architectures.
  Measure wall time, peak RSS, raw and distinct triples, compressed output,
  index size/build time, and representative query latency.
- [ ] Before a full rebuild, review measured capacity. BaseOS alone has
  3,236,779 declaration occurrences. The cost driver is full declaration
  representation, not 1,199 rtld edges. Stay within deployed memory/time/disk
  limits; if it does not fit, stop for an explicit storage/indexing decision.
  Do not silently restore ingestion filters or claim complete coverage.
- [ ] Commit the consumer guard and durable evidence after review. No whole
  upstream corpus in git; keep content-addressed source artifacts separately.

### Task 5: Publish replacements and verify service

**Files:** `P/docs/GRAPH-PUBLICATION.md`, new
`P/docs/reviews/rpm-contract/cutover.md`; use existing
`P/etl/scripts/upload-nt.sh`, `P/deploy/quadlet/scripts/qlever-rebuild-index.sh`,
and their manifest/rebuild tests. Avoid introducing a second publication system.

**Interfaces:** One signed-off inventory of graph URI → old generation → new
generation, linked to source, collector, ontology, profile, and audit digests.
Record raw-source and output digests separately; a mutable cache is not an
immutable provenance archive.

- [ ] Inventory every RPM graph and affected derived graph from the current
  service. For graph families without a collector, obtain an explicit decision
  to recollect or retire; do not let legacy fallback silently retain them.
- [ ] Acquire sources and build replacement generations without selecting them
  for service. Ensure checkpoint reuse cannot replay pre-contract output.
- [ ] Validate replacements with Task 4's gates. Test manifest integrity and
  index-selection behavior with existing graph-manifest/rebuild test suites.
- [ ] Assemble a replacement index from the approved generation set; exclude
  superseded RPM-derived metrics. Preserve the prior graph generations and
  index, and test rollback before switching publication.
- [ ] Verify the same counts, queries, types, provenance, and absence of legacy
  projections against the served endpoint. Compare index inventory digests,
  not merely successful collector exit codes or HTTP status.
- [ ] Close platform#62 only after collector **and served corpus** evidence is
  attached. Close ontology#19 after its agreed deliverables ship. Keep broader
  research separately tracked. Reclamation requires a later retention decision.

## Parallelism and stop conditions

Task 2 and source capture can start immediately. Task 1 is the short semantic
decision gate; Task 3 development can proceed once its contract is agreed,
before release. Consumer work can proceed in parallel against fixtures.
Tasks 4 and 5 gate broad rollout, not research completion. A source-faithful,
non-resolving RPM profile is the deliverable; cross-ecosystem generalization is
not on this critical path.

Stop for a decision if nominal capability semantics are rejected, evidence
cannot be preserved, or measured capacity is insufficient. Do not use “pre-1.0”
to excuse unsupported claims; it permits correcting them without inventing a
compatibility requirement.

## Academic basis and limits of the claim

- **Guarino and Welty (2002), OntoClean:** identity and taxonomic distinctions
  motivate separating a source occurrence from a named feature and a package.
  This plan does not claim a full OntoClean analysis of every class.
  [Evaluating Ontological Decisions with OntoClean](https://doi.org/10.1145/503124.503150).
- **Abate, Boender, Di Cosmo, and Zacchiroli (2009), ESEM:** syntactic occurrence
  is not semantic necessity. Strong dependency quantifies over healthy
  installations and requires installability to avoid vacuity. This supports
  withholding unsupported package-impact metrics, not claiming this release
  computes strong dependencies.
  [Strong Dependencies between Software Components](https://www.mancoosi.org/papers/esem-2009.pdf).
- **Treinen and Zacchiroli (2009), CUDF 2.0, TR003:** a useful formal reference
  for universes, features, constraints, and solutions; a technical report,
  not evidence that RPM maps to CUDF without semantic work.
  [CUDF 2.0](https://www.mancoosi.org/reports/tr3.pdf).
- **OSGi Core 8, Resource API:** prior art for resource-specific declarations,
  namespaced matching, and separate resolved wires. PackageGraph's nominal
  capability reference is not owl:equivalentClass to an OSGi capability offer.
  [Resource API](https://docs.osgi.org/specification/osgi.core/8.0.0/framework.resource.html).
- **Native RPM and createrepo_c:** authority for RPM interpretation and the
  specific metadata producer; pin versions when testing. Repodata is already
  a projection of headers, not an exhaustive source of runtime/installability
  truth. [RPM dependency manual](https://rpm-software-management.github.io/rpm/man/rpm-dependencies.7),
  [createrepo_c parsing](https://github.com/rpm-software-management/createrepo_c/blob/master/src/parsehdr.c).
- **W3C SHACL:** shape conformance depends on selected focus nodes and the
  validation environment; independent coverage assertions are needed.
  [SHACL targets](https://www.w3.org/TR/shacl/#targets).

The defensible claim is a tested, provenance-bearing representation of an
explicit RPM metadata profile with documented information loss in convenience
views. RDF syntax, passing CI, or zero reasoner diagnostics alone establish
neither domain truth nor academic novelty. Peer review remains an external
assessment; this plan supplies falsifiable claims and reproducible evidence.
