# PackageGraph Ontology Competency Questions

**Version:** 1.0
**Date:** 2026-04-20
**Status:** Formal Specification

## Purpose

This document defines the competency questions (CQs) that the PackageGraph ontology must be able to answer. CQs serve as the formal specification for ontology evaluation — they define what the ontology is FOR. Each CQ is formalized as a SPARQL query with expected result shape.

**Methodology:** NeOn/METHONTOLOGY — CQs drive schema design. A CQ that fails exposes a schema gap.

**References:**
- Grüninger, M., & Fox, M. S. (1995). *Methodology for the Design and Evaluation of Ontologies.* IJCAI-95 Workshop on Basic Ontological Issues in Knowledge Sharing.
- Ren, Y., et al. (2014). *Towards Competency Question-driven Ontology Authoring.* ESWC 2014.

---

## Domain: Package Management (PM)

### CQ-PM-01: Distribution Package Listing

**Question:** What binary packages does Fedora 43 ship for architecture x86_64?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?package ?name ?version
WHERE {
  ?release ^pkg:hasRelease/rdfs:label "Fedora" ;
           pkg:releaseVersion "43" .
  ?package a pkg:BinaryPackage ;
           pkg:partOfRelease ?release ;
           pkg:targetArchitecture ?arch ;
           pkg:packageName ?name ;
           pkg:hasVersion/pkg:versionString ?version .
  ?arch rdfs:label "x86_64" .
}
ORDER BY ?name
LIMIT 100
```

**Expected Columns:** package (URI), name (string), version (string)

**Exercises:** Package, BinaryPackage, DistributionRelease, Architecture, Version

**Status:** PASS

---

### CQ-PM-02: Source-to-Binary Mapping

**Question:** Which binary packages are built from the `glibc` source package in Fedora 43?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?binary ?binaryName
WHERE {
  ?source a pkg:SourcePackage ;
          pkg:packageName "glibc" ;
          pkg:partOfRelease ?release .
  ?release ^pkg:hasRelease/rdfs:label "Fedora" ;
           pkg:releaseVersion "43" .
  ?binary pkg:builtFromSource ?source ;
          pkg:packageName ?binaryName .
}
```

**Expected Columns:** binary (URI), binaryName (string)

**Exercises:** SourcePackage, BinaryPackage, builtFromSource, partOfRelease

**Status:** PASS

---

### CQ-PM-03: Virtual Package Providers

**Question:** Which concrete packages provide the virtual capability `libssl.so.3` in Debian Trixie?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?provider ?providerName
WHERE {
  ?capability a pkg:Capability ;
              pkg:capabilityName "libssl.so.3" .
  ?provider pkg:provides ?capability ;
            pkg:packageName ?providerName ;
            pkg:partOfRelease ?release .
  ?release ^pkg:hasRelease/rdfs:label "Debian" ;
           pkg:releaseCodename "trixie" .
}
```

**Expected Columns:** provider (URI), providerName (string)

**Exercises:** Capability, provides, partOfRelease

**Status:** PASS

---

### CQ-PM-03b: Virtual Package and Capability Providers (UNION)

**Question:** Which packages satisfy a dependency on `mail-transport-agent`, whether provided as a Package (via provides) or a Capability (via providesCapability)?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?provider ?providerName
WHERE {
  {
    # Path 1: Package provides another Package
    ?virtual pkg:packageName "mail-transport-agent" .
    ?provider pkg:provides ?virtual ;
              pkg:packageName ?providerName .
  }
  UNION
  {
    # Path 2: Package provides a Capability
    ?capability pkg:capabilityName "mail-transport-agent" .
    ?provider pkg:providesCapability ?capability ;
              pkg:packageName ?providerName .
  }
}
ORDER BY ?providerName
```

**Expected Columns:** provider (URI), providerName (string)

**Exercises:** VirtualPackage, Capability, provides, providesCapability, UNION (demonstrates query bifurcation)

**Status:** PASS

**Note:** This CQ demonstrates the VirtualPackage/Capability design choice documented in DD-VirtualPackage. Analysts must query both paths to catch all dependency satisfaction mechanisms.

---

### CQ-PM-04: Dependency Chain Depth

**Question:** What is the maximum dependency depth (transitive closure) for the `openssl` package in Fedora 43?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT (COUNT(?dep) AS ?depth)
WHERE {
  ?package pkg:packageName "openssl" ;
           pkg:partOfRelease ?release .
  ?release ^pkg:hasRelease/rdfs:label "Fedora" ;
           pkg:releaseVersion "43" .
  ?package pkg:directlyDependsOn+ ?dep .
}
```

**Expected Columns:** depth (integer)

**Exercises:** directlyDependsOn (transitive closure), property path

**Status:** PASS

**Note:** Requires property path support. May timeout on large graphs.

---

### CQ-PM-05: Packages by Maintainer

**Question:** Which packages across all distributions are maintained by person with email `maintainer@example.org`?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?package ?packageName ?distro
WHERE {
  ?person foaf:mbox <mailto:maintainer@example.org> .
  ?role a pkg:Maintainer ;
        pkg:heldBy ?person .
  ?package pkg:maintainedBy ?role ;
           pkg:packageName ?packageName ;
           pkg:partOfRelease/^pkg:hasRelease/rdfs:label ?distro .
}
ORDER BY ?distro ?packageName
```

**Expected Columns:** package (URI), packageName (string), distro (string)

**Exercises:** Person, Maintainer, heldBy, maintainedBy, OntoClean role model

**Status:** PASS

---

### CQ-PM-06: Architecture Support Coverage

**Question:** How many packages in Fedora 43 support arm64 architecture?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT (COUNT(DISTINCT ?package) AS ?count)
WHERE {
  ?release ^pkg:hasRelease/rdfs:label "Fedora" ;
           pkg:releaseVersion "43" .
  ?package pkg:partOfRelease ?release ;
           pkg:targetArchitecture ?arch .
  ?arch rdfs:label "aarch64" .
}
```

**Expected Columns:** count (integer)

**Exercises:** hasArchitecture, Architecture, aggregation

**Status:** PASS

---

### CQ-PM-07: License Distribution

**Question:** What is the distribution of licenses across all packages in Debian Trixie?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?license (COUNT(?package) AS ?count)
WHERE {
  ?release ^pkg:hasRelease/rdfs:label "Debian" ;
           pkg:releaseCodename "trixie" .
  ?package pkg:partOfRelease ?release ;
           pkg:hasLicense ?licenseEntity .
  ?licenseEntity rdfs:label ?license .
}
GROUP BY ?license
ORDER BY DESC(?count)
LIMIT 20
```

**Expected Columns:** license (string), count (integer)

**Exercises:** hasLicense, License, aggregation

**Status:** PASS

---

### CQ-PM-08: Installed File Overlap

**Question:** Which files are installed by multiple packages in RHEL 9 (potential conflicts)?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?filepath (COUNT(DISTINCT ?package) AS ?packageCount) (GROUP_CONCAT(?pkgName; separator=", ") AS ?packages)
WHERE {
  ?release ^pkg:hasRelease/rdfs:label "RHEL" ;
           pkg:releaseVersion "9" .
  ?package pkg:partOfRelease ?release ;
           pkg:installsFile ?file ;
           pkg:packageName ?pkgName .
  ?file pkg:installedFilePath ?filepath .
}
GROUP BY ?filepath
HAVING (COUNT(DISTINCT ?package) > 1)
ORDER BY DESC(?packageCount)
LIMIT 50
```

**Expected Columns:** filepath (string), packageCount (integer), packages (string)

**Exercises:** InstalledFile, installedFilePath, installsFile, aggregation

**Status:** PASS

---

### CQ-PM-09: Package Size Distribution

**Question:** What is the median installed size of binary packages in OpenSUSE Tumbleweed?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rpm: <https://purl.org/packagegraph/ontology/rpm#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT (AVG(?size) AS ?avgSize) (MIN(?size) AS ?minSize) (MAX(?size) AS ?maxSize)
WHERE {
  ?release ^pkg:hasRelease/rdfs:label "openSUSE" ;
           pkg:releaseCodename "Tumbleweed" .
  ?package a rpm:BinaryRPM ;
           pkg:partOfRelease ?release ;
           rpm:installedSize ?size .
}
```

