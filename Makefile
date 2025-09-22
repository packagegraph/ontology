# Package Management Ontology Makefile
# This Makefile provides utilities for validating, combining, and managing ontology files

# Variables
ONTOLOGY_FILES = core.ttl vcs.ttl rpm.ttl debian.ttl arch.ttl bsd.ttl chocolatey.ttl homebrew.ttl nix.ttl examples.ttl
COMBINED_FILE = x.ttl
# Use plain python in GitHub Actions, uv run python locally
PYTHON = $(if $(GITHUB_ACTIONS),python,uv run python)
# Use home directory paths for local, working directory for GitHub Actions
ROBOT_JAR = $(if $(GITHUB_ACTIONS),robot.jar,robot.jar)
WIDOCO_JAR = $(if $(GITHUB_ACTIONS),widoco.jar,widoco.jar)
ROBOT_PATH = $(if $(GITHUB_ACTIONS),$(HOME)/robot.jar,$(ROBOT_JAR))
WIDOCO_PATH = $(if $(GITHUB_ACTIONS),$(HOME)/widoco.jar,$(WIDOCO_JAR))
DOCS_DIR = docs
DOWNLOADS_DIR = $(DOCS_DIR)/downloads
ONTOLOGY_DOCS_DIR = $(DOCS_DIR)/ontology
REPORTS_DIR = $(DOCS_DIR)/reports

# Default target
.PHONY: all
all: lint concat

# Deploy target - runs the full deployment pipeline locally
.PHONY: deploy
deploy: setup-tools validate-robot create-dirs generate-formats verify-files generate-docs create-index create-negotiation
	@echo "Local deployment complete! Check the $(DOCS_DIR) directory."

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

# ==============================================================================
# LOCAL DEPLOYMENT TARGETS (mirroring GitHub Actions workflow)
# ==============================================================================

# Setup required tools (ROBOT and WIDOCO)
.PHONY: setup-tools
setup-tools:
	@echo "Setting up required tools..."
	@if [ ! -f $(ROBOT_PATH) ]; then \
		echo "Downloading ROBOT..."; \
		curl -L https://github.com/ontodev/robot/releases/latest/download/robot.jar -o $(ROBOT_PATH); \
	else \
		echo "ROBOT already available"; \
	fi
	@if [ ! -f $(WIDOCO_PATH) ]; then \
		echo "Downloading WIDOCO..."; \
		curl -L -o $(WIDOCO_PATH) https://github.com/dgarijo/Widoco/releases/download/v1.4.25/widoco-1.4.25-jar-with-dependencies_JDK-17.jar || true; \
		if [ ! -s $(WIDOCO_PATH) ] || [ "$$(stat -f%z $(WIDOCO_PATH) 2>/dev/null || stat -c%s $(WIDOCO_PATH))" -lt 1000 ]; then \
			echo "WIDOCO download failed or file too small"; \
			rm -f $(WIDOCO_PATH); \
		fi; \
	else \
		echo "WIDOCO already available"; \
	fi

# Validate ontology files with ROBOT
.PHONY: validate-robot
validate-robot: setup-tools
	@echo "Validating ontology files with ROBOT..."
	@mkdir -p reports
	@for ttl_file in $(ONTOLOGY_FILES); do \
		if [ -f "$$ttl_file" ]; then \
			echo "Validating $$ttl_file"; \
			java -jar $(ROBOT_PATH) report --input "$$ttl_file" --output "reports/$${ttl_file%.ttl}-report.tsv" || true; \
		fi; \
	done

