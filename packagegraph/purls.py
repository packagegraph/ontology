"""Canonical PURL validation, separate from entity roles and collection coverage.

SHACL supplies portable structural checks. This parser-backed gate must also run
on each collector graph before publication; a regex is not a PURL parser.
"""
import argparse
from dataclasses import dataclass
import re

from packageurl import PackageURL, ValidationSeverity
from packageurl.validate import DEFINITIONS_BY_TYPE
from rdflib import Graph, Literal, Namespace, RDF
from rdflib.namespace import XSD

PKG = Namespace("https://purl.org/packagegraph/ontology/core#")
RPM_SOURCE = Namespace("https://purl.org/packagegraph/ontology/rpm#").SourceRPM
PROFILE_CLASSES = {
    "rpm": Namespace("https://purl.org/packagegraph/ontology/rpm#").BinaryRPM,
    "deb": Namespace("https://purl.org/packagegraph/ontology/deb#").BinaryPackage,
    "maven": Namespace("https://purl.org/packagegraph/ontology/maven#").MavenArtifact,
}


def parse_canonical(value: str) -> PackageURL:
    """Parse canonical syntax and enforce known ecosystem conventions.

Unregistered types still get general syntax checks. Registered types use the
reference parser's type definitions. RPM epoch is a qualifier, never version text.
"""
    if not re.match(r"^pkg:[a-z][a-z0-9.+-]*/", value):
        raise ValueError("expected canonical pkg:type/name syntax")
    parsed = PackageURL.from_string(value)
    if parsed.to_string() != value:
        raise ValueError(f"noncanonical PURL; canonical form is {parsed.to_string()}")
    if parsed.type in DEFINITIONS_BY_TYPE:
        errors = [m.message for m in parsed.validate(strict=True)
                  if m.severity == ValidationSeverity.ERROR]
        if errors:
            raise ValueError("; ".join(errors))
    if parsed.type == "rpm" and parsed.version and ":" in parsed.version:
        raise ValueError("RPM epoch belongs in the epoch qualifier")
    if parsed.type in ("rpm", "deb") and parsed.namespace != parsed.namespace.lower():
        raise ValueError("RPM/Debian vendor namespaces must be lowercase")
    return parsed


def identity_purl(parsed: PackageURL) -> str:
    """Remove version-specific components while retaining identity qualifiers."""
    qualifiers = dict(parsed.qualifiers)
    if parsed.type == "rpm":
        qualifiers.pop("epoch", None)
    return PackageURL(parsed.type, parsed.namespace, parsed.name,
                      qualifiers=qualifiers, subpath=parsed.subpath).to_string()


@dataclass(frozen=True)
class PurlError:
    subject: object
    message: str


def validate_graph(graph: Graph, profile: str | None = None) -> list[PurlError]:
    """Validate one graph, optionally enforcing a supported producer's coverage.

Profiles require collected packages, their identities and source packages. Maven
also requires resolved dependency identities. RPM/Debian capability targets are
excluded. No PURLs are synthesized and separate graphs must be checked separately.
"""
    if profile is not None and profile not in PROFILE_CLASSES:
        raise ValueError(f"unknown collection profile: {profile}")
    identities = set(graph.subjects(RDF.type, PKG.PackageIdentity))
    identities.update(graph.objects(None, PKG.isVersionOf))
    packages = set(graph.subjects(PKG.isVersionOf, None))
    packages.update(graph.objects(None, PKG.builtFromSource))
    for kind in (PKG.Package, PKG.BinaryPackage, PKG.SourcePackage, RPM_SOURCE, *PROFILE_CLASSES.values()):
        packages.update(graph.subjects(RDF.type, kind))
    required = set()
    if profile:
        collected = set(graph.subjects(RDF.type, PROFILE_CLASSES[profile]))
        required.update(collected)
        if profile in ("rpm", "deb"):
            required.update(graph.subjects(RDF.type, PKG.SourcePackage))
        if profile == "rpm":
            required.update(graph.subjects(RDF.type, RPM_SOURCE))
        for package in collected:
            required.update(graph.objects(package, PKG.isVersionOf))
            required.update(graph.objects(package, PKG.builtFromSource))
            if profile == "maven":
                required.update(graph.objects(package, PKG.directlyDependsOn))
    errors = []
    parsed_values = {}
    for subject in sorted(set(graph.subjects(PKG.purl, None)) | required, key=str):
        values = list(graph.objects(subject, PKG.purl))
        if len(values) > 1 or (subject in required and len(values) != 1):
            errors.append(PurlError(subject, "expected exactly one PURL" if subject in required
                                    else "expected at most one PURL"))
        for value in values:
            try:
                if not isinstance(value, Literal) or value.datatype != XSD.anyURI:
                    raise ValueError("PURL must be an xsd:anyURI literal")
                parsed = parse_canonical(str(value))
                if subject in identities and (parsed.version or
                                             (parsed.type == "rpm" and "epoch" in parsed.qualifiers)):
                    raise ValueError("identity PURL must omit version and RPM epoch")
                if subject in packages and not parsed.version:
                    raise ValueError("concrete package PURL requires a version")
                if subject in required and parsed.type != profile:
                    raise ValueError(f"{profile} profile requires PURL type {profile}")
                parsed_values[subject] = parsed
            except ValueError as error:
                errors.append(PurlError(subject, str(error)))
    for package, identity in graph.subject_objects(PKG.isVersionOf):
        if package in parsed_values and identity in parsed_values:
            if identity_purl(parsed_values[package]) != parsed_values[identity].to_string():
                errors.append(PurlError(package, "package PURL does not match its identity PURL"))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--profile", choices=PROFILE_CLASSES)
    args = parser.parse_args()
    failed = False
    for path in args.files:
        errors = validate_graph(Graph().parse(path), args.profile)
        for error in errors:
            print(f"{path}: {error.subject}: {error.message}")
        failed |= bool(errors)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
