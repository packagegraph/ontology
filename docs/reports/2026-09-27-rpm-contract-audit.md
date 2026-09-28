# RPM contract audit — 2026-09-27

> **Status: audit evidence, not an approved specification.** This is an
> independent review of platform PR #110 against ontology v0.15.0, recorded so
> the measurements behind the amendments proposed in
> [#19](https://github.com/packagegraph/ontology/issues/19) can be checked.
> Nothing here is adopted ontology policy, and no term named in it exists yet.

## Scope and verdict

Reviewed platform `0fa40b132f747fc3de10dd7038386f83b7b9a3ea` (PR #110)
against ontology `60017af10288e2cd30268434d18355e43435e674` (v0.15.0).
PR #110 is an effective provides-only correction, not completion of the RPM
contract. At the GitHub check it remained open, with five successful CI checks
and publication skipped. No implementation, GitHub state, or production data
was changed by this audit.

The recommended next step is the
[bounded resolution plan](../superpowers/plans/2026-09-27-rpm-contract-resolution.md).

## Reproduced results

The current revision passed `cargo test --all-targets --locked --offline
--quiet --target-dir /tmp/platform-audit-target`: **1,103 library tests plus
56 other-target tests, 1,159 total**. Tests ran in an isolated git-archive
snapshot, with loopback access for mock HTTP servers.

| Claim or risk | Independent finding |
|---|---|
| New capability traversal | Both predicates are present in `extract.rs:143`; the actual BFS and extraction functions now retain a providesCapability edge. |
| Complete capability extraction | Still false: `extract.rs:288` removes `rdf:type pkg:Capability` because the class IRI was not visited. A valid five-triple fixture becomes four triples, with its name and label retained. |
| SHACL as proof of preservation | A deliberately malformed source capability fails CapabilityShape; after extraction it conforms with zero class targets. Restoring only its type makes it fail again. This reproduction uses the actual shape, no ontology graph, and `inference='none'`. RDFS-enabled validation with the ontology loaded can behave differently. |
| Correct XML attribute values | `rpm.rs:819` reads raw attribute bytes without entity decoding. The actual streaming parser returns `(foo &gt;= 1 or bar)` for XML encoding the value `(foo >= 1 or bar)`. |
| Complete source attributes | `RpmDep` ignores `pre`; the measured source contains 1,573 such attributes. The proposal explicitly defers this field, so the omission is disclosed, but a five-attribute representation is not all of primary.xml. |
| One node per source entry | The requested seven-component content key is not occurrence identity. The source contains exact duplicate entries as well as differently constrained repeated names. |
| Prefix policy | The same filtering predicate still discards config/rtld/rpmlib entries on the requires and provides paths. Calling this a policy makes it explicit, not semantically complete. |
| Remaining identity fabrication | Requires, conflicts, and obsoletes still manufacture package identities. Requires also emits directlyDependsOn and reified pkg:Dependency; declaration terms are not yet released. |
| Downstream metrics | `enrich_revdeps.rs:103` counts directlyDependsOn targets; `enrich_blast_radius.rs:84` consumes those counts. Neither is a provider resolver. |

The type-loss bug predates the latest traversal fix. The two new tests cover
query traversal and edge filtering, not the complete extracted description.
The production SHACL helper uses RDFS inference; this audit does **not** claim
that every existing validation route passes vacuously.

## Fresh source measurement

Source: AlmaLinux 9 BaseOS, x86_64 repository tree, fetched September 27.
The tree contains multiple package architectures; x86_64 here identifies the
repository URL, not an assertion about every package record.

- Repository: `https://repo.almalinux.org/almalinux/9/BaseOS/x86_64/os/`
- repomd revision: `1790420699`
- repomd SHA-256: `665fbbe98e2238b7a0c14480616e213ceb02208ba485825da6caa8f485dfc773`
- Compressed primary SHA-256: `efbe328b6173f71ee384b8a07792d447457bc8f3434439f2bb427b5735662a58`
- Uncompressed primary SHA-256: `2991b157fe0a1edc84269a516547918135851f5c379fd9b4918405a321a3b87b`

Both primary digests were checked against repomd. Counts below are XML entry
occurrences or package blocks, not RDF triples or distinct capability nodes.

| Prefix | Provides entries / blocks | Requires entries / blocks | Distinct provided tokens |
|---|---:|---:|---:|
| rtld( | 10 / 10 | 1,199 / 1,199 | 1 |
| config( | 423 / 423 | 0 / 0 | 175 |
| rpmlib( | 0 / 0 | 0 / 0 | 0 |

There are 2,996 package records, 3,210,726 Provides entries, 24,619 Requires,
560 Conflicts, and 874 Obsoletes: **3,236,779 supported-section occurrences**.
There are 103 rich Requires occurrences and 1,573 `pre="1"` attributes.
Exact duplicates within one package and section contribute 189 extra Requires
entries and 13 extra Provides entries. A content-keyed set collapses those
occurrences even if every currently proposed key field is included.

The team's rtld measurement is reproduced. Its config measurement (433 / 2)
is not reproduced on this snapshot; without its source digest this is an
unresolved reproducibility difference, not proof its earlier count was wrong.

## Native semantics that constrain the design

The [RPM dependency manual](https://rpm-software-management.github.io/rpm/man/rpm-dependencies.7)
distinguishes process-supplied rpmlib requirements from package-supplied
capabilities. It also specifies that Obsoletes matches package Name/EVR,
not arbitrary Provides. A common name does not erase these distinctions.

The inspected [createrepo_c implementation](https://github.com/rpm-software-management/createrepo_c/blob/master/src/parsehdr.c)
filters rpmlib in its **requires** branch. That explains absence on this route;
it is not a universal restriction on XML or all producers. Its `pre` flag is
derived from several RPM flags, not exclusively the pre-install scriptlet.
Preserving the raw repodata flag does not recover the full original header.
Inspected parsehdr.c SHA-256:
`c096c2f96667e5b6fafccbe6b681a5fbc744ecf44f5c05f7621894610e778451`.

The proposed prefix exceptions should therefore be removed from canonical
declaration/reference preservation. Filter presentation or analytical views
when needed, with a named policy and measured cost. Outgoing-only BFS does
not automatically fan out to all incoming requirers of a shared capability.

## Reproduction artifacts and limits

Current audit workspace: `/tmp/packagegraph-rpm-plan-audit.acLGAH`.

- `all-targets.log`: full test results.
- `etl/pg-collect/examples/audit_rpm_contract.rs`: calls actual Rust extractor
  and XML parser functions without altering their implementation.
- `audit_extract_types.py`: RDFLib HTTP fixture and real CapabilityShape checks.
- `audit_source.py`: independent streaming XML counts and digest verification.
- Source bytes: `/tmp/rpm-source-audit.3klY1T/{repomd.xml,primary.xml.gz}`.

Run the source counter with `python3 audit_source.py /tmp/rpm-source-audit.3klY1T`.
Build the example with `cargo build --example audit_rpm_contract --locked
--offline --target-dir /tmp/platform-audit-target` from the snapshot's
`etl/pg-collect` directory. Run `audit_extract_types.py` using the ontology
virtual environment, passing that example executable and `core/core.shacl.ttl`.
The fixture server requires loopback socket permission.

The earlier actual collector canary is retained in
`/tmp/packagegraph-pr110-audit.VJcO6M/REPORT.md`: 57 Extras packages, 83 labelled
capabilities, 102 source-matched non-filtered provision pairs, and 57 self
provisions. That run was at `9590fb7`, not a fresh collection at `0fa40b1`.
It found four remaining conflict-only identities and two obsolete-only
identities, not six conflict-only identities. Current validation adds the
fresh BaseOS source analysis, current test suite, and current extractor/parser
reproductions; it does not certify a completed production recollection or index.

Temporary artifacts are not a durable evidence archive. Preserve the relevant
fixtures, scripts, manifests, and reports with the implementation PRs; do not
commit whole upstream corpora to git.
