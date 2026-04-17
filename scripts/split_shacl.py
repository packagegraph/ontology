#!/usr/bin/env python3
"""Split monolithic shacl.ttl into per-module .shacl.ttl files."""

from pathlib import Path
from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import SH

# Map namespace URIs to module directories
NS_TO_DIR = {
    "https://purl.org/packagegraph/ontology/core#": "core",
    "https://purl.org/packagegraph/ontology/security#": "extensions/security",
    "https://purl.org/packagegraph/ontology/vcs#": "extensions/vcs",
    "https://purl.org/packagegraph/ontology/metrics#": "extensions/metrics",
    "https://purl.org/packagegraph/ontology/slsa#": "extensions/slsa",
    "https://purl.org/packagegraph/ontology/debian#": "ecosystems/debian",
    "https://purl.org/packagegraph/ontology/rpm#": "ecosystems/rpm",
    "https://purl.org/packagegraph/ontology/apk#": "ecosystems/apk",
    "https://purl.org/packagegraph/ontology/pacman#": "ecosystems/pacman",
    "https://purl.org/packagegraph/ontology/portage#": "ecosystems/portage",
    "https://purl.org/packagegraph/ontology/xbps#": "ecosystems/xbps",
    "https://purl.org/packagegraph/ontology/bsdpkg#": "ecosystems/bsdpkg",
    "https://purl.org/packagegraph/ontology/nix#": "ecosystems/nix",
    "https://purl.org/packagegraph/ontology/homebrew#": "ecosystems/homebrew",
    "https://purl.org/packagegraph/ontology/chocolatey#": "ecosystems/chocolatey",
    "https://purl.org/packagegraph/ontology/flatpak#": "ecosystems/flatpak",
    "https://purl.org/packagegraph/ontology/snap#": "ecosystems/snap",
    "https://purl.org/packagegraph/ontology/npm#": "ecosystems/npm",
    "https://purl.org/packagegraph/ontology/pypi#": "ecosystems/pypi",
    "https://purl.org/packagegraph/ontology/cargo#": "ecosystems/cargo",
    "https://purl.org/packagegraph/ontology/gomod#": "ecosystems/gomod",
    "https://purl.org/packagegraph/ontology/conda#": "ecosystems/conda",
    "https://purl.org/packagegraph/ontology/maven#": "ecosystems/maven",
    "https://purl.org/packagegraph/ontology/rubygems#": "ecosystems/rubygems",
    "https://purl.org/packagegraph/ontology/cpan#": "ecosystems/cpan",
    "https://purl.org/packagegraph/ontology/cran#": "ecosystems/cran",
    "https://purl.org/packagegraph/ontology/hackage#": "ecosystems/hackage",
    "https://purl.org/packagegraph/ontology/nuget#": "ecosystems/nuget",
    "https://purl.org/packagegraph/ontology/hex#": "ecosystems/hex",
    "https://purl.org/packagegraph/ontology/bitbake#": "ecosystems/bitbake",
    "https://purl.org/packagegraph/ontology/buildroot#": "ecosystems/buildroot",
    "https://purl.org/packagegraph/ontology/opkg#": "ecosystems/opkg",
}


def classify_shape(shape_uri, target_class_uri):
    """Determine which module a shape belongs to based on its target class."""
    tc = str(target_class_uri)
    for ns, directory in NS_TO_DIR.items():
        if tc.startswith(ns):
            return directory
    # Fallback: use shape URI namespace
    su = str(shape_uri)
    for ns, directory in NS_TO_DIR.items():
        if su.startswith(ns):
            return directory
    return "core"


def get_shape_triples(g, shape):
    """Get all triples belonging to a shape (the shape node + its blank node properties)."""
    triples = set()
    for p, o in g.predicate_objects(shape):
        triples.add((shape, p, o))
        # Follow blank nodes (property shapes)
        if isinstance(o, URIRef):
            continue
        for p2, o2 in g.predicate_objects(o):
            triples.add((o, p2, o2))
            if not isinstance(o2, URIRef) and not hasattr(o2, 'toPython'):
                for p3, o3 in g.predicate_objects(o2):
                    triples.add((o2, p3, o3))
    return triples


def main():
    g = Graph()
    g.parse("shacl.ttl", format="turtle")

    # Group shapes by module
    module_shapes: dict[str, set] = {}

    for shape in g.subjects(RDF.type, SH.NodeShape):
        targets = list(g.objects(shape, SH.targetClass))
        if targets:
            module = classify_shape(shape, targets[0])
        else:
            module = classify_shape(shape, shape)

        if module not in module_shapes:
            module_shapes[module] = set()
        module_shapes[module].update(get_shape_triples(g, shape))

    # Write per-module .shacl.ttl files
    for module_dir, triples in sorted(module_shapes.items()):
        module_name = Path(module_dir).name
        out_g = Graph()

        # Copy all namespace bindings
        for prefix, ns in g.namespaces():
            out_g.bind(prefix, ns)

        for s, p, o in triples:
            out_g.add((s, p, o))

        outpath = Path(module_dir) / f"{module_name}.shacl.ttl"
        out_g.serialize(destination=str(outpath), format="turtle")
        print(f"  {outpath}: {len(triples)} triples ({len(list(out_g.subjects(RDF.type, SH.NodeShape)))} shapes)")

    # Remove old monolithic file
    Path("shacl.ttl").unlink()
    print(f"\nSplit into {len(module_shapes)} module SHACL files, removed shacl.ttl")


if __name__ == "__main__":
    main()
