# PackageGraph Namespace Registry

This document is the authoritative registry of namespace identifiers for the PackageGraph ontology suite. All ontology namespaces use the PURL base `https://purl.org/packagegraph/ontology/`.

## Naming Convention

- **Name the packaging system, not the distribution.** Use the package manager or format name (e.g., `pacman#` not `archlinux#`, `portage#` not `gentoo#`), following the `rpm#`/`debian#` convention. This allows the namespace to cover all distributions using that packaging system.
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
| `pacman#` | `pacman.ttl` | `/packagegraph/ontology/pacman` | Pacman (PKGBUILD, AUR — Arch, Manjaro, SteamOS) |
| `bsdpkg#` | `bsdpkg.ttl` | `/packagegraph/ontology/bsdpkg` | BSD pkg(8) and ports (FreeBSD, GhostBSD, MidnightBSD) |
| `homebrew#` | `homebrew.ttl` | `/packagegraph/ontology/homebrew` | Homebrew (macOS + Linux) |
| `chocolatey#` | `chocolatey.ttl` | `/packagegraph/ontology/chocolatey` | Chocolatey (Windows, NuGet-based) |
| `nix#` | `nix.ttl` | `/packagegraph/ontology/nix` | Nix (cross-platform, functional) |
| `vcs#` | `vcs.ttl` | `/packagegraph/ontology/vcs` | Version control systems |
| `security#` | `security.ttl` | `/packagegraph/ontology/security` | Vulnerabilities and advisories |
| `slsa#` | `slsa.ttl` | `/packagegraph/ontology/slsa` | SLSA supply chain attestation |
| `metrics#` | `metrics.ttl` | `/packagegraph/ontology/metrics` | Code metrics and analysis |
| `redhat#` | `redhat.ttl` | `/packagegraph/ontology/redhat` | Red Hat vendor extension (AppCompat, RHEL sets) |
| `dq#` | `dq.ttl` | `/packagegraph/ontology/dq` | Data quality issues (ETL validation) |
| `shacl#` | `shacl.ttl` | `/packagegraph/ontology/shacl` | SHACL validation shapes |
| `rubygems#` | `rubygems.ttl` | `/packagegraph/ontology/rubygems` | RubyGems (Ruby packages) |
| `maven#` | `maven.ttl` | `/packagegraph/ontology/maven` | Maven Central (Java/JVM artifacts) |
| `cpan#` | `cpan.ttl` | `/packagegraph/ontology/cpan` | CPAN (Perl distributions) |
| `cran#` | `cran.ttl` | `/packagegraph/ontology/cran` | CRAN (R packages) |
| `hackage#` | `hackage.ttl` | `/packagegraph/ontology/hackage` | Hackage (Haskell packages) |
| `nuget#` | `nuget.ttl` | `/packagegraph/ontology/nuget` | NuGet (.NET packages) |
| `hex#` | `hex.ttl` | `/packagegraph/ontology/hex` | Hex.pm (Elixir/Erlang packages) |
| `apk#` | `apk.ttl` | `/packagegraph/ontology/apk` | APK (apk-tools — Alpine, postmarketOS) |
| `portage#` | `portage.ttl` | `/packagegraph/ontology/portage` | Portage (emerge, ebuilds — Gentoo, ChromeOS, Flatcar) |
| `xbps#` | `xbps.ttl` | `/packagegraph/ontology/xbps` | XBPS (Void Linux) |
| `npm#` | `npm.ttl` | `/packagegraph/ontology/npm` | npm/yarn/pnpm (JavaScript/TypeScript) |
| `pypi#` | `pypi.ttl` | `/packagegraph/ontology/pypi` | PyPI (Python packages) |
| `cargo#` | `cargo.ttl` | `/packagegraph/ontology/cargo` | Cargo/crates.io (Rust) |
| `gomod#` | `gomod.ttl` | `/packagegraph/ontology/gomod` | Go modules |
| `conda#` | `conda.ttl` | `/packagegraph/ontology/conda` | Conda (cross-language scientific computing) |
| `flatpak#` | `flatpak.ttl` | `/packagegraph/ontology/flatpak` | Flatpak (cross-distro application sandboxing) |
| `snap#` | `snap.ttl` | `/packagegraph/ontology/snap` | Snap (cross-distro application packaging) |
| `bitbake#` | `bitbake.ttl` | `/packagegraph/ontology/bitbake` | BitBake/OpenEmbedded (Yocto, other OE-based systems) |
| `buildroot#` | `buildroot.ttl` | `/packagegraph/ontology/buildroot` | Buildroot (embedded Linux build system) |
| `opkg#` | `opkg.ttl` | `/packagegraph/ontology/opkg` | opkg (OpenWRT, Entware, embedded Linux) |

## Reserved Namespaces

Names reserved for future ontology modules. No TTL file or PURL exists yet.

