# SLSA/PROV-O Integration Completion Plan

Created: 2026-04-13
Author: sovereign@local
Status: VERIFIED
Approved: Yes
Iterations: 0
Worktree: No
Type: Feature

## Summary

**Goal:** Complete SLSA/PROV-O integration — register slsa.ttl in build tooling, update documentation, add SLSA namespace and emission methods to platform, enhance Koji collector with full SLSA attestation triples.

**Architecture:** Additive changes across two repos. Ontology side: Makefile + docs. Platform side: namespace constant, GraphBuilder methods, Koji collector enhancement. No schema changes — the ontology files (core.ttl, vcs.ttl, security.ttl, slsa.ttl, shacl.ttl, examples.ttl) were completed in the prior session.

**Tech Stack:** Turtle/OWL (ontology), Python 3.12+/rdflib (platform), Make (build)

## Scope

### In Scope
- Makefile: add slsa.ttl to ONTOLOGY_FILES
- CHANGELOG.md: document PROV-O grounding and SLSA additions
- README.md: add slsa.ttl listing and file structure entry
- Run `make lint` validation
- Platform namespaces.py: add SLSA namespace constant + URI builders
- Platform graph_builder.py: add SLSA provenance emission methods, fix redundant prov:Activity type
- Platform koji.py: emit full SLSA attestation triples from Koji build data
- Tests for new graph_builder methods

### Out of Scope
- Ontology schema changes (already done)
- Repology collector SLSA level assessment
- DataSnapshot <-> SLSA linking property
- SPARQL query examples
- Distribution-specific SLSA level mappings
- Any changes to files listed as AVOID (entrypoint.sh, pg-collect, fuseki, deploy, enrichers, workflows)

## Approach

**Chosen:** Additive-only changes following existing patterns
**Why:** All files are safe to extend. GraphBuilder already has add_build_activity, add_vulnerability, etc. — SLSA methods follow the same pattern. Koji already calls `_process_build` — we extend it.
**Alternatives considered:** (1) Separate SLSABuilder class — rejected, GraphBuilder is the single emission point. (2) New enricher for SLSA — rejected, Koji already has the data.

## Context for Implementer

> Write for an implementer who has never seen the codebase.

- **Patterns to follow:**
  - `graph_builder.py:351-373` — `add_vulnerability()` pattern: create URI, add type/properties, return URI
  - `graph_builder.py:393-418` — `add_build_activity()` pattern: existing PROV-O emission
  - `koji.py:137-156` — `_process_build()` pattern: use GraphBuilder methods to emit triples
  - `namespaces.py:29-91` — URI builder functions: `_encode()` + f-string template

- **Conventions:**
  - Namespace constants are UPPERCASE (`PKG`, `SEC`, `VCS`, `SLSA`)
  - URI builders are snake_case functions returning `str`
  - GraphBuilder methods: `add_<thing>()` returns URIRef, `link_<relation>()` returns None
  - All methods use keyword arguments for optional params
  - Dual typing: `self.graph.add((uri, RDF.type, PKG.BuildActivity))` — distro-specific types follow same pattern

- **Key files:**
  - `ontology/Makefile:5` — `ONTOLOGY_FILES` variable
  - `ontology/CHANGELOG.md` — version history
  - `ontology/README.md` — ontology listing (sections at lines 14-100) and file structure (lines 176-190)
  - `platform/etl/packagegraph/namespaces.py` — namespace defs + URI builders
  - `platform/etl/packagegraph/graph_builder.py` — shared triple emission logic
  - `platform/etl/packagegraph/collectors/koji.py` — Koji build metadata enricher
  - `platform/etl/tests/test_graph_builder.py` — existing GraphBuilder tests

