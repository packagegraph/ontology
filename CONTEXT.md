# Package Management Ontology - Development Context

## Project Overview

This project contains a comprehensive collection of RDF/OWL ontologies for representing software packages, repositories, and metadata across major package management systems. The project enables semantic representation and analysis of package ecosystems across different platforms.

## Repository Information

- **Repository**: `git@github.com:packagegraph/ontology.git`
- **Current Branch**: `main`
- **Working Directory**: `/Users/bharrington/Projects/packagegraph/ontology`

## Technology Stack

### Core Technologies
- **RDF/OWL**: Semantic web technologies for ontology definition
- **Python 3.12**: Main programming language (see `.python-version`)
- **uv**: Python package manager and virtual environment tool
- **Turtle (.ttl)**: Primary RDF serialization format
- **ROBOT**: OWL ontology development toolkit
- **WIDOCO**: Web ontology documentation generator

### Python Dependencies
- **click**: CLI framework for command-line tools
- **rdflib**: Python library for RDF manipulation
- **requests**: HTTP client for repository data collection
- **pylint/ruff**: Code linting and formatting tools

## Project Structure

### Ontology Files (Core Assets)
```
├── core.ttl           # Base ontology with common concepts
├── vcs.ttl           # Version control system integration
├── debian.ttl        # Debian/APT package management
├── rpm.ttl           # RPM/YUM/DNF package management
├── arch.ttl          # Arch Linux package management
├── bsd.ttl           # BSD ports system
├── chocolatey.ttl    # Windows Chocolatey package management
├── homebrew.ttl      # macOS Homebrew package management
├── nix.ttl           # Nix functional package management
└── examples.ttl      # Example instances and usage patterns
```

### Python Package (`packagegraph/`)
```
packagegraph/
├── __init__.py           # Package initialization
├── checker.py            # Ontology validation and testing
├── collector.py          # Base collector interface
├── debian_collector.py   # Debian repository data collection
├── rpm_collector.py      # RPM repository data collection
└── profiler.py          # Performance profiling utilities
```

### Key Configuration Files
- `pyproject.toml`: Python project configuration and dependencies
- `Makefile`: Build automation and validation scripts
- `main.py`: CLI entry point for data collection and ontology management
- `catalog-v001.xml`: OWL catalog for ontology imports
- `.python-version`: Python version specification (3.12)

### Documentation and Build Output
- `docs/`: Generated documentation and website files
- `reports/`: Validation reports from ROBOT
- `robot.jar`: ROBOT ontology toolkit executable
- `widoco.jar`: WIDOCO documentation generator

## Development Workflow

### Environment Setup
```bash
# Python environment is managed by uv
# Dependencies are installed automatically when using uv commands
```

### Key Make Targets
```bash
make lint              # Validate all TTL files for syntax
make concat            # Combine all ontologies into single file
make stats             # Show ontology statistics
make check             # Run comprehensive validation
make deploy            # Full deployment pipeline (docs + validation)
make serve             # Serve documentation locally on :8000
```

### CLI Tool Usage
```bash
# ETL operations
python main.py collect <repo-url> --repo-type debian --output-file packages.ttl
python main.py check   # Run validation suite
python main.py convert # Convert ontologies to different formats

# Using uv (recommended)
uv run python main.py collect <repo-url> --repo-type debian
```

### Ontology Development
1. **Edit ontologies**: Modify `.ttl` files using Turtle syntax
2. **Validate locally**: Run `make lint` to check syntax
3. **Test integration**: Run `make check` for full validation
4. **Generate docs**: Run `make deploy` to create documentation
5. **Preview**: Run `make serve` to view docs at localhost:8000



## Build and Validation System

### Validation Pipeline
1. **Syntax Validation**: Python rdflib parsing of each ontology
2. **ROBOT Validation**: Advanced OWL reasoning and consistency checks
3. **Import Resolution**: Validates ontology import relationships
4. **Format Generation**: Converts to RDF/XML, JSON-LD, N-Triples
5. **Documentation**: Generates HTML docs with WIDOCO

### Continuous Integration
- GitHub Actions workflow mirrors local `make deploy` process
- Automatic validation on commits
- GitHub Pages deployment for documentation
- Content negotiation support for different RDF formats

## Data Collection Features

### Supported Repository Types
- **Debian/APT**: Collects from Debian package repositories
- **RPM**: Collects from RPM-based repositories (CentOS, RHEL, etc.)

### ETL Capabilities
- Parallel processing with configurable workers
- Incremental loading to existing RDF graphs
- Performance profiling and optimization
- Multiple output formats (Turtle, N-Triples, etc.)

## Development Guidelines

### Ontology Best Practices
- Use relative imports (`<core.ttl>` not web URLs)
- Follow OWL 2 DL compliance requirements
- Add `rdfs:label` and `rdfs:comment` for all terms
- Maintain namespace consistency
- Use appropriate cardinality constraints
- Complete ontology metadata including version info, creation date, and licensing information
- Always do the following:
  - Use PascalCase for classes and camelCase for properties
  - Use proper import statements linking specialized ontologies to core
  - Use namespaces consistently across ontologies
  - Use equivalent property declarations for cross-format compatibility
  - Ensure object properties use proper domain and range specifications, particularly cross-format equivalence properties
  - Prefer object properties over string-based properties
  - Structure version components (release, revision, epoch) as properties of the version instance
  - Mark unique identifier properties as owl:FunctionalProperty
  - Implement comprehensive validation rules using SHACL
  - Organize orphaned properties into logical hierarchies
  - Implement unified dependency modeling with core properties
  - Standardize person/agent representation across all ontologies
  - Enhance version representation using structured objects

### Code Style
- Python code follows project formatting standards
- Use type hints where appropriate
- Comprehensive CLI help and documentation
- Error handling for network operations and parsing

### Testing and Quality
- All ontologies must pass `make lint` validation
- ROBOT validation reports stored in `reports/`
- Example instances in `examples.ttl` demonstrate usage
- Performance profiling available for optimization

## Namespace Management

Each ontology uses its own namespace:
- Core: `http://packagegraph.github.io/ontology/core#`
- VCS: `http://packagegraph.github.io/ontology/vcs#`
- Debian: `http://packagegraph.github.io/ontology/debian#`
- RPM: `http://packagegraph.github.io/ontology/rpm#`
- And similar patterns for other package systems

## Current State

### Modified Files (per git status)
- `M Makefile`: Build system modifications
- `M catalog-v001.xml`: OWL catalog updates
- `?? convert_to_graphson.py`: New conversion utility (untracked)

### Development Tools Ready
- Python 3.12 environment configured
- uv package manager available
- ROBOT and WIDOCO tools downloadable via Makefile
- Comprehensive validation and documentation pipeline

## Getting Started

For new developers:
1. Clone the repository
2. Ensure Python 3.12 and uv are installed
3. Run `make help` to see available commands
4. Start with `make lint` to validate the current state
5. Use `make deploy` to build full documentation locally
6. Modify ontologies and validate with `make check`

This project provides a robust foundation for semantic representation of package management systems with comprehensive tooling for development, validation, and deployment.