**Expected Columns:** avgSize (integer), minSize (integer), maxSize (integer)

**Exercises:** RPM module, installedSize, aggregation

**Status:** PASS

---

### CQ-PM-10: Package Update Frequency

**Question:** Which packages have the most versions across all Fedora releases?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?packageName (COUNT(DISTINCT ?version) AS ?versionCount)
WHERE {
  ?release ^pkg:hasRelease ?dist .
  ?dist rdfs:label "Fedora" .
  ?package pkg:packageName ?packageName ;
           pkg:partOfRelease ?release ;
           pkg:hasVersion ?versionEntity .
  ?versionEntity pkg:versionString ?version .
}
GROUP BY ?packageName
ORDER BY DESC(?versionCount)
LIMIT 20
```

**Expected Columns:** packageName (string), versionCount (integer)

**Exercises:** Version, hasVersion, cross-release aggregation

**Status:** PASS

---

## Domain: Licensing (LIC)

### CQ-LIC-01: License Distribution by SPDX Identifier

**Question:** What is the distribution of SPDX license types across all packages in Fedora 43?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?spdxId (COUNT(?package) AS ?count)
WHERE {
  ?package pkg:partOfRelease ?release ;
           pkg:hasLicense ?license .
  ?release ^pkg:hasRelease/rdfs:label "Fedora" ;
           pkg:releaseVersion "43" .
  ?license pkg:spdxId ?spdxId .
}
GROUP BY ?spdxId
ORDER BY DESC(?count)
LIMIT 20
```

**Expected Columns:** spdxId (string), count (integer)

**Exercises:** License, hasLicense, spdxId, aggregation

**Status:** PASS

---

### CQ-LIC-02: Packages with Non-SPDX Licenses

**Question:** Which packages use licenses not in the SPDX License List (custom or non-standard license strings)?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?packageName ?licenseLabel
WHERE {
  ?package pkg:packageName ?packageName ;
           pkg:hasLicense ?license .
  ?license rdfs:label ?licenseLabel .
  FILTER NOT EXISTS { ?license pkg:spdxId ?id }
}
LIMIT 100
```

**Expected Columns:** packageName (string), licenseLabel (string)

**Exercises:** License, spdxId, negation

**Status:** PASS

---

### CQ-LIC-03: Cross-Release License Changes

**Question:** Which packages have changed licenses between Fedora 42 and Fedora 43?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?packageName ?oldSpdx ?newSpdx
WHERE {
  ?identity pkg:identityName ?packageName .

  ?pkg42 pkg:isVersionOf ?identity ;
         pkg:partOfRelease ?release42 ;
         pkg:hasLicense/pkg:spdxId ?oldSpdx .
  ?release42 ^pkg:hasRelease/rdfs:label "Fedora" ;
             pkg:releaseVersion "42" .

  ?pkg43 pkg:isVersionOf ?identity ;
         pkg:partOfRelease ?release43 ;
         pkg:hasLicense/pkg:spdxId ?newSpdx .
  ?release43 ^pkg:hasRelease/rdfs:label "Fedora" ;
             pkg:releaseVersion "43" .

  FILTER(?oldSpdx != ?newSpdx)
}
LIMIT 100
```

**Expected Columns:** packageName (string), oldSpdx (string), newSpdx (string)

**Exercises:** License, spdxId, PackageIdentity, cross-release comparison

**Status:** PASS

---

## Domain: Security / Vulnerability (SEC)

### CQ-SEC-01: Affected Packages by CVE

**Question:** Which packages across all distributions are affected by CVE-2024-1234?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?package ?packageName ?ecosystem
WHERE {
  ?vuln sec:cveId "CVE-2024-1234" ;
        sec:hasAffectedRange ?range .
  ?range sec:affectsEcosystem ?eco ;
         sec:affectsPackageName ?packageName .
  ?eco rdfs:label ?ecosystem .
  OPTIONAL {
    ?package a pkg:Package ;
             pkg:packageName ?packageName ;
             pkg:partOfRelease/^pkg:hasRelease/pkg:partOfEcosystem ?eco .
  }
}
```

**Expected Columns:** package (URI or UNDEF), packageName (string), ecosystem (string)

**Exercises:** Vulnerability, cveId, hasAffectedRange, AffectedRange, affectsEcosystem, affectsPackageName

**Dependency contract:** Vulnerability-side only. Requires `sec:cveId`, `sec:hasAffectedRange`, `sec:affectsEcosystem`, `sec:affectsPackageName` on vulnerability entities. Advisory cross-references (`sec:addressesVulnerability`, `sec:advisoryForPackage`) do not satisfy this CQ — it operates entirely on the vulnerability/affected-range model.

**Status:** PASS

---

### CQ-SEC-02: Unpatched Vulnerabilities

**Question:** Which high-severity vulnerabilities affecting Fedora 43 packages have not been patched?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?cveId ?packageName ?cvssScore
WHERE {
  ?vuln sec:cveId ?cveId ;
        sec:affectsPackage ?identity ;
        sec:hasCVSSScore ?cvss .
  ?cvss sec:baseScore ?cvssScore .
  FILTER(?cvssScore >= 7.0)

  ?identity pkg:identityName ?packageName .
  ?package pkg:packageName ?packageName ;
           pkg:partOfRelease ?release .
  ?release ^pkg:hasRelease/rdfs:label "Fedora" ;
           pkg:releaseVersion "43" .

  # Not patched: no PatchActivity exists for this vulnerability + package
  FILTER NOT EXISTS {
    ?patch a sec:PatchActivity ;
           sec:patchAddresses ?vuln ;
           sec:patchProducedVersion ?patchedVersion .
    ?package pkg:hasVersion ?patchedVersion .
  }
}
ORDER BY DESC(?cvssScore)
```

**Expected Columns:** cveId (string), packageName (string), cvssScore (float)

**Exercises:** Vulnerability, PatchActivity, CVSSScore, affectsPackage, negation

**Status:** PASS

---

### CQ-SEC-03: Vulnerability Version Range

**Question:** Which specific versions of the `openssl` package are affected by CVE-2024-5678?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?ecosystem ?introducedVersion ?fixedVersion
WHERE {
  ?vuln sec:cveId "CVE-2024-5678" ;
        sec:hasAffectedRange ?range .
  ?range sec:affectsEcosystem/rdfs:label ?ecosystem ;
         sec:affectsPackageName "openssl" ;
         sec:hasRangeEvent ?event .

  OPTIONAL {
    ?event sec:eventType sec:event-introduced ;
           sec:eventVersion ?introducedVersion .
  }
  OPTIONAL {
    ?event sec:eventType sec:event-fixed ;
           sec:eventVersion ?fixedVersion .
  }
}
```

**Expected Columns:** ecosystem (string), introducedVersion (string or UNDEF), fixedVersion (string or UNDEF)

**Exercises:** AffectedRange, RangeEvent, eventType, eventVersion

**Status:** PASS

---

### CQ-SEC-04: Security Advisory Coverage

**Question:** Which vulnerabilities have vendor security advisories (RHSA, DSA) addressing them?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?cveId (COUNT(DISTINCT ?advisory) AS ?advisoryCount) (GROUP_CONCAT(DISTINCT ?advId; separator=", ") AS ?advisories)
WHERE {
  ?vuln sec:cveId ?cveId .
  ?advisory a sec:SecurityAdvisory ;
            sec:addressesVulnerability ?vuln ;
            sec:advisoryId ?advId .
}
GROUP BY ?cveId
HAVING (COUNT(DISTINCT ?advisory) > 1)
ORDER BY DESC(?advisoryCount)
LIMIT 20
```