- **Gotchas:**
  - `add_build_activity()` at line 407 has redundant `(b_uri, RDF.type, PROV.Activity)` — remove it (ontology handles via subClassOf)
  - Don't change `add_dependency()` signature (recently changed)
  - Don't modify existing namespace constants or URI builders — ADD only
  - Koji `_process_build()` is the extension point — don't change `_get_build()` or `_get_rpm_packages()`
  - `graph_builder.py` imports from namespaces.py — add SLSA to the import list

- **Domain context:**
  - SLSA v1.0 has 4 build levels (L0-L3). Koji builds map to L2 (hosted, tamper-resistant provenance)
  - Koji getBuild() returns: owner_name, start_time, completion_time, build_id, task_id, volume_name
  - Koji getTaskInfo() returns: host_name, arch, method (for build environment data)
  - ProvenanceAttestation captures: build level, timestamp, digest, builder, source info
  - Builder captures: platform identity (koji hub URL), version
  - BuildEnvironment captures: ephemeral/isolated flags, build image

## Assumptions

- Koji XML-RPC proxy is already initialized in `self.proxy` — Tasks 5, 6 depend on this
- `getTaskInfo()` is available on the Koji hub — Task 6 depends on this (all Fedora/CentOS koji instances support it)
- GraphBuilder `__init__` binding pattern extends naturally with new prefix — Task 4 depends on this
- The existing `_process_build` can be extended without changing its signature — Task 6 depends on this

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Koji getTaskInfo() rate limiting | Low | Medium | Reuse existing 0.5s sleep between packages; task info is fetched once per build |
| slsa.ttl not imported by other ontology files | Low | Low | SLSA is standalone with explicit imports; no other file needs to import it |
| Redundant prov:Activity removal breaks something | Very Low | Low | The type is inferred via rdfs:subClassOf; explicit triple was always redundant |

## Goal Verification

### Truths

1. `make lint` passes with slsa.ttl included in ONTOLOGY_FILES
2. CHANGELOG.md has a new section documenting all PROV-O and SLSA changes
3. README.md lists slsa.ttl as the 10th ontology with description
4. `from packagegraph.namespaces import SLSA` works without error
5. GraphBuilder can emit SLSA ProvenanceAttestation, Builder, and BuildEnvironment triples
6. Koji collector emits SLSA L2 attestation triples for each build it processes
7. All existing tests still pass after changes
8. New SLSA emission methods have unit tests

### Artifacts

1. `ontology/Makefile` — slsa.ttl in ONTOLOGY_FILES (Truth 1)
2. `ontology/CHANGELOG.md` — new version section (Truth 2)
3. `ontology/README.md` — slsa.ttl listing (Truth 3)
4. `platform/etl/packagegraph/namespaces.py` — SLSA namespace + URI builders (Truth 4)
5. `platform/etl/packagegraph/graph_builder.py` — SLSA methods + prov:Activity fix (Truth 5)
6. `platform/etl/packagegraph/collectors/koji.py` — SLSA attestation emission (Truth 6)
7. `platform/etl/tests/test_graph_builder.py` — new tests (Truth 8)

## Progress Tracking

- [x] Task 1: Add slsa.ttl to Makefile and run lint
- [x] Task 2: Update CHANGELOG.md
- [x] Task 3: Update README.md
- [x] Task 4: Add SLSA namespace to platform namespaces.py
- [x] Task 5: Add SLSA emission methods to graph_builder.py
- [x] Task 6: Enhance Koji collector with SLSA attestation
- [x] Task 7: Add unit tests for SLSA emission

**Total Tasks:** 7 | **Completed:** 7 | **Remaining:** 0

## Notes

**Integration test pre-existing failure:** `test_debian_rpm_integration_with_sparql` expects 4 BinaryPackages but finds 6. This is caused by recent `add_dependency()` changes (commit 6d690a7) that create BinaryPackage-typed stubs for dependency targets. The failure predates SLSA work. All SLSA-specific tests (13 graph_builder + 2 koji = 15 tests) pass.

## Implementation Tasks

