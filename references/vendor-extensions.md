# Vendor Extensions Guide

## Overview

> The core ontology provides abstract extension points (classes like PackageSet, Distribution). Vendors create their own ontology file in their own namespace that `owl:imports` core and adds vendor-specific instances and properties. The core ontology never knows about — or is polluted by — vendor concepts.

A vendor extension is a standalone Turtle file that extends the core PackageGraph ontology with concepts specific to a single vendor's products, processes, or classifications. Each extension lives in its own namespace (e.g., `redhat#`, `suse#`), imports the core files it depends on, and adds vendor-specific individuals and properties.

This pattern keeps the core ontology clean and generic while allowing any vendor to layer on their own product taxonomy, lifecycle classifications, or package metadata without coordinating with other vendors or modifying shared files.

## When to Use a Vendor Extension

**Use when:** the concept is specific to one vendor's products, processes, or classifications. Examples:

- Red Hat ACG lifecycle levels
- RHIVOS Core, RHEL BaseOS, RHEL AppStream package sets
- SUSE support level classifications
- Canonical Pro subscription tiers

**Don't use when:** the concept applies across multiple vendors or distributions. Vulnerability tracking, code quality metrics, patch counts, commit activity, and similar cross-cutting concerns belong in the shared ontology files (`security.ttl`, `metrics.ttl`, `vcs.ttl`).

## Creating a Vendor Extension — Step by Step

### 1. Choose a namespace

Follow the project convention:

```
https://packagegraph.github.io/ontology/<vendorname>#
```

For example: `https://packagegraph.github.io/ontology/redhat#`

### 2. Choose a prefix

Pick a short, lowercase prefix for readability:

| Vendor | Prefix |
|--------|--------|
| Red Hat | `rh:` |
| SUSE | `suse:` |
| Canonical | `canonical:` |

### 3. Declare the ontology with imports

Your extension must declare itself as an `owl:Ontology` and import every core file it extends:

```turtle
<https://packagegraph.github.io/ontology/vendorname#> a owl:Ontology ;
    owl:imports <core.ttl> , <rpm.ttl> .
```

Only import what you actually use. If you only extend `pkg:PackageSet` from `core.ttl`, you only need to import `core.ttl`. If you also add properties with `rdfs:domain rpm:RPMPackage`, import `rpm.ttl` as well.

### 4. Add standard metadata

Include title, description, version, creation date, and license:

```turtle
<https://packagegraph.github.io/ontology/vendorname#> a owl:Ontology ;
    rdfs:label "VendorName Extension Ontology" ;
    rdfs:comment "Vendor-specific extensions for VendorName products" ;
    dcterms:created "2025-01-01"^^xsd:date ;
    dcterms:creator "Package Management Ontology Project" ;
    dcterms:title "VendorName Extension Ontology" ;
    dcterms:description "..." ;
    dcterms:license <https://creativecommons.org/publicdomain/zero/1.0/> ;
    owl:versionInfo "0.1.0" ;
    owl:imports <core.ttl> .
```

### 5. Define vendor-specific PackageSet instances

Instantiate `pkg:PackageSet` for each of your product's package groupings:

```turtle
vn:MyProductCore a owl:NamedIndividual, pkg:PackageSet ;
    rdfs:label "My Product Core" ;
    rdfs:comment "Core packages for My Product" .
```

Each instance is a named individual that represents a concrete package set in your product lineup.

### 6. Define vendor-specific properties

Add data or object properties on existing core classes. Use `rdfs:domain` to target the class you are extending:

```turtle
vn:supportLevel a owl:DatatypeProperty ;
    rdfs:label "support level" ;
    rdfs:comment "The vendor support level for this package" ;
    rdfs:domain rpm:RPMPackage ;
    rdfs:range xsd:string .
```

### 7. Never redefine or modify core classes

You can reference core classes (`pkg:PackageSet`, `rpm:RPMPackage`, `pkg:Distribution`) in `rdfs:domain` and `rdfs:range` declarations. You must **not** redefine them, add restrictions to them, or change their labels, comments, or class hierarchy. Extension means adding new terms that point to existing classes — not changing the classes themselves.

## Walkthrough: `redhat.ttl`

The `redhat.ttl` file is the reference implementation of a vendor extension. Here is an annotated walkthrough.

### Ontology declaration and imports

```turtle
@prefix rh: <https://packagegraph.github.io/ontology/redhat#> .
@prefix pkg: <https://packagegraph.github.io/ontology/core#> .
@prefix rpm: <https://packagegraph.github.io/ontology/rpm#> .

<https://packagegraph.github.io/ontology/redhat#> a owl:Ontology ;
    rdfs:label "Red Hat Vendor Extension Ontology" ;
    rdfs:comment "Vendor-specific extension ontology for Red Hat products, ..." ;
    dcterms:created "2025-09-05"^^xsd:date ;
    dcterms:license <https://creativecommons.org/publicdomain/zero/1.0/> ;
    owl:versionInfo "0.3.0" ;
    owl:imports <core.ttl> , <rpm.ttl> .
```