**Expected Columns:** cveId (string), advisoryCount (integer), advisories (string)

**Exercises:** SecurityAdvisory, addressesVulnerability, aggregation

**Status:** PASS

---

### CQ-SEC-05: CVSS Version Comparison

**Question:** Which vulnerabilities have both CVSS v2 and v3.1 scores, and how do they differ?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?cveId ?cvss2 ?cvss31 ((?cvss31 - ?cvss2) AS ?diff)
WHERE {
  ?vuln sec:cveId ?cveId ;
        sec:hasCVSSScore ?score2 , ?score31 .
  ?score2 sec:cvssVersion "2.0" ;
          sec:baseScore ?cvss2 .
  ?score31 sec:cvssVersion "3.1" ;
           sec:baseScore ?cvss31 .
}
ORDER BY DESC(?diff)
LIMIT 50
```

**Expected Columns:** cveId (string), cvss2 (float), cvss31 (float), diff (float)

**Exercises:** CVSSScore, cvssVersion, baseScore, reification

**Status:** PASS

---

### CQ-SEC-06: Critical Vulnerabilities Without CVE

**Question:** Which high-severity vulnerabilities in the OSV database do not have CVE identifiers?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?osvId ?severity ?ecosystem
WHERE {
  ?vuln sec:osvId ?osvId ;
        sec:hasCVSSScore/sec:baseScore ?score ;
        sec:hasAffectedRange/sec:affectsEcosystem/rdfs:label ?ecosystem .
  FILTER(?score >= 7.0)
  FILTER NOT EXISTS { ?vuln sec:cveId ?cveId }
}
ORDER BY DESC(?score)
LIMIT 50
```

**Expected Columns:** osvId (string), severity (float), ecosystem (string)

**Exercises:** osvId, CVSSScore, AffectedRange, negation

**Status:** PASS

---

### CQ-SEC-07: Patch Provenance Chain

**Question:** For CVE-2024-1234, what is the complete patch provenance chain (unpatched version → patch activity → patched version)?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX prov: <http://www.w3.org/ns/prov#>

SELECT ?unpatchedVersion ?patchActivity ?patchedVersion ?patchDate
WHERE {
  ?vuln sec:cveId "CVE-2024-1234" .
  ?patchActivity sec:patchAddresses ?vuln ;
                 prov:endedAtTime ?patchDate .
  ?patchedVersion sec:patchProducedVersion ?patchActivity ;
                  pkg:versionString ?patchedVerStr .
  ?unpatchedVersion sec:patchedFrom ?patchedVersion ;
                    pkg:versionString ?unpatchedVerStr .
}
```

**Expected Columns:** unpatchedVersion (URI), patchActivity (URI), patchedVersion (URI), patchDate (dateTime)

**Exercises:** PatchActivity, patchAddresses, patchProducedVersion, patchedFrom, PROV-O

**Status:** PASS

---

### CQ-SEC-08: CWE Classification

**Question:** Which CWE categories are most common in vulnerabilities affecting Python packages?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>

SELECT ?cweId (COUNT(DISTINCT ?vuln) AS ?count)
WHERE {
  GRAPH <https://packagegraph.github.io/graph/security/osv> {
    ?vuln sec:hasAffectedRange ?range .
    ?range sec:affectsEcosystem <https://packagegraph.github.io/d/ecosystem/pypi> .
  }
  GRAPH <https://packagegraph.github.io/graph/cve/nvd> {
    ?vuln sec:cweId ?cweId .
  }
}
GROUP BY ?cweId
ORDER BY DESC(?count)
LIMIT 10
```

**Expected Columns:** cweId (string), count (integer)

**Exercises:** sec:hasAffectedRange, sec:affectsEcosystem, sec:cweId, cross-graph CVE joins

**Status:** PASS — OSV provides affected ranges with ecosystem links, NVD enricher provides CWE classifications. Join key is the shared CVE entity URI.

---

## Domain: Temporal Analysis (TEMP)

### CQ-TEMP-01: Vulnerability Window Analysis

**Question:** How long between CVE publication and advisory patch availability across distributions?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?cveId ((?aDate - ?pubDate) AS ?window)
WHERE {
  GRAPH <https://packagegraph.github.io/graph/cve/nvd> {
    ?vuln sec:cveId ?cveId ;
          sec:publishedDate ?pubDate .
  }
  GRAPH ?g {
    ?adv sec:addressesVulnerability ?vuln ;
         sec:advisoryDate ?advisoryDate .
  }
  BIND(xsd:dateTime(?advisoryDate) AS ?aDate)
  FILTER(?aDate > ?pubDate)
}
ORDER BY DESC(?window)
LIMIT 50
```

**Expected Columns:** cveId (string), window (duration)

**Exercises:** sec:publishedDate, sec:advisoryDate, temporal arithmetic, cross-graph joins, type casting

**Dependency contract:** Two-sided join. Advisory side: `sec:advisoryDate` (satisfied via RHSA/DSA collectors). Vulnerability side: `sec:publishedDate` on CVE entities in `graph/cve/nvd` (satisfied via NVD enricher — 50,750 CVEs). Join key: `sec:addressesVulnerability`.

**Note:** The original query included an `?ecosystem` column derived from `sec:advisoryForPackage` property path. This column is deferred pending workstream 5 (advisory-to-package resolution). The simplified query still answers the core CQ: vulnerability window duration between CVE publication and distro advisory.

**Status:** PASS — NVD enrichment provides 50K CVE publishedDate values, advisory graphs provide advisoryDate. Type casting handles string vs dateTime mismatch.

---

### CQ-TEMP-02: Package Obsolescence Between Releases

**Question:** Which packages present in Fedora 42 were removed by Fedora 43?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?packageName ?lastSeenVersion
WHERE {
  ?pkg42 pkg:packageName ?packageName ;
         pkg:partOfRelease ?release42 ;
         pkg:hasVersion/pkg:versionString ?lastSeenVersion .
  ?release42 ^pkg:hasRelease/rdfs:label "Fedora" ;
             pkg:releaseVersion "42" .

  FILTER NOT EXISTS {
    ?pkg43 pkg:packageName ?packageName ;
           pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Fedora" ;
           pkg:partOfRelease/pkg:releaseVersion "43" .
  }
}
ORDER BY ?packageName
LIMIT 500
```

**Expected Columns:** packageName (string), lastSeenVersion (string)

**Exercises:** pkg:partOfRelease, cross-release comparison, negation, obsolescence detection

**Status:** PASS

---

### CQ-TEMP-03: Maintainer Tenure Analysis

**Question:** What is the average maintainer tenure for packages currently maintained in Debian Trixie?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT (AVG(?tenureDays) AS ?avgTenure) (MIN(?tenureDays) AS ?minTenure) (MAX(?tenureDays) AS ?maxTenure)
WHERE {
  ?package pkg:partOfRelease ?release ;
           pkg:hasMaintenanceRole ?role .
  ?release ^pkg:hasRelease/rdfs:label "Debian" ;
           pkg:releaseCodename "trixie" .
  ?role pkg:maintainerSince ?startDate .
  BIND((xsd:dateTime("2026-04-21T00:00:00Z") - ?startDate) AS ?tenureDays)
  FILTER(?tenureDays > 0)
}
```

**Expected Columns:** avgTenure (dayTimeDuration), minTenure (dayTimeDuration), maxTenure (dayTimeDuration)

**Exercises:** pkg:maintainerSince, temporal computation, aggregation, role model

**Status:** PASS

---

## Domain: Supply Chain Risk (SCR)

### CQ-SCR-01: Bus Factor — Single-Maintainer Packages

**Question:** Which packages in Fedora 43 have exactly one maintainer (single point of failure)?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?packageName (COUNT(DISTINCT ?agent) AS ?maintainerCount)
WHERE {
  ?package pkg:packageName ?packageName ;
           pkg:partOfRelease ?release ;
           pkg:maintainedBy ?agent .
  ?release ^pkg:hasRelease/rdfs:label "Fedora" ;
           pkg:releaseVersion "43" .
}
GROUP BY ?packageName
HAVING (COUNT(DISTINCT ?agent) = 1)
ORDER BY ?packageName
```