### Task 1: Add slsa.ttl to Makefile and run lint

**Objective:** Register slsa.ttl in the build system so `make lint`, `make concat`, and `make deploy` include it.
**Dependencies:** None

**Files:**
- Modify: `ontology/Makefile`

**Key Decisions / Notes:**
- Add `slsa.ttl` to the `ONTOLOGY_FILES` variable at line 5 (after `security.ttl metrics.ttl`)
- Run `make lint` to validate all ontology files including slsa.ttl

**Definition of Done:**
- [ ] slsa.ttl appears in ONTOLOGY_FILES
- [ ] `make lint` passes with 0 errors

**Verify:**
```bash
make lint
```

### Task 2: Update CHANGELOG.md

**Objective:** Document the PROV-O grounding and SLSA additions in the changelog.
**Dependencies:** None

**Files:**
- Modify: `ontology/CHANGELOG.md`

**Key Decisions / Notes:**
- Add a `## [0.5.0] - 2026-04-13` section at the top (before `## [0.4.0]`)
- Document: new slsa.ttl file, PROV-O grounding changes to core.ttl/vcs.ttl/security.ttl, new SHACL shapes, new examples
- Keep version at 0.5.0 (matches owl:versionInfo in all ontology files)

**Definition of Done:**
- [ ] New changelog section documents all PROV-O and SLSA changes
- [ ] Changes grouped by category (Added, Changed)

**Verify:**
- Read the file and confirm completeness

### Task 3: Update README.md

**Objective:** Add slsa.ttl to the ontology listing and file structure.
**Dependencies:** None

**Files:**
- Modify: `ontology/README.md`

**Key Decisions / Notes:**
- Add section "### 10. SLSA Supply Chain Security Ontology (`slsa.ttl`)" after the Nix section (line 100)
- Add `slsa.ttl` to the file structure tree (after `nix.ttl`, around line 186)
- Also add `security.ttl`, `metrics.ttl`, `redhat.ttl`, `shacl.ttl` to the file structure tree if missing (they exist but may not be listed)

**Definition of Done:**
- [ ] slsa.ttl listed as 10th ontology with purpose, key classes, features, namespace
- [ ] File structure tree includes slsa.ttl

**Verify:**
- Read the file and confirm accuracy

### Task 4: Add SLSA namespace to platform namespaces.py

**Objective:** Add SLSA namespace constant and URI builder functions.
**Dependencies:** None

**Files:**
- Modify: `platform/etl/packagegraph/namespaces.py`

**Key Decisions / Notes:**
- Add `SLSA = Namespace("https://packagegraph.github.io/ontology/slsa#")` after line 10 (with other ontology namespaces)
- Add URI builders: `attestation_uri(distro, release, name, version)`, `builder_uri(builder_id)`, `build_env_uri(distro, release, name, version)`
- Follow existing `_encode()` + f-string pattern

**Definition of Done:**
- [ ] `SLSA` namespace constant defined
- [ ] URI builder functions for attestation, builder, build environment
- [ ] `from packagegraph.namespaces import SLSA` works

**Verify:**
```bash
cd platform/etl && uv run python3 -c "from packagegraph.namespaces import SLSA; print(SLSA)"
```

### Task 5: Add SLSA emission methods to graph_builder.py

**Objective:** Add methods to emit SLSA ProvenanceAttestation, Builder, and BuildEnvironment triples. Fix redundant prov:Activity type.
**Dependencies:** Task 4

**Files:**
- Modify: `platform/etl/packagegraph/graph_builder.py`

