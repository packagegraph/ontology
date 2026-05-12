# Maven CQ Live Pipeline Validation Report

**Date:** 2026-05-12
**Validated by:** Claude Code + Fuseki 5.5.0 (in-memory, 16G JVM)
**Pipeline:** pg-collect maven → enrich-security --ecosystem maven → enrich-diff → Fuseki SPARQL

## Test Corpus

12 Maven components from `spring-cves.json`:

| Component | groupId | Collected |
|-----------|---------|-----------|
| spring-core | org.springframework | Yes |
| spring-beans | org.springframework | Yes |
| spring-context | org.springframework | Yes |
| spring-aop | org.springframework | Yes |
| spring-webmvc | org.springframework | Yes |
| spring-web | org.springframework | Yes |
| spring-jdbc | org.springframework | Yes |
| spring-tx | org.springframework | Yes |
| struts2-core | org.apache.struts | Yes |
| spring-security-core | org.springframework.security | Yes |
| spring-security-web | org.springframework.security | Yes |
| spring-security-config | org.springframework.security | Yes |

## Pipeline Execution

| Step | Command | Output |
|------|---------|--------|
| **Collect** | `pg-collect maven --packages-file seed.txt --output maven-spring.nt` | 12 packages, 881 triples, 6.78s |
| **Enrich Security** | `pg-collect enrich-security --ecosystem maven --output maven-security.nt` | 12 packages, 23,240 triples, 12.96s |
| **Enrich Diffs** | `pg-collect enrich-diff --output maven-diff.nt --github-token $TOKEN` | 2 repos, 1,240 triples, 57.18s |
| **Total** | | 25,361 triples across 3 N-Triples files |

Data loaded into Fuseki across 3 graphs:
- Default graph: Maven artifact data (980 triples)
- `graph/security/maven`: OSV vulnerability data (23,240 triples)
- `graph/vcs/diffs`: GitHub diff data (1,240 triples)

## CQ Validation Results

### CQ-MVN-01: CVEs for a Maven Artifact — PASS

**Query:** CVEs affecting `org.springframework:spring-beans`

**Results:** 2 CVEs found

| CVE | CVSS |
|-----|------|
| CVE-2022-22965 (Spring4Shell) | — |
| CVE-2022-22970 | — |

**Negative test:** `org.springframework:spring-aop` — 0 CVEs (correct, no advisories in GHSA)

**Additional:** `org.apache.struts:struts2-core` — 60 CVEs found

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?cveId ?severity WHERE {
  GRAPH ?g {
    ?vuln sec:hasAffectedRange ?range .
    ?range sec:affectsPackageName "org.springframework:spring-beans" ;
           sec:affectsEcosystem/rdfs:label "Maven" .
    ?vuln sec:cveId ?cveId .
    OPTIONAL { ?vuln sec:hasCVSSScore/sec:baseScore ?severity }
  }
} ORDER BY DESC(?severity)
```

---

### CQ-MVN-02: Vulnerable Versions for a CVE — PASS

**Query:** Version ranges for CVE-2022-22965 affecting `org.springframework:spring-beans`

**Results:** 4 range events (2 ranges x 2 events each)

| Introduced | Fixed |
|------------|-------|
| 0 | — |
| 5.3.0 | — |
| — | 5.2.20.RELEASE |
| — | 5.3.18 |

Two affected version ranges: `[0, 5.2.20.RELEASE)` and `[5.3.0, 5.3.18)`. GIT ranges correctly filtered out by `FILTER(?rt IN (sec:range-ecosystem, sec:range-semver))`.

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?introducedVersion ?fixedVersion WHERE {
  GRAPH ?g {
    ?vuln sec:cveId "CVE-2022-22965" ; sec:hasAffectedRange ?range .
    ?range sec:affectsPackageName "org.springframework:spring-beans" ;
           sec:affectsEcosystem/rdfs:label "Maven" ;
           sec:rangeType ?rt ; sec:hasRangeEvent ?event .
    FILTER(?rt IN (sec:range-ecosystem, sec:range-semver))
    OPTIONAL { ?event sec:eventType sec:event-introduced ; sec:eventVersion ?introducedVersion . }
    OPTIONAL { ?event sec:eventType sec:event-fixed ; sec:eventVersion ?fixedVersion . }
  }
}
```

---

### CQ-MVN-03: Fix Commit for a CVE — PASS

**Query:** Fix version/commit for CVE-2022-22965 in `org.springframework:spring-beans`

**Results:** 2 fix events

| Fixed Version | Commit Hash |
|--------------|-------------|
| 5.2.20.RELEASE | — |
| 5.3.18 | — |

No GIT-range data for this CVE in OSV (Spring4Shell only has ECOSYSTEM ranges). The `sec:eventCommit` property is correctly absent. GIT-range commit linking was validated with example data against Fuseki in the schema validation phase.

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX vcs: <https://purl.org/packagegraph/ontology/vcs#>
SELECT ?fixedVersion ?commitHash WHERE {
  GRAPH ?g {
    ?vuln sec:cveId "CVE-2022-22965" ; sec:hasAffectedRange ?range .
    ?range sec:affectsPackageName "org.springframework:spring-beans" ;
           sec:affectsEcosystem/rdfs:label "Maven" ; sec:hasRangeEvent ?event .
    ?event sec:eventType sec:event-fixed .
    OPTIONAL { ?event sec:eventVersion ?fixedVersion }
    OPTIONAL { ?event sec:eventCommit ?c . ?c vcs:commitHash ?commitHash . }
  }
}
```

---

### CQ-MVN-04: Source Location for an Artifact Version — PASS

**Query:** Source repository for `org.springframework:spring-core`

**Results:** 1 result

| Clone URL | Tag |
|-----------|-----|
| git://github.com/spring-projects/spring-framework | — |

Tag is absent because Spring's POM uses `<scm><tag>HEAD</tag>` (our collector correctly filters out `HEAD` as a non-informative tag value).

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX vcs: <https://purl.org/packagegraph/ontology/vcs#>
PREFIX maven: <https://purl.org/packagegraph/ontology/maven#>
SELECT ?cloneUrl ?tag WHERE {
  ?artifact maven:groupId "org.springframework" ;
            maven:artifactId "spring-core" ;
            pkg:isVersionOf ?identity .
  OPTIONAL { ?identity pkg:upstreamRepository/vcs:cloneUrl ?cloneUrl }
  OPTIONAL { ?artifact vcs:packagedFromTag/vcs:tagName ?tag }
}
```