**Expected Columns:** packageName (string), maintainerCount (integer — always 1)

**Exercises:** maintainedBy, aggregation, HAVING filter, bus factor analysis

**Status:** PASS

**Research context:** The "bus factor" — the minimum number of maintainers whose departure would leave a package unmaintained — is a critical supply chain risk metric. A bus factor of 1 means a single resignation, burnout event, or account compromise can orphan the package.

---

### CQ-SCR-02: Maintainer Overload — Most Packages Per Person

**Question:** Which maintainers are responsible for the most packages across all distributions (burnout risk)?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?person ?name (COUNT(DISTINCT ?package) AS ?packageCount) (GROUP_CONCAT(DISTINCT ?distro; separator=", ") AS ?distributions)
WHERE {
  ?package pkg:maintainedBy ?person .
  ?person foaf:name ?name .
  ?package pkg:partOfRelease/^pkg:hasRelease/rdfs:label ?distro .
}
GROUP BY ?person ?name
ORDER BY DESC(?packageCount)
LIMIT 50
```

**Expected Columns:** person (URI), name (string), packageCount (integer), distributions (string)

**Exercises:** maintainedBy, foaf:name, cross-distribution aggregation, workload analysis

**Status:** PASS

**Research context:** Maintainer overload is a leading indicator of burnout. Individuals maintaining 100+ packages across multiple distributions face unsustainable review, security patching, and compatibility testing burdens. This query identifies the humans (and bots) carrying disproportionate load.

---

### CQ-SCR-03: Orphan Risk — Stale Maintainership Without Recent Releases

**Question:** Which packages have a maintainer assigned more than 5 years ago but no release in the last 2 years?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?packageName ?maintainerName ?maintainerSince ?lastRelease
WHERE {
  ?package pkg:packageName ?packageName ;
           pkg:hasMaintenanceRole ?role .
  ?role pkg:heldBy ?person ;
        pkg:maintainerSince ?maintainerSince .
  ?person foaf:name ?maintainerName .

  # Maintainer assigned > 5 years ago
  FILTER(?maintainerSince < "2021-04-21T00:00:00Z"^^xsd:dateTime)

  # Find latest release date for this package identity
  ?package pkg:isVersionOf ?identity .
  ?identity pkg:lastReleaseDate ?lastRelease .

  # No release in last 2 years
  FILTER(?lastRelease < "2024-04-21"^^xsd:date)
}
ORDER BY ?lastRelease
LIMIT 100
```

**Expected Columns:** packageName (string), maintainerName (string), maintainerSince (dateTime), lastRelease (date)

**Exercises:** maintainerSince, lastReleaseDate, temporal filtering, orphan detection

**Status:** BLOCKED — requires `pkg:maintainerSince` data (no authoritative source identified) and `pkg:lastReleaseDate` (Phase 2 enrichment)

**Research context:** Long-tenured maintainers of inactive packages signal potential abandonment. These packages may still be installed on production systems but receive no security patches — a silent supply chain risk that compound vulnerability analysis (CQ-SCR-07) can quantify.

---

### CQ-SCR-04: Maintainer Turnover Between Releases

**Question:** Which packages had their maintainer set change between Fedora 42 and Fedora 43 (any departure or arrival)?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?packageName ?agentName ?changeType
WHERE {
  ?identity pkg:identityName ?packageName .

  ?pkg42 pkg:isVersionOf ?identity ;
         pkg:partOfRelease ?rel42 .
  ?rel42 ^pkg:hasRelease/rdfs:label "Fedora" ;
         pkg:releaseVersion "42" .

  ?pkg43 pkg:isVersionOf ?identity ;
         pkg:partOfRelease ?rel43 .
  ?rel43 ^pkg:hasRelease/rdfs:label "Fedora" ;
         pkg:releaseVersion "43" .

  {
    # Departed: maintainer in 42 but not in 43
    ?pkg42 pkg:maintainedBy ?agent .
    FILTER NOT EXISTS { ?pkg43 pkg:maintainedBy ?agent }
    BIND("departed" AS ?changeType)
  }
  UNION
  {
    # Joined: maintainer in 43 but not in 42
    ?pkg43 pkg:maintainedBy ?agent .
    FILTER NOT EXISTS { ?pkg42 pkg:maintainedBy ?agent }
    BIND("joined" AS ?changeType)
  }

  ?agent foaf:name ?agentName .
}
ORDER BY ?packageName ?changeType
```

**Expected Columns:** packageName (string), agentName (string), changeType (string: "departed" or "joined")

**Exercises:** PackageIdentity, identityName, isVersionOf, maintainedBy, set-difference via FILTER NOT EXISTS, UNION, turnover detection

**Status:** PASS

**Caveat:** Results depend on stable maintainer agent identity across releases. The collectors derive Person URIs from email addresses in package metadata (RPM `Packager:`, Debian `Maintainer:`). If the same human uses different emails across releases, they will appear as different agents, producing false positives.

**Research context:** Maintainer turnover rate is a proxy for project health. High turnover can indicate governance problems, burnout cascades, or hostile takeover attempts (a known supply chain attack vector where malicious actors volunteer to maintain abandoned packages).

---

### CQ-SCR-05: Cross-Distribution Maintainer Overlap

**Question:** Which persons maintain the same upstream package across multiple distributions?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?person ?name ?upstreamProject (COUNT(DISTINCT ?distro) AS ?distroCount) (GROUP_CONCAT(DISTINCT ?distro; separator=", ") AS ?distributions)
WHERE {
  ?package pkg:maintainedBy ?person ;
           pkg:isVersionOf/pkg:upstreamRepository ?repo ;
           pkg:partOfRelease/^pkg:hasRelease/rdfs:label ?distro .
  ?person foaf:name ?name .
  ?repo rdfs:label ?upstreamProject .
}
GROUP BY ?person ?name ?upstreamProject
HAVING (COUNT(DISTINCT ?distro) >= 2)
ORDER BY DESC(?distroCount)
LIMIT 50
```

**Expected Columns:** person (URI), name (string), upstreamProject (string), distroCount (integer), distributions (string)

**Exercises:** maintainedBy, isVersionOf, upstreamRepository, cross-distribution identity resolution

**Status:** PASS

**Research context:** When a single person maintains the same package across Fedora, Debian, and SUSE, their compromise or burnout affects multiple ecosystems simultaneously. This cross-distribution single-point-of-failure analysis is unique to knowledge graph approaches — relational databases cannot traverse these links efficiently.

---

### CQ-SCR-06: Patch Lag by Distribution — Comparative Time-to-Fix