The extension declares the `rh:` prefix for its own namespace and imports both `core.ttl` (for `pkg:PackageSet`) and `rpm.ttl` (for `rpm:RPMPackage`). Standard metadata follows the same pattern as the core files.

### PackageSet instances

```turtle
rh:RHIVOSCore a owl:NamedIndividual, pkg:PackageSet ;
    rdfs:label "RHIVOS Core RPM Set" ;
    rdfs:comment "The core package set for Red Hat In-Vehicle Operating System, ..." .

rh:RHELBaseOS a owl:NamedIndividual, pkg:PackageSet ;
    rdfs:label "RHEL BaseOS" ;
    rdfs:comment "The base operating system package set ..." .

rh:RHELAppStream a owl:NamedIndividual, pkg:PackageSet ;
    rdfs:label "RHEL AppStream" ;
    rdfs:comment "The application stream package set ..." .
```

Each instance is typed as both `owl:NamedIndividual` and `pkg:PackageSet`. These are concrete named individuals — RHIVOS Core, RHEL BaseOS, and RHEL AppStream — that represent actual Red Hat product package groupings. Packages can be linked to them using the core property `pkg:memberOfPackageSet`.

### ACG lifecycle level properties

```turtle
rh:acgLifecycleLevel a owl:DatatypeProperty ;
    rdfs:label "ACG lifecycle level" ;
    rdfs:comment "The RHEL Application Compatibility Guide lifecycle classification
                  (0=ignore, 1=high priority, 2-3=medium, 4=low priority)" ;
    rdfs:domain rpm:RPMPackage ;
    rdfs:range xsd:integer .

rh:acgLifecycleLevelLabel a owl:DatatypeProperty ;
    rdfs:label "ACG lifecycle level label" ;
    rdfs:comment "Human-readable label for the ACG lifecycle level" ;
    rdfs:domain rpm:RPMPackage ;
    rdfs:range xsd:string .
```

These two properties attach Red Hat-specific lifecycle metadata to `rpm:RPMPackage` instances. The numeric level and its human-readable label are both defined as datatype properties. Note that `rdfs:domain` points to `rpm:RPMPackage` — a class defined in `rpm.ttl`, not redefined here. The extension adds new properties that apply to existing classes without modifying `rpm.ttl` in any way.

## Loading Vendor Extensions

To load the full ontology stack into a triplestore, load core files first, then vendor extensions:

```
LOAD <core.ttl>
LOAD <vcs.ttl>
LOAD <rpm.ttl>
LOAD <security.ttl>
LOAD <metrics.ttl>
LOAD <redhat.ttl>     # vendor extension — loaded last
```

Vendor extensions declare `owl:imports` for their dependencies, so most triplestores will handle the load order automatically. The explicit order above is for clarity and for systems that do not auto-resolve imports.

You can load multiple vendor extensions side by side. Each lives in its own namespace, so there are no conflicts:

```
LOAD <redhat.ttl>
LOAD <suse.ttl>
LOAD <canonical.ttl>
```

## Template

Copy this template to start a new vendor extension:

```turtle
# Vendor Extension Template
@prefix vn:      <https://packagegraph.github.io/ontology/vendorname#> .
@prefix pkg:     <https://packagegraph.github.io/ontology/core#> .
@prefix rpm:     <https://packagegraph.github.io/ontology/rpm#> .
@prefix owl:     <http://www.w3.org/2002/07/owl#> .
@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .

<https://packagegraph.github.io/ontology/vendorname#> a owl:Ontology ;
    rdfs:label "VendorName Package Ontology Extension" ;
    rdfs:comment "Vendor-specific extensions for VendorName products" ;
    dcterms:created "2025-01-01"^^xsd:date ;
    dcterms:license <https://creativecommons.org/publicdomain/zero/1.0/> ;
    owl:versionInfo "0.1.0" ;
    owl:imports <core.ttl> .

# Package Set instances
vn:MyProductCore a pkg:PackageSet ;
    rdfs:label "My Product Core" ;
    rdfs:comment "Core packages for My Product" .

# Vendor-specific properties
vn:supportLevel a owl:DatatypeProperty ;
    rdfs:label "support level" ;
    rdfs:comment "The vendor support level for this package" ;
    rdfs:domain rpm:RPMPackage ;
    rdfs:range xsd:string .
```

Replace `vendorname` with your vendor's short name, `vn:` with your chosen prefix, and adjust the package sets and properties to match your products.
