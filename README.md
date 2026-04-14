# Package Management RDF Ontologies

A comprehensive collection of RDF/OWL ontologies for representing software
packages, repositories, and metadata across major package management systems.

## Overview

This project provides formal RDF schemas (ontologies) that enable semantic
representation of software packages and their ecosystems. Each ontology captures
the unique characteristics and metadata structures of different package
management systems while maintaining interoperability through a common base
ontology.

## Ontologies Included

### 1. Core Package Ontology (`core.ttl`)

- **Purpose**: Base ontology defining common concepts across all package
  management systems
- **Key Classes**: Package, Repository, PackageManager, Dependency, Version,
  Maintainer, License, Architecture
- **Key Properties**: packageName, description, homepage, downloadURL,
  installSize, checksum
- **Namespace**: `https://purl.org/packagegraph/ontology/core#`

### 2. VCS Integration Ontology (`vcs.ttl`)

- **Purpose**: Represents version control system integration and source code
  management
- **Key Classes**: Repository, Commit, Tag, Branch, SourcePackage
- **Key Features**: Git integration, commit tracking, tag-based packaging
- **Namespace**: `https://purl.org/packagegraph/ontology/vcs#`

### 3. Debian/APT Ontology (`debian.ttl`)

- **Purpose**: Represents Debian packages (.deb), APT repositories, and
  Debian-specific metadata
- **Key Classes**: DebianPackage, SourcePackage, BinaryPackage, Suite,
  Component, Section, Priority
- **Key Features**: Debian control file metadata, dependency types (depends,
  recommends, suggests), maintainer scripts
- **Namespace**: `https://purl.org/packagegraph/ontology/debian#`

### 4. RPM Ontology (`rpm.ttl`)

- **Purpose**: Represents RPM packages, YUM/DNF repositories, and RPM-specific
  metadata
- **Key Classes**: RPMPackage, SourceRPM, BinaryRPM, RPMGroup, NEVR, Changelog
- **Key Features**: RPM header tags, build metadata, file information, changelog
  entries
- **Namespace**: `https://purl.org/packagegraph/ontology/rpm#`

### 5. Arch Linux Ontology (`arch.ttl`)

- **Purpose**: Represents Arch packages, PKGBUILD files, and Pacman repositories
  including AUR
- **Key Classes**: ArchPackage, PKGBUILD, SplitPackage, AUR, SRCINFO,
  PackageGroup
- **Key Features**: PKGBUILD functions, checksums, build options, package groups
- **Namespace**: `https://purl.org/packagegraph/ontology/archlinux#`

### 6. FreeBSD Ports Ontology (`freebsd.ttl`)

- **Purpose**: Represents FreeBSD ports (FreeBSD, OpenBSD, NetBSD), Makefiles, and
  ports trees
- **Key Classes**: Port, PortsTree, Makefile, PortSkeleton, Distinfo, Category,
  Flavor
- **Key Features**: Port build configuration, patches, options, master sites,
  flavors
- **Namespace**: `https://purl.org/packagegraph/ontology/freebsd#`

### 7. Chocolatey Ontology (`chocolatey.ttl`)

- **Purpose**: Represents Chocolatey packages, NuGet format, and
  Windows-specific metadata
- **Key Classes**: ChocolateyPackage, Nupkg, Nuspec, ChocolateyScript,
  InstallScript, UninstallScript
- **Key Features**: PowerShell scripts, installer types, registry keys,
  Windows-specific properties
- **Namespace**: `https://purl.org/packagegraph/ontology/chocolatey#`

### 8. Homebrew Ontology (`homebrew.ttl`)

- **Purpose**: Represents Homebrew formulas, casks, taps, and macOS-specific
  packaging
- **Key Classes**: Formula, Cask, Tap, Bottle, SoftwareSpec, Artifact (Apps,
  Fonts, etc.)
- **Key Features**: Build specifications, dependency types, macOS application
  artifacts, bottles
- **Namespace**: `https://purl.org/packagegraph/ontology/homebrew#`