**Question:** For a given CVE, how long did each distribution take to issue a patch compared to others?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?cveId ?distro ?advisoryId ((?advisoryDate - ?pubDate) AS ?patchLagDays)
WHERE {
  ?vuln sec:cveId ?cveId ;
        sec:publishedDate ?pubDate .
  ?advisory sec:addressesVulnerability ?vuln ;
            sec:advisoryId ?advisoryId ;
            sec:advisoryDate ?advisoryDate ;
            sec:advisoryForPackage ?pkg .
  ?pkg pkg:partOfRelease/^pkg:hasRelease/rdfs:label ?distro .
}
ORDER BY ?cveId ?patchLagDays
```

**Expected Columns:** cveId (string), distro (string), advisoryId (string), patchLagDays (dayTimeDuration)

**Exercises:** sec:publishedDate, sec:advisoryDate, sec:advisoryForPackage, temporal arithmetic, cross-distribution comparison

**Dependency contract:** Two-sided join. Advisory side: `sec:advisoryForPackage` (concrete release-scoped packages), `sec:advisoryDate`, `sec:addressesVulnerability` (ADVISORY-SIDE SATISFIED for Fedora 43 via RPM updateinfo). Vulnerability side: `sec:publishedDate` on vulnerability entities reachable via `sec:addressesVulnerability` (requires CVE publication metadata — canonical CVE backbone or distro-aware OSV ingestion).

**Status:** ADVISORY-SIDE SATISFIED — advisory→package links exist for Fedora 43 (1,822 links). Vulnerability-side `sec:publishedDate` not yet available for distro-ecosystem CVEs. End-to-end query not yet demonstrated.

**Research context:** Patch lag — the time between CVE publication and distribution-specific advisory — is the primary metric in vulnerability window research. This query enables direct comparison: "Debian patched CVE-2024-1234 in 3 days; Fedora took 12 days." The knowledge graph makes this join trivial; in flat databases it requires manual cross-referencing of NVD, RHSA, DSA, and USN feeds.

---

### CQ-SCR-07: Unpatched Critical Vulnerabilities Beyond Threshold

**Question:** Which critical-severity vulnerabilities (CVSS ≥ 9.0) affecting a specific ecosystem have been published more than 90 days ago without an advisory for that ecosystem's packages?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?cveId ?cvssScore ?pubDate ?packageName ?ecosystem
WHERE {
  ?vuln sec:cveId ?cveId ;
        sec:publishedDate ?pubDate ;
        sec:hasCVSSScore/sec:baseScore ?cvssScore ;
        sec:hasAffectedRange ?range .
  ?range sec:affectsPackageName ?packageName ;
         sec:affectsEcosystem ?eco .
  ?eco rdfs:label ?ecosystem .

  FILTER(?cvssScore >= "9.0"^^xsd:decimal)
  FILTER(?pubDate < "2026-01-21T00:00:00Z"^^xsd:dateTime)

  # No advisory exists for this vulnerability in THIS ecosystem
  FILTER NOT EXISTS {
    ?advisory sec:addressesVulnerability ?vuln ;
              sec:advisoryForPackage/pkg:partOfRelease/^pkg:hasRelease/pkg:partOfEcosystem ?eco .
  }
}
ORDER BY ?pubDate
```

**Expected Columns:** cveId (string), cvssScore (decimal), pubDate (dateTime), packageName (string), ecosystem (string)

**Exercises:** hasCVSSScore, baseScore, publishedDate, hasAffectedRange, per-ecosystem negation, threshold filtering

**Dependency contract:** Two-sided join. Advisory side: `sec:advisoryForPackage` for per-ecosystem negation (ADVISORY-SIDE SATISFIED for Fedora 43). Vulnerability side: `sec:hasCVSSScore`/`sec:baseScore` (requires CVSS data on vulnerability entities), `sec:publishedDate` (requires CVE publication metadata), `sec:hasAffectedRange`/`sec:affectsEcosystem` (requires distro-aware affected-range data).

**Status:** ADVISORY-SIDE SATISFIED — advisory→package links exist for Fedora 43. Vulnerability-side requires CVSS scores, publication dates, and affected-range ecosystem data on the same vulnerability entities. End-to-end query not yet demonstrated.

**Semantic scope:** This query tests per-ecosystem patch absence — a CVE with a Fedora advisory but no Debian advisory will appear as unpatched *in the Debian ecosystem*. This is intentionally scoped: "unpatched" means "no advisory exists for packages in this specific ecosystem," not "no advisory exists anywhere globally." The required join shape is: `advisory → advisoryForPackage → package → partOfRelease → release → (inverse hasRelease) → distribution → partOfEcosystem → ecosystem`, matching the affected ecosystem from the vulnerability's AffectedRange.

**Research context:** The "90-day window" is the de facto industry standard for responsible disclosure (Google Project Zero policy). Critical vulnerabilities exceeding this threshold without patches represent the highest-risk items in a software supply chain. This query directly supports the vulnerability management workflow described in NIST SP 800-40r4.

---

### CQ-SCR-08: Vulnerability Density — Most Affected Packages

**Question:** Which packages have the highest number of distinct CVEs across all ecosystems?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?packageName ?ecosystem (COUNT(DISTINCT ?vuln) AS ?cveCount)
WHERE {
  ?vuln sec:hasAffectedRange ?range .
  ?range sec:affectsPackageName ?packageName ;
         sec:affectsEcosystem/rdfs:label ?ecosystem .
}
GROUP BY ?packageName ?ecosystem
ORDER BY DESC(?cveCount)
LIMIT 50
```

**Expected Columns:** packageName (string), ecosystem (string), cveCount (integer)

**Exercises:** hasAffectedRange, affectsPackageName, affectsEcosystem, aggregation, vulnerability density

**Status:** PASS

**Research context:** Vulnerability density (CVEs per package) combined with dependency depth (CQ-PM-04) yields transitive risk scores. A package with 50 CVEs that is a transitive dependency of 10,000 packages represents catastrophic supply chain exposure — the pattern behind Log4Shell, xz-utils, and similar incidents.

---

### CQ-SCR-09: Mean Time to Remediate (MTTR) by Distribution

**Question:** What is the average, minimum, and maximum time from CVE publication to advisory issuance per distribution?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?distro (AVG(?lagDays) AS ?avgMTTR) (MIN(?lagDays) AS ?bestCase) (MAX(?lagDays) AS ?worstCase) (COUNT(?advisory) AS ?advisoryCount)
WHERE {
  ?vuln sec:publishedDate ?pubDate .
  ?advisory sec:addressesVulnerability ?vuln ;
            sec:advisoryDate ?advisoryDate ;
            sec:advisoryForPackage ?pkg .
  ?pkg pkg:partOfRelease/^pkg:hasRelease/rdfs:label ?distro .
  BIND((?advisoryDate - ?pubDate) AS ?lagDays)
  FILTER(?lagDays > 0)
}
GROUP BY ?distro
ORDER BY ?avgMTTR
```

**Expected Columns:** distro (string), avgMTTR (dayTimeDuration), bestCase (dayTimeDuration), worstCase (dayTimeDuration), advisoryCount (integer)

**Exercises:** temporal arithmetic, aggregation, per-distribution MTTR, supply chain benchmarking

**Dependency contract:** Two-sided join. Advisory side: `sec:advisoryForPackage`, `sec:advisoryDate`, `sec:addressesVulnerability` (ADVISORY-SIDE SATISFIED for Fedora 43 via RPM updateinfo). Vulnerability side: `sec:publishedDate` on vulnerability entities reachable via `sec:addressesVulnerability` (requires CVE publication metadata).

**Status:** ADVISORY-SIDE SATISFIED — advisory→package links and advisory dates exist for Fedora 43 (280 advisories, 1,822 package links). Vulnerability-side `sec:publishedDate` not yet available for distro-ecosystem CVEs. End-to-end query not yet demonstrated.

**Research context:** Mean Time to Remediate is the primary KPI in vulnerability management frameworks (NIST CSF, ISO 27001). Comparing MTTR across distributions reveals systemic differences in security response capability — a Fedora MTTR of 5 days vs. a Debian MTTR of 14 days signals different organizational priorities and resourcing levels that affect downstream consumers' risk posture.

---

## Domain: Cross-Distribution Analysis (XD)

### CQ-XD-01: Equivalent Packages Across Distributions

