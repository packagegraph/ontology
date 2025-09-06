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

### 1. Core Package Ontology (`core-package-ontology.ttl`)

- **Purpose**: Base ontology defining common concepts across all package
  management systems
- **Key Classes**: Package, Repository, PackageManager, Dependency, Version,
  Maintainer, License, Architecture
- **Key Properties**: packageName, description, homepage, downloadURL,
  installSize, checksum
- **Namespace**: `http://packagegraph.github.io/ontology/core#`

### 2. Debian/APT Ontology (`debian-package-ontology.ttl`)

- **Purpose**: Represents Debian packages (.deb), APT repositories, and
  Debian-specific metadata
- **Key Classes**: DebianPackage, SourcePackage, BinaryPackage, Suite,
  Component, Section, Priority
- **Key Features**: Debian control file metadata, dependency types (depends,
  recommends, suggests), maintainer scripts
- **Namespace**: `http://packagegraph.github.io/ontology/debian#`

### 3. RPM Ontology (`rpm-package-ontology.ttl`)

- **Purpose**: Represents RPM packages, YUM/DNF repositories, and RPM-specific
  metadata
- **Key Classes**: RPMPackage, SourceRPM, BinaryRPM, RPMGroup, NEVR, Changelog
- **Key Features**: RPM header tags, build metadata, file information, changelog
  entries
- **Namespace**: `http://packagegraph.github.io/ontology/rpm#`

### 4. Arch Linux Ontology (`arch-package-ontology.ttl`)

- **Purpose**: Represents Arch packages, PKGBUILD files, and Pacman repositories
  including AUR
- **Key Classes**: ArchPackage, PKGBUILD, SplitPackage, AUR, SRCINFO,
  PackageGroup
- **Key Features**: PKGBUILD functions, checksums, build options, package groups
- **Namespace**: `http://packagegraph.github.io/ontology/archlinux#`

### 5. BSD Ports Ontology (`bsd-package-ontology.ttl`)

- **Purpose**: Represents BSD ports (FreeBSD, OpenBSD, NetBSD), Makefiles, and
  ports trees
- **Key Classes**: Port, PortsTree, Makefile, PortSkeleton, Distinfo, Category,
  Flavor
- **Key Features**: Port build configuration, patches, options, master sites,
  flavors
- **Namespace**: `http://packagegraph.github.io/ontology/bsd#`

### 6. Chocolatey Ontology (`chocolatey-package-ontology.ttl`)

- **Purpose**: Represents Chocolatey packages, NuGet format, and
  Windows-specific metadata
- **Key Classes**: ChocolateyPackage, Nupkg, Nuspec, ChocolateyScript,
  InstallScript, UninstallScript
- **Key Features**: PowerShell scripts, installer types, registry keys,
  Windows-specific properties
- **Namespace**: `http://packagegraph.github.io/ontology/chocolatey#`

### 7. Homebrew Ontology (`homebrew-package-ontology.ttl`)

- **Purpose**: Represents Homebrew formulas, casks, taps, and macOS-specific
  packaging
- **Key Classes**: Formula, Cask, Tap, Bottle, SoftwareSpec, Artifact (Apps,
  Fonts, etc.)
- **Key Features**: Build specifications, dependency types, macOS application
  artifacts, bottles
- **Namespace**: `http://packagegraph.github.io/ontology/homebrew#`

### 8. Nix Ontology (`nix-package-ontology.ttl`)

- **Purpose**: Represents Nix derivations, expressions, Nixpkgs, and functional
  package management
- **Key Classes**: Derivation, StoreDerivation, NixExpression, Flake,
  StdenvMkDerivation
- **Key Features**: Build phases, store paths, reproducible builds, functional
  dependencies
- **Namespace**: `http://packagegraph.github.io/ontology/nix#`

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
├── core-package-ontology.ttl      # Base ontology (8 classes, 18 properties)
├── debian-package-ontology.ttl    # Debian/APT (8 classes, 35 properties)  
├── rpm-package-ontology.ttl       # RPM/YUM/DNF (8 classes, 45 properties)
├── arch-package-ontology.ttl      # Arch Linux (7 classes, 40 properties)
├── bsd-package-ontology.ttl       # BSD Ports (13 classes, 55 properties)
├── chocolatey-package-ontology.ttl # Chocolatey (8 classes, 38 properties)
├── homebrew-package-ontology.ttl  # Homebrew (23 classes, 65 properties)
├── nix-package-ontology.ttl       # Nix (15 classes, 75 properties)
├── package-examples.ttl           # Example instances
├── package-ontologies.ttl         # Combined consolidated file
└── README.md                      # This documentation
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
- **Annotation Properties**: Metadata about the ontologies themselves
- **Named Individuals**: Common instances (licenses, architectures, etc.)

### Namespace Management

Each ontology uses its own namespace to avoid conflicts:

- Core: `http://packagegraph.github.io/ontology/core#`
- Debian: `http://packagegraph.github.io/ontology/debian#`
- RPM: `http://packagegraph.github.io/ontology/rpm#`
- Arch: `http://packagegraph.github.io/ontology/archlinux#`
- BSD: `http://packagegraph.github.io/ontology/bsd#`
- Chocolatey: `http://packagegraph.github.io/ontology/chocolatey#`
- Homebrew: `http://packagegraph.github.io/ontology/homebrew#`
- Nix: `http://packagegraph.github.io/ontology/nix#`

## Validation and Quality

### Schema Validation

- OWL 2 DL compliant ontologies
- No circular dependencies between imports
- Consistent use of datatypes and object properties
- Comprehensive documentation with rdfs:label and rdfs:comment

### Coverage Analysis

The ontologies cover the major metadata elements found in each package format:

- **Debian**: Control file fields, dependency relationships, maintainer scripts
- **RPM**: RPM header tags, spec file metadata, build information
- **Arch**: PKGBUILD variables, dependency arrays, build functions
- **BSD**: Makefile variables, port options, distinfo checksums
- **Chocolatey**: NuSpec elements, PowerShell scripts, Windows-specific data
- **Homebrew**: Formula DSL, cask artifacts, dependency specifications
- **Nix**: Derivation attributes, build phases, store paths

## Contributing

To extend or modify these ontologies:

1. **Follow OWL/RDF Best Practices**: Use appropriate property types, maintain
   consistency
1. **Extend Base Classes**: New package types should subclass existing core
   classes where possible
1. **Document Changes**: Add rdfs:label and rdfs:comment for all new terms
1. **Test Compatibility**: Ensure changes don't break existing instances
1. **Update Examples**: Add examples demonstrating new features

## License

These ontologies are released under the CC0 License, allowing free use,
modification, and distribution.

## Future Work

Potential extensions and improvements:

- Container image ontologies (Docker, OCI)
- Language-specific package managers (npm, pip, cargo, gem)
- Mobile app stores (Google Play, App Store)
- Enterprise package management (SCCM, Jamf)
- Package security and vulnerability metadata
- Build system integration (Maven, Gradle, CMake)
- Reproducible build attestation
- Software supply chain provenance

## Contact

This is an open-source project. Contributions, suggestions, and feedback are
welcome through standard open-source collaboration channels.
