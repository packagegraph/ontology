#!/usr/bin/env python3
"""
Add @en language tags and rdfs:isDefinedBy to all schema elements.

Walks all ontology .ttl files (not examples) and:
1. Adds @en language tag to all plain literals on rdfs:label, rdfs:comment, IAO:0000115
2. Adds rdfs:isDefinedBy <ontology-uri> to all owl:Class, owl:ObjectProperty, owl:DatatypeProperty

Usage:
    cd ontology
    uv run python3 scripts/add_schema_annotations.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path
from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef

# Namespaces
IAO = Namespace("http://purl.obolibrary.org/obo/IAO_")
SH = Namespace("http://www.w3.org/ns/shacl#")


def derive_ontology_uri(file_path: Path) -> str:
    """
    Derive the ontology URI from the file path.

    Examples:
        core/core.ttl → https://purl.org/packagegraph/ontology/core#
        extensions/security/security.ttl → https://purl.org/packagegraph/ontology/security#
        ecosystems/rpm/rpm.ttl → https://purl.org/packagegraph/ontology/rpm#
    """
    parts = file_path.parts

    if parts[0] == "core":
        module = "core"
    elif parts[0] == "extensions":
        module = parts[1]  # security, vcs, slsa, metrics, dq
    elif parts[0] == "ecosystems":
        module = parts[1]  # rpm, deb, npm, etc.
    else:
        # Fallback for references/ or other dirs
        module = file_path.stem

    return f"https://purl.org/packagegraph/ontology/{module}#"


def add_annotations(file_path: Path, dry_run: bool = False) -> tuple[int, int]:
    """
    Add @en language tags and rdfs:isDefinedBy to a single ontology file.

    Returns:
        (lang_tags_added, isDefinedBy_added)
    """
    print(f"Processing {file_path}...")

    g = Graph()
    g.parse(file_path, format="turtle")

    ontology_uri = URIRef(derive_ontology_uri(file_path))

    lang_tags = 0
    is_defined_by = 0

    # Add language tags to plain literals on rdfs:label, rdfs:comment, IAO:0000115
    properties_needing_tags = [RDFS.label, RDFS.comment, IAO["0000115"]]

    for prop in properties_needing_tags:
        for s, p, o in list(g.triples((None, prop, None))):
            if isinstance(o, Literal) and o.language is None and o.datatype is None:
                # Plain literal without language tag
                new_literal = Literal(str(o), lang="en")
                g.remove((s, p, o))
                g.add((s, p, new_literal))
                lang_tags += 1

    # Add language tags to SHACL sh:message (validation error messages)
    for s, p, o in list(g.triples((None, SH.message, None))):
        if isinstance(o, Literal) and o.language is None and o.datatype is None:
            new_literal = Literal(str(o), lang="en")
            g.remove((s, p, o))
            g.add((s, p, new_literal))
            lang_tags += 1

    # Add rdfs:isDefinedBy to all classes and properties
    entity_types = [OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty]

    for entity_type in entity_types:
        for entity in g.subjects(RDF.type, entity_type):
            # Skip blank nodes
            if isinstance(entity, URIRef):
                # Only add if not already present
                if not any(g.triples((entity, RDFS.isDefinedBy, None))):
                    g.add((entity, RDFS.isDefinedBy, ontology_uri))
                    is_defined_by += 1

    if not dry_run:
        # Serialize back to Turtle
        # Use format='turtle' with base=None to preserve relative URIs within the namespace
        g.serialize(destination=str(file_path), format="turtle")

    return lang_tags, is_defined_by


def main():
    parser = argparse.ArgumentParser(description="Add schema annotations to ontology files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    args = parser.parse_args()

    # Find all ontology .ttl files (not examples, not in .venv)
    ontology_files = []

    for pattern in ["core/*.ttl", "extensions/*/*.ttl", "ecosystems/*/*.ttl"]:
        for f in Path(".").glob(pattern):
            # Skip examples and .venv
            if ".examples." in f.name or ".venv" in str(f):
                continue
            ontology_files.append(f)

    ontology_files.sort()

    print(f"Found {len(ontology_files)} ontology files\n")

    if args.dry_run:
        print("DRY RUN — no files will be modified\n")

    total_lang_tags = 0
    total_is_defined_by = 0

    for f in ontology_files:
        try:
            lang_tags, is_defined_by = add_annotations(f, args.dry_run)
            total_lang_tags += lang_tags
            total_is_defined_by += is_defined_by
            print(f"  {lang_tags} language tags, {is_defined_by} isDefinedBy\n")
        except Exception as e:
            print(f"  ERROR: {e}\n", file=sys.stderr)
            continue

    print(f"Total: {total_lang_tags} language tags, {total_is_defined_by} isDefinedBy added")

    if not args.dry_run:
        print("\nRunning make lint to verify...")
        import subprocess
        result = subprocess.run(["uv", "run", "make", "lint"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ All files still parse as valid Turtle")
        else:
            print("✗ Lint failed:")
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