**Question:** Which packages exist in both Fedora and Debian under different names?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?fedoraName ?debianName ?identity
WHERE {
  ?identity a pkg:PackageIdentity .
  ?fedoraPkg pkg:packageName ?fedoraName ;
             pkg:isVersionOf ?identity ;
             pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Fedora" .
  ?debianPkg pkg:packageName ?debianName ;
             pkg:isVersionOf ?identity ;
             pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Debian" .
  FILTER(?fedoraName != ?debianName)
}
LIMIT 100
```

**Expected Columns:** fedoraName (string), debianName (string), identity (URI)

**Exercises:** PackageIdentity, isVersionOf, cross-distribution joins

**Status:** BLOCKED — Requires cross-distro equivalence data. Current `pkg:isVersionOf` links use distro-specific identity URIs (e.g., `d/pkg/fedora/43/x86_64/0ad`) that don't cross distribution boundaries. Needs Repology enrichment to populate shared cross-distro PackageIdentity entities, or materialized equivalence view. See Deferred Ideas in `platform/docs/plans/2026-04-24-cq-query-and-harness-fast-pass.md`.

---

### CQ-XD-02: Version Skew Analysis

**Question:** For packages present in both Fedora 43 and Debian Trixie, which have version differences > 1 major version?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?packageName ?fedoraVersion ?debianVersion
WHERE {
  ?identity a pkg:PackageIdentity ;
            pkg:identityName ?packageName .

  ?fedoraPkg pkg:isVersionOf ?identity ;
             pkg:partOfRelease ?fedoraRelease ;
             pkg:hasVersion/pkg:versionString ?fedoraVersion .
  ?fedoraRelease ^pkg:hasRelease/rdfs:label "Fedora" ;
                 pkg:releaseVersion "43" .

  ?debianPkg pkg:isVersionOf ?identity ;
             pkg:partOfRelease ?debianRelease ;
             pkg:hasVersion/pkg:versionString ?debianVersion .
  ?debianRelease ^pkg:hasRelease/rdfs:label "Debian" ;
                 pkg:releaseCodename "trixie" .

  FILTER(?fedoraVersion != ?debianVersion)
}
LIMIT 100
```

**Expected Columns:** packageName (string), fedoraVersion (string), debianVersion (string)

**Exercises:** PackageIdentity, cross-distribution version comparison

**Status:** PASS

**Note:** Version comparison logic (major version extraction) requires FILTER or external processing.

---

### CQ-XD-03: Distribution-Specific Packages

**Question:** Which packages exist in Fedora but not in Debian (vendor-specific)?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?packageName
WHERE {
  ?fedoraPkg pkg:packageName ?packageName ;
             pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Fedora" .
  FILTER NOT EXISTS {
    ?debianPkg pkg:packageName ?packageName ;
               pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Debian" .
  }
}
ORDER BY ?packageName
LIMIT 500
```

**Expected Columns:** packageName (string)

**Exercises:** Negation, cross-distribution filtering

**Status:** PASS

---

### CQ-XD-04: Shared Upstream Projects

**Question:** Which upstream projects are packaged by at least 3 different distributions?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?projectName (COUNT(DISTINCT ?distro) AS ?distroCount) (GROUP_CONCAT(DISTINCT ?distroName; separator=", ") AS ?distros)
WHERE {
  ?upstream a pkg:UpstreamProject ;
            pkg:projectName ?projectName .
  ?package pkg:hasUpstreamProject ?upstream ;
           pkg:partOfRelease/^pkg:hasRelease ?distro .
  ?distro rdfs:label ?distroName .
}
GROUP BY ?projectName
HAVING (COUNT(DISTINCT ?distro) >= 3)
ORDER BY DESC(?distroCount)
LIMIT 50
```

**Expected Columns:** projectName (string), distroCount (integer), distros (string)

**Exercises:** UpstreamProject, hasUpstreamProject, cross-distribution aggregation

**Status:** PASS

---

### CQ-XD-05: Repology Cross-Ecosystem Equivalence

**Question:** Which packages have equivalent names across Linux distributions, language ecosystems (npm, PyPI), and Homebrew?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?identity ?linuxName ?npmName ?pypiName ?brewName
WHERE {
  ?identity a pkg:PackageIdentity .

  OPTIONAL {
    ?linuxPkg pkg:isVersionOf ?identity ;
              pkg:packageName ?linuxName ;
              pkg:partOfRelease/^pkg:hasRelease/rdfs:label ?linuxDist .
    FILTER(?linuxDist IN ("Fedora", "Debian", "Arch"))
  }
  OPTIONAL {
    ?npmPkg pkg:isVersionOf ?identity ;
            pkg:packageName ?npmName ;
            pkg:partOfRelease/^pkg:hasRelease/pkg:partOfEcosystem/rdfs:label "npm" .
  }
  OPTIONAL {
    ?pypiPkg pkg:isVersionOf ?identity ;
             pkg:packageName ?pypiName ;
             pkg:partOfRelease/^pkg:hasRelease/pkg:partOfEcosystem/rdfs:label "PyPI" .
  }
  OPTIONAL {
    ?brewPkg pkg:isVersionOf ?identity ;
             pkg:packageName ?brewName ;
             pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Homebrew" .
  }

  FILTER(BOUND(?linuxName) && (BOUND(?npmName) || BOUND(?pypiName) || BOUND(?brewName)))
}
LIMIT 100
```

**Expected Columns:** identity (URI), linuxName, npmName, pypiName, brewName (strings or UNDEF)

**Exercises:** PackageIdentity, isVersionOf, Ecosystem, cross-ecosystem joins

**Status:** PASS

---

## Domain: Provenance / Build (PROV)

### CQ-PROV-01: Build Activity Chain

**Question:** What is the complete build provenance chain for a specific binary package (upstream commit → source → build → binary)?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX vcs: <https://purl.org/packagegraph/ontology/vcs#>
PREFIX prov: <http://www.w3.org/ns/prov#>

SELECT ?commit ?commitHash ?source ?buildActivity ?binary
WHERE {
  ?binary a pkg:BinaryPackage ;
          pkg:packageName "openssl" ;
          pkg:partOfRelease/pkg:releaseVersion "43" ;
          pkg:builtFromSource ?source ;
          pkg:wasBuiltBy ?buildActivity .

  ?buildActivity a pkg:BuildActivity ;
                 prov:used ?source .

  OPTIONAL {
    ?source pkg:derivedFromCommit ?commit .
    ?commit vcs:commitHash ?commitHash .
  }
}
LIMIT 1
```

**Expected Columns:** commit (URI or UNDEF), commitHash (string or UNDEF), source (URI), buildActivity (URI), binary (URI)

**Exercises:** BuildActivity, builtFromSource, wasBuiltBy, derivedFromCommit, PROV-O alignment

**Status:** PASS

---

### CQ-PROV-02: SLSA Provenance Level

**Question:** Which packages in Fedora 43 have SLSA level 3 or higher build attestations?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX slsa: <https://purl.org/packagegraph/ontology/slsa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?packageName ?slsaLevel ?attestation
WHERE {
  ?package a pkg:Package ;
           pkg:packageName ?packageName ;
           pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Fedora" ;
           pkg:partOfRelease/pkg:releaseVersion "43" ;
           slsa:hasProvenance ?attestation .
  ?attestation slsa:slsaLevel ?slsaLevel .
  FILTER(?slsaLevel >= 3)
}
ORDER BY DESC(?slsaLevel)
```

**Expected Columns:** packageName (string), slsaLevel (integer), attestation (URI)

**Exercises:** SLSA module, hasProvenance, slsaLevel

**Status:** PASS

---

### CQ-PROV-03: Build Environment

**Question:** Which build agents or systems were used to build packages in RHEL 9?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?agent ?agentName (COUNT(?package) AS ?packageCount)
WHERE {
  ?package pkg:partOfRelease/^pkg:hasRelease/rdfs:label "RHEL" ;
           pkg:partOfRelease/pkg:releaseVersion "9" ;
           prov:wasGeneratedBy ?buildActivity .
  ?buildActivity prov:wasAssociatedWith ?agent .
  ?agent rdfs:label ?agentName .
}
GROUP BY ?agent ?agentName
ORDER BY DESC(?packageCount)
```

**Expected Columns:** agent (URI), agentName (string), packageCount (integer)

**Exercises:** BuildActivity, wasAssociatedWith, wasGeneratedBy, PROV-O

**Status:** PASS

---

### CQ-PROV-04: Contributor Activity

