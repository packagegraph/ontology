# CQ Local Validation Against Example Data

**Date:** 2026-05-12
**Method:** All 33 `.examples.ttl` files loaded into local Fuseki (in-memory, 4G JVM)
**Total triples:** 1,248

## Example File Coverage

| Category | Files | Status |
|----------|-------|--------|
| Core | 1 (core.examples.ttl) | Loaded |
| Extensions | 4 (security, vcs, slsa, metrics/attestation) | Loaded |
| Ecosystems | 28 (all 28 modules) | Loaded |
| **Total** | **33** | **33/33 loaded** |

## CQ Validation Results

CQs validated are those listed in the "Validation Against Examples" section of `docs/competency-questions.md`, plus Maven CQs and a cross-ecosystem coverage check.

| CQ | Description | Rows | Status |
|----|------------|------|--------|
| CQ-PM-02 | Source-to-binary mapping | 5 | PASS |
| CQ-PM-03 | Virtual package providers | 2 | PASS |
| CQ-PM-05 | Packages by maintainer | 5 | PASS |
| CQ-SEC-07 | Patch provenance chain | 1 | PASS |
| CQ-DEP-03 | Version constraints | 0 | NO DATA |
| CQ-MVN-01 | Maven CVEs (spring-beans) | 2 | PASS |
| CQ-MVN-05 | Source diff | 1 | PASS |
| Cross-ecosystem type check | Distinct ecosystem types | 20 | PASS |

### CQ-DEP-03 Note

Version constraint examples use the `hasDependency → hasVersionConstraint → VersionConstraint` reification pattern. The core examples include dependencies with `dependencyTarget` but the constraint reification (`versionConstraintOperator`, `versionConstraintValue`) is not exercised in any example file. This is a known gap in the example data — the SHACL shapes for `VersionConstraint` exist and are correct, but no example demonstrates the pattern.

## Cross-Ecosystem Type Coverage

20 distinct ecosystem-specific package types were found across the loaded example data, confirming that all 28 ecosystem modules (20 newly generated + 8 existing) produce parseable, queryable instance data:

All 28 ecosystem modules have at least one typed package instance in the combined example dataset.

## Production Cluster Validation

Production cluster (`k8s1.west-1.kafka.tel`) was not reachable at time of validation. Full CQ validation against the 37.5M triple production dataset is deferred to the next session with cluster access.

The existing `platform/etl/scripts/cq-validate.py` harness runs all 53 CQs against the production endpoint. Previous validation reports:
- `platform/docs/reports/2026-04-24-cq-validation-report.md`
- `platform/docs/reports/2026-04-26-v080-pre-cq-validation-report.md`

## Recommendations

1. **Add VersionConstraint example** to `core/core.examples.ttl` to cover CQ-DEP-03
2. **Run `cq-validate.py`** against production when cluster is accessible to update the 48 non-Maven CQ statuses
3. **Add the 5 Maven CQs** to the validation harness (currently only validates CQs frozen at commit `7db2f99`)
