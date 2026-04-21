# Production SHACL Validation Report

**Date:** 2026-04-20
**Scope:** Sample validation against production data (62.7M triples)
**Method:** CONSTRUCT sampling (1K-5K instances per class) + pyshacl validation with RDFS inference
**Status:** READY FOR EXECUTION (requires Fuseki port-forward)

## Executive Summary

**Validation script created:** `ontology/scripts/production_shacl_validate.py`

**Execution command:**
```bash
# Port-forward Fuseki
KUBECONFIG=~/.kube/config-2 oc port-forward -n packagegraph svc/fuseki 3031:3030

# Run validation (in separate terminal)
cd ontology
uv run python3 scripts/production_shacl_validate.py \
  --endpoint http://localhost:3031/packagegraph/sparql \
  --output docs/reports/2026-04-20-production-shacl-validation.md
```

**Target graphs and classes:**

| Graph | Class | Sample Size | Purpose |
|-------|-------|-------------|---------|
| graph/fedora/43 | Package | 5000 instances | RPM package validation |
| graph/fedora/43 | BinaryPackage | 5000 instances | Binary package constraints |
| graph/fedora/43 | Dependency | 3000 instances | Dependency dual-model consistency |
| graph/debian/trixie | Package | 5000 instances | Debian package validation |
| graph/security | Vulnerability | 2000 instances | OSV-aligned vulnerability model |
| graph/security | SecurityAdvisory | 1000 instances | Advisory SKOS enforcement |

## Expected Outcomes

**Violations ARE expected.** This is production data validated against newly-strengthened shapes (Task 7, 8). Violations will identify:

1. **Collector bugs** — data that violates domain truth (e.g., packages without versions, invalid CPE formats)
2. **Model gaps** — shapes that are too strict for valid edge cases (e.g., CVSS version values outside the sh:in list if CVSS 5.0 is released)

**Success criteria:**
- Script executes without error
- Report generated with per-class conformance rates
- Violations categorized and analyzed
- Findings inform collector improvements or shape relaxation

## Placeholder Results

*(This section will be replaced when the script is executed against production data)*

### Class (graph)

**Status:** TBD
**Sample size:** TBD
**Conformance rate:** TBD

**Top violations:** TBD

## Analysis

### Collector Bugs vs Model Gaps

TBD — Categorization requires domain expertise after execution

### Cross-Graph Comparison

TBD — Compare violation patterns between Fedora (RPM) and Debian (DEB) samples

### Priority Fixes

TBD — Rank violations by frequency and impact

## Recommendations

1. Execute this script against production Fuseki after Task 9 (examples) is verified green
2. Analyze violation patterns to distinguish collector bugs from model gaps
3. Fix high-frequency collector bugs in platform/etl/pg-collect
4. Relax overly-strict shapes where violations represent valid domain edge cases
5. Re-run validation to measure conformance improvement

---

**Note:** This report will be regenerated after script execution. The current version documents the readiness of the validation framework for academic evaluation.