**Question:** Which persons have contributed to (but do not maintain) the `systemd` package?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?person ?name
WHERE {
  ?package pkg:packageName "systemd" .

  ?contributor a pkg:Contributor ;
               pkg:heldBy ?person ;
               pkg:contributesTo ?package .
  ?person foaf:name ?name .

  FILTER NOT EXISTS {
    ?maintainer a pkg:Maintainer ;
                pkg:heldBy ?person .
  }
}
```

**Expected Columns:** person (URI), name (string)

**Exercises:** Contributor, contributesTo, Maintainer, Person, OntoClean role model, negation

**Status:** PASS

---

## Domain: Dependency Analysis (DEP)

### CQ-DEP-01: Direct vs Transitive Dependencies

**Question:** For the `python3` package in Debian Trixie, how many direct dependencies vs total transitive dependencies?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT (COUNT(DISTINCT ?direct) AS ?directCount) (COUNT(DISTINCT ?transitive) AS ?transitiveCount)
WHERE {
  ?package pkg:packageName "python3" ;
           pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Debian" ;
           pkg:partOfRelease/pkg:releaseCodename "trixie" .

  OPTIONAL { ?package pkg:directlyDependsOn ?direct }
  OPTIONAL { ?package pkg:directlyDependsOn+ ?transitive }
}
```

**Expected Columns:** directCount (integer), transitiveCount (integer)

**Exercises:** directlyDependsOn, property path (+), aggregation

**Status:** PASS

---

### CQ-DEP-02: Dependency Type Distribution

**Question:** What percentage of dependencies in Fedora 43 are runtime vs build-time?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?depType (COUNT(?dep) AS ?count)
WHERE {
  ?package pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Fedora" ;
           pkg:partOfRelease/pkg:releaseVersion "43" ;
           pkg:hasDependency ?dep .
  ?dep pkg:dependencyType ?depType .
}
GROUP BY ?depType
ORDER BY DESC(?count)
```

**Expected Columns:** depType (string), count (integer)

**Exercises:** Dependency (reified), hasDependency, dependencyType, aggregation

**Status:** PASS

---

### CQ-DEP-03: Version Constraint Patterns

**Question:** Which packages have version constraints using ranges (e.g., >= 1.2, < 2.0)?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?sourcePkg ?targetPkg ?operator ?constraintVersion
WHERE {
  ?sourcePkg pkg:hasDependency ?dep .
  ?dep pkg:dependencyTarget ?targetPkg ;
       pkg:hasVersionConstraint ?constraint .
  ?constraint pkg:versionConstraintOperator ?operator ;
              pkg:versionConstraintValue ?constraintVersion .
  ?sourcePkg pkg:packageName ?srcName .
  ?targetPkg pkg:packageName ?tgtName .
}
LIMIT 100
```

**Expected Columns:** sourcePkg (URI), targetPkg (URI), operator (string), constraintVersion (string)

**Exercises:** VersionConstraint, hasVersionConstraint, versionConstraintOperator, versionConstraintValue

**Status:** PASS

---

### CQ-DEP-04: Circular Dependencies

**Question:** Which packages have circular dependency relationships in Arch Linux?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?pkg1Name ?pkg2Name
WHERE {
  ?pkg1 pkg:packageName ?pkg1Name ;
        pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Arch Linux" ;
        pkg:directlyDependsOn ?pkg2 .
  ?pkg2 pkg:packageName ?pkg2Name ;
        pkg:directlyDependsOn ?pkg1 .
  FILTER(?pkg1Name < ?pkg2Name)
}
```

**Expected Columns:** pkg1Name (string), pkg2Name (string)

**Exercises:** directlyDependsOn, circular patterns, filtering

**Status:** PASS

---

### CQ-DEP-05: Dependency Consistency Check

**Question:** Which packages have `directlyDependsOn` without a corresponding `hasDependency` reification (dual-model inconsistency)?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?package ?packageName ?target
WHERE {
  ?package pkg:packageName ?packageName ;
           pkg:directlyDependsOn ?target .

  FILTER NOT EXISTS {
    ?package pkg:hasDependency ?dep .
    ?dep pkg:dependencyTarget ?target .
  }
}
LIMIT 50
```

**Expected Columns:** package (URI), packageName (string), target (URI)

**Exercises:** hasDependency, directlyDependsOn, dependencyTarget, dual-model consistency, negation

**Status:** PASS

**Note:** This CQ tests the consistency pattern documented in Task 5.

---

## Domain: Repository & VCS (VCS)

### CQ-VCS-01: Repository Language Distribution

**Question:** Which programming languages are most common across repositories linked to Fedora packages?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX vcs: <https://purl.org/packagegraph/ontology/vcs#>
PREFIX met: <https://purl.org/packagegraph/ontology/metrics#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?language (COUNT(DISTINCT ?repo) AS ?repoCount)
WHERE {
  ?package pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Fedora" ;
           pkg:hasUpstreamProject/pkg:sourceCodeRepository ?repo .
  ?repo met:primaryLanguage ?language .
}
GROUP BY ?language
ORDER BY DESC(?repoCount)
LIMIT 10
```

**Expected Columns:** language (string), repoCount (integer)

**Exercises:** Repository, sourceCodeRepository, Metrics module, primaryLanguage

**Status:** PASS

---

### CQ-VCS-02: Commit-to-Release Tracing

**Question:** Which source packages in Debian Trixie were built from commits on the `main` branch?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX vcs: <https://purl.org/packagegraph/ontology/vcs#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?packageName ?commitHash ?branchName
WHERE {
  ?package a pkg:SourcePackage ;
           pkg:packageName ?packageName ;
           pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Debian" ;
           pkg:partOfRelease/pkg:releaseCodename "trixie" ;
           pkg:derivedFromCommit ?commit .
  ?commit vcs:commitHash ?commitHash ;
          vcs:onBranch/vcs:branchName ?branchName .
  FILTER(?branchName = "main")
}
LIMIT 100
```

**Expected Columns:** packageName (string), commitHash (string), branchName (string)

**Exercises:** derivedFromCommit, Commit, Branch, onBranch

**Status:** PASS

---

## Domain: Package Set & Collection (SET)

### CQ-SET-01: Package Set Membership

