#!/usr/bin/env python3
"""Split monolithic examples.ttl into per-module .examples.ttl files."""

import re
from pathlib import Path
from rdflib import Graph

PREFIXES = """\
@prefix ex:    <https://purl.org/packagegraph/ontology/examples#> .
@prefix pkg:   <https://purl.org/packagegraph/ontology/core#> .
@prefix deb:   <https://purl.org/packagegraph/ontology/debian#> .
@prefix rpm:   <https://purl.org/packagegraph/ontology/rpm#> .
@prefix pacman:  <https://purl.org/packagegraph/ontology/pacman#> .
@prefix bsdpkg:   <https://purl.org/packagegraph/ontology/bsdpkg#> .
@prefix choco: <https://purl.org/packagegraph/ontology/chocolatey#> .
@prefix brew:  <https://purl.org/packagegraph/ontology/homebrew#> .
@prefix nix:   <https://purl.org/packagegraph/ontology/nix#> .
@prefix doap:  <http://usefulinc.com/ns/doap#> .
@prefix dct:   <http://purl.org/dc/terms/> .
@prefix dc:    <http://purl.org/dc/elements/1.1/> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix foaf:  <http://xmlns.com/foaf/0.1/> .
@prefix spdx:  <http://spdx.org/rdf/terms#> .
@prefix spdxl: <http://spdx.org/licenses/> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix sec:   <https://purl.org/packagegraph/ontology/security#> .
@prefix met:   <https://purl.org/packagegraph/ontology/metrics#> .
@prefix rh:    <https://purl.org/packagegraph/ontology/redhat#> .
@prefix slsa:  <https://purl.org/packagegraph/ontology/slsa#> .
@prefix vcs:   <https://purl.org/packagegraph/ontology/vcs#> .
@prefix prov:  <http://www.w3.org/ns/prov#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
"""

# Map section titles to module directories
SECTION_MAP = {
    "Debian (3)": "ecosystems/debian",
    "RPM (3)": "ecosystems/rpm",
    "Arch Linux (3)": "ecosystems/pacman",
    "BSD Ports (3)": "ecosystems/bsdpkg",
    "Chocolatey (3)": "ecosystems/chocolatey",
    "Homebrew (3)": "ecosystems/homebrew",
    "Nix (3)": "ecosystems/nix",
    "Security (CVE and Advisory examples)": "extensions/security",
    "Code Metrics and Language examples": "extensions/metrics",
    "Package Set and Vendor Extension examples": "core",
    "Patch examples (SRPM with distro patches)": "ecosystems/rpm",
    "PROV-O Provenance Chain Example": "core",
    "SLSA Provenance Attestation Example": "extensions/slsa",
    "Security Patch Provenance Example": "extensions/security",
    "Inverse Property Examples (Task 1)": "core",
    "Capability Examples (Task 2)": "core",
    "Cross-Ecosystem Identity Linking (Task 3)": "core",
    "External Identifiers (Task 4)": "core",
}


def parse_sections(text):
    """Parse examples.ttl into sections delimited by #### or ==== comment blocks."""
    lines = text.split("\n")
    sections = []
    current_name = "preamble"
    current_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect section header: line of #### or ==== followed by # Title
        if re.match(r'^#{10,}$', line.strip()) or re.match(r'^# ={10,}$', line.strip()):
            # Look for title on next line
            if i + 1 < len(lines):
                title_line = lines[i + 1].strip()
                title_match = re.match(r'^#\s+(.+)$', title_line)
                if title_match:
                    # Save current section
                    if current_lines:
                        sections.append((current_name, "\n".join(current_lines)))
                    current_name = title_match.group(1).strip()
                    current_lines = []
                    # Skip the header block (top bar, title, bottom bar)
                    i += 2
                    if i < len(lines) and (re.match(r'^#{10,}$', lines[i].strip()) or re.match(r'^# ={10,}$', lines[i].strip())):
                        i += 1
                    continue

        current_lines.append(line)
        i += 1

    if current_lines:
        sections.append((current_name, "\n".join(current_lines)))

    return sections


def main():
    text = Path("examples.ttl").read_text()
    sections = parse_sections(text)

    print(f"Found {len(sections)} sections:")
    for name, content in sections:
        lines = [l for l in content.split("\n") if l.strip()]
        print(f"  '{name}': {len(lines)} lines")

    # Group by module
    module_content: dict[str, list[str]] = {}

    for name, content in sections:
        if name == "preamble":
            # Extract shared resources (licenses, maintainers) but skip prefixes/metadata
            shared = []
            past_metadata = False
            for line in content.split("\n"):
                if line.startswith("@prefix") or not line.strip():
                    continue
                if line.startswith("<https://purl.org/packagegraph/ontology/examples"):
                    past_metadata = False
                    continue
                if re.match(r'^  (dc|dct|owl|rdfs):', line.strip()):
                    continue
                if line.strip().startswith("# License") or line.strip().startswith("spdxl:"):
                    past_metadata = True
                if past_metadata:
                    shared.append(line)
            if shared:
                module_content.setdefault("core", []).append("\n".join(shared))
            continue

        module = SECTION_MAP.get(name)
        if module is None:
            # Fuzzy match
            for key, val in SECTION_MAP.items():
                if key in name or name in key:
                    module = val
                    break
        if module is None:
            print(f"  WARNING: Unmapped section '{name}' → core")
            module = "core"

        header = f"# {'=' * 60}\n# {name}\n# {'=' * 60}\n"
        module_content.setdefault(module, []).append(header + content)

    # Write per-module .examples.ttl files
    for module_dir, content_parts in sorted(module_content.items()):
        module_name = Path(module_dir).name
        outpath = Path(module_dir) / f"{module_name}.examples.ttl"

        full_content = PREFIXES + "\n" + "\n\n".join(content_parts)

        try:
            g = Graph()
            g.parse(data=full_content, format="turtle")
            outpath.write_text(full_content)
            print(f"  {outpath}: {len(g)} triples")
        except Exception as e:
            print(f"  ERROR {outpath}: {e}")
            outpath.write_text(full_content)

    Path("examples.ttl").unlink()
    print(f"\nSplit into {len(module_content)} module example files, removed examples.ttl")


if __name__ == "__main__":
    main()
