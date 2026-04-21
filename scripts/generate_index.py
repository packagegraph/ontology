#!/usr/bin/env python3
"""Generate the GitHub Pages index.html with semantic grouping and Widoco links."""

import sys
from pathlib import Path

DOCS_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_site")
ONTOLOGY_DOCS_DIR = Path(sys.argv[2]) if len(sys.argv) > 2 else DOCS_DIR / "ontology"
DOWNLOADS_DIR = Path(sys.argv[3]) if len(sys.argv) > 3 else DOCS_DIR / "downloads"

MODULES = {
    "Core": {
        "description": "Foundational classes and properties shared across all ecosystems",
        "modules": [
            ("core", "Package, Version, Dependency, Distribution, Architecture, License, Person, Maintainer, BuildActivity, PackageIdentity"),
        ]
    },
    "System-Level Package Managers": {
        "description": "Linux distributions and OS-level package management",
        "modules": [
            ("deb", "Debian/Ubuntu (.deb) packages, APT repositories, sections, priorities"),
            ("rpm", "RPM/DNF packages, epochs, disttags, changelogs, weak dependencies"),
            ("pacman", "Arch Linux packages, groups, hooks, provides/conflicts"),
            ("apk", "Alpine Linux packages, APKBUILD scripts, branches"),
            ("portage", "Gentoo ebuilds, USE flags, slots, EAPI, eclasses"),
            ("homebrew", "macOS formulae, casks, bottles, taps"),
            ("nix", "Nix derivations, channels, stdenv, functional builds"),
            ("xbps", "Void Linux XBPS packages"),
            ("opkg", "OpenWrt embedded Linux packages"),
            ("bsdpkg", "FreeBSD/NetBSD/OpenBSD ports, flavors, options"),
            ("chocolatey", "Windows Chocolatey/NuGet packages, PowerShell scripts"),
            ("bitbake", "Yocto/OpenEmbedded recipes, layers, machines"),
            ("buildroot", "Buildroot packages, defconfigs, build infrastructures"),
        ]
    },
    "Language Ecosystem Managers": {
        "description": "Programming language package registries and dependency managers",
        "modules": [
            ("npm", "Node.js/JavaScript, scopes, workspaces, peer dependencies"),
            ("pypi", "Python packages, wheels, sdists, extras, classifiers"),
            ("cargo", "Rust crates, features, editions, targets"),
            ("gomod", "Go modules, replace directives, module proxies"),
            ("maven", "Java/JVM artifacts, groupId:artifactId:version, POM"),
            ("nuget", ".NET packages, target frameworks"),
            ("rubygems", "Ruby gems, platforms, gemspec"),
            ("cpan", "Perl distributions, PAUSE IDs, modules"),
            ("cran", "R packages, Depends/Imports/Suggests"),
            ("hackage", "Haskell packages, Cabal metadata"),
            ("hex", "Elixir/Erlang packages, mix/rebar3"),
            ("conda", "Anaconda packages, channels, feedstocks"),
        ]
    },
    "Application Distribution": {
        "description": "Application packaging and distribution formats",
        "modules": [
            ("flatpak", "Linux desktop apps, runtimes, sandboxing"),
            ("snap", "Ubuntu Snap apps, confinement, interfaces"),
        ]
    },
    "Extensions": {
        "description": "Cross-cutting concerns extending the core model",
        "modules": [
            ("security", "CVE vulnerabilities, OSV ranges, CVSS scores, security advisories, patch provenance"),
            ("vcs", "Git repositories, commits, branches, tags, pull requests"),
            ("slsa", "Build provenance attestations, SLSA levels, builder identity"),
            ("metrics", "Code analysis: lines of code, cyclomatic complexity, language breakdowns"),
            ("dq", "Data quality issues and metadata validation"),
        ]
    },
    "Vendor Extensions": {
        "description": "Distribution-specific vendor metadata",
        "modules": [
            ("redhat", "Red Hat RHEL package sets, BaseOS/AppStream"),
        ]
    },
}

def has_widoco_docs(module_name):
    doc_dir = ONTOLOGY_DOCS_DIR / module_name
    return doc_dir.exists() and (doc_dir / "index-en.html").exists()

def has_downloads(module_name):
    return (DOWNLOADS_DIR / f"{module_name}.ttl").exists()

