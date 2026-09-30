# Academic rigor review: bounded RPM declaration changes

Date: 2026-09-30. Scope: the implementation beginning at `0739cc5`, its review
corrections, and the separately proposed cross-distribution correspondence work.
This is an engineering/semantic review with a fresh-context reviewer, not
external academic peer review or certification of the whole ontology.

## Assessment

The bounded RPM profile is defensible as an explicitly scoped representation of
source declarations, subject to the source-to-publication gates in the
[contract](../rpm-declaration-contract.md). It does not establish dependency
resolution, empirical accuracy of cross-distribution matching, or novelty of a
general capability ontology. These limits are part of the result, not omitted
future details.

| Question | Evidence and conclusion | Remaining limit |
|---|---|---|
| What is identified? | Package context, a nominal RPM feature reference, and a source-entry occurrence have separate identifiers and roles. Occurrence vectors distinguish repeated positions and changed sources. | The URI convention is not a full metaphysical identity theory for all software capabilities. |
| Are declarations confused with dependencies? | The new class is not a subclass of `pkg:Dependency`; tests prohibit dependency/package typing and inferred package edges from shared capabilities. | No native solver or strong-dependency computation is implemented. |
| Is source information preserved? | Six decoded attributes and four sections are explicitly bounded; empty and absent differ; examples and queries preserve duplicate occurrences. | Ontology fixtures do not prove that a collector emitted every occurrence or decoded XML correctly. Independent retained-source comparison is still required. |
| Are relation kinds interpreted correctly? | Obsoletes has no capability link; Conflicts has no shortcut; opaque expressions are not flattened; observed internal tokens are retained. | Native expression parsing, ordering and provider compatibility are not claimed. |
| Are tests non-vacuous? | Positive fixture counts, negative mutations, asserted-data validation, and separate entailment probes run. An independently discovered targeting gap was reproduced and fixed. | A completely omitted source occurrence is invisible to SHACL alone. |
| Are core commitments silently changed? | RDF graph comparison against `60017af` found zero removed core triples and exactly three added `skos:scopeNote` annotations. Core logical axioms are unchanged. | This is not a formal conservativity proof over every possible external ontology. |
| Is the work reproducible? | Tests, examples, URI vectors and a pinned native producer reference accompany the implementation. | Current collector and served-corpus acceptance must retain sources, manifests, queries, outputs and tool versions. |

## Findings and disposition

1. **Structural validation defect, corrected.** The initial shape targeted only
   three declaration-specific fields. A partial record retaining only flags,
   epoch, version, release, pre, or declaredCapability escaped validation, even
   beside a valid declaration. Six negative probes reproduced this. All nine
   declaration-specific predicates now select subjects as focus nodes. The new
   regression failed six cases before the change and passed afterward. This
   follows the actual [SHACL subjects-of target semantics](https://www.w3.org/TR/shacl/#targetSubjectsOf),
   not an inference that positive focus counts alone certify coverage.
2. **OntoClean attribution, corrected in the modified decision section.** The
   old paragraph presented a modeling choice as an OntoClean conclusion and
   described every Package as a concrete installable unit, despite the existing
   definition admitting metadata-only references. It now distinguishes the
   choice from a formal evaluation and does not infer non-membership merely
   from absent size/checksum values.
3. **Identifier distinctness, qualified here.** Different occurrence IRIs and
   preserved SPARQL rows express the producer's identifier convention. They do
   not alone entail different individuals in OWL, which has no unique-name
   assumption. The SHA-256 recipe also relies on practical collision resistance,
   not a mathematical claim that hashes are injective. No quadratic collection
   of `owl:differentFrom` assertions or new OWL keys is introduced.
   [OWL 2 Primer, equality and inequality](https://www.w3.org/TR/owl2-primer/#Equality_and_Inequality_of_Individuals).

## Academic and normative grounding

- Guarino, N., and Welty, C. (2002), *Evaluating Ontological Decisions with
  OntoClean*, CACM 45(2), 61–65, [DOI](https://doi.org/10.1145/503124.503150).
  The supplied paper was inspected for its identity/unity and subsumption
  analysis. That motivates distinguishing a named feature from an occurrence
  mentioning it; it does not certify this ontology. A full OntoClean claim
  would require explicit metaproperty analysis not supplied by this change.
- Abate, P., Boender, J., Di Cosmo, R., and Zacchiroli, S. (2009), *Strong
  Dependencies between Software Components*, ESEM, 89–99,
  [author manuscript](https://arxiv.org/abs/0905.4226).
  The distinction between declared syntax and semantic dependency supports
  withholding unsupported impact metrics. This profile does not implement the
  paper's strong-dependency analysis or validate its outcomes on RPM.
- [RPM dependency manual](https://rpm-software-management.github.io/rpm/man/rpm-dependencies.7)
  and [createrepo_c `cr_flag_to_str`, pinned revision](https://github.com/rpm-software-management/createrepo_c/blob/c8c070ab03bca0cb26b1ab2a4d5f2a59ca7cd50f/src/misc.c):
  native relation interpretation and the five supported comparison flags.
  They are domain/implementation authorities, not academic publications.
- [SHACL](https://www.w3.org/TR/shacl/) governs graph validation relative to
  targets and constraints. Conformance does not establish source truth or
  completeness. [PROV-O](https://www.w3.org/TR/prov-o/) supplies derivation
  vocabulary; a provenance assertion is not itself proof that source bytes
  were retained or that extraction was faithful.

## Verification result and limits

The required `make lint validate reason test-cq check-version` gates passed
after the targeting correction. They include 24 RPM tests. The initial shape
suite failed 55 assertions, URI tests failed four cases, the query regression
failed on zero declarations, and the review regression failed six orphan-field
cases before their corresponding changes. The tested core RDF delta contains
only the three annotations described above. Full unittest discovery passed
52 tests after installing the previously missing test dependencies in an
isolated environment; unittest does not execute the pytest-only live checks.

The broader Python suite is **not wholly green**: 52 tests passed, 15 existing
live PURL tests failed, and 14 existing namespace tests skipped missing legacy
root-level Turtle paths. The module redirect tests receive HTTP 307 while
asserting only 301/302; the base-domain assertion also fails. That test file is
unchanged from main. These results neither invalidate the demonstrated RPM
invariants nor certify published term dereferenceability. They must not be
reported as a clean full-suite run or silently removed to obtain one.

## Deferred correspondence proposal

The separately recorded proposal distinguishes upstream-family discovery,
package-role correspondence and compatibility, includes monorepo/fork and
homepage counterexamples, and requires evidence and abstentions. Those are
appropriate design commitments. Accepted
[DEP-12](https://dep-team.pages.debian.net/deps/dep12/) is practical upstream
metadata prior art, not evidence that a matcher is accurate.

The OpenSSL role examples are motivating cases, not a benchmark. Historical
endpoint observations lack a retained acceptance dataset in that proposal.
No precision/recall, installation compatibility, ABI equivalence, vulnerability
transfer, or novelty claim is validated. The proposed project-identity axiom
review remains separate from this RPM implementation.

## What this review deliberately does not certify

Collector decoding/emission, extraction completeness, source archives and
manifests, graph-generation selection, stale-metric retirement, capacity,
release tagging, index cutover and rollback remain platform/release acceptance
work. Existing unrelated ontology axioms and OntoClean claims were not subjected
to a full ontology-wide audit. Academic novelty and peer-review acceptance
require external evaluation; no reviewer or test suite here can guarantee them.