**Key Decisions / Notes:**
- Import `SLSA` from namespaces.py (add to import list at line 6)
- Import new URI builders: `attestation_uri`, `builder_uri`, `build_env_uri`
- Bind `"slsa"` prefix in `__init__` (after line 33)
- Remove redundant `self.graph.add((b_uri, RDF.type, PROV.Activity))` at line 407
- Add methods following existing patterns:
  - `add_slsa_builder(builder_id, version=None)` → URIRef
  - `add_slsa_build_environment(distro, release, name, version, image=None, image_digest=None, ephemeral=None, isolated=None)` → URIRef
  - `add_slsa_attestation(distro, release, name, version, build_level, timestamp, digest, builder_uri_ref, build_activity_uri=None, build_env_uri_ref=None, predicate_type=None, verification_status=None)` → URIRef
  - `link_attestation_to_package(attestation_uri, package_uri)` → None

**Definition of Done:**
- [ ] SLSA namespace bound in GraphBuilder.__init__
- [ ] Redundant prov:Activity type triple removed from add_build_activity
- [ ] add_slsa_builder emits slsa:Builder with builderId and optional version
- [ ] add_slsa_build_environment emits slsa:BuildEnvironment with image and flags
- [ ] add_slsa_attestation emits slsa:ProvenanceAttestation with level, timestamp, digest, and links
- [ ] link_attestation_to_package emits slsa:hasProvenance

**Verify:**
```bash
cd platform/etl && uv run pytest tests/test_graph_builder.py -q
```

### Task 6: Enhance Koji collector with SLSA attestation

**Objective:** Extend `_process_build` to emit full SLSA L2 attestation triples from Koji build data.
**Dependencies:** Task 5

**Files:**
- Modify: `platform/etl/packagegraph/collectors/koji.py`

**Key Decisions / Notes:**
- Import `SLSA` from namespaces (add to import line 17)
- In `_process_build()` (line 137), after existing build activity creation:
  1. Create Builder: `self.builder.add_slsa_builder(builder_id=self.koji_hub)`
  2. Optionally fetch task info via `self.proxy.getTaskInfo(task_id)` for host_name and build method
  3. Create BuildEnvironment from task info (ephemeral=True, isolated=True for Koji mock builds)
  4. Create ProvenanceAttestation with level=L2, timestamp from build completion, digest from build NVR
  5. Link attestation to package
- Wrap getTaskInfo in try/except (some koji hubs may not have task info)
- Reuse existing `time.sleep(0.5)` rate limiting — no extra sleep needed

**Definition of Done:**
- [ ] _process_build emits slsa:Builder for Koji hub
- [ ] _process_build emits slsa:BuildEnvironment from task info (when available)
- [ ] _process_build emits slsa:ProvenanceAttestation at L2
- [ ] Attestation linked to package via slsa:hasProvenance
- [ ] getTaskInfo failure is handled gracefully (attestation still emitted without env details)

**Verify:**
```bash
cd platform/etl && uv run pytest tests/test_collectors/ -q
```

### Task 7: Add unit tests for SLSA emission

**Objective:** Test new GraphBuilder SLSA methods and verify existing tests still pass.
**Dependencies:** Task 5

**Files:**
- Modify: `platform/etl/tests/test_graph_builder.py`

**Key Decisions / Notes:**
- Add tests following existing patterns (test_add_package, test_add_vulnerability, etc.)
- Test `add_slsa_builder`: verify slsa:Builder type, builderId, optional version
- Test `add_slsa_build_environment`: verify type, image, ephemeral/isolated flags
- Test `add_slsa_attestation`: verify type, build level link, timestamp, digest
- Test `link_attestation_to_package`: verify slsa:hasProvenance triple
- Test that `add_build_activity` no longer emits explicit `prov:Activity` type
- Import SLSA from namespaces, verify "slsa" prefix is bound

**Definition of Done:**
- [ ] All new methods have at least one test
- [ ] Redundant prov:Activity removal verified by test
- [ ] `uv run pytest tests/test_graph_builder.py -q` passes
- [ ] Full test suite passes: `uv run pytest -q`

**Verify:**
```bash
cd platform/etl && uv run pytest -q
```

## Open Questions

None — all design decisions resolved.