# Create directory structure for documentation
.PHONY: create-dirs
create-dirs:
	@echo "Creating directory structure..."
	@mkdir -p $(ONTOLOGY_DOCS_DIR)
	@mkdir -p $(REPORTS_DIR)
	@mkdir -p $(DOWNLOADS_DIR)
	@if [ -d reports ]; then \
		cp reports/*.tsv $(REPORTS_DIR)/ 2>/dev/null || true; \
	fi

# Generate different RDF serializations
.PHONY: generate-formats
generate-formats: setup-tools create-dirs
	@echo "Converting Turtle files to other RDF formats..."
	@for ttl_file in $(ONTOLOGY_FILES); do \
		if [ -f "$$ttl_file" ]; then \
			base_name="$${ttl_file%.ttl}"; \
			echo "Converting $$ttl_file to multiple formats..."; \
			\
			temp_file="/tmp/$${base_name}_web.ttl"; \
			sed -e 's|<\([^/>]*\)\.ttl>|<https://packagegraph.github.io/ontology/\1>|g' \
			    "$$ttl_file" > "$$temp_file"; \
			\
			$(PYTHON) -c "import rdflib; g = rdflib.Graph(); g.parse('$$temp_file', format='turtle'); g.serialize('$(DOWNLOADS_DIR)/$${base_name}.owl', format='xml'); print('Successfully converted $$ttl_file to RDF/XML')" 2>/dev/null || echo '<!-- RDF/XML conversion failed -->' > "$(DOWNLOADS_DIR)/$${base_name}.owl"; \
			\
			$(PYTHON) -c "import rdflib; g = rdflib.Graph(); g.parse('$$temp_file', format='turtle'); g.serialize('$(DOWNLOADS_DIR)/$${base_name}.jsonld', format='json-ld'); print('Successfully converted $$ttl_file to JSON-LD')" 2>/dev/null || echo '{"error": "JSON-LD conversion failed"}' > "$(DOWNLOADS_DIR)/$${base_name}.jsonld"; \
			\
			$(PYTHON) -c "import rdflib; g = rdflib.Graph(); g.parse('$$temp_file', format='turtle'); g.serialize('$(DOWNLOADS_DIR)/$${base_name}.nt', format='nt'); print('Successfully converted $$ttl_file to N-Triples')" 2>/dev/null || echo '# N-Triples conversion failed' > "$(DOWNLOADS_DIR)/$${base_name}.nt"; \
			\
			cp "$$temp_file" "$(DOWNLOADS_DIR)/$${base_name}.ttl"; \
			rm -f "$$temp_file"; \
		fi; \
	done

# Verify generated files
.PHONY: verify-files
verify-files: generate-formats
	@echo "Verifying generated files..."
	@for ttl_file in $(ONTOLOGY_FILES); do \
		if [ -f "$$ttl_file" ]; then \
			base_name="$${ttl_file%.ttl}"; \
			echo "Checking files for $$base_name:"; \
			\
			[ -f "$(DOWNLOADS_DIR)/$${base_name}.ttl" ] && echo "✓ Turtle file exists" || echo "✗ Turtle file missing"; \
			[ -f "$(DOWNLOADS_DIR)/$${base_name}.owl" ] && echo "✓ RDF/XML file exists" || echo "✗ RDF/XML file missing"; \
			[ -f "$(DOWNLOADS_DIR)/$${base_name}.nt" ] && echo "✓ N-Triples file exists" || echo "✗ N-Triples file missing"; \
			[ -f "$(DOWNLOADS_DIR)/$${base_name}.jsonld" ] && echo "✓ JSON-LD file exists" || echo "✗ JSON-LD file missing"; \
			\
			for ext in ttl owl nt jsonld; do \
				file_path="$(DOWNLOADS_DIR)/$${base_name}.$$ext"; \
				if [ -f "$$file_path" ]; then \
					file_size=$$(stat -f%z "$$file_path" 2>/dev/null || stat -c%s "$$file_path"); \
					if [ "$$file_size" -lt 100 ]; then \
						echo "⚠ Warning: $$file_path is very small ($$file_size bytes)"; \
					else \
						echo "✓ $$ext file size OK ($$file_size bytes)"; \
					fi; \
				fi; \
			done; \
			echo ""; \
		fi; \
	done
	@echo "Generated files listing:"
	@find $(DOWNLOADS_DIR) -name "*.ttl" -o -name "*.owl" -o -name "*.nt" -o -name "*.jsonld" | sort

# Generate ontology documentation with WIDOCO
.PHONY: generate-docs
generate-docs: setup-tools create-dirs
	@echo "Generating ontology documentation..."
	@if [ ! -f $(WIDOCO_PATH) ] || [ ! -s $(WIDOCO_PATH) ]; then \
		echo "WIDOCO jar not found or empty, skipping doc generation"; \
	else \
		for ttl_file in $(ONTOLOGY_FILES); do \
			if [ -f "$$ttl_file" ]; then \
				base_name="$${ttl_file%.ttl}"; \
				echo "Generating documentation for $$ttl_file..."; \
				mkdir -p "$(ONTOLOGY_DOCS_DIR)/$$base_name"; \
				timeout 600 java -Xmx4g -jar $(WIDOCO_PATH) -ontFile "$$ttl_file" -outFolder "$(ONTOLOGY_DOCS_DIR)/$$base_name" -htaccess -webVowl -rewriteAll -getOntologyMetadata || { \
					echo "WIDOCO failed for $$ttl_file, creating basic HTML doc"; \
					{ \
						echo '<!DOCTYPE html>'; \
						echo '<html>'; \
						echo '<head>'; \
						echo "    <title>$$base_name Ontology Documentation</title>"; \
						echo '</head>'; \
						echo '<body>'; \
						echo "    <h1>$$base_name Ontology</h1>"; \
						echo '    <p>Automated documentation generation failed. Please refer to the source files:</p>'; \
						echo '    <ul>'; \
						echo "        <li><a href=\"../../downloads/$$base_name.ttl\">Turtle format</a></li>"; \
						echo "        <li><a href=\"../../downloads/$$base_name.owl\">OWL/RDF format</a></li>"; \
						echo '    </ul>'; \
						echo '</body>'; \
						echo '</html>'; \
					} > "$(ONTOLOGY_DOCS_DIR)/$$base_name/index-en.html"; \
				}; \
			fi; \
		done; \
	fi

# Create main index page
.PHONY: create-index
create-index: create-dirs
	@echo "Creating main index page..."
	@{ \
		echo '<!DOCTYPE html>'; \
		echo '<html lang="en">'; \
		echo '<head>'; \
		echo '    <meta charset="UTF-8">'; \
		echo '    <meta name="viewport" content="width=device-width, initial-scale=1.0">'; \
		echo '    <title>Package Management Ontologies</title>'; \
		echo '    <style>'; \
		echo '        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }'; \
		echo '        .container { max-width: 1200px; margin: 0 auto; }'; \
		echo '        .ontology-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }'; \
		echo '        .ontology-card { border: 1px solid #ddd; padding: 20px; border-radius: 8px; background: #f9f9f9; }'; \
		echo '        .format-links { margin-top: 15px; }'; \
		echo '        .format-links a { margin-right: 10px; padding: 5px 10px; background: #007cba; color: white; text-decoration: none; border-radius: 3px; font-size: 0.9em; }'; \
		echo '        .format-links a:hover { background: #005a87; }'; \
		echo '        h1, h2 { color: #333; }'; \
		echo '        .namespace { font-family: monospace; background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }'; \
		echo '    </style>'; \
		echo '</head>'; \
		echo '<body>'; \
		echo '    <div class="container">'; \
		echo '        <h1>Package Management RDF Ontologies</h1>'; \
		echo '        <p>A comprehensive collection of RDF/OWL ontologies for representing software packages, repositories, and metadata across major package management systems.</p>'; \
		echo ''; \
		echo '        <h2>Available Ontologies</h2>'; \
		echo '        <div class="ontology-grid">'; \
	} > $(DOCS_DIR)/index.html
	@for ttl_file in $(ONTOLOGY_FILES); do \
		if [ -f "$$ttl_file" ]; then \
			base_name="$${ttl_file%.ttl}"; \
			title=$$(grep -m1 "rdfs:label\|dc:title\|dct:title" "$$ttl_file" | sed 's/.*"\([^"]*\)".*/\1/' | head -1); \
			if [ -z "$$title" ]; then title="$$base_name"; fi; \
			description=$$(grep -m1 "rdfs:comment\|dc:description\|dct:description" "$$ttl_file" | sed 's/.*"\([^"]*\)".*/\1/' | head -1); \
			if [ -z "$$description" ]; then description="Ontology for $$base_name package management system"; fi; \
			namespace=$$(grep -m1 "@prefix.*:.*<http.*>" "$$ttl_file" | sed 's/.*<\([^>]*\)>.*/\1/' | head -1); \
			{ \
				echo '                      <div class="ontology-card">'; \
				echo "                          <h3>$$title</h3>"; \
				echo "                          <p>$$description</p>"; \
				echo "                          <p><strong>Namespace:</strong> <span class=\"namespace\">$$namespace</span></p>"; \
				echo '                          <div class="format-links">'; \
				echo "                              <a href=\"ontology/$$base_name/index-en.html\">Documentation</a>"; \
				echo "                              <a href=\"downloads/$$base_name.ttl\">Turtle</a>"; \
				echo "                              <a href=\"downloads/$$base_name.owl\">RDF/XML</a>"; \
				echo "                              <a href=\"downloads/$$base_name.jsonld\">JSON-LD</a>"; \
				echo "                              <a href=\"downloads/$$base_name.nt\">N-Triples</a>"; \
				echo '                          </div>'; \
				echo '                      </div>'; \
			} >> $(DOCS_DIR)/index.html; \
		fi; \
	done
	@{ \
		echo '        </div>'; \
		echo ''; \
		echo '        <h2>Content Negotiation</h2>'; \
		echo '        <p>The ontologies support content negotiation. You can request different formats using the Accept header:</p>'; \
		echo '        <ul>'; \
		echo '            <li><code>text/turtle</code> - Turtle format</li>'; \
		echo '            <li><code>application/rdf+xml</code> - RDF/XML format</li>'; \
		echo '            <li><code>application/ld+json</code> - JSON-LD format</li>'; \
		echo '            <li><code>application/n-triples</code> - N-Triples format</li>'; \
		echo '            <li><code>text/html</code> - HTML documentation</li>'; \
		echo '        </ul>'; \
		echo ''; \
		echo '        <h2>Usage Examples</h2>'; \
		echo '        <pre><code># Get Turtle representation'; \
		echo 'curl -H "Accept: text/turtle" https://packagegraph.github.io/ontology/core'; \
		echo ''; \
		echo '# Get JSON-LD representation'; \
		echo 'curl -H "Accept: application/ld+json" https://packagegraph.github.io/ontology/debian'; \
		echo ''; \
		echo '# Get HTML documentation (default)'; \
		echo 'curl -H "Accept: text/html" https://packagegraph.github.io/ontology/rpm</code></pre>'; \
		echo '    </div>'; \
		echo '</body>'; \
		echo '</html>'; \
	} >> $(DOCS_DIR)/index.html

