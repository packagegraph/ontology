# Package Management Ontology Makefile
# This Makefile provides utilities for validating, combining, and managing ontology files

# Variables
ONTOLOGY_FILES = core.ttl vcs.ttl rpm.ttl debian.ttl arch.ttl bsd.ttl chocolatey.ttl homebrew.ttl nix.ttl
COMBINED_FILE = x.ttl
PYTHON = uv run python

# Default target
.PHONY: all
all: lint concat

# Lint individual ontology files for syntax validation
.PHONY: lint
lint:
	@echo "Validating ontology files..."
	@for file in $(ONTOLOGY_FILES); do \
		if [ -f "$$file" ]; then \
			echo "Checking $$file..."; \
			$(PYTHON) -c "import rdflib; g = rdflib.Graph(); g.parse('$$file', format='turtle'); print('✓ $$file parses correctly')" || exit 1; \
		else \
			echo "⚠ Warning: $$file not found, skipping"; \
		fi; \
	done
	@echo "All ontology files validated successfully!"

# Concatenate all ontology files into a single combined file
.PHONY: concat
concat:
	@echo "Combining ontology files into $(COMBINED_FILE)..."
	@echo "# Combined Package Management Ontology" > $(COMBINED_FILE)
	@echo "# Generated from: $(ONTOLOGY_FILES)" >> $(COMBINED_FILE)
	@echo "# Generated on: $$(date)" >> $(COMBINED_FILE)
	@echo "" >> $(COMBINED_FILE)
	@for file in $(ONTOLOGY_FILES); do \
		if [ -f "$$file" ]; then \
			echo "Adding $$file..."; \
			echo "" >> $(COMBINED_FILE); \
			echo "# ============================================================================" >> $(COMBINED_FILE); \
			echo "# $$file" >> $(COMBINED_FILE); \
			echo "# ============================================================================" >> $(COMBINED_FILE); \
			cat "$$file" >> $(COMBINED_FILE); \
		else \
			echo "⚠ Warning: $$file not found, skipping"; \
		fi; \
	done
	@echo "Combined ontology created: $(COMBINED_FILE)"

# Validate the combined ontology file
.PHONY: lint-combined
lint-combined: concat
	@echo "Validating combined ontology file..."
	@$(PYTHON) -c "import rdflib; g = rdflib.Graph(); g.parse('$(COMBINED_FILE)', format='turtle'); print('✓ Combined ontology parses correctly')"

# Clean generated files
.PHONY: clean
clean:
	@echo "Cleaning generated files..."
	@rm -f $(COMBINED_FILE)
	@echo "Cleaned!"

# Count triples in individual ontologies
.PHONY: stats
stats:
	@echo "Ontology statistics:"
	@echo "===================="
	@for file in $(ONTOLOGY_FILES); do \
		if [ -f "$$file" ]; then \
			count=$$($(PYTHON) -c "import rdflib; g = rdflib.Graph(); g.parse('$$file', format='turtle'); print(len(g))"); \
			printf "%-20s: %s triples\n" "$$file" "$$count"; \
		fi; \
	done

# Count triples in combined ontology
.PHONY: stats-combined
stats-combined: concat
	@echo "Combined ontology statistics:"
	@echo "============================"
	@count=$$($(PYTHON) -c "import rdflib; g = rdflib.Graph(); g.parse('$(COMBINED_FILE)', format='turtle'); print(len(g))"); \
	printf "%-20s: %s triples\n" "$(COMBINED_FILE)" "$$count"

# Format ontology files (pretty print)
.PHONY: format
format:
	@echo "Formatting ontology files..."
	@for file in $(ONTOLOGY_FILES); do \
		if [ -f "$$file" ]; then \
			echo "Formatting $$file..."; \
			$(PYTHON) -c "import rdflib; g = rdflib.Graph(); g.parse('$$file', format='turtle'); g.serialize(destination='$$file.tmp', format='turtle'); import os; os.rename('$$file.tmp', '$$file')"; \
		fi; \
	done
	@echo "All files formatted!"

# Generate documentation
.PHONY: docs
docs:
	@echo "Generating ontology documentation..."
	@mkdir -p docs
	@for file in $(ONTOLOGY_FILES); do \
		if [ -f "$$file" ]; then \
			echo "Documenting $$file..."; \
			$(PYTHON) -c "import rdflib; from rdflib.namespace import RDF, RDFS, OWL; g = rdflib.Graph(); g.parse('$$file', format='turtle'); classes = list(g.subjects(RDF.type, OWL.Class)); properties = list(g.subjects(RDF.type, OWL.ObjectProperty)) + list(g.subjects(RDF.type, OWL.DatatypeProperty)); print(f'Classes: {len(classes)}, Properties: {len(properties)}')" > docs/$$file.stats; \
		fi; \
	done
	@echo "Documentation generated in docs/ directory"

# Validate with external tools (if available)
.PHONY: validate-external
validate-external:
	@echo "Running external validation tools..."
	@if command -v rapper >/dev/null 2>&1; then \
		echo "Using rapper for validation..."; \
		for file in $(ONTOLOGY_FILES); do \
			if [ -f "$$file" ]; then \
				echo "Validating $$file with rapper..."; \
				rapper -i turtle -c "$$file" || exit 1; \
			fi; \
		done; \
	else \
		echo "rapper not found, skipping external validation"; \
		echo "Install rapper with: apt-get install raptor2-utils (Ubuntu/Debian) or brew install raptor (macOS)"; \
	fi

# Check for common issues
.PHONY: check
check: lint
	@echo "Running additional checks..."
	@echo "Checking for undefined prefixes..."
	@for file in $(ONTOLOGY_FILES); do \
		if [ -f "$$file" ]; then \
			echo "Checking $$file for undefined prefixes..."; \
			$(PYTHON) -c "import re; content = open('$$file').read(); prefixes = set(re.findall(r'@prefix\s+(\w+):', content)); used = set(re.findall(r'(\w+):', content)) - {'http', 'https', 'file', 'urn'}; undefined = used - prefixes - {'_'}; [print(f'⚠ Undefined prefix in $$file: {p}') for p in sorted(undefined) if p]"; \
		fi; \
	done
	@echo "Prefix check complete!"

# Install dependencies
.PHONY: install-deps
install-deps:
	@echo "Installing Python dependencies..."
	@uv add rdflib
	@echo "Dependencies installed!"

# Help target
.PHONY: help
help:
	@echo "Package Management Ontology Makefile"
	@echo "====================================="
	@echo ""
	@echo "Available targets:"
	@echo "  all              - Run lint and concat (default)"
	@echo "  lint             - Validate individual ontology files"
	@echo "  concat           - Combine all ontology files into $(COMBINED_FILE)"
	@echo "  lint-combined    - Validate the combined ontology file"
	@echo "  clean            - Remove generated files"
	@echo "  stats            - Show statistics for individual ontologies"
	@echo "  stats-combined   - Show statistics for combined ontology"
	@echo "  format           - Format/pretty-print ontology files"
	@echo "  docs             - Generate documentation"
	@echo "  validate-external- Validate using external tools (rapper)"
	@echo "  check            - Run additional checks (undefined prefixes, etc.)"
	@echo "  install-deps     - Install required Python dependencies"
	@echo "  help             - Show this help message"
	@echo ""
	@echo "Files processed: $(ONTOLOGY_FILES)"
	@echo "Combined output:  $(COMBINED_FILE)"