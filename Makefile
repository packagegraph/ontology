# PackageGraph Ontology Makefile
# Module-scoped validation, linting, and deployment

PYTHON = $(if $(GITHUB_ACTIONS),python,uv run python)
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

.PHONY: deploy deploy-quick
DOWNLOADS_DIR = $(DOCS_DIR)/downloads
ONTOLOGY_DOCS_DIR = $(DOCS_DIR)/ontology
REPORTS_DIR = $(DOCS_DIR)/reports

deploy: lint validate
	@echo "Building deployment..."
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
	@echo "Generating index.html..."
	@$(PYTHON) -c "\
print('<!DOCTYPE html>'); \
print('<html lang=\"en\">'); \
print('<head>'); \
print('  <meta charset=\"UTF-8\">'); \
print('  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">'); \
print('  <title>PackageGraph Ontology v0.6.0</title>'); \
print('  <style>'); \
print('    body { font-family: system-ui; max-width: 1200px; margin: 2rem auto; padding: 0 2rem; }'); \
print('    h1 { border-bottom: 3px solid #333; padding-bottom: 0.5rem; }'); \
print('    .module { border: 1px solid #ddd; padding: 1rem; margin: 1rem 0; border-radius: 4px; }'); \
print('    .module h3 { margin-top: 0; }'); \
print('    .downloads { margin-top: 0.5rem; }'); \
print('    .downloads a { margin-right: 1rem; color: #0066cc; }'); \
print('    code { background: #f4f4f4; padding: 0.2rem 0.4rem; border-radius: 3px; }'); \
print('  </style>'); \
print('</head>'); \
print('<body>'); \
print('  <h1>PackageGraph Ontology</h1>'); \
print('  <p><strong>Version:</strong> 0.6.0 | <strong>License:</strong> CC0 1.0</p>'); \
print('  <p>A rigorous OWL 2 ontology for cross-distribution package analysis.</p>'); \
print('  <p><a href=\"https://github.com/packagegraph/ontology\">GitHub Repository</a> | <a href=\"https://github.com/packagegraph/ontology/blob/main/CHANGELOG.md\">Changelog</a> | <a href=\"https://github.com/packagegraph/ontology/blob/main/docs/competency-questions.md\">Competency Questions</a></p>'); \
print('  <h2>Downloads</h2>'); \
import os, glob; \
[print(f'  <div class=\"module\"><h3>{os.path.basename(f)[:-4]}</h3><div class=\"downloads\"><a href=\"downloads/{os.path.basename(f)}\">Turtle</a><a href=\"downloads/{os.path.basename(f)[:-4]}.nt\">N-Triples</a><a href=\"downloads/{os.path.basename(f)[:-4]}.jsonld\">JSON-LD</a></div></div>') for f in sorted(glob.glob('$(DOWNLOADS_DIR)/*.ttl'))]; \
print('  <hr>'); \
print('  <p style=\"margin-top: 2rem; color: #666;\">Generated from PackageGraph Ontology v0.6.0</p>'); \
print('</body>'); \
print('</html>')" > $(DOCS_DIR)/index.html
	@echo "Deployment complete: $(DOCS_DIR)/"

deploy-quick: lint
	@$(MAKE) deploy --no-print-directory
	@echo "Deployment complete: $(DOCS_DIR)/"

deploy-quick: lint
	@$(MAKE) deploy --no-print-directory

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
	@echo "  make stats           Triple counts per module"
	@echo "  make concat          Bundle all ontologies into x.ttl"
	@echo "  make deploy          Full deployment pipeline"
	@echo "  make serve           Serve docs at :8000"
	@echo ""
	@echo "Modules: $(MODULES)"