### System-Level Package Ecosystems

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `openbsd#` | OpenBSD | pkg_add, ports (different structure from FreeBSD) |
| `pkgsrc#` | pkgsrc | NetBSD-origin, runs on NetBSD, SmartOS/illumos, macOS, Linux |
| `guix#` | GNU Guix | Functional (like Nix), Scheme-based |
| ~~`wolfi#`~~ | Wolfi | Uses apk — packages belong in `apk#` namespace, not a separate namespace |

### Language-Level Package Ecosystems

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `cocoapods#` | CocoaPods | iOS/macOS Swift/Objective-C. |
| `pub#` | pub.dev | Dart/Flutter. |
| `opam#` | opam | OCaml. |
| `vcpkg#` | vcpkg | C/C++ (Microsoft). |
| `conan#` | Conan | C/C++ (JFrog). |
| `swift#` | Swift Package Manager | Apple ecosystem (iOS/macOS/Linux). |

### Scientific/HPC Ecosystems

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `spack#` | Spack | HPC package manager (national labs, supercomputing) |
| `easybuild#` | EasyBuild | HPC software build framework |
| `bioconductor#` | Bioconductor | R bioinformatics (distinct from CRAN) |
| `modules#` | Environment Modules/Lmod | Version-switched software stacks (not packages per se, but models the selection layer) |

### Embedded/IoT Ecosystems

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `platformio#` | PlatformIO | Embedded development, cross-platform |
| `espidf#` | ESP-IDF | Espressif IoT, highly vendored component system |
| `arduino#` | Arduino Library Manager | Simplified embedded |
| `zephyr#` | Zephyr RTOS (west) | Modular RTOS |

### Container/Infrastructure Ecosystems

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `oci#` | OCI container images | Docker Hub, GHCR, Quay |
| `helm#` | Helm charts | Kubernetes package manager, Artifact Hub |
| `olm#` | Operator Lifecycle Manager | Operator bundles, OperatorHub.io, CSVs/CRDs |
| `kustomize#` | Kustomize | Components, bases, overlays as reusable units |
| `carvel#` | Carvel | Package/PackageInstall CRDs (kapp, imgpkg, vendir) |
| `crossplane#` | Crossplane | Compositions, Providers, infrastructure packages |
| `krew#` | Krew | kubectl plugin manager |
| `timoni#` | Timoni | CUE-based Kubernetes package manager |
| `terraform#` | Terraform modules/providers | Infrastructure as code (HCL) |
| `ansible#` | Ansible collections/roles | Ansible Galaxy, automation playbooks |
| `pulumi#` | Pulumi packages | Infrastructure as code (multi-language) |

Note: **Artifact Hub** (`artifacthub.io`) is a **registry** that hosts multiple formats (Helm, OLM, Falco, OPA, etc.) — analogous to PyPI for pip. It is not a namespace itself; packages in Artifact Hub are typed by their format's namespace (`helm#`, `olm#`, etc.).

### Configuration Management

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `puppet#` | Puppet Forge | Puppet modules |
| `chef#` | Chef Supermarket | Chef cookbooks |
| `salt#` | Salt formulas | SaltStack |

### Editor/IDE Extensions

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `vscode#` | VS Code Marketplace | Extensions for VS Code/Codium |
| `jetbrains#` | JetBrains Plugin Repository | IntelliJ/PyCharm/GoLand/etc. plugins |
| `elpa#` | Emacs packages | ELPA, MELPA, GNU ELPA |
| `vimplugin#` | Vim/Neovim plugins | vim-plug, lazy.nvim, packer, native packages |

### Content Management

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `wordpress#` | WordPress plugins/themes | 55,000+ plugins, own repo format and metadata |
| `drupal#` | Drupal modules | Drupal.org packaging |

### TeX/Academic

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `ctan#` | CTAN | Comprehensive TeX Archive Network (TeX/LaTeX packages) |

### AI/ML Models

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `huggingface#` | Hugging Face Hub | Models, datasets, spaces. NOT `hf#` (ambiguous). |
| `ollama#` | Ollama | LLM model library, Modelfile format |
| `onnx#` | ONNX Model Zoo | Neural network interchange format |

### Firmware

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `fwupd#` | LVFS/fwupd | Linux Vendor Firmware Service — firmware updates as packages |

### Mobile

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `fdroid#` | F-Droid | Open source Android apps, own repo format/metadata |

### WASM/Emerging

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `wasm#` | WebAssembly components | WASI, component model — emerging standard |

### Build System Dependencies

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `bazel#` | Bazel | External dependencies (MODULE.bazel, bzlmod) |

### Enterprise/Legacy UNIX

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `ips#` | Image Packaging System | Solaris/illumos pkg(5) |

### SBOM Formats (Meta-Packaging)

| Namespace | Ecosystem | Notes |
|-----------|-----------|-------|
| `cyclonedx#` | CycloneDX | SBOM format — describes packages from other ecosystems |
| `spdxpkg#` | SPDX package descriptions | Distinct from SPDX license vocabulary already in use as external vocab |

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