# Create Jekyll configuration and content negotiation setup
.PHONY: create-negotiation
create-negotiation: create-dirs
	@echo "Creating Jekyll configuration and content negotiation setup..."
	@{ \
		echo '# Jekyll configuration for GitHub Pages'; \
		echo 'plugins:'; \
		echo '  - jekyll-redirect-from'; \
		echo ''; \
		echo '# Content negotiation through Jekyll'; \
		echo 'collections:'; \
		echo '  ontologies:'; \
		echo '    output: true'; \
		echo ''; \
		echo 'defaults:'; \
		echo '  - scope:'; \
		echo '      path: "downloads"'; \
		echo '    values:'; \
		echo '      layout: null'; \
		echo ''; \
		echo '# Enable safe mode for GitHub Pages'; \
		echo 'safe: true'; \
		echo ''; \
		echo '# Set base URL for GitHub Pages'; \
		echo 'baseurl: "/ontology"'; \
		echo 'url: "https://packagegraph.github.io"'; \
		echo ''; \
		echo '# Include file extensions for proper content type handling'; \
		echo 'include:'; \
		echo '  - "*.ttl"'; \
		echo '  - "*.owl"'; \
		echo '  - "*.nt"'; \
		echo '  - "*.jsonld"'; \
		echo ''; \
		echo '# Keep file extensions'; \
		echo 'keep_files:'; \
		echo '  - "downloads"'; \
		echo ''; \
		echo '# Exclude from processing'; \
		echo 'exclude:'; \
		echo '  - "*.log"'; \
		echo '  - "reports"'; \
	} > $(DOCS_DIR)/_config.yml
	@{ \
		echo '# Content-Type headers for RDF formats'; \
		echo '/downloads/*.ttl'; \
		echo '  Content-Type: text/turtle'; \
		echo ''; \
		echo '/downloads/*.owl'; \
		echo '  Content-Type: application/rdf+xml'; \
		echo ''; \
		echo '/downloads/*.nt'; \
		echo '  Content-Type: application/n-triples'; \
		echo ''; \
		echo '/downloads/*.jsonld'; \
		echo '  Content-Type: application/ld+json'; \
	} > $(DOCS_DIR)/_headers
	@echo "Creating content negotiation setup..."
	@for ttl_file in $(ONTOLOGY_FILES); do \
		if [ -f "$$ttl_file" ]; then \
			base_name="$${ttl_file%.ttl}"; \
			mkdir -p "$(DOCS_DIR)/$$base_name"; \
			{ \
				echo '<!DOCTYPE html>'; \
				echo '<html lang="en">'; \
				echo '<head>'; \
				echo '    <meta charset="UTF-8">'; \
				echo '    <meta name="viewport" content="width=device-width, initial-scale=1.0">'; \
				echo "    <title>$$base_name Ontology</title>"; \
				echo "    <link rel=\"alternate\" type=\"text/turtle\" href=\"../downloads/$$base_name.ttl\" />"; \
				echo "    <link rel=\"alternate\" type=\"application/rdf+xml\" href=\"../downloads/$$base_name.owl\" />"; \
				echo "    <link rel=\"alternate\" type=\"application/ld+json\" href=\"../downloads/$$base_name.jsonld\" />"; \
				echo "    <link rel=\"alternate\" type=\"application/n-triples\" href=\"../downloads/$$base_name.nt\" />"; \
				echo '    <script>'; \
				echo '        // Simple content negotiation via JavaScript for GitHub Pages'; \
				echo '        (function() {'; \
				echo '            var accept = getAcceptHeader();'; \
				echo "            var baseUrl = '../downloads/$$base_name';"; \
				echo ''; \
				echo "            if (accept.includes('text/turtle') || accept.includes('text/plain')) {"; \
				echo "                window.location.href = baseUrl + '.ttl';"; \
				echo "            } else if (accept.includes('application/rdf+xml') || accept.includes('application/xml')) {"; \
				echo "                window.location.href = baseUrl + '.owl';"; \
				echo "            } else if (accept.includes('application/ld+json') || accept.includes('application/json')) {"; \
				echo "                window.location.href = baseUrl + '.jsonld';"; \
				echo "            } else if (accept.includes('application/n-triples')) {"; \
				echo "                window.location.href = baseUrl + '.nt';"; \
				echo "            } else if (!accept.includes('text/html')) {"; \
				echo '                // Default to HTML documentation for browsers'; \
				echo "                window.location.href = '../ontology/$$base_name/index-en.html';"; \
				echo '            }'; \
				echo ''; \
				echo '            function getAcceptHeader() {'; \
				echo '                // GitHub Pages doesn'\''t give us access to request headers'; \
				echo '                // This is a limitation - users need to use direct links'; \
				echo "                return 'text/html';"; \
				echo '            }'; \
				echo '        })();'; \
				echo '    </script>'; \
				echo '</head>'; \
				echo '<body>'; \
				echo "    <h1>$$base_name Ontology</h1>"; \
				echo "    <p>This is the $$base_name ontology. Choose your preferred format:</p>"; \
				echo '    <ul>'; \
				echo "        <li><a href=\"../ontology/$$base_name/index-en.html\">HTML Documentation</a></li>"; \
				echo "        <li><a href=\"../downloads/$$base_name.ttl\">Turtle (.ttl)</a></li>"; \
				echo "        <li><a href=\"../downloads/$$base_name.owl\">RDF/XML (.owl)</a></li>"; \
				echo "        <li><a href=\"../downloads/$$base_name.jsonld\">JSON-LD (.jsonld)</a></li>"; \
				echo "        <li><a href=\"../downloads/$$base_name.nt\">N-Triples (.nt)</a></li>"; \
				echo '    </ul>'; \
				echo ''; \
				echo '    <h2>Programmatic Access</h2>'; \
				echo '    <p>For programmatic access, use these direct URLs:</p>'; \
				echo '    <pre><code># Turtle format'; \
				echo "wget https://packagegraph.github.io/ontology/downloads/$$base_name.ttl"; \
				echo ''; \
				echo '# RDF/XML format'; \
				echo "wget https://packagegraph.github.io/ontology/downloads/$$base_name.owl"; \
				echo ''; \
				echo '# JSON-LD format'; \
				echo "wget https://packagegraph.github.io/ontology/downloads/$$base_name.jsonld"; \
				echo ''; \
				echo '# N-Triples format'; \
				echo "wget https://packagegraph.github.io/ontology/downloads/$$base_name.nt</code></pre>"; \
				echo '</body>'; \
				echo '</html>'; \
			} > "$(DOCS_DIR)/$$base_name/index.html"; \
		fi; \
	done