def generate_html():
    html = []
    html.append("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PackageGraph Ontology v0.6.0</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
           max-width: 1100px; margin: 0 auto; padding: 2rem; color: #333; line-height: 1.6; }
    h1 { font-size: 2rem; border-bottom: 3px solid #2c3e50; padding-bottom: 0.5rem; margin-bottom: 0.5rem; }
    .subtitle { color: #666; font-size: 1.1rem; margin-bottom: 2rem; }
    .badges { margin-bottom: 2rem; }
    .badges span { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 4px;
                   font-size: 0.85rem; margin-right: 0.5rem; margin-bottom: 0.25rem; }
    .badge-version { background: #2c3e50; color: white; }
    .badge-owl { background: #27ae60; color: white; }
    .badge-shacl { background: #2980b9; color: white; }
    .badge-license { background: #8e44ad; color: white; }
    .nav { background: #f8f9fa; padding: 1rem; border-radius: 6px; margin-bottom: 2rem; }
    .nav a { margin-right: 1.5rem; color: #2980b9; text-decoration: none; font-weight: 500; }
    .nav a:hover { text-decoration: underline; }
    .section { margin-bottom: 2.5rem; }
    .section h2 { color: #2c3e50; border-bottom: 1px solid #ecf0f1; padding-bottom: 0.3rem; }
    .section-desc { color: #666; font-style: italic; margin-bottom: 1rem; }
    .module-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; }
    .module { border: 1px solid #ddd; border-radius: 6px; padding: 1rem; transition: box-shadow 0.2s; }
    .module:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .module h3 { margin: 0 0 0.3rem 0; font-size: 1rem; }
    .module h3 a { color: #2c3e50; text-decoration: none; }
    .module h3 a:hover { color: #2980b9; }
    .module p { margin: 0 0 0.5rem 0; font-size: 0.85rem; color: #666; }
    .module-links { font-size: 0.8rem; }
    .module-links a { margin-right: 0.75rem; color: #2980b9; text-decoration: none; }
    .module-links a:hover { text-decoration: underline; }
    .module-links .doc-link { font-weight: 600; }
    .highlight { background: #fff3cd; border-color: #ffc107; }
    footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #ecf0f1; color: #999; font-size: 0.85rem; }
  </style>
</head>
<body>
  <h1>PackageGraph Ontology</h1>
  <p class="subtitle">A rigorous OWL 2 ontology for cross-distribution package analysis and software supply chain research.</p>

  <div class="badges">
    <span class="badge-version">v0.6.0</span>
    <span class="badge-owl">OWL 2 DL</span>
    <span class="badge-shacl">29 SHACL Shapes</span>
    <span class="badge-license">CC0 1.0</span>
  </div>

  <div class="nav">
    <a href="https://github.com/packagegraph/ontology">GitHub</a>
    <a href="https://github.com/packagegraph/ontology/blob/main/CHANGELOG.md">Changelog</a>
    <a href="https://github.com/packagegraph/ontology/blob/main/docs/competency-questions.md">33 Competency Questions</a>
    <a href="https://github.com/packagegraph/ontology/blob/main/docs/design-decisions.md">Design Decisions</a>
    <a href="https://github.com/packagegraph/ontology/blob/main/docs/reports/2026-04-20-evaluation-comparison.md">vs SPDX/CycloneDX/OSV</a>
  </div>
""")

    for group_name, group_data in MODULES.items():
        html.append(f'  <div class="section">')
        html.append(f'    <h2>{group_name}</h2>')
        html.append(f'    <p class="section-desc">{group_data["description"]}</p>')
        html.append(f'    <div class="module-grid">')

        for module_name, desc in group_data["modules"]:
            widoco = has_widoco_docs(module_name)
            downloads = has_downloads(module_name)
            highlight = ' highlight' if module_name == 'core' else ''

            html.append(f'      <div class="module{highlight}">')

            if widoco:
                html.append(f'        <h3><a href="ontology/{module_name}/index-en.html">{module_name}</a></h3>')
            else:
                html.append(f'        <h3>{module_name}</h3>')

            html.append(f'        <p>{desc}</p>')
            html.append(f'        <div class="module-links">')

            if widoco:
                html.append(f'          <a class="doc-link" href="ontology/{module_name}/index-en.html">Documentation</a>')
                webvowl_path = ONTOLOGY_DOCS_DIR / module_name / "webvowl" / "index.html"
                if webvowl_path.exists():
                    html.append(f'          <a href="ontology/{module_name}/webvowl/index.html">WebVOWL</a>')

            if downloads:
                html.append(f'          <a href="downloads/{module_name}.ttl">Turtle</a>')
                html.append(f'          <a href="downloads/{module_name}.nt">N-Triples</a>')
                html.append(f'          <a href="downloads/{module_name}.jsonld">JSON-LD</a>')

            html.append(f'        </div>')
            html.append(f'      </div>')

        html.append(f'    </div>')
        html.append(f'  </div>')

    html.append("""
  <footer>
    <p>PackageGraph Ontology v0.6.0 &mdash; <a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0 1.0 Universal</a></p>
    <p>34 modules | 253 classes | 29 ecosystems | 5 extensions | OWL 2 DL decidable | OntoClean compliant</p>
  </footer>
</body>
</html>""")

    return "\n".join(html)


if __name__ == "__main__":
    index_path = DOCS_DIR / "index.html"
    index_path.write_text(generate_html())
    print(f"  Generated {index_path}")
