# PackageGraph Ontology

**Version:** 0.6.0
**License:** CC0 1.0 Universal
**Status:** ✅ OWL 2 DL | ✅ OntoClean Compliant | ✅ 30/30 Modules SHACL Valid

A rigorous OWL 2 ontology for cross-distribution package analysis and software supply chain research.

---

## Overview

PackageGraph is an **analytical ontology** designed for research queries that SBOM formats (SPDX, CycloneDX) cannot answer:

- **Cross-distribution analysis:** Which packages exist in both Fedora and Debian under different names? How do their dependency trees differ?
- **Vulnerability impact modeling:** Which packages are affected by CVE-X across all distributions, accounting for backported patches?
- **Provenance tracing:** What is the complete build chain from upstream commit → source package → binary → installed files?
- **Longitudinal studies:** How has the dependency closure of openssl evolved across 10 Fedora releases?

**Key distinction:** SPDX/CycloneDX describe **artifacts** (what's in this build). PackageGraph describes **distributions** (how 15 Linux distributions package the same upstream projects).

**Not a replacement for SBOMs** — PackageGraph is complementary. SPDX excels at compliance workflows; PackageGraph excels at SPARQL-based analytical queries across ecosystems.

---

## Quick Start

```bash
# Validate all ontology modules
make lint                  # Parse all 77 .ttl files
make validate-all          # Run SHACL validation on 30 modules

# Statistics
make stats                 # Show triple counts per module

# Validate a single module
make validate-rpm          # SHACL-validate just the RPM module
make validate-security     # SHACL-validate just the security module

# Generate deployment artifacts
make deploy                # Creates _site/ with TTL, N-Triples, JSON-LD serializations
```

**Requirements:** Python 3.12+, `uv` package manager, `rdflib`, `pyshacl`

```bash
# Install dependencies
pip install uv
uv pip install rdflib pyshacl
```

---

## What's New in v0.6.0

**Academic readiness release** — journal-level semantic rigor across all 34 modules:

- ✅ **33 competency questions** formalized as SPARQL (7 domains) → [docs/competency-questions.md](docs/competency-questions.md)
- ✅ **OSV-aligned vulnerability model** (AffectedRange, RangeEvent, CVSSScore) → aligned with OSV schema 1.6
- ✅ **Properties-as-taxonomy** for dependencyType (OWL 2 punning) → harmonizes dual-model (reified + shortcut)
- ✅ **OntoClean compliance** (rigid/anti-rigid distinction, Person/Maintainer role model)
- ✅ **OWL 2 DL decidability** (SROIQ violations eliminated, property chain axioms)
- ✅ **Upper ontology alignment** (PROV-O, FOAF, SPDX, DOAP) → lightweight vocabulary integration
- ✅ **29 SHACL shapes** (64% core coverage) → structural integrity validation
- ✅ **3,568 @en language tags** on schema definitions → internationalization support
- ✅ **1,161 rdfs:isDefinedBy** declarations → Linked Data dereferenceability
- ✅ **Design decisions documented** → [docs/design-decisions.md](docs/design-decisions.md)
- ✅ **Evaluation comparison** → [vs SPDX/CycloneDX/OSV](docs/reports/2026-04-20-evaluation-comparison.md)

See [CHANGELOG.md](CHANGELOG.md) for full release notes.

---

## Ontology Modules

### Core (1 module)

| Module | Classes | Properties | Description |
|--------|---------|------------|-------------|
| **core** | 36 | 165 | Package, Version, Dependency, Distribution, Architecture, License, Person, Maintainer, Contributor, BuildActivity, PackageIdentity, VirtualPackage, PhantomPackage, MetaPackage, VersionConstraint |

**Key patterns:**
- Binary/Source package split
- Dependency dual-model (reified + shortcut via owl:propertyChainAxiom)
- OntoClean-compliant Person (rigid) / Maintainer (anti-rigid role)
- Properties-as-taxonomy for dependencyType

**Namespace:** `https://purl.org/packagegraph/ontology/core#`

### Ecosystems (29 modules)

#### System-Level Package Managers (13 modules)

| Module | Namespace | Description |
|--------|-----------|-------------|
| **deb** | `deb#` | Debian/Ubuntu packages — sections, priorities, multi-arch, Pre-Depends |
| **rpm** | `rpm#` | RPM/DNF packages — epochs, disttags, changelogs, weak dependencies |
| **pacman** | `pacman#` | Arch Linux packages — groups, provides/conflicts, install/remove hooks |
| **apk** | `apk#` | Alpine Linux packages — repository branches, APKBUILD scripts |
| **portage** | `portage#` | Gentoo packages — ebuilds, USE flags, slots, EAPI, eclasses |
| **homebrew** | `brew#` | macOS packages — formulae, casks, bottles, taps |
| **nix** | `nix#` | Nix packages — derivations, channels, stdenv, functional builds |
| **xbps** | `xbps#` | Void Linux packages — XBPS-specific properties |
| **opkg** | `opkg#` | OpenWrt packages — embedded Linux package management |
| **bsdpkg** | `bsdpkg#` | FreeBSD/NetBSD/OpenBSD ports — makefiles, flavors, options |
| **bitbake** | `bitbake#` | Yocto/OpenEmbedded — recipes, layers, machines, distros |
| **buildroot** | `buildroot#` | Buildroot packages — defconfigs, build infrastructures |
| **redhat** | `rh#` | Red Hat vendor extensions — RHEL package sets, BaseOS/AppStream |

#### Language Ecosystem Managers (16 modules)

| Module | Namespace | Description |
|--------|-----------|-------------|
| **npm** | `npm#` | Node.js/JavaScript — scopes, workspaces, peer deps, scripts |
| **pypi** | `pypi#` | Python packages — wheels, sdists, extras, classifiers, PEP 517 |
| **cargo** | `cargo#` | Rust crates — features, editions, targets, dev-dependencies |
| **gomod** | `gomod#` | Go modules — module paths, replace directives, go.sum |
| **maven** | `maven#` | Java/JVM artifacts — groupId:artifactId:version, scopes, POM |
| **nuget** | `nuget#` | .NET packages — target frameworks, prerelease, listed status |
| **rubygems** | `rubygems#` | Ruby gems — platforms, gemspec metadata |
| **cpan** | `cpan#` | Perl distributions — PAUSE IDs, maturity levels, modules |
| **cran** | `cran#` | R packages — Depends/Imports/Suggests/LinkingTo, compilation |
| **hackage** | `hackage#` | Haskell packages — Cabal metadata, GHC compatibility |
| **hex** | `hex#` | Elixir/Erlang — mix/rebar3, retirement status |
| **conda** | `conda#` | Anaconda packages — channels, feedstocks, recipes |
| **flatpak** | `flatpak#` | Linux desktop apps — runtimes, extensions, sandboxing |
| **snap** | `snap#` | Ubuntu Snap apps — confinement, interfaces, tracks |
| **chocolatey** | `choco#` | Windows packages — NuGet format, PowerShell scripts, shims |

### Extensions (5 modules)

| Module | Namespace | Description |
|--------|-----------|-------------|
| **security** | `sec#` | CVE vulnerabilities, OSV ranges, CVSS scores, security advisories, patch provenance |
| **vcs** | `vcs#` | Git repositories, commits, branches, tags, pull requests, contributor activity |
| **slsa** | `slsa#` | Build provenance attestations, SLSA levels, builder identity |
| **metrics** | `met#` | Code analysis — lines of code, cyclomatic complexity, language breakdowns |
| **dq** | `dq#` | Data quality issues and metadata validation |

---

## Key Features

### Semantic Web Best Practices

- **OWL 2 DL decidability** — no OWL Full violations, SROIQ-compliant reasoning
- **OntoClean methodology** — rigid/anti-rigid distinction (Person vs Maintainer roles)
- **IAO:0000115 definitions** — every class and property has formal OBO Foundry definitions
- **@en language tags** on all schema elements — internationalization support
- **rdfs:isDefinedBy** on all entities — Linked Data dereferenceability
- **PROV-O alignment** — build activities, provenance chains
- **FOAF integration** — person entities, maintainer attribution

### Cross-Ecosystem Analysis

- **PackageIdentity** class — version-agnostic identity enables cross-distribution queries
- **29 specialized ecosystem modules** — captures ecosystem-specific semantics (RPM epochs, Debian sections, npm scopes)
- **Dependency dual-model** — reified (with version constraints) + shortcut (for graph traversal)
- **Properties-as-taxonomy** — dependencyType values are property URIs (pkg:buildDependsOn, pkg:recommends, etc.)

### Vulnerability & Security

- **OSV-aligned model** — AffectedRange with SEMVER/ECOSYSTEM/GIT events (introduced/fixed)
- **CVSS reification** — supports multiple CVSS versions (2.0, 3.0, 3.1, 4.0) per vulnerability
- **Patch provenance** — PatchActivity links vulnerabilities through build chains
- **CVE + GHSA support** — not all vulnerabilities have CVEs

### Validation & Quality

- **30 modules with SHACL shapes** — 29 NodeShapes enforce structural constraints
- **Validation passing** — all 77 .ttl files parse, all 30 modules SHACL valid
- **33 competency questions** — specification of what the ontology can answer
- **Production validation framework** — scripts/production_shacl_validate.py for Fuseki data

---

## Directory Structure

```
ontology/
├── core/
│   ├── core.ttl                    # 36 core classes, 165 properties
│   ├── core.shacl.ttl              # 22 SHACL NodeShapes
│   ├── core.examples.ttl           # Example instances
│   └── skos-schemes.ttl            # Dependency types, severity, advisory types
│
├── ecosystems/                     # 29 ecosystem-specific modules
│   ├── deb/deb.ttl                 # Debian packages
│   ├── rpm/rpm.ttl                 # RPM packages
│   ├── pacman/pacman.ttl           # Arch Linux
│   ├── npm/npm.ttl                 # Node.js
│   ├── pypi/pypi.ttl               # Python
│   ├── cargo/cargo.ttl             # Rust
│   ├── maven/maven.ttl             # Java/JVM
│   └── ... (22 more)
│
├── extensions/                     # 5 extension modules
│   ├── security/security.ttl       # Vulnerabilities, CVEs, advisories
│   ├── vcs/vcs.ttl                 # Git, commits, repositories
│   ├── slsa/slsa.ttl               # Build provenance
│   ├── metrics/metrics.ttl         # Code analysis metrics
│   └── dq/dq.ttl                   # Data quality
│
├── references/
│   └── alignments.ttl              # PROV-O, SPDX, Schema.org, FOAF mappings
│
├── scripts/                        # Validation and tooling
│   ├── validate_module.py          # Per-module SHACL validation
│   ├── production_shacl_validate.py # Fuseki production data validation
│   ├── add_schema_annotations.py   # Bulk @en tags + isDefinedBy
│   └── fix_ecosystem_patterns.py   # Ecosystem anti-pattern remediation
│
├── docs/
│   ├── competency-questions.md     # 33 CQs as formal specification
│   ├── design-decisions.md         # Adopted patterns + documented rejections
│   └── reports/
│       ├── 2026-04-20-evaluation-comparison.md  # vs SPDX/CycloneDX/OSV
│       └── 2026-04-20-production-shacl-validation.md
│
├── Makefile                        # Build, validation, deployment
├── CHANGELOG.md                    # Version history
└── pyproject.toml                  # Python tooling dependencies
```

---

## Applications

### 1. Cross-Distribution Package Research

**Query:** Which packages exist in both Fedora and Debian under different names?

```sparql
PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>

SELECT ?fedoraName ?debianName ?identity WHERE {
  ?identity a pkg:PackageIdentity .
  ?fedoraPkg pkg:hasIdentity ?identity ;
             pkg:packageName ?fedoraName ;
             pkg:partOfRelease/pkg:distributionName "Fedora" .
  ?debianPkg pkg:hasIdentity ?identity ;
             pkg:packageName ?debianName ;
             pkg:partOfRelease/pkg:distributionName "Debian" .
  FILTER(?fedoraName != ?debianName)
}
```

**Answer:** PackageIdentity enables cross-distribution joins. See [33 competency questions](docs/competency-questions.md) for more examples.

### 2. Vulnerability Impact Analysis

**Query:** Which packages across all distributions are affected by CVE-2024-1234 with version ranges?

Uses the OSV-aligned model (AffectedRange, RangeEvent) to provide precise version-specific vulnerability data, not just package-name matching.

### 3. Dependency Blast Radius

**Query:** What is the transitive dependency closure for openssl in Fedora 43?

```sparql
?package pkg:packageName "openssl" ;
         pkg:directlyDependsOn+ ?dep .
```

Property path traversal using the materialized shortcut properties.

### 4. Provenance Chain Tracing

**Query:** Trace a binary package back through its build to the upstream commit.

See CQ-PROV-01 for the full provenance chain query (upstream commit → source → build → binary).

---

## Technical Details

### Ontology Design Principles

1. **Modular architecture** — 34 independent modules with owl:imports
2. **Dual-model for dependencies** — reified (Dependency class with constraints) + shortcut (directlyDependsOn) linked via owl:propertyChainAxiom
3. **OntoClean rigor** — Person (rigid identity) vs Maintainer/Contributor (anti-rigid roles)
4. **Properties-as-taxonomy** — dependencyType values are property URIs (pkg:buildDependsOn, pkg:recommends, etc.) via OWL 2 punning
5. **FAIR compliance** — PROV-O/FOAF/SPDX vocabulary reuse, @en language tags, rdfs:isDefinedBy

### OWL 2 Features

- **Property characteristics:** Symmetric (conflicts, equivalentInDistribution), Asymmetric (replaces, builtFromSource), Irreflexive (enforced via SHACL SPARQL, not OWL characteristic for chain-derived properties)
- **Property chain axioms:** directlyDependsOn derived from hasDependency → dependencyTarget
- **Disjointness constraints:** owl:AllDisjointClasses groups prevent type confusion
- **Punning:** Property URIs used as individuals in dependencyType values

### SHACL Validation

- **29 NodeShapes** across core + security modules
- **64% core class coverage** (22 of 36 core classes have shapes)
- **SKOS enforcement:** sh:in constraints on enumerations (advisorySeverity, advisoryType, dependencyType)
- **SPARQL constraints:** IrreflexiveDependsOnShape, DependencyConsistencyShape
- **All examples pass validation** — pyshacl with RDFS inference

### Namespace Convention

- **Ontology definitions:** `https://purl.org/packagegraph/ontology/{module}#`
- **Data instances:** `https://packagegraph.github.io/d/{type}/{path}`
- **Named graphs:** `https://packagegraph.github.io/graph/{distribution}/{release}`

---

## Validation

Run the full validation suite:

```bash
make lint          # Parse all .ttl files → All 77 files valid
make validate-all  # SHACL validation → 30/30 modules SHACL OK
```

Per-module validation:

```bash
uv run python scripts/validate_module.py rpm
uv run python scripts/validate_module.py security
```

Production data validation (requires Fuseki):

```bash
# Port-forward to cluster
KUBECONFIG=~/.kube/config-2 oc port-forward -n packagegraph svc/fuseki 3031:3030

# Validate against production data
uv run python scripts/production_shacl_validate.py \
  --endpoint http://localhost:3031/packagegraph/sparql
```

---

## Documentation

- **[CHANGELOG.md](CHANGELOG.md)** — version history and release notes
- **[Competency Questions](docs/competency-questions.md)** — 33 CQs as formal specification
- **[Design Decisions](docs/design-decisions.md)** — adopted patterns, documented rejections
- **[Evaluation Comparison](docs/reports/2026-04-20-evaluation-comparison.md)** — PackageGraph vs SPDX vs CycloneDX vs OSV
- **[Production Validation Report](docs/reports/2026-04-20-production-shacl-validation.md)** — conformance framework

---

## Contributing

### Adding a New Ecosystem Module

See [scripts/README.md](scripts/README.md) for the workflow:

1. Create `ecosystems/{name}/{name}.ttl`
2. Add classes extending pkg:BinaryPackage or pkg:SourcePackage
3. Declare shortcut properties as rdfs:subPropertyOf of appropriate core properties
4. Add SHACL shapes in `{name}.shacl.ttl`
5. Create examples in `{name}.examples.ttl`
6. Run `make validate-{name}` to verify
7. Add entry to this README and NAMESPACES.md

### Design Guidelines

- **Use properties-as-taxonomy** — don't create string-based dependency type properties
- **Subclass correctly** — extend BinaryPackage (if ecosystem distributes pre-built) or SourcePackage (if source)
- **Map dev/test deps** to pkg:buildDependsOn, optional deps to pkg:suggests/recommends
- **Follow OntoClean** — roles are anti-rigid, identities are rigid
- **Add PROV-O alignment** — author/maintainer properties should reference prov:wasAttributedTo in comments

---

## License

[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) — public domain dedication.

You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.

---

## Citation

```bibtex
@misc{packagegraph2026,
  title={PackageGraph: An OWL 2 Ontology for Cross-Distribution Package Analysis},
  author={PackageGraph Project},
  year={2026},
  version={0.6.0},
  url={https://purl.org/packagegraph/ontology/core}
}
```

---

## Links

- **Ontology browsing:** https://packagegraph.github.io/ontology/
- **Source repository:** https://github.com/packagegraph/ontology
- **Dataset (Fuseki):** 62.7M triples across 15 named graphs
- **Related:** [PackageGraph Platform](https://github.com/packagegraph/platform) — Rust collectors and enrichers
