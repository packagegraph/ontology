# Bounded RPM primary.xml declaration contract

Profile: `rpm-primary-v1`. Implementation of the decisions accepted on
[ontology#19](https://github.com/packagegraph/ontology/issues/19#issuecomment-5902540436).
This profile is not released until the implementation is merged and a new
ontology version is tagged. Platform publication must pin that release.

## Scope and meaning

Record one occurrence for every `rpm:entry` in Provides, Requires, Conflicts and
Obsoletes, including self-provides, duplicate entries, config/rtld/rpmlib tokens,
and opaque expressions. Do not synthesize declarations for missing source
entries. Weak dependencies, filelists, solver integration, expression ASTs and
cross-distribution correspondence are outside this profile.

Declarations record source observations, not packages, chosen providers or
installation truth. They remain outside `pkg:Dependency` for this delivery.
There is no permanent OWL disjointness axiom precluding later unification.
The existing core domains, ranges and global capability definition are unchanged.

## Vocabulary and represented information

Sixteen new vocabulary terms: two classes (`rpm:DependencyDeclaration`,
`rpm:DeclarationKind`), four kind individuals, and ten properties:

| Property | Object/value | Required on a declaration |
|---|---|---|
| `rpm:hasDeclaration` | Package → declaration | Explicit inverse link on the package |
| `rpm:declaringPackage` | Declaration → collected Package | Exactly one |
| `rpm:declarationKind` | Provides, Requires, Conflicts, Obsoletes | Exactly one |
| `rpm:declaredToken` | XML-decoded `name` | Exactly one nonempty string |
| `rpm:declaredCapability` | RPM-scoped Capability | Conditional, at most one |
| `rpm:declarationFlags` | XML-decoded `flags` | Optional string |
| `rpm:declarationEpoch` | XML-decoded `epoch` | Optional string |
| `rpm:declarationVersion` | XML-decoded `ver` | Optional string |
| `rpm:declarationRelease` | XML-decoded `rel` | Optional string |
| `rpm:declarationPre` | XML-decoded `pre` | Optional string |

Every declaration also has an explicit type, label and one `prov:wasDerivedFrom`
link to an immutable primary.xml source represented as `pkg:DataSnapshot`.
Keep the source bytes and digest manifest retrievable; no new provenance terms
are introduced. Both package/declaration directions are serialized because
consumers such as QLever do not perform OWL inverse-property inference.

Decode XML entities exactly once, without further trimming, case folding or
Unicode normalization. Missing attributes produce no value; present empty
attributes remain empty strings. In particular, do not synthesize epoch zero.
`pre` is preserved, not interpreted as exclusively pre-install ordering.
Keep unknown attributes in the source and report them as outside represented
coverage. Malformed input must not disappear while publication reports success.

The fidelity claim covers these six attributes in four sections, not all RPM
headers or a reconstructed spec-file expression. A leading `(` marks an opaque
expression candidate; it is not a syntax-validity or satisfiability assertion.

## Conditional rules

| Kind/token | Capability link | Token-level shortcut |
|---|---|---|
| Simple Provides | Required | `pkg:providesCapability` |
| Simple Requires | Required | `pkg:requiresCapability` |
| Simple Conflicts | Required | None |
| Obsoletes | Absent | None |
| Opaque expression candidate | Absent | None |

Obsoletes retains a package-name/EVR selector rather than an arbitrary provided
capability; see the [RPM dependency manual](https://rpm-software-management.github.io/rpm/man/rpm-dependencies.7).
There is no prefix exception for simple tokens. The source producer may omit
entries, but the collector may not silently filter those actually present.

Shortcuts erase constraint, ordering and occurrence information. A package may
both require and conflict with the same nominal feature: its Requires occurrence
can support a requiresCapability edge, but its Conflicts occurrence cannot.
Validation checks supporting occurrences, not a blanket ban on an edge whenever
a conflicting declaration exists. Do not flatten expression operands.

Version attributes admit exactly two structural states:

- All flags/epoch/version/release absent.
- Flags and version present, with epoch and release optional.

The createrepo_c profile permits `EQ`, `GE`, `GT`, `LE`, and `LT`, matching
[`cr_flag_to_str` at createrepo_c revision c8c070a](https://github.com/rpm-software-management/createrepo_c/blob/c8c070ab03bca0cb26b1ab2a4d5f2a59ca7cd50f/src/misc.c#L49-L69).
The original request's inclusion of `NE` was unsupported by that producer.
`NE`, unknown flags and prohibited combinations fail this profile; retain the
source and report the reason rather than coercing or dropping the entry.
Empty optional strings are preserved; shape conformance does not certify native
RPM expression validity or version-comparison semantics.

No declaration, capability or expression manufactures a PackageIdentity.
Profiled packages do not emit legacy `rpm:rpm*`, `pkg:directlyProvides`,
`pkg:directlyDependsOn` or `pkg:hasDependency` projections from these observations.
Token/name equality never licenses a property chain into package dependencies.

## Identity and validation boundaries

Follow the exact [URI policy and test vectors](../URI-POLICY.md#bounded-rpm-primaryxml-profile).
Capability identity is naming system plus decoded token. Declaration identity is
source occurrence plus declaring-package context; repeated equal entries stay
distinct. Recompression does not change the uncompressed digest. The published
manifest pins one data base and source/collector/ontology/profile versions.

Three new node shapes validate declarations, referenced capabilities, and their
declaring packages. Targets include objects of `hasDeclaration` and subjects of
declaration fields so stripping a type does not hide a malformed record.
Run on **asserted data with inference disabled first**, then separately under
the declared reasoning regime. RDFS/OWL can restore absent types or inverse
links; inferred conformance is not evidence of complete serialization.

SHACL checks structure, linkage, canonical capability encoding and declaration
IRI syntax. It cannot establish from RDF alone that the declared source existed,
that every source occurrence was emitted, or that a declaration hash matches its
source location. The independent platform audit must reconstruct occurrence keys
from retained primary.xml, compare all six fields and occurrence counts, check
base consistency, and detect omitted or merged records. A graph with all relevant
data deleted must fail coverage even if SHACL has no focus nodes.

`make validate-rpm-contract` runs the shape, URI and prohibited-entailment tests;
it is included in `make validate` and therefore in the existing CI build gate.
OWL-RL probes check specific prohibited consequences, not full OWL-DL consistency.

## Consumer queries and publication handoff

Requirements with recorded constraints (bind the capability to a scoped IRI):

```sparql
PREFIX rpm: <https://purl.org/packagegraph/ontology/rpm#>
SELECT ?package ?declaration ?capability ?flags ?epoch ?version ?release WHERE {
  ?declaration a rpm:DependencyDeclaration ;
    rpm:declaringPackage ?package ; rpm:declarationKind rpm:Requires ;
    rpm:declaredCapability ?capability .
  OPTIONAL { ?declaration rpm:declarationFlags ?flags }
  OPTIONAL { ?declaration rpm:declarationEpoch ?epoch }
  OPTIONAL { ?declaration rpm:declarationVersion ?version }
  OPTIONAL { ?declaration rpm:declarationRelease ?release }
}
```

Opaque expressions must be selected by token syntax, not merely by missing
`declaredCapability`: Obsoletes legitimately has no such link too.

```sparql
PREFIX rpm: <https://purl.org/packagegraph/ontology/rpm#>
SELECT ?declaration ?kind ?token WHERE {
  ?declaration a rpm:DependencyDeclaration ;
    rpm:declarationKind ?kind ; rpm:declaredToken ?token .
  FILTER(STRSTARTS(STR(?token), "("))
}
```

Scope operational queries to selected package/enrichment graph generations.
Provider candidates, solver-selected providers, unattempted resolution and
unsatisfiability are distinct. Package-level RPM impact metrics are withheld
visibly until justified resolution semantics exist; orphan-target diagnostics
do not establish those semantics.

After release: pin/sync the ontology, finish declaration emission and extraction,
pass independent retained-source/canary audits, review capacity, replace every
retained RPM generation and affected derived results, build/validate a replacement
index, then switch with rollback retained. Unsupported historical graphs require
an explicit recollect-or-retire decision. No purge is a prerequisite.
Ontology#19 closes after its agreed deliverables ship; platform#62 remains open
until collector output, served data and consumers are verified.