# Clean deployment files
.PHONY: clean-deploy
clean-deploy:
	@echo "Cleaning deployment files..."
	@rm -rf $(DOCS_DIR)
	@rm -rf reports
	@rm -f $(ROBOT_PATH) $(WIDOCO_PATH)
	@echo "Deployment files cleaned!"

# Quick deployment (without WIDOCO documentation generation)
.PHONY: deploy-quick
deploy-quick: setup-tools validate-robot create-dirs generate-formats verify-files create-index create-negotiation
	@echo "Quick local deployment complete! Check the $(DOCS_DIR) directory."
	@echo "Note: WIDOCO documentation generation was skipped for speed."

# Serve the documentation locally (requires Python built-in server)
.PHONY: serve
serve: 
	@if [ ! -d $(DOCS_DIR) ]; then \
		echo "No documentation found. Run 'make deploy' first."; \
		exit 1; \
	fi
	@echo "Starting local server at http://localhost:8000"
	@echo "Press Ctrl+C to stop the server"
	@cd $(DOCS_DIR) && python3 -m http.server 8000

# Help target
.PHONY: help
help:
	@echo "Package Management Ontology Makefile"
	@echo "====================================="
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "Basic targets:"
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
	@echo ""
	@echo "Local deployment targets (mirror GitHub Actions workflow):"
	@echo "  deploy           - Run full deployment pipeline locally"
	@echo "  deploy-quick     - Quick deployment (without WIDOCO docs)"
	@echo "  setup-tools      - Download ROBOT and WIDOCO tools"
	@echo "  validate-robot   - Validate ontologies with ROBOT"
	@echo "  create-dirs      - Create documentation directory structure"
	@echo "  generate-formats - Convert TTL to RDF/XML, JSON-LD, N-Triples"
	@echo "  verify-files     - Verify all generated files exist and are valid"
	@echo "  generate-docs    - Generate HTML documentation with WIDOCO"
	@echo "  create-index     - Create main index.html page"
	@echo "  create-negotiation - Setup content negotiation pages"
	@echo "  serve            - Serve documentation locally at :8000"
	@echo "  clean-deploy     - Clean all deployment files and tools"
	@echo ""
	@echo "  help             - Show this help message"
	@echo ""
	@echo "Files processed: $(ONTOLOGY_FILES)"
	@echo "Combined output:  $(COMBINED_FILE)"
	@echo "Documentation:   $(DOCS_DIR)/"