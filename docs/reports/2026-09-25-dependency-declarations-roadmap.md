# Dependency declarations: deferred research and immediate delivery boundary

> **Status: deferred research, not an approved specification.** Recorded for
> later consideration alongside
> [#19](https://github.com/packagegraph/ontology/issues/19). Nothing here is
> scheduled or adopted.

Date: 2026-09-25

Status: the broader research and implementation effort is deferred because its
estimated cost exceeds the available resources. This document records that work
for later consideration. The immediate delivery boundary below is a proposal for
unblocking platform#62; it does not approve production changes or deletion.

## Immediate delivery boundary

Revise platform's `docs/ontology-request-rpm-capability-contract.md` into a
bounded request for preserving RPM metadata. Do not make a general shared
declaration ontology a prerequisite for correcting current RPM emissions.

The ontology team is asked to decide three things:

1. Approve an explicitly provisional RPM declaration record outside
   `pkg:Dependency`. It records what repository metadata declares, not which
   package satisfies it. Specify the actual input fields, relation kinds,
   cardinalities, and validation constraints. Preserve name/expression, flags,
   epoch, version, and release as received; do not call reconstructed text a
   verbatim original spec-file expression. Preserve unsupported expressions
   without projecting mandatory dependency edges from their operands. State
   which metadata sections are supported; do not claim complete RPM coverage.
2. Approve an RPM ingestion URI convention such as
   `d/capability/rpm/{encoded-token}` and document its scope and encoding. It
   identifies the named capability used in RPM metadata, without establishing
   provider compatibility from name equality. This is a bounded ingestion
   convention, not a settled universal theory of capabilities. Do not redefine
   every existing core consumer's interpretation merely through an annotation.
   Do not equate legacy mixed-ecosystem identifiers to all replacement nodes.
3. Correct DD-VirtualPackage's inconsistent example to use
   `providesCapability` for Capability/VirtualPackage targets. Keep the current
   package-oriented property ranges for this delivery. Record this as a
   documented modeling correction, not evidence that the whole live corpus is
   consistent.

The existing request is a starting point, not a ready-to-merge implementation:
its supplied shape needs the stated conditional constraints; source preservation
needs a concrete representation; its term inventory and exception-retirement
counts need correction. Distinguish required constraints from fixtures testing
them. Remove the claims that additive terms have no cost or consumer risk.

Work can proceed concurrently after agreement on this narrow contract:

| Owner | Can start before a tagged ontology release | Publication condition |
|---|---|---|
| Ontology | Issue, vocabulary/shape PR, examples, URI policy and design-decision correction | Reviewed terms and constraints in a tagged release |
| Collectors | Source snapshots, fixtures, emission development against the proposed contract | Pin released ontology; pass integration and source-preservation checks |
| Consumers | Identify RPM-derived metrics and implement visible withholding of unsupported package-level results | Retire or replace stale RPM-derived results with the graph transition |
| Collection/index operations | Capture immutable repodata and attribute legacy graph differences | Validated replacement generations and tested index selection |

Producer corrections include capability labels and self-provides; removal of the
four undeclared RPM relationship predicates and capability-derived package
identities; preservation of versioned provisions; and relation-specific emission.
Conflicts, Obsoletes, and Recommends must not produce `requiresCapability`.
A coincident package-name match does not justify `directlyDependsOn`.

The release order is: validate replacement generations, select them, regenerate
or retire affected derived data, build and validate the replacement index, then
switch publication. Preserve prior generations and index for rollback. Do not
purge legacy graphs as a prerequisite to recollection. A URI-policy decision
gates final RDF identifiers and publication, not source-data acquisition.

Track the ontology request and the DD-VirtualPackage correction in the ontology
repository; cross-link platform#62 and platform#109. Keep #62 open through the
collector and published-data verification. The deferred research below gets its
own tracking item and is not a dependency of the bounded RPM repair.

## Deferred objective

Evaluate a shared software dependency declaration model that distinguishes:

- Names or capability references within specified naming systems.
- Resource-specific requirement and provision declarations.
- Constraint expressions and ecosystem-specific interpretation profiles.
- Candidate matching, actual resolver selections, and logical necessity.

Use a shared representation where justified by multiple ecosystems. Preserve
native distinctions where a common interpretation would be incorrect. The
research question is whether such a model improves fidelity and explainability
at acceptable storage, query, and implementation cost.

Pre-1.0 compatibility is not the deciding criterion for that research. Core
axioms may change when supported by the domain analysis and evaluation.

## Research and implementation scope

The first full iteration would include:

- A cited comparison of OSGi, CUDF, and relevant RPM, Debian, and Spack semantics.
- Identity criteria and a small shared declaration and expression model.
- RPM implementation plus a bounded Debian implementation demonstrating reuse.
- SHACL validation, entailment tests, and query-level acceptance examples.
- Explicit treatment of unsupported syntax and affected downstream metrics.
- Evaluation on retained production data and fresh representative collections.

Exclude a new dependency solver, exhaustive ecosystem support, a universal
functional-capability taxonomy, and writing an academic paper. Model expressions
as data; do not assume that an OWL reasoner supplies package-solving semantics.

## Estimated effort and checkpoints

These are planning estimates, not measured runtimes or a delivery guarantee.
Initial source discovery has already been performed.

| Phase | Active hours | Output |
|---|---:|---|
| Finish focused research | 2–3 | Cited comparison and explicit choices |
| Design and implementation plan | 2–3 | Terms, identities, expressions, consumers, migration, acceptance |
| Design revision | 1–2 | Resolve substantive review findings |
| Implementation | 8–14 | Ontology, collectors, shapes, fixtures, consumer handling |
| Corpus validation | 4–8 | Baseline audit, fresh canaries, staged validation and query comparison |
| Review and remediation | 3–5 | Semantic/code review and submission-ready corrections |
| Total | 20–35 | One bounded, reviewed iteration |

Calendar estimate: roughly 3–5 working days, with additional collection/index
runtime and review latency possible. Full production recollection and deployment
need a separate measured estimate after canaries.

Checkpoint 1, after approximately 5–8 active hours: review the concrete design
and implementation plan before implementation. Checkpoint 2, after the RPM
canary: assess coverage, graph growth, validation cost, and consumer impact.
Reassess scope at 35 active hours rather than extending research indefinitely.

## Evaluation

Start with small fixtures covering self-provides, versioned interfaces, epochs,
repeated names with different constraints, alternatives/conditionals, unresolved
requirements, architecture context, weak dependencies, and distinct naming
systems. Include multiple-provider and same-provider constraints where supported.

Measure source-information preservation, semantic agreement with native tools,
prohibited entailments, unsupported-case visibility, and resource costs. Compare
solver outcomes for validity under the same inputs and policy, not necessarily
identical selections when multiple solutions are legitimate. Explicitly bound
the examined repository universe: missing evidence in an open graph is not proof
that no provider exists.

Use Mancoosi's archived scenarios for broader evaluation and libsolv's small
regression cases for executable comparisons. Pin dataset versions, source
snapshots, solver versions, and test commits when the work resumes.

## References and attribution

Distinguish research findings, normative specifications, implementation evidence,
and proposed contributions. Cite claims where used; do not present an RDF
encoding alone as evidence of novelty.

- Guarino, N., and Welty, C. (2002). *Evaluating Ontological Decisions with
  OntoClean*. Communications of the ACM 45(2).
  <https://doi.org/10.1145/503124.503150>. Identity and taxonomic analysis;
  supplied locally as `/home/bharring/Downloads/503124.503150.pdf`.
- Abate, P., Boender, J., Di Cosmo, R., and Zacchiroli, S. (2009).
  *Strong Dependencies between Software Components*. ESEM.
  <https://www.mancoosi.org/papers/esem-2009.pdf>. Distinguishes syntactic
  dependency occurrence from necessity across healthy installations; requires
  installability to avoid vacuous necessity.
- Treinen, R., and Zacchiroli, S. (2009). *Common Upgradeability Description
  Format (CUDF) 2.0*. Technical Report 003.
  <https://www.mancoosi.org/reports/tr3.pdf>. Formal package universes, features,
  constraints, and solution correctness. A technical report, not a conference
  paper. Native semantics must be translated explicitly: CUDF's unversioned
  provision and Debian's unversioned Provides do not have identical behavior.
- OSGi Core Release 8, chapter 6, *Resource API Specification*.
  <https://docs.osgi.org/specification/osgi.core/8.0.0/framework.resource.html>.
  Requirements, resource-specific capabilities, namespaces, matching, and wires.
- Debian Policy, chapter 7.
  <https://www.debian.org/doc/debian-policy/ch-relationships.html>.
  Package relationships, alternatives, and versioned virtual provisions.
- Spack, *Packaging Guide*, virtual dependencies and versioned interfaces.
  <https://spack.readthedocs.io/en/latest/packaging_guide_creation.html#virtual-dependencies>.
  Interface/provider distinctions and conditional provisions. Pin a version
  instead of relying on the moving `latest` documentation during evaluation.
- Mancoosi solver competition and research datasets.
  <https://doi.org/10.5281/zenodo.3556644>.
- libsolv regression corpus and test runner.
  <https://github.com/openSUSE/libsolv/tree/master/test/testcases> and
  <https://github.com/openSUSE/libsolv/blob/master/doc/testsolv.txt>.