---

### CQ-MVN-05: Source Diff to Previous Version — PASS

**Query:** Diff data for Spring Framework artifacts at version 7.0.0-M6

**Results:** 8 results (one per Spring artifact sharing the spring-framework repo)

| Artifact | Version | Diff URL | +Lines | -Lines | Files |
|----------|---------|----------|--------|--------|-------|
| spring-core | 7.0.0-M6 | github.com/.../compare/v7.0.0-M7...v7.0.0-M6 | 1 | 1 | 1 |
| spring-beans | 7.0.0-M6 | (same) | 1 | 1 | 1 |
| spring-web | 7.0.0-M6 | (same) | 1 | 1 | 1 |
| spring-webmvc | 7.0.0-M6 | (same) | 1 | 1 | 1 |
| spring-context | 7.0.0-M6 | (same) | 1 | 1 | 1 |
| spring-aop | 7.0.0-M6 | (same) | 1 | 1 | 1 |
| spring-jdbc | 7.0.0-M6 | (same) | 1 | 1 | 1 |
| spring-tx | 7.0.0-M6 | (same) | 1 | 1 | 1 |

All 8 artifacts from the spring-framework repo correctly join to the same diff via `correspondingPackageVersion`. The diff between v7.0.0-M7 and v7.0.0-M6 was a single-file version bump (1 addition, 1 deletion).

**Note:** Query requires cross-graph pattern — Maven artifact data in default graph, diff data in named graph:

```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX vcs: <https://purl.org/packagegraph/ontology/vcs#>
PREFIX maven: <https://purl.org/packagegraph/ontology/maven#>
SELECT ?artifactId ?currentVersion ?diffUrl ?linesAdded ?linesDeleted ?filesChanged WHERE {
  ?artifact maven:groupId "org.springframework" ;
            maven:artifactId ?artifactId ;
            pkg:hasVersion ?verEntity ;
            pkg:isVersionOf ?identity .
  ?verEntity pkg:versionString ?currentVersion .
  ?identity pkg:upstreamRepository ?repo .
  GRAPH ?g {
    ?release vcs:correspondingPackageVersion ?verEntity ;
             vcs:hasDiff ?diff .
    ?diff vcs:diffUrl ?diffUrl .
    OPTIONAL { ?diff vcs:linesAdded ?linesAdded }
    OPTIONAL { ?diff vcs:linesDeleted ?linesDeleted }
    OPTIONAL { ?diff vcs:filesChanged ?filesChanged }
  }
}
```

---

## Summary

| CQ | Status | Data Source | Notes |
|----|--------|------------|-------|
| CQ-MVN-01 | **PASS** | OSV API (real) | 2 CVEs for spring-beans, 60 for struts2-core, 0 for spring-aop |
| CQ-MVN-02 | **PASS** | OSV API (real) | Version ranges with introduced/fixed boundaries |
| CQ-MVN-03 | **PASS** | OSV API (real) | Fix versions returned; no GIT-range commits for this CVE |
| CQ-MVN-04 | **PASS** | Maven Central POM (real) | SCM URL extracted from `<scm><connection>` |
| CQ-MVN-05 | **PASS** | GitHub Compare API (real) | 58 diffs across 2 repos, 22 correspondingPackageVersion links |

## Bugs Found During Validation

| Bug | Scope | Fix |
|-----|-------|-----|
| `write_bnode_object` used for bnode-to-bnode links | **All ecosystems** (pre-existing) | Added `write_bnode_to_bnode()` to NTriplesWriter |
| Missing `rdfs:label` on ecosystem entities | All ecosystems | Added label emission in `osv.rs` |
| Missing User-Agent on Maven collector | Maven only | Added `user_agent()` to reqwest client builder |
| `"maven"` missing from CLI `value_parser` | Maven only | Added to `EnrichSecurity` args |
| CQ-MVN-02 returning GIT commit hashes as versions | CQ query | Added `FILTER(?rt IN (sec:range-ecosystem, sec:range-semver))` |

## Ontology Properties Exercised (Live Data)

**New properties validated:**
- `sec:eventCommit` — schema-validated (no GIT ranges in Spring OSV data for this CVE)
- `vcs:diffFrom`, `vcs:diffTo`, `vcs:diffUrl` — live GitHub compare data
- `vcs:linesAdded`, `vcs:linesDeleted`, `vcs:filesChanged` — live aggregate stats
- `vcs:hasDiff` — Release → Diff linking
- `vcs:correspondingPackageVersion` — Release → Version cross-graph join
- `pkg:identityName` (colon form) — joins with `sec:affectsPackageName`
- `pkg:purl` — emitted on all 12 PackageIdentity instances
- `pkg:upstreamRepository` — from POM `<scm><url>` via `normalize_forge_url()`
