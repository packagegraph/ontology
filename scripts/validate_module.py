#!/usr/bin/env python3
"""Per-module SHACL validation. Loads only the module's ontology + its imports."""

import sys
from pathlib import Path
from rdflib import Graph

# Map namespace URIs to module directories (for resolving owl:imports)
NS_TO_PATH = {
    "https://purl.org/packagegraph/ontology/core#": "core/core.ttl",
    "https://purl.org/packagegraph/ontology/vcs#": "extensions/vcs/vcs.ttl",
    "https://purl.org/packagegraph/ontology/security#": "extensions/security/security.ttl",
    "https://purl.org/packagegraph/ontology/metrics#": "extensions/metrics/metrics.ttl",
    "https://purl.org/packagegraph/ontology/slsa#": "extensions/slsa/slsa.ttl",
    "https://purl.org/packagegraph/ontology/dq#": "extensions/dq/dq.ttl",
    "https://purl.org/packagegraph/ontology/attestation#": "extensions/attestation/attestation.ttl",
    "https://purl.org/packagegraph/ontology/rpm#": "ecosystems/rpm/rpm.ttl",
}

MODULE_DIRS = {
    "core": "core",
    **{d.name: str(d) for d in Path("extensions").iterdir() if d.is_dir()},
    **{d.name: str(d) for d in Path("ecosystems").iterdir() if d.is_dir()},
}


def find_module_files(module_name):
    """Find ontology, SHACL, and example files for a module."""
    d = MODULE_DIRS.get(module_name)
    if not d:
        print(f"Unknown module: {module_name}")
        sys.exit(1)

    d = Path(d)
    ontology = d / f"{module_name}.ttl"
    shacl = d / f"{module_name}.shacl.ttl"
    examples = d / f"{module_name}.examples.ttl"

    return ontology, shacl, examples


def resolve_imports(ontology_path):
    """Parse owl:imports from a file using rdflib and return paths to imported ontologies.

    Ontology files use prefixed names for imports (e.g. ``owl:imports att:, pkg:``),
    so regex on raw text cannot resolve them.  Parsing the file with rdflib expands
    prefixed names to full URIs, which we then look up in NS_TO_PATH.
    """
    from rdflib import OWL

    g = Graph()
    g.parse(str(ontology_path), format="turtle")
    paths = []
    for _, _, imported in g.triples((None, OWL.imports, None)):
        uri = str(imported)
        path = NS_TO_PATH.get(uri)
        if not path:
            # Try with trailing # (namespace form vs ontology IRI)
            path = NS_TO_PATH.get(uri + "#")
        if path and Path(path).exists():
            paths.append(path)
    return paths


def validate_module(module_name, quiet=False):
    """Validate a single module: load ontology + imports + SHACL, run pyshacl."""
    ontology, shacl, examples = find_module_files(module_name)

    if not ontology.exists():
        if not quiet:
            print(f"  SKIP {module_name}: no ontology file")
        return True

    # Build data graph: imports + module ontology + examples
    data_g = Graph()

    # Load imports (recursively would be better, but one level is sufficient)
    import_paths = resolve_imports(ontology)
    for ip in import_paths:
        data_g.parse(ip, format="turtle")

    # Load module ontology
    data_g.parse(str(ontology), format="turtle")

    # Load examples if present
    if examples.exists():
        data_g.parse(str(examples), format="turtle")

    # If no SHACL shapes, just validate parsing
    if not shacl.exists():
        if not quiet:
            print(f"  ✓ {module_name}: {len(data_g)} triples (no SHACL shapes)")
        return True

    # Run SHACL validation
    try:
        from pyshacl import validate
        shacl_g = Graph()
        shacl_g.parse(str(shacl), format="turtle")

        conforms, _, results_text = validate(
            data_g, shacl_graph=shacl_g, inference="rdfs",
            serialize_report_graph=False
        )

        if conforms:
            print(f"  ✓ {module_name}: {len(data_g)} triples, SHACL OK")
        else:
            print(f"  ✗ {module_name}: SHACL violations")
            # Show first few violations
            for line in results_text.split("\n")[:10]:
                print(f"    {line}")
        return conforms

    except ImportError:
        if not quiet:
            print(f"  ⚠ {module_name}: pyshacl not installed, skipping SHACL")
        return True


def main():
    if "--all" in sys.argv:
        print("Validating all modules:")
        all_ok = True
        for name in sorted(MODULE_DIRS.keys()):
            if not validate_module(name):
                all_ok = False
        sys.exit(0 if all_ok else 1)
    elif len(sys.argv) > 1:
        name = sys.argv[1]
        ok = validate_module(name)
        sys.exit(0 if ok else 1)
    else:
        print("Usage: validate_module.py <module-name> | --all")
        sys.exit(1)


if __name__ == "__main__":
    main()
