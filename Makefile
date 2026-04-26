# PackageGraph Ontology Makefile
# Module-scoped validation, linting, and deployment

PYTHON = $(if $(GITHUB_ACTIONS),python,uv run python)
WIDOCO_JAR = widoco.jar
DOCS_DIR = _site

# Module discovery
CORE_DIR = core
EXT_DIRS = $(wildcard extensions/*)
ECO_DIRS = $(wildcard ecosystems/*)
ALL_MODULE_DIRS = $(CORE_DIR) $(EXT_DIRS) $(ECO_DIRS)

# Find all ontology .ttl files (not .shacl.ttl or .examples.ttl)
ONTOLOGY_FILES = $(foreach d,$(ALL_MODULE_DIRS),$(wildcard $(d)/$(notdir $(d)).ttl))
SHACL_FILES = $(foreach d,$(ALL_MODULE_DIRS),$(wildcard $(d)/$(notdir $(d)).shacl.ttl))
EXAMPLE_FILES = $(foreach d,$(ALL_MODULE_DIRS),$(wildcard $(d)/$(notdir $(d)).examples.ttl))
ALL_TTL_FILES = $(ONTOLOGY_FILES) $(SHACL_FILES) $(EXAMPLE_FILES)

# Extract module names for per-module targets
MODULES = $(foreach d,$(ALL_MODULE_DIRS),$(notdir $(d)))

.PHONY: all lint validate validate-all help

# Default
all: lint validate

# ─── Linting ──────────────────────────────────────────────────────────────────

# Validate all .ttl files parse as valid Turtle
lint:
	@echo "Validating all .ttl files..."
	@errors=0; \
	for f in $(ALL_TTL_FILES); do \
		$(PYTHON) -c "from rdflib import Graph; g = Graph(); g.parse('$$f', format='turtle'); print(f'  ✓ $$f ({len(g)} triples)')" 2>/dev/null \
		|| { echo "  ✗ $$f"; errors=$$((errors + 1)); }; \
	done; \
	if [ $$errors -gt 0 ]; then echo "\n$$errors file(s) failed"; exit 1; fi; \
	echo "\nAll $(words $(ALL_TTL_FILES)) files valid"

# ─── Per-Module SHACL Validation ──────────────────────────────────────────────

# Validate a single module: loads core + module deps + module ontology + module SHACL
# Usage: make validate-rpm, make validate-debian, etc.
define MODULE_VALIDATE
.PHONY: validate-$(1)
validate-$(1):
	@$(PYTHON) scripts/validate_module.py $(1)
endef

$(foreach m,$(MODULES),$(eval $(call MODULE_VALIDATE,$(m))))

# Validate all modules
validate: validate-all
validate-all:
	@echo "Validating all modules..."
	@$(PYTHON) scripts/validate_module.py --all

# Cross-module integration validation
.PHONY: validate-integration
validate-integration:
	@echo "Cross-module integration validation..."
	@$(PYTHON) scripts/validate_integration.py

# ─── Version Consistency ─────────────────────────────────────────────────────

.PHONY: check-version
check-version:
	@echo "Checking version consistency across modules..."
	@EXPECTED=$$(grep -m1 'owl:versionInfo' core/core.ttl | sed 's/.*"\(.*\)".*/\1/'); \
	echo "Expected version: $$EXPECTED"; \
	FAIL=0; \
	for f in $(ONTOLOGY_FILES) references/alignments.ttl; do \
		VER=$$(grep 'owl:versionInfo' "$$f" 2>/dev/null | sed 's/.*"\(.*\)".*/\1/'); \
		VIRI=$$(grep 'owl:versionIRI' "$$f" 2>/dev/null | grep -o '/[0-9][^>]*' | sed 's|^/||'); \
		if [ -z "$$VER" ]; then \
			echo "  ✗ $$f — missing owl:versionInfo"; FAIL=1; \
		elif [ "$$VER" != "$$EXPECTED" ]; then \
			echo "  ✗ $$f — versionInfo '$$VER' != '$$EXPECTED'"; FAIL=1; \
		elif [ -z "$$VIRI" ]; then \
			echo "  ✗ $$f — missing owl:versionIRI"; FAIL=1; \
		elif [ "$$VIRI" != "$$EXPECTED" ]; then \
			echo "  ✗ $$f — versionIRI '$$VIRI' != '$$EXPECTED'"; FAIL=1; \
		else \
			echo "  ✓ $$f ($$VER)"; \
		fi; \
	done; \
	if [ $$FAIL -eq 1 ]; then echo "Version check FAILED"; exit 1; fi; \
	echo "All modules consistent at v$$EXPECTED"

# ─── Statistics ───────────────────────────────────────────────────────────────

.PHONY: stats
stats:
	@echo "Module statistics:"
	@echo "═══════════════════════════════════════════════════════"
	@for f in $(ONTOLOGY_FILES); do \
		count=$$($(PYTHON) -c "from rdflib import Graph; g = Graph(); g.parse('$$f', format='turtle'); print(len(g))"); \
		printf "  %-45s %s triples\n" "$$f" "$$count"; \
	done
	@echo "───────────────────────────────────────────────────────"
	@echo "  $(words $(ONTOLOGY_FILES)) ontology modules"
	@echo "  $(words $(SHACL_FILES)) SHACL shape files"
	@echo "  $(words $(EXAMPLE_FILES)) example files"

# ─── Concatenation ────────────────────────────────────────────────────────────

COMBINED_FILE = x.ttl

.PHONY: concat
concat:
	@echo "Combining ontology files into $(COMBINED_FILE)..."
	@echo "# Combined PackageGraph Ontology" > $(COMBINED_FILE)
	@echo "# Generated on: $$(date)" >> $(COMBINED_FILE)
	@for f in $(ONTOLOGY_FILES); do \
		echo "" >> $(COMBINED_FILE); \
		echo "# ═══ $$f ═══" >> $(COMBINED_FILE); \
		cat "$$f" >> $(COMBINED_FILE); \
	done
	@echo "Combined: $(words $(ONTOLOGY_FILES)) files → $(COMBINED_FILE)"

.PHONY: clean
clean:
	@rm -f $(COMBINED_FILE)

# ─── Deployment (GitHub Pages) ────────────────────────────────────────────────

.PHONY: deploy deploy-quick setup-tools generate-docs create-index
DOWNLOADS_DIR = $(DOCS_DIR)/downloads
ONTOLOGY_DOCS_DIR = $(DOCS_DIR)/ontology
REPORTS_DIR = $(DOCS_DIR)/reports

setup-tools:
	@if [ ! -f $(WIDOCO_JAR) ] || [ ! -s $(WIDOCO_JAR) ]; then \
		echo "Downloading Widoco..."; \
		curl -sL -o $(WIDOCO_JAR) https://github.com/dgarijo/Widoco/releases/download/v1.4.25/widoco-1.4.25-jar-with-dependencies_JDK-17.jar || true; \
		if [ ! -s $(WIDOCO_JAR) ]; then \
			echo "  ⚠ Widoco download failed — docs will be generated without visualization"; \
			rm -f $(WIDOCO_JAR); \
		fi; \
	fi

generate-docs: setup-tools
	@echo "Generating ontology documentation..."
	@if [ ! -f $(WIDOCO_JAR) ] || [ ! -s $(WIDOCO_JAR) ]; then \
		echo "  ⚠ Widoco not available — skipping HTML documentation generation"; \
	else \
		for f in $(ONTOLOGY_FILES); do \
			base=$$(basename "$$f" .ttl); \
			echo "  Generating docs for $$base..."; \
			mkdir -p "$(ONTOLOGY_DOCS_DIR)/$$base"; \
			timeout 120 java -Xmx2g -jar $(WIDOCO_JAR) \
				-ontFile "$$f" \
				-outFolder "$(ONTOLOGY_DOCS_DIR)/$$base" \
				-webVowl -rewriteAll -getOntologyMetadata \
				-includeImportedOntologies 2>/dev/null \
			|| echo "    ⚠ $$base: Widoco generation failed (non-fatal)"; \
		done; \
	fi

create-index:
	@echo "Creating index page..."
	@$(PYTHON) scripts/generate_index.py $(DOCS_DIR) $(ONTOLOGY_DOCS_DIR) $(DOWNLOADS_DIR)

deploy: lint validate setup-tools
	@echo "Building deployment..."
	@mkdir -p $(DOWNLOADS_DIR) $(REPORTS_DIR) $(ONTOLOGY_DOCS_DIR)
	@echo "Generating serializations..."
	@for f in $(ONTOLOGY_FILES); do \
		base=$$(basename "$$f" .ttl); \
		$(PYTHON) -c "\
from rdflib import Graph; g = Graph(); g.parse('$$f', format='turtle'); \
g.serialize('$(DOWNLOADS_DIR)/$$base.ttl', format='turtle'); \
g.serialize('$(DOWNLOADS_DIR)/$$base.nt', format='nt'); \
g.serialize('$(DOWNLOADS_DIR)/$$base.jsonld', format='json-ld'); \
print('  $$base: ttl + nt + jsonld')" 2>/dev/null || echo "  $$base: conversion failed"; \
	done
	@$(MAKE) generate-docs --no-print-directory
	@$(MAKE) create-index --no-print-directory
	@echo "Deployment complete: $(DOCS_DIR)/"

deploy-quick: lint setup-tools
	@echo "Quick deployment (no SHACL validation, no Widoco)..."
	@mkdir -p $(DOWNLOADS_DIR) $(REPORTS_DIR) $(ONTOLOGY_DOCS_DIR)
	@for f in $(ONTOLOGY_FILES); do \
		base=$$(basename "$$f" .ttl); \
		$(PYTHON) -c "\
from rdflib import Graph; g = Graph(); g.parse('$$f', format='turtle'); \
g.serialize('$(DOWNLOADS_DIR)/$$base.ttl', format='turtle'); \
g.serialize('$(DOWNLOADS_DIR)/$$base.nt', format='nt'); \
g.serialize('$(DOWNLOADS_DIR)/$$base.jsonld', format='json-ld'); \
print('  $$base: ttl + nt + jsonld')" 2>/dev/null || echo "  $$base: conversion failed"; \
	done
	@$(MAKE) create-index --no-print-directory
	@echo "Quick deployment complete: $(DOCS_DIR)/"

.PHONY: serve
serve:
	@cd $(DOCS_DIR) && python3 -m http.server 8000

.PHONY: clean-deploy
clean-deploy:
	@rm -rf $(DOCS_DIR) reports

# ─── Help ─────────────────────────────────────────────────────────────────────

help:
	@echo "PackageGraph Ontology"
	@echo "═══════════════════════════════════════════════════════"
	@echo ""
	@echo "  make                 Lint + validate all modules"
	@echo "  make lint            Parse-check all .ttl files"
	@echo "  make validate-all    SHACL-validate every module"
	@echo "  make validate-NAME   SHACL-validate one module"
	@echo "                       (e.g., make validate-rpm)"
	@echo "  make check-version   Verify owl:versionInfo/IRI consistency"
	@echo "  make stats           Triple counts per module"
	@echo "  make concat          Bundle all ontologies into x.ttl"
	@echo "  make deploy          Full deployment (docs + serializations)"
	@echo "  make deploy-quick    Quick deploy (no Widoco, no SHACL)"
	@echo "  make serve           Serve docs at :8000"
	@echo ""
	@echo "Modules: $(MODULES)"
