# PackageGraph Namespace Registry

This document is the authoritative registry of namespace identifiers for the PackageGraph ontology suite. All ontology namespaces use the PURL base `https://purl.org/packagegraph/ontology/`.

## Naming Convention

- **Use the ecosystem's canonical self-identifier.** What does the project call itself? Use that.
- **No platform prefixes** (`linux-`, `macos-`, `windows-`) — ecosystems define their own scope.
- **No language prefixes** (`python-`, `javascript-`) — registries define their own scope.
- **No vendor prefixes** (`v-`) — vendor status is documented in ontology metadata.
- **One namespace per packaging ecosystem.** An ecosystem is defined by its format + tooling.
- **Register PURLs only when the TTL file exists.** Reserved names prevent conflicts but don't get PURLs until implemented.

## Current Namespaces

Ontology modules with TTL files and registered PURLs.

| Namespace | File | PURL | Description |
|-----------|------|------|-------------|
| `core#` | `core.ttl` | `/packagegraph/ontology/core` | Base classes shared by all ecosystems |
| `debian#` | `debian.ttl` | `/packagegraph/ontology/debian` | Debian/Ubuntu (apt, dpkg, .deb) |
| `rpm#` | `rpm.ttl` | `/packagegraph/ontology/rpm` | RPM ecosystem (dnf, zypper, yum) |
| `archlinux#` | `arch.ttl` | `/packagegraph/ontology/archlinux` | Arch Linux (pacman, PKGBUILD, AUR) |
| `freebsd#` | `freebsd.ttl` | `/packagegraph/ontology/freebsd` | FreeBSD (pkg, ports) |
| `homebrew#` | `homebrew.ttl` | `/packagegraph/ontology/homebrew` | Homebrew (macOS + Linux) |
| `chocolatey#` | `chocolatey.ttl` | `/packagegraph/ontology/chocolatey` | Chocolatey (Windows, NuGet-based) |
| `nix#` | `nix.ttl` | `/packagegraph/ontology/nix` | Nix (cross-platform, functional) |
| `vcs#` | `vcs.ttl` | `/packagegraph/ontology/vcs` | Version control systems |
| `security#` | `security.ttl` | `/packagegraph/ontology/security` | Vulnerabilities and advisories |
| `slsa#` | `slsa.ttl` | `/packagegraph/ontology/slsa` | SLSA supply chain attestation |
| `metrics#` | `metrics.ttl` | `/packagegraph/ontology/metrics` | Code metrics and analysis |
| `redhat#` | `redhat.ttl` | `/packagegraph/ontology/redhat` | Red Hat vendor extension (AppCompat, RHEL sets) |
| `shacl#` | `shacl.ttl` | `/packagegraph/ontology/shacl` | SHACL validation shapes |

## Reserved Namespaces

Names reserved for future ontology modules. No TTL file or PURL exists yet.

### System-Level Package Ecosystems

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `openbsd#` | OpenBSD | pkg_add, ports (different structure from FreeBSD) |
| `pkgsrc#` | pkgsrc | NetBSD-origin, runs on NetBSD, SmartOS/illumos, macOS, Linux |
| `alpine#` | Alpine Linux | apk, musl-based, widely used in containers |
| `portage#` | Gentoo | emerge, ebuilds, USE flags, source-based |
| `flatpak#` | Flatpak | Application sandboxing, cross-distro |
| `snap#` | Snap | Cross-distro application packaging (Canonical) |
| `guix#` | GNU Guix | Functional (like Nix), Scheme-based |
| `void#` | Void Linux | xbps, independent distro |
| `wolfi#` | Wolfi | Chainguard's distroless-oriented distro |

### Language-Level Package Ecosystems

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `npm#` | npm/yarn/pnpm | JavaScript/TypeScript registry. NOT `nodejs#`. |
| `pypi#` | pip/PyPI | Python registry. NOT `pip#` or `python#`. |
| `crates#` | crates.io/cargo | Rust registry. |
| `maven#` | Maven Central | Java/Kotlin/Scala. |
| `nuget#` | NuGet | .NET. Note: Chocolatey is a layer on NuGet. |
| `rubygems#` | RubyGems | Ruby. |
| `gomod#` | Go modules | NOT `go#` (overloaded — board game). |
| `hackage#` | Hackage | Haskell. |
| `cran#` | CRAN | R. |
| `cpan#` | CPAN | Perl. |
| `cocoapods#` | CocoaPods | iOS/macOS Swift/Objective-C. |
| `pub#` | pub.dev | Dart/Flutter. |
| `hex#` | Hex.pm | Elixir/Erlang. |
| `opam#` | opam | OCaml. |
| `conda#` | Conda | Cross-language scientific computing. NOT `anaconda#`. |
| `vcpkg#` | vcpkg | C/C++ (Microsoft). |
| `conan#` | Conan | C/C++ (JFrog). |

### Embedded/IoT Ecosystems

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `platformio#` | PlatformIO | Embedded development, cross-platform |
| `espidf#` | ESP-IDF | Espressif IoT, highly vendored component system |
| `arduino#` | Arduino Library Manager | Simplified embedded |
| `zephyr#` | Zephyr RTOS (west) | Modular RTOS |
| `yocto#` | Yocto/OpenEmbedded | Embedded Linux build system, layers/recipes |

### Container/Infrastructure Ecosystems

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `oci#` | OCI container images | Docker Hub, GHCR, Quay |
| `helm#` | Helm charts | Kubernetes package manager |
| `terraform#` | Terraform modules/providers | Infrastructure as code |
| `ansible#` | Ansible collections/roles | Ansible Galaxy, automation playbooks |

### Vendor Extensions

| Namespace | Vendor | Extends |
|-----------|--------|---------|
| `canonical#` | Canonical | `debian#`, `snap#` |
| `suse#` | SUSE | `rpm#` |
| `amazon#` | Amazon | `rpm#` (AL2023), potentially `oci#` |

## Process for Adding a New Namespace

1. Check this registry for conflicts with existing or reserved names
2. Choose the ecosystem's canonical self-identifier as the namespace name
3. Create the TTL file with proper ontology metadata (dcterms:abstract, owl:versionInfo, etc.)
4. Add to the "Current Namespaces" table above
5. Register PURL redirect at `purl.org/admin/domain/packagegraph`
6. Add to the PURL mapping generator (`scripts/generate-purl-mappings.sh`)
7. Run `uv run pytest tests/test_purl_redirects.py` to verify