### 9. Nix Ontology (`nix.ttl`)

- **Purpose**: Represents Nix derivations, expressions, Nixpkgs, and functional
  package management
- **Key Classes**: Derivation, StoreDerivation, NixExpression, Flake,
  StdenvMkDerivation
- **Key Features**: Build phases, store paths, reproducible builds, functional
  dependencies
- **Namespace**: `https://purl.org/packagegraph/ontology/nix#`

### 10. SLSA Supply Chain Security Ontology (`slsa.ttl`)

- **Purpose**: Models SLSA (Supply-chain Levels for Software Artifacts)
  provenance attestations and build security
- **Key Classes**: ProvenanceAttestation, BuildLevel, Builder, SourceAttestation,
  BuildEnvironment
- **Key Features**: SLSA build levels (L0-L3), cryptographic attestations, build
  isolation and ephemeral environment tracking, PROV-O grounded
- **Namespace**: `https://purl.org/packagegraph/ontology/slsa#`

### 11. Security Ontology (`security.ttl`)

- **Purpose**: Models CVE vulnerabilities, security advisories, and patch
  provenance
- **Key Classes**: Vulnerability, SecurityAdvisory, PatchActivity
- **Key Features**: CVSS scoring, advisory-to-CVE mapping, affected/fixed version
  tracking, patch derivation chains
- **Namespace**: `https://purl.org/packagegraph/ontology/security#`

### 12. Code Metrics Ontology (`metrics.ttl`)

- **Purpose**: Represents code analysis metrics and programming language
  properties
- **Key Classes**: CodeMetrics, LanguageMetrics, ProgrammingLanguage
- **Key Features**: Lines of code counts, memory safety flags, garbage collection
  tracking
- **Namespace**: `https://purl.org/packagegraph/ontology/metrics#`

## Key Features

### Comprehensive Metadata Coverage

- **Package Information**: Names, versions, descriptions, licenses, maintainers
- **Build Information**: Source URLs, checksums, build dependencies, build
  scripts
- **Installation Details**: File lists, install sizes, configuration files
- **Repository Structure**: Package organization, categories, sections,
  priorities
- **Dependency Relationships**: Runtime, build-time, optional, and conflicting
  dependencies

### System-Specific Extensions

Each ontology captures unique features of its package management system:

- **Debian**: Suite/component structure, maintainer scripts, policy compliance
- **RPM**: NEVR versioning, spec files, RPM tags, build environments
- **Arch**: PKGBUILD structure, AUR integration, split packages
- **BSD**: Ports tree organization, build options, master sites, flavors
- **Chocolatey**: PowerShell integration, Windows installer types, registry
  handling
- **Homebrew**: Formula/cask distinction, tap system, bottle distribution
- **Nix**: Functional derivations, store paths, reproducible builds, flakes

### Interoperability Design

- **Common Base**: All ontologies extend the core package ontology
- **Standard Vocabularies**: Reuses established vocabularies (Dublin Core, FOAF,
  DOAP, SPDX)
- **Consistent Naming**: Follows RDF/OWL best practices and naming conventions
- **Cross-References**: Enables linking packages across different systems

### OWL 2 Compliance and Cardinality Constraints

- **Functional Properties**: Unique identifiers, checksums, and URLs marked as functional
- **Cardinality Restrictions**: Mandatory properties with exact cardinality constraints
- **Qualified Cardinality**: Complex constraints using owl:onClass restrictions
- **Property Equivalencies**: Cross-format property mappings for interoperability
- **Protégé Compatible**: All ontologies load successfully in Protégé ontology editor

## Usage Examples

The `package-examples.ttl` file demonstrates how to represent real packages
using these ontologies:

