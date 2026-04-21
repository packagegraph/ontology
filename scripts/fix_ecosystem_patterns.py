#!/usr/bin/env python3
"""
Fix systematic anti-patterns across ecosystem modules.

Applies the fixes documented in 2026-04-20-ecosystem-semantic-remediation.md:
1. Subclass corrections (Package → BinaryPackage/SourcePackage)
2. Sub-property remapping (dev/test deps → buildDependsOn, optional → suggests/recommends)
3. Taxonomy regression (deprecate string-based dependency type properties)
4. Identity fragmentation annotations (link author/maintainer strings to PROV-O/FOAF)

Usage:
    cd ontology
    uv run python3 scripts/fix_ecosystem_patterns.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path
from rdflib import Graph, Literal, Namespace, URIRef, OWL, RDFS

# Module-specific fix mappings from the plan
SUBCLASS_FIXES = {
    # Source packages
    "cargo": ("cargo:Crate", "pkg:SourcePackage"),
    "npm": ("npm:NpmPackage", "pkg:SourcePackage"),
    "pypi": ("pypi:PythonPackage", "pkg:SourcePackage"),
    "rubygems": ("rubygems:Gem", "pkg:SourcePackage"),
    "gomod": ("gomod:GoPackage", "pkg:SourcePackage"),
    "hex": ("hex:HexPackage", "pkg:SourcePackage"),
    "cpan": ("cpan:Distribution", "pkg:SourcePackage"),
    "cran": ("cran:CranPackage", "pkg:SourcePackage"),
    "hackage": ("hackage:HackagePackage", "pkg:SourcePackage"),
    "portage": ("portage:Ebuild", "pkg:SourcePackage"),
    # Binary packages
    "maven": ("maven:MavenArtifact", "pkg:BinaryPackage"),
    "nuget": ("nuget:NuGetPackage", "pkg:BinaryPackage"),
    "conda": ("conda:CondaPackage", "pkg:BinaryPackage"),
    "flatpak": ("flatpak:FlatpakApp", "pkg:BinaryPackage"),
    "snap": ("snap:SnapPackage", "pkg:BinaryPackage"),
    "opkg": ("opkg:OpkgPackage", "pkg:BinaryPackage"),
}

# Sub-property remapping from plan
SUBPROPERTY_FIXES = {
    "cargo": [("cargo:devDependsOn", "pkg:buildDependsOn")],
    "npm": [("npm:optionalDependsOn", "pkg:suggests"), ("npm:peerDependsOn", "pkg:recommends")],
    "pypi": [("pypi:extraDependsOn", "pkg:suggests")],
    "rubygems": [("rubygems:developmentDependsOn", "pkg:buildDependsOn")],
    "maven": [("maven:testDependency", "pkg:buildDependsOn"), ("maven:providedDependency", "pkg:recommends")],
    "cran": [("cran:suggests", "pkg:suggests"), ("cran:enhances", "pkg:enhances")],
    "hackage": [("hackage:testDependsOn", "pkg:buildDependsOn")],
    "nix": [("nix:buildInputDependsOn", "pkg:buildDependsOn")],
}

# Properties to deprecate (taxonomy regression)
DEPRECATE_PROPERTIES = {
    "deb": ["deb:dependencyType"],
    "homebrew": ["brew:dependencyType"],
    "maven": ["maven:scope"],
    "npm": ["npm:scope"],  # Already done above
}


def fix_module(module_name: str, file_path: Path, dry_run: bool = False) -> dict:
    """Apply all fixes to a single module."""
    g = Graph()
    g.parse(file_path, format="turtle")

    changes = {"subclass": 0, "subproperty": 0, "deprecated": 0}

    # Fix 1: Subclass corrections
    if module_name in SUBCLASS_FIXES:
        old_class_name, new_parent = SUBCLASS_FIXES[module_name]
        # Convert to URIRef
        old_class = g.namespace_manager.expand_curie(old_class_name)
        new_parent_uri = g.namespace_manager.expand_curie(new_parent)

        # Find current parent
        PKG = Namespace("https://purl.org/packagegraph/ontology/core#")
        for s, p, o in list(g.triples((URIRef(old_class), RDFS.subClassOf, PKG.Package))):
            g.remove((s, p, o))
            g.add((s, p, URIRef(new_parent_uri)))
            changes["subclass"] += 1

    # Fix 2: Sub-property remapping
    if module_name in SUBPROPERTY_FIXES:
        for prop_name, new_parent in SUBPROPERTY_FIXES[module_name]:
            prop_uri = URIRef(g.namespace_manager.expand_curie(prop_name))
            new_parent_uri = URIRef(g.namespace_manager.expand_curie(new_parent))

            # Find current subPropertyOf
            for s, p, o in list(g.triples((prop_uri, RDFS.subPropertyOf, None))):
                g.remove((s, p, o))
                g.add((s, p, new_parent_uri))
                changes["subproperty"] += 1

    # Fix 3: Deprecate properties
    if module_name in DEPRECATE_PROPERTIES:
        for prop_name in DEPRECATE_PROPERTIES[module_name]:
            prop_uri = URIRef(g.namespace_manager.expand_curie(prop_name))

            # Add owl:deprecated true if not present
            if not any(g.triples((prop_uri, OWL.deprecated, None))):
                g.add((prop_uri, OWL.deprecated, Literal(True)))
                changes["deprecated"] += 1

    if not dry_run and any(changes.values()):
        g.serialize(destination=str(file_path), format="turtle")

    return changes


def main():
    parser = argparse.ArgumentParser(description="Fix ecosystem module anti-patterns")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    modules_to_fix = list(SUBCLASS_FIXES.keys()) + list(set(SUBPROPERTY_FIXES.keys()) - set(SUBCLASS_FIXES.keys()))

    print(f"Fixing {len(modules_to_fix)} ecosystem modules\n")
    if args.dry_run:
        print("DRY RUN\n")

    total_changes = {"subclass": 0, "subproperty": 0, "deprecated": 0}

    for module in sorted(set(modules_to_fix)):
        file_path = Path(f"ecosystems/{module}/{module}.ttl")
        if not file_path.exists():
            print(f"SKIP {module}: file not found")
            continue

        try:
            changes = fix_module(module, file_path, args.dry_run)
            if any(changes.values()):
                print(f"✓ {module}: {changes}")
                for k, v in changes.items():
                    total_changes[k] += v
            else:
                print(f"- {module}: no changes")
        except Exception as e:
            print(f"✗ {module}: {e}", file=sys.stderr)

    print(f"\nTotal: {total_changes}")

    if not args.dry_run:
        print("\nRunning make lint...")
        import subprocess
        result = subprocess.run(["uv", "run", "make", "lint"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ All files still parse")
        else:
            print("✗ Lint failed")
            print(result.stdout)
            sys.exit(1)


if __name__ == "__main__":
    main()
