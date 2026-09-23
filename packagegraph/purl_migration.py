"""Regenerate PURLs in an offline, single-graph export without dropping facts.

This never sends updates to production. Keep the export's named-graph identity
when loading the validated result through the platform replacement pipeline.
"""
import argparse
from pathlib import Path
import re
from urllib.parse import unquote_to_bytes

import rdflib
from packageurl import PackageURL
from rdflib import Graph, Literal, RDF
from rdflib.namespace import XSD

from packagegraph.purls import PKG, identity_purl, parse_canonical, validate_graph


def normalize_legacy(value: str) -> PackageURL:
    # The reference parser normalizes permissively. Reject inputs for which that
    # normalization would discard evidence before allowing encoding/order fixes.
    if re.search(r"%(?![0-9A-Fa-f]{2})|\s", value):
        raise ValueError(f"invalid legacy syntax: {value}")
    try:
        unquote_to_bytes(value).decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError(f"invalid legacy syntax (UTF-8): {value}") from error
    path, _, subpath = value.partition("#")
    if "#" in value and any(part in ("", ".", "..")
                            for part in unquote_to_bytes(subpath).decode().split("/")):
        raise ValueError(f"invalid legacy syntax (subpath): {value}")
    coordinates, _, qualifiers_text = path.partition("?")
    if coordinates.endswith("@"):
        raise ValueError(f"invalid legacy syntax (empty version): {value}")
    if "?" in path:
        keys = []
        for qualifier in qualifiers_text.split("&"):
            key, separator, qualifier_value = qualifier.partition("=")
            if not separator or not qualifier_value or not re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]*", key):
                raise ValueError(f"invalid legacy syntax (qualifier): {value}")
            keys.append(key.lower())
        if len(keys) != len(set(keys)):
            raise ValueError(f"invalid legacy syntax (duplicate qualifier): {value}")
    parsed = PackageURL.from_string(value)
    qualifiers = dict(parsed.qualifiers)
    version = parsed.version
    if parsed.type == "rpm" and version and ":" in version:
        epoch, version = version.split(":", 1)
        if not epoch.isdecimal() or ("epoch" in qualifiers and qualifiers["epoch"] != epoch):
            raise ValueError(f"ambiguous RPM epoch: {value}")
        if int(epoch):
            qualifiers["epoch"] = epoch
    result = PackageURL(parsed.type, parsed.namespace, parsed.name, version,
                        qualifiers, parsed.subpath)
    return parse_canonical(result.to_string())


def migrate_graph(graph: Graph) -> Graph:
    """Return a regenerated copy; refuse ambiguous/unmatched evidence atomically."""
    result = Graph(identifier=graph.identifier)
    for prefix, namespace in graph.namespaces():
        result.bind(prefix, namespace)
    result += graph
    identities = set(graph.subjects(RDF.type, PKG.PackageIdentity))
    identities.update(graph.objects(None, PKG.isVersionOf))
    for identity in identities:
        values = list(graph.objects(identity, PKG.purl))
        if not values:
            continue  # Coverage is separate: do not invent a mapping.
        parsed = [normalize_legacy(str(value)) for value in values]
        bases = {identity_purl(value) for value in parsed}
        if len(bases) != 1:
            raise ValueError(f"{identity}: conflicting identity coordinates")
        base = PackageURL.from_string(bases.pop())
        matched = set()
        for package in graph.subjects(PKG.isVersionOf, identity):
            version_nodes = list(graph.objects(package, PKG.hasVersion))
            versions = {str(value) for node in version_nodes
                        for value in graph.objects(node, PKG.versionString)}
            if len(versions) != 1:
                raise ValueError(f"{package}: need exactly one recorded version to regenerate PURL")
            version = versions.pop()
            qualifiers = dict(base.qualifiers)
            if base.type == "rpm":
                # pg-collect records version-release.arch and stores epoch
                # separately. Strip arch only with corroborating release data.
                releases = {str(v) for node in version_nodes for v in graph.objects(node, PKG.release)}
                epochs = {str(v) for node in version_nodes for v in graph.objects(node, PKG.epoch)}
                if len(releases) > 1 or len(epochs) > 1:
                    raise ValueError(f"{package}: ambiguous RPM version evidence")
                arch = qualifiers.get("arch")
                if releases and arch:
                    release = releases.pop()
                    if version.endswith(f"-{release}.{arch}"):
                        version = version[:-(len(arch) + 1)]
                    elif not version.endswith(f"-{release}"):
                        raise ValueError(f"{package}: RPM release does not match version evidence")
                if epochs:
                    epoch = epochs.pop()
                    if not epoch.isdecimal():
                        raise ValueError(f"{package}: invalid recorded RPM epoch")
                    if int(epoch):
                        qualifiers["epoch"] = epoch
            expected = normalize_legacy(PackageURL(base.type, base.namespace, base.name,
                                                   version, qualifiers, base.subpath).to_string())
            for value in parsed:
                if value.version and value.to_string() == expected.to_string():
                    matched.add(value.to_string())
            old_package_values = list(graph.objects(package, PKG.purl))
            if any(normalize_legacy(str(value)).to_string() != expected.to_string()
                   for value in old_package_values):
                raise ValueError(f"{package}: existing package PURL conflicts with version evidence")
            result.set((package, PKG.purl, Literal(expected.to_string(), datatype=XSD.anyURI)))
        unmatched = {value.to_string() for value in parsed if value.version} - matched
        if unmatched:
            raise ValueError(f"{identity}: no matching package for {sorted(unmatched)}")
        result.set((identity, PKG.purl, Literal(base.to_string(), datatype=XSD.anyURI)))
    # Existing concrete/source PURLs also get canonical encoding and RPM epoch.
    for subject, value in list(result.subject_objects(PKG.purl)):
        if subject not in identities:
            canonical = normalize_legacy(str(value)).to_string()
            result.remove((subject, PKG.purl, value))
            result.add((subject, PKG.purl, Literal(canonical, datatype=XSD.anyURI)))
    errors = validate_graph(result)
    if errors:
        raise ValueError("; ".join(f"{error.subject}: {error.message}" for error in errors))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--format", default="nt", choices=("nt", "turtle"))
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve() or args.output.exists():
        parser.error("output must be a new file; retain the original export for rollback")
    # Preserve literal lexical forms (e.g. snapshot timestamps ending in Z).
    # This CLI owns the process; API callers control parsing of their graph.
    rdflib.NORMALIZE_LITERALS = False
    migrated = migrate_graph(Graph().parse(args.input, format=args.format))
    with args.output.open("x") as output:
        # Stable N-Triples helps review diffs and works with platform graph inputs.
        output.write("".join(sorted(migrated.serialize(format="nt").splitlines(keepends=True))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