```turtle
# Debian vim package
ex:vim-debian a deb:BinaryPackage ;
    pkg:packageName "vim" ;
    pkg:description "Vi IMproved - enhanced vi editor" ;
    deb:version "2:9.0.1378-2" ;
    deb:architecture "amd64" ;
    deb:inSuite deb:unstable ;
    deb:inComponent deb:main .

# Homebrew wget formula  
ex:wget-brew a brew:Formula ;
    brew:formulaName "wget" ;
    pkg:version "1.21.4" ;
    brew:desc "Internet file retriever" ;
    brew:hasStable ex:wget-stable .

# Nix hello derivation
ex:hello-nix a nix:StdenvMkDerivation ;
    nix:pname "hello" ;
    nix:version "2.12.1" ;
    pkg:description "A program that produces a familiar, friendly greeting" ;
    nix:doCheck true .
```

## File Structure

```
├── core.ttl                       # Base ontology (25+ classes, 40+ properties)
├── vcs.ttl                        # Version control integration
├── security.ttl                   # CVE vulnerabilities and security advisories
├── metrics.ttl                    # Code metrics and language properties
├── slsa.ttl                       # SLSA supply chain provenance attestations
├── shacl.ttl                      # SHACL validation shapes
├── debian.ttl                     # Debian/APT (8 classes, 35+ properties)
├── rpm.ttl                        # RPM/YUM/DNF (8 classes, 45+ properties)
├── redhat.ttl                     # Red Hat vendor extensions (RHEL/RHIVOS)
├── arch.ttl                       # Arch Linux (7 classes, 40+ properties)
├── freebsd.ttl                    # FreeBSD Ports (13 classes, 55+ properties)
├── chocolatey.ttl                 # Chocolatey (8 classes, 38+ properties)
├── homebrew.ttl                   # Homebrew (23 classes, 65+ properties)
├── nix.ttl                        # Nix (15 classes, 75+ properties)
├── examples.ttl                   # Example instances
├── packagegraph/                  # Python package for data collection
└── README.md                      # This documentation

Note: ETL tools have moved to the platform repository.
```

## Applications

These ontologies enable various applications:

### 1. Package Discovery and Search

- Semantic search across multiple package ecosystems
- Cross-system package recommendation
- Dependency analysis and visualization

### 2. Package Management Tools

- Universal package metadata APIs
- Cross-platform dependency resolution
- Package migration and conversion tools

### 3. Research and Analytics

- Package ecosystem analysis
- Software supply chain research
- Dependency vulnerability tracking
- Package maintenance patterns

### 4. Integration and Interoperability

- Container image metadata standardization
- CI/CD pipeline package tracking
- Software bill of materials (SBOM) generation
- Package provenance and attestation

### 5. Data Collection and ETL

- **Repository Harvesting**: Automated extraction of package metadata from APT and RPM repositories
- **Knowledge Graph Construction**: Builds comprehensive linked data graphs from package ecosystems
- **Data Pipeline Integration**: Supports batch and incremental data processing workflows
- **Multi-format Export**: Converts semantic data to various RDF serializations for different use cases

## Technical Details

### Ontology Design Principles

- **Modularity**: Each system has its own ontology importing the core
- **Extensibility**: Easy to add new package systems or extend existing ones
- **Consistency**: Common patterns for similar concepts across systems
- **Completeness**: Captures both common and unique metadata for each system

### RDF/OWL Features Used

- **Class Hierarchies**: Inheritance relationships between package types
- **Property Hierarchies**: Specialization of dependency and relationship types
- **Domain/Range Restrictions**: Type safety for properties
- **Functional Properties**: Ensures uniqueness of key identifiers and checksums
- **Cardinality Restrictions**: Enforces mandatory and optional property constraints
- **Qualified Cardinality**: Complex restrictions on property values with class constraints
- **Property Equivalencies**: Cross-format mappings for interoperability
- **Annotation Properties**: Metadata about the ontologies themselves including IAO definitions
- **Named Individuals**: Common instances (licenses, architectures, etc.)

### Namespace Management

Each ontology uses its own namespace to avoid conflicts:

- Core: `https://purl.org/packagegraph/ontology/core#`
- VCS: `https://purl.org/packagegraph/ontology/vcs#`
- Debian: `https://purl.org/packagegraph/ontology/debian#`
- RPM: `https://purl.org/packagegraph/ontology/rpm#`
- Arch: `https://purl.org/packagegraph/ontology/archlinux#`
- FreeBSD: `https://purl.org/packagegraph/ontology/freebsd#`
- Chocolatey: `https://purl.org/packagegraph/ontology/chocolatey#`
- Homebrew: `https://purl.org/packagegraph/ontology/homebrew#`
- Nix: `https://purl.org/packagegraph/ontology/nix#`

## Validation and Quality

### OWL 2 Compliance

- **OWL 2 DL Compliant**: All ontologies conform to OWL 2 DL profile
- **Cardinality Constraints**: Comprehensive use of functional properties and cardinality restrictions
- **Protégé Validated**: All files load successfully in Protégé ontology editor
- **Cross-Format Equivalencies**: Property mappings enable package format interoperability

### Schema Validation

- No circular dependencies between imports
- Consistent use of datatypes and object properties  
- Comprehensive IAO_0000115 definitions for all terms
- Proper namespace management and relative imports

### Coverage Analysis

The ontologies cover the major metadata elements found in each package format:

- **Debian**: Control file fields, dependency relationships, maintainer scripts
- **RPM**: RPM header tags, spec file metadata, build information
- **Arch**: PKGBUILD variables, dependency arrays, build functions
- **BSD**: Makefile variables, port options, distinfo checksums
- **Chocolatey**: NuSpec elements, PowerShell scripts, Windows-specific data
- **Homebrew**: Formula DSL, cask artifacts, dependency specifications
- **Nix**: Derivation attributes, build phases, store paths

## Development and Validation

### Build System

The project includes a Makefile for validation and testing:

```bash
make lint           # Validate all TTL files for syntax errors
make lint-combined  # Validate the combined ontology file
```

### Import Structure

All ontologies use relative imports for better portability:
- `owl:imports <core.ttl>` instead of web URLs
- Enables local development and Protégé compatibility

### ETL Tools

ETL (Extract, Transform, Load) tools for package repository data collection have moved to the `platform` repository. The platform repo includes:

- **packagegraph-etl**: Python package for collecting and transforming package metadata
- **Collectors**: Support for Debian APT and RPM repositories
- **Parallel Processing**: Configurable worker pools and chunking
- **Minio Integration**: Content-addressable storage for RDF snapshots
- **TDB2 Building**: Apache Jena tools for creating indexed SPARQL databases

See the `platform` repository for ETL usage and deployment.

## Contributing

To extend or modify these ontologies:

1. **Follow OWL/RDF Best Practices**: Use appropriate property types, maintain
   consistency
1. **Extend Base Classes**: New package types should subclass existing core
   classes where possible
1. **Document Changes**: Add rdfs:label and rdfs:comment for all new terms
1. **Test Compatibility**: Ensure changes don't break existing instances
1. **Update Examples**: Add examples demonstrating new features
1. **Validate Changes**: Run `make lint` to ensure OWL 2 compliance

## License

These ontologies are released under the CC0 License, allowing free use,
modification, and distribution.

## Future Work

Potential extensions and improvements:

### Ontology Extensions
- Container image ontologies (Docker, OCI)
- Language-specific package managers (npm, pip, cargo, gem)
- Mobile app stores (Google Play, App Store)
- Enterprise package management (SCCM, Jamf)
- Package security and vulnerability metadata
- Build system integration (Maven, Gradle, CMake)

### ETL Tool Enhancements
- Additional repository format support (Arch AUR, Homebrew taps, Nix channels)
- Real-time streaming data collection
- Graph database integration (Neo4j, Amazon Neptune)
- Machine learning pipeline integration for package analysis
- Distributed processing with Apache Spark

### Advanced Features
- Reproducible build attestation
- Software supply chain provenance
- Automated vulnerability scanning integration
- Package ecosystem health metrics

## Contact

This is an open-source project. Contributions, suggestions, and feedback are
welcome through standard open-source collaboration channels.