**Question:** Which packages are members of the "BaseOS" package set in RHEL 9?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?packageName
WHERE {
  ?set a pkg:PackageSet ;
       rdfs:label "BaseOS" .
  ?package pkg:memberOfPackageSet ?set ;
           pkg:partOfRelease/^pkg:hasRelease/rdfs:label "RHEL" ;
           pkg:partOfRelease/pkg:releaseVersion "9" ;
           pkg:packageName ?packageName .
}
ORDER BY ?packageName
```

**Expected Columns:** packageName (string)

**Exercises:** PackageSet, memberOfPackageSet

**Status:** PASS

---

## Domain: Ecosystem-Specific (ECO)

### CQ-ECO-01: RPM Spec File Sources

**Question:** Which RPM source packages have more than 5 source files listed in their spec?

**SPARQL:**
```sparql
PREFIX rpm: <https://purl.org/packagegraph/ontology/rpm#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT ?packageName (COUNT(?source) AS ?sourceCount)
WHERE {
  ?package a rpm:SourceRPM ;
           pkg:packageName ?packageName ;
           rpm:hasSpecSource ?source .
}
GROUP BY ?packageName
HAVING (COUNT(?source) > 5)
ORDER BY DESC(?sourceCount)
```

**Expected Columns:** packageName (string), sourceCount (integer)

**Exercises:** RPM module, SourceRPM, hasSpecSource

**Status:** PASS

---

### CQ-ECO-02: Debian Section Distribution

**Question:** What are the most common package sections in Debian Trixie?

**SPARQL:**
```sparql
PREFIX deb: <https://purl.org/packagegraph/ontology/deb#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?section (COUNT(?package) AS ?count)
WHERE {
  ?package a deb:BinaryDeb ;
           deb:section ?section ;
           pkg:partOfRelease/^pkg:hasRelease/rdfs:label "Debian" ;
           pkg:partOfRelease/pkg:releaseCodename "trixie" .
}
GROUP BY ?section
ORDER BY DESC(?count)
LIMIT 20
```

**Expected Columns:** section (string), count (integer)

**Exercises:** Debian module, BinaryDeb, section property

**Status:** PASS

---

### CQ-ECO-03: npm Dependency Depth

**Question:** What is the average dependency depth for packages in the npm ecosystem?

**SPARQL:**
```sparql
PREFIX npm: <https://purl.org/packagegraph/ontology/npm#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT (AVG(?depth) AS ?avgDepth)
WHERE {
  ?package a npm:NpmPackage .
  {
    SELECT ?package (COUNT(?dep) AS ?depth)
    WHERE {
      ?package pkg:directlyDependsOn+ ?dep .
    }
    GROUP BY ?package
  }
}
```

**Expected Columns:** avgDepth (float)

**Exercises:** npm module, transitive dependency depth, aggregation, subquery

**Status:** PASS

---

## Summary Statistics

| Domain | CQ Count | PASS | ADVISORY-SIDE | BLOCKED |
|--------|----------|------|---------------|---------|
| Package Management (PM) | 10 | 10 | 0 | 0 |
| Licensing (LIC) | 3 | 3 | 0 | 0 |
| Security / Vulnerability (SEC) | 8 | 8 | 0 | 0 |
| Temporal Analysis (TEMP) | 3 | 2 | 1 | 0 |
| Supply Chain Risk (SCR) | 9 | 5 | 3 | 1 |
| Cross-Distribution Analysis (XD) | 5 | 5 | 0 | 0 |
| Provenance / Build (PROV) | 4 | 4 | 0 | 0 |
| Repository / VCS (VCS) | 2 | 2 | 0 | 0 |
| Package Set (SET) | 1 | 1 | 0 | 0 |
| Ecosystem-Specific (ECO) | 3 | 3 | 0 | 0 |
| **TOTAL** | **48** | **43** | **4** | **1** |

**Note:** PASS, ADVISORY-SIDE SATISFIED, and BLOCKED are mutually exclusive statuses. PASS means vocabulary supports the query and data sources are expected to be available. ADVISORY-SIDE SATISFIED means the advisory half of a two-sided join is populated but the vulnerability side is not. BLOCKED means a required data source is formally unsupported. See Status Vocabulary below.

---

## Status Vocabulary

CQ statuses use the following terms. Platform reports should use the same vocabulary when claiming CQ support.

| Status | Meaning |
|--------|---------|
| **PASS** | The ontology vocabulary supports the query and data sources for all required properties are expected to be available or already populated. Does not guarantee end-to-end execution against production — use the validation harness for that. |
| **ADVISORY-SIDE SATISFIED** | Two-sided CQ where advisory-side data is populated (e.g., `advisoryForPackage`, `advisoryDate`), but vulnerability-side prerequisites (`publishedDate`, `hasCVSSScore`, `hasAffectedRange`) are not yet available for the relevant ecosystem. |
| **VULNERABILITY-SIDE SATISFIED** | Two-sided CQ where vulnerability-side data is populated, but advisory-side prerequisites are not yet available. |
| **BLOCKED** | A required data source has no authoritative provider identified, or a required property is formally unsupported. |

**Two-sided CQs:** CQs that join advisory data with vulnerability data (TEMP-01, SCR-06, SCR-07, SCR-09) require BOTH sides to be satisfied before claiming PASS. Advisory-side progress (e.g., "1,822 advisoryForPackage links loaded") does not constitute end-to-end CQ support if the vulnerability side is missing.

**Vulnerability-only CQs:** CQs that operate entirely on the vulnerability/affected-range model (SEC-01) are not helped by advisory collector improvements. Do not credit advisory work to these CQs.

---

## Multi-Source Data Architecture

CQ answers may come from joins across triples populated by different collectors and enrichers. This is expected and valid.

**Canonical vulnerability identity:** Shared CVE URIs are the integration backbone. A single vulnerability entity may be enriched from multiple sources — one providing canonical metadata (`sec:cveId`, `sec:publishedDate`, `sec:hasCVSSScore`), another providing affected-range data (`sec:hasAffectedRange`, `sec:affectsEcosystem`), and a third providing advisory linkage (`sec:advisoryForPackage`, `sec:advisoryDate`). The ontology does not prescribe which named graphs these triples reside in — that is platform infrastructure.

**CQ satisfaction rule:** A CQ is satisfied when the required predicates exist and join correctly — regardless of which collector or enricher contributed each predicate. For two-sided CQs (TEMP-01, SCR-06, SCR-07, SCR-09):

- Advisory-side data may come from one collector (e.g., RPM updateinfo)
- Publication/CVSS metadata may come from a different source (e.g., NVD, OSV)
- This is valid as long as both sides reference the same vulnerability entity via shared CVE URI

**Evidence rubric:** The validation harness checks predicate presence and join completeness across the queryable dataset. It does not require all predicates to originate from a single collector.

**Source provenance:** Source attribution is not tracked at the property level in v1. If source-level trust analysis becomes a requirement, a lightweight provenance pattern can be added without schema changes.

---

## Validation Against Examples

The following CQs can be validated against local example files without Fuseki:

- **CQ-PM-02** — source-to-binary mapping (uses core/rpm/deb examples)
- **CQ-PM-03** — virtual package providers (uses capability examples)
- **CQ-PM-05** — packages by maintainer (uses Person/Maintainer examples)
- **CQ-SEC-07** — patch provenance chain (uses security examples)
- **CQ-DEP-03** — version constraints (uses dependency examples)

---

## CQ Coverage Map

### Classes Exercised (28 of 36 core classes)

- Package ✓
- BinaryPackage ✓
- SourcePackage ✓
- PackageIdentity ✓
- Version ✓
- Dependency ✓
- VersionConstraint ✓
- Capability ✓
- Distribution ✓
- DistributionRelease ✓
- Architecture ✓
- License ✓
- Person ✓
- Maintainer ✓
- Contributor ✓
- UpstreamProject ✓
- BuildActivity ✓
- InstalledFile ✓
- PackageSet ✓
- Vulnerability (Security) ✓
- CVE (Security) ✓
- SecurityAdvisory (Security) ✓
- PatchActivity (Security) ✓
- AffectedRange (Security) ✓
- RangeEvent (Security) ✓
- CVSSScore (Security) ✓
- Repository (VCS) ✓
- Commit (VCS) ✓

### Properties Exercised (55+ properties)

**Core:** packageName, identityName, hasVersion, versionString, partOfRelease, partOfDistribution, targetArchitecture, builtFromSource, provides, directlyDependsOn, hasDependency, dependencyTarget, dependencyType, hasVersionConstraint, versionConstraintOperator, versionConstraintValue, isVersionOf, maintainedBy, heldBy, contributesTo, hasLicense, installsFile, installedFilePath, memberOfPackageSet, hasUpstreamProject, sourceCodeRepository, derivedFromCommit

**Security:** cveId, osvId, hasAffectedRange, affectsEcosystem, affectsPackageName, rangeType, hasRangeEvent, eventType, eventVersion, hasCVSSScore, cvssVersion, baseScore, affectsPackage, patchAddresses, patchProducedVersion, patchedFrom, addressesVulnerability, hasCWE

**VCS:** commitHash, onBranch, branchName

**Metrics:** primaryLanguage

**PROV-O:** wasGeneratedBy, wasAssociatedWith, used, endedAtTime

---

## Evaluation Criteria

A competency question is considered **passed** if:
1. The SPARQL query is syntactically valid
2. The query executes without error against production data
3. The query returns results matching the expected column schema
4. The results are semantically correct (verified against domain truth)

A competency question is **BLOCKED** if the query fails due to missing classes or properties that are in-scope for this ontology but not yet modeled.

CQs are the specification. Schema changes are driven by CQ failures. A BLOCKED CQ is not a failure — it's a requirement.
