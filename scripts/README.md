# Ontology Scripts

## Everyday Workflows

### Validate modules

```bash
# Validate a single module (loads only its imports + SHACL)
make validate-rpm
make validate-deb

# Validate all modules
make validate-all

# Parse-check all .ttl files (no SHACL, just syntax)
make lint
```

Implemented by `validate_module.py`. Each module loads only `core.ttl` + its declared `owl:imports` + its own `.shacl.ttl` — not the entire ontology.

### Add a new ecosystem module

1. Create the directory and ontology file:
   ```
   ecosystems/<name>/<name>.ttl
   ```
2. Add `owl:imports <https://purl.org/packagegraph/ontology/core#>` in the ontology header
3. Add a SHACL shape file: `ecosystems/<name>/<name>.shacl.ttl`
4. Register in `NAMESPACES.md` (Current Namespaces table)
5. Add to `catalog-v001.xml`
6. Regenerate and sync PURLs (see below)

The Makefile auto-discovers modules — no Makefile changes needed.

### Regenerate PURL mappings

After adding/renaming modules, regenerate the PURL mapping JSON:

```bash
bash scripts/generate-purl-mappings.sh > purl-mappings.json
```

Then sync to the live PURL registry:

```bash
# Dry run — see what would change
bash scripts/sync-purls.sh --dry-run

# Apply
bash scripts/sync-purls.sh
```

Requires a valid cookie file at `../.purl-cookie` (Netscape format, exported from a logged-in `purl.archive.org` session).

---

## Script Reference

### generate-purl-mappings.sh

Scans all ontology `.ttl` files across `core/`, `extensions/*/`, `ecosystems/*/` and produces a JSON file mapping PURL paths to their redirect targets. Used as ground truth for PURL registration.

```bash
# Generate JSON to stdout
bash scripts/generate-purl-mappings.sh

# Validate live PURLs
bash scripts/generate-purl-mappings.sh --check
```

### sync-purls.sh

Automates PURL registration at `purl.archive.org` using `playwright-cli` with cookie-based authentication. Reads `purl-mappings.json`, compares against the live registry, adds missing entries and updates stale targets.

```bash
bash scripts/sync-purls.sh              # apply changes
bash scripts/sync-purls.sh --dry-run    # preview only
```

**Prerequisites:** `playwright-cli` installed, `../.purl-cookie` with valid session cookies.

### validate_module.py

Per-module SHACL validation. Called by `make validate-<module>` and `make validate-all`.

```bash
# Single module
uv run python scripts/validate_module.py rpm

# All modules
uv run python scripts/validate_module.py --all
```

Loads the module's ontology + its `owl:imports` dependencies + examples, then runs `pyshacl` against the module's `.shacl.ttl` shapes.

### split_shacl.py / split_examples.py

One-time migration scripts used to split the monolithic `shacl.ttl` and `examples.ttl` into per-module files. Not needed for ongoing work — kept for reference.

### fix_imports.py

One-time migration script that rewrote `owl:imports <core.ttl>` (relative file paths) to `owl:imports <https://purl.org/packagegraph/ontology/core#>` (namespace URIs) across all modules. Not needed for ongoing work.
