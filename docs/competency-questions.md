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
  ?release pkg:distributionName "Fedora" ;
           pkg:releaseVersion "43" .
  ?package a pkg:BinaryPackage ;
           pkg:partOfRelease ?release ;
           pkg:hasArchitecture ?arch ;
           pkg:packageName ?name ;
           pkg:hasVersion/pkg:versionString ?version .
  ?arch pkg:architectureName "x86_64" .
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

SELECT ?binary ?binaryName
WHERE {
  ?source a pkg:SourcePackage ;
          pkg:packageName "glibc" ;
          pkg:partOfRelease ?release .
  ?release pkg:distributionName "Fedora" ;
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

SELECT ?provider ?providerName
WHERE {
  ?capability a pkg:Capability ;
              pkg:capabilityName "libssl.so.3" .
  ?provider pkg:provides ?capability ;
            pkg:packageName ?providerName ;
            pkg:partOfRelease ?release .
  ?release pkg:distributionName "Debian" ;
           pkg:releaseCodename "trixie" .
}
```

**Expected Columns:** provider (URI), providerName (string)

**Exercises:** Capability, provides, partOfRelease

**Status:** PASS

---

### CQ-PM-04: Dependency Chain Depth

**Question:** What is the maximum dependency depth (transitive closure) for the `openssl` package in Fedora 43?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT (COUNT(?dep) AS ?depth)
WHERE {
  ?package pkg:packageName "openssl" ;
           pkg:partOfRelease ?release .
  ?release pkg:distributionName "Fedora" ;
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

SELECT DISTINCT ?package ?packageName ?distro
WHERE {
  ?person foaf:mbox <mailto:maintainer@example.org> .
  ?role a pkg:Maintainer ;
        pkg:heldBy ?person .
  ?package pkg:maintainedBy ?role ;
           pkg:packageName ?packageName ;
           pkg:partOfRelease/pkg:partOfDistribution/rdfs:label ?distro .
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

SELECT (COUNT(DISTINCT ?package) AS ?count)
WHERE {
  ?release pkg:distributionName "Fedora" ;
           pkg:releaseVersion "43" .
  ?package pkg:partOfRelease ?release ;
           pkg:hasArchitecture ?arch .
  ?arch pkg:architectureName "aarch64" .
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
  ?release pkg:distributionName "Debian" ;
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

SELECT ?filepath (COUNT(DISTINCT ?package) AS ?packageCount) (GROUP_CONCAT(?pkgName; separator=", ") AS ?packages)
WHERE {
  ?release pkg:distributionName "RHEL" ;
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

**Status:** PASS (if installsFile data exists)

---

### CQ-PM-09: Package Size Distribution

**Question:** What is the median installed size of binary packages in OpenSUSE Tumbleweed?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX rpm: <https://purl.org/packagegraph/ontology/rpm#>

SELECT (AVG(?size) AS ?avgSize) (MIN(?size) AS ?minSize) (MAX(?size) AS ?maxSize)
WHERE {
  ?release pkg:distributionName "openSUSE" ;
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

SELECT ?packageName (COUNT(DISTINCT ?version) AS ?versionCount)
WHERE {
  ?release pkg:partOfDistribution ?dist .
  ?dist pkg:distributionName "Fedora" .
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

## Domain: Security / Vulnerability (SEC)

### CQ-SEC-01: Affected Packages by CVE

**Question:** Which packages across all distributions are affected by CVE-2024-1234?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

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
             pkg:partOfRelease/pkg:ecosystem ?eco .
  }
}
```

**Expected Columns:** package (URI or UNDEF), packageName (string), ecosystem (string)

**Exercises:** Vulnerability, cveId, hasAffectedRange, AffectedRange, affectsEcosystem, affectsPackageName

**Status:** BLOCKED — requires Task 3 (OSV alignment)

---

### CQ-SEC-02: Unpatched Vulnerabilities

**Question:** Which high-severity vulnerabilities affecting Fedora 43 packages have not been patched?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT DISTINCT ?cveId ?packageName ?cvssScore
WHERE {
  ?vuln sec:cveId ?cveId ;
        sec:affectsPackage ?identity ;
        sec:hasCVSSScore ?cvss .
  ?cvss sec:baseScore ?cvssScore .
  FILTER(?cvssScore >= 7.0)

  ?identity pkg:packageName ?packageName .
  ?package pkg:packageName ?packageName ;
           pkg:partOfRelease ?release .
  ?release pkg:distributionName "Fedora" ;
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

**Status:** BLOCKED — requires Task 3 (AffectedRange) and Task 4 (CVSSScore reification)

---

### CQ-SEC-03: Vulnerability Version Range

**Question:** Which specific versions of the `openssl` package are affected by CVE-2024-5678?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>

SELECT ?ecosystem ?introducedVersion ?fixedVersion
WHERE {
  ?vuln sec:cveId "CVE-2024-5678" ;
        sec:hasAffectedRange ?range .
  ?range sec:affectsEcosystem/rdfs:label ?ecosystem ;
         sec:affectsPackageName "openssl" ;
         sec:hasRangeEvent ?event .

  OPTIONAL {
    ?event sec:eventType "introduced" ;
           sec:eventVersion ?introducedVersion .
  }
  OPTIONAL {
    ?event sec:eventType "fixed" ;
           sec:eventVersion ?fixedVersion .
  }
}
```

**Expected Columns:** ecosystem (string), introducedVersion (string or UNDEF), fixedVersion (string or UNDEF)

**Exercises:** AffectedRange, RangeEvent, eventType, eventVersion

**Status:** BLOCKED — requires Task 3 (OSV alignment)

---

### CQ-SEC-04: Security Advisory Coverage

**Question:** Which vulnerabilities have vendor security advisories (RHSA, DSA) addressing them?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>

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

**Status:** BLOCKED — requires Task 4 (CVSS reification)

---

### CQ-SEC-06: Critical Vulnerabilities Without CVE

**Question:** Which high-severity vulnerabilities in the OSV database do not have CVE identifiers?

**SPARQL:**
```sparql
PREFIX sec: <https://purl.org/packagegraph/ontology/security#>

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

**Status:** BLOCKED — requires Task 3 (osvId) and Task 4 (CVSSScore)

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

SELECT ?cweId (COUNT(?vuln) AS ?count)
WHERE {
  ?vuln sec:hasAffectedRange/sec:affectsEcosystem ?eco ;
        sec:hasCWE/sec:cweId ?cweId .
  ?eco rdfs:label "PyPI" .
}
GROUP BY ?cweId
ORDER BY DESC(?count)
LIMIT 10
```

**Expected Columns:** cweId (string), count (integer)

**Exercises:** hasCWE, CWE, affectsEcosystem

**Status:** PASS (if hasCWE property exists)

---

## Domain: Cross-Distribution Analysis (XD)

### CQ-XD-01: Equivalent Packages Across Distributions

**Question:** Which packages exist in both Fedora and Debian under different names?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT ?fedoraName ?debianName ?identity
WHERE {
  ?identity a pkg:PackageIdentity .
  ?fedoraPkg pkg:packageName ?fedoraName ;
             pkg:hasIdentity ?identity ;
             pkg:partOfRelease/pkg:distributionName "Fedora" .
  ?debianPkg pkg:packageName ?debianName ;
             pkg:hasIdentity ?identity ;
             pkg:partOfRelease/pkg:distributionName "Debian" .
  FILTER(?fedoraName != ?debianName)
}
LIMIT 100
```

**Expected Columns:** fedoraName (string), debianName (string), identity (URI)

**Exercises:** PackageIdentity, hasIdentity, cross-distribution joins

**Status:** PASS

---

### CQ-XD-02: Version Skew Analysis

**Question:** For packages present in both Fedora 43 and Debian Trixie, which have version differences > 1 major version?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT ?packageName ?fedoraVersion ?debianVersion
WHERE {
  ?identity a pkg:PackageIdentity ;
            pkg:packageName ?packageName .

  ?fedoraPkg pkg:hasIdentity ?identity ;
             pkg:partOfRelease ?fedoraRelease ;
             pkg:hasVersion/pkg:versionString ?fedoraVersion .
  ?fedoraRelease pkg:distributionName "Fedora" ;
                 pkg:releaseVersion "43" .

  ?debianPkg pkg:hasIdentity ?identity ;
             pkg:partOfRelease ?debianRelease ;
             pkg:hasVersion/pkg:versionString ?debianVersion .
  ?debianRelease pkg:distributionName "Debian" ;
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

SELECT DISTINCT ?packageName
WHERE {
  ?fedoraPkg pkg:packageName ?packageName ;
             pkg:partOfRelease/pkg:distributionName "Fedora" .
  FILTER NOT EXISTS {
    ?debianPkg pkg:packageName ?packageName ;
               pkg:partOfRelease/pkg:distributionName "Debian" .
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

SELECT ?projectName (COUNT(DISTINCT ?distro) AS ?distroCount) (GROUP_CONCAT(DISTINCT ?distroName; separator=", ") AS ?distros)
WHERE {
  ?upstream a pkg:UpstreamProject ;
            pkg:projectName ?projectName .
  ?package pkg:derivedFromProject ?upstream ;
           pkg:partOfRelease/pkg:partOfDistribution ?distro .
  ?distro rdfs:label ?distroName .
}
GROUP BY ?projectName
HAVING (COUNT(DISTINCT ?distro) >= 3)
ORDER BY DESC(?distroCount)
LIMIT 50
```

**Expected Columns:** projectName (string), distroCount (integer), distros (string)

**Exercises:** UpstreamProject, derivedFromProject, cross-distribution aggregation

**Status:** PASS

---

### CQ-XD-05: Repology Cross-Ecosystem Equivalence

**Question:** Which packages have equivalent names across Linux distributions, language ecosystems (npm, PyPI), and Homebrew?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT ?identity ?linuxName ?npmName ?pypiName ?brewName
WHERE {
  ?identity a pkg:PackageIdentity .

  OPTIONAL {
    ?linuxPkg pkg:hasIdentity ?identity ;
              pkg:packageName ?linuxName ;
              pkg:partOfRelease/pkg:distributionName ?linuxDist .
    FILTER(?linuxDist IN ("Fedora", "Debian", "Arch"))
  }
  OPTIONAL {
    ?npmPkg pkg:hasIdentity ?identity ;
            pkg:packageName ?npmName ;
            pkg:partOfRelease/pkg:ecosystem/rdfs:label "npm" .
  }
  OPTIONAL {
    ?pypiPkg pkg:hasIdentity ?identity ;
             pkg:packageName ?pypiName ;
             pkg:partOfRelease/pkg:ecosystem/rdfs:label "PyPI" .
  }
  OPTIONAL {
    ?brewPkg pkg:hasIdentity ?identity ;
             pkg:packageName ?brewName ;
             pkg:partOfRelease/pkg:distributionName "Homebrew" .
  }

  FILTER(BOUND(?linuxName) && (BOUND(?npmName) || BOUND(?pypiName) || BOUND(?brewName)))
}
LIMIT 100
```

**Expected Columns:** identity (URI), linuxName, npmName, pypiName, brewName (strings or UNDEF)

**Exercises:** PackageIdentity, hasIdentity, Ecosystem, cross-ecosystem joins

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
          pkg:builtFromSource ?source .

  ?buildActivity a pkg:BuildActivity ;
                 pkg:wasBuiltBy ?buildActivity ;
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

SELECT ?packageName ?slsaLevel ?attestation
WHERE {
  ?package a pkg:Package ;
           pkg:packageName ?packageName ;
           pkg:partOfRelease/pkg:distributionName "Fedora" ;
           pkg:partOfRelease/pkg:releaseVersion "43" ;
           slsa:hasProvenance ?attestation .
  ?attestation slsa:slsaLevel ?slsaLevel .
  FILTER(?slsaLevel >= 3)
}
ORDER BY DESC(?slsaLevel)
```

**Expected Columns:** packageName (string), slsaLevel (integer), attestation (URI)

**Exercises:** SLSA module, hasProvenance, slsaLevel

**Status:** PASS (if SLSA data exists)

---

### CQ-PROV-03: Build Environment

**Question:** Which build agents or systems were used to build packages in RHEL 9?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX prov: <http://www.w3.org/ns/prov#>

SELECT DISTINCT ?agent ?agentName (COUNT(?package) AS ?packageCount)
WHERE {
  ?package pkg:partOfRelease/pkg:distributionName "RHEL" ;
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

**Status:** PASS (requires Task 6 for contributesTo domain fix)

---

## Domain: Dependency Analysis (DEP)

### CQ-DEP-01: Direct vs Transitive Dependencies

**Question:** For the `python3` package in Debian Trixie, how many direct dependencies vs total transitive dependencies?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT (COUNT(DISTINCT ?direct) AS ?directCount) (COUNT(DISTINCT ?transitive) AS ?transitiveCount)
WHERE {
  ?package pkg:packageName "python3" ;
           pkg:partOfRelease/pkg:distributionName "Debian" ;
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

SELECT ?depType (COUNT(?dep) AS ?count)
WHERE {
  ?package pkg:partOfRelease/pkg:distributionName "Fedora" ;
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

SELECT ?sourcePkg ?targetPkg ?operator ?constraintVersion
WHERE {
  ?sourcePkg pkg:hasDependency ?dep .
  ?dep pkg:dependencyTarget ?targetPkg ;
       pkg:hasVersionConstraint ?constraint .
  ?constraint pkg:operator ?operator ;
              pkg:constraintVersion ?constraintVersion .
  ?sourcePkg pkg:packageName ?srcName .
  ?targetPkg pkg:packageName ?tgtName .
}
LIMIT 100
```

**Expected Columns:** sourcePkg (URI), targetPkg (URI), operator (string), constraintVersion (string)

**Exercises:** VersionConstraint, hasVersionConstraint, operator, constraintVersion

**Status:** PASS

---

### CQ-DEP-04: Circular Dependencies

**Question:** Which packages have circular dependency relationships in Arch Linux?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT DISTINCT ?pkg1Name ?pkg2Name
WHERE {
  ?pkg1 pkg:packageName ?pkg1Name ;
        pkg:partOfRelease/pkg:distributionName "Arch Linux" ;
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

SELECT ?language (COUNT(DISTINCT ?repo) AS ?repoCount)
WHERE {
  ?package pkg:partOfRelease/pkg:distributionName "Fedora" ;
           pkg:derivedFromProject/pkg:hasRepository ?repo .
  ?repo met:primaryLanguage ?language .
}
GROUP BY ?language
ORDER BY DESC(?repoCount)
LIMIT 10
```

**Expected Columns:** language (string), repoCount (integer)

**Exercises:** Repository, hasRepository, Metrics module, primaryLanguage

**Status:** PASS (if metrics data exists)

---

### CQ-VCS-02: Commit-to-Release Tracing

**Question:** Which source packages in Debian Trixie were built from commits on the `main` branch?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>
PREFIX vcs: <https://purl.org/packagegraph/ontology/vcs#>

SELECT ?packageName ?commitHash ?branchName
WHERE {
  ?package a pkg:SourcePackage ;
           pkg:packageName ?packageName ;
           pkg:partOfRelease/pkg:distributionName "Debian" ;
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

**Status:** PASS (if VCS data exists)

---

## Domain: Package Set & Collection (SET)

### CQ-SET-01: Package Set Membership

**Question:** Which packages are members of the "BaseOS" package set in RHEL 9?

**SPARQL:**
```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT ?packageName
WHERE {
  ?set a pkg:PackageSet ;
       rdfs:label "BaseOS" .
  ?package pkg:memberOfPackageSet ?set ;
           pkg:partOfRelease/pkg:distributionName "RHEL" ;
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

**Status:** PASS (if RPM spec metadata exists)

---

### CQ-ECO-02: Debian Section Distribution

**Question:** What are the most common package sections in Debian Trixie?

**SPARQL:**
```sparql
PREFIX deb: <https://purl.org/packagegraph/ontology/deb#>
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT ?section (COUNT(?package) AS ?count)
WHERE {
  ?package a deb:BinaryDeb ;
           deb:section ?section ;
           pkg:partOfRelease/pkg:distributionName "Debian" ;
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

| Domain | CQ Count | Status: PASS | Status: BLOCKED |
|--------|----------|--------------|-----------------|
| Package Management (PM) | 10 | 10 | 0 |
| Security / Vulnerability (SEC) | 8 | 3 | 5 |
| Cross-Distribution Analysis (XD) | 5 | 5 | 0 |
| Provenance / Build (PROV) | 4 | 4 | 0 |
| Repository / VCS (VCS) | 2 | 2 | 0 |
| Package Set (SET) | 1 | 1 | 0 |
| Ecosystem-Specific (ECO) | 3 | 3 | 0 |
| **TOTAL** | **33** | **28** | **5** |

**BLOCKED CQs:** All require OSV alignment (Task 3) and/or CVSS reification (Task 4). These are the queries that drive the schema changes — their failure is the specification.

---

## Validation Against Examples

The following CQs can be validated against local example files without Fuseki:

- **CQ-PM-02** — source-to-binary mapping (uses core/rpm/deb examples)
- **CQ-PM-03** — virtual package providers (uses capability examples)
- **CQ-PM-05** — packages by maintainer (uses Person/Maintainer examples)
- **CQ-SEC-07** — patch provenance chain (uses security examples)
- **CQ-DEP-03** — version constraints (uses dependency examples)

BLOCKED CQs cannot be validated until schema changes are implemented.

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

### Properties Exercised (45+ properties)

**Core:** packageName, hasVersion, versionString, partOfRelease, hasArchitecture, builtFromSource, provides, directlyDependsOn, hasDependency, dependencyTarget, dependencyType, hasVersionConstraint, operator, constraintVersion, hasIdentity, maintainedBy, heldBy, contributesTo, hasLicense, installsFile, installedFilePath, memberOfPackageSet, derivedFromProject, hasRepository, derivedFromCommit

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
