#!/usr/bin/env bash
# generate-purl-mappings.sh — Generate JSON file of expected PURL redirects
#
# Scans all TTL files for ontology namespace declarations and produces a JSON
# file mapping PURL paths to their expected redirect targets. This JSON serves
# as ground truth for validating that all required PURLs are registered at
# purl.org/admin/domain/packagegraph.
#
# Usage:
#   ./scripts/generate-purl-mappings.sh                    # stdout
#   ./scripts/generate-purl-mappings.sh > purl-mappings.json   # file
#   ./scripts/generate-purl-mappings.sh --check            # validate live
#
# Output format:
#   {
#     "purl_domain": "/packagegraph",
#     "purl_base": "https://purl.org/packagegraph",
#     "target_base": "https://packagegraph.github.io/ontology/downloads",
#     "generated": "2026-04-14T12:00:00Z",
#     "mappings": [
#       {
#         "purl_path": "/packagegraph/ontology/core",
#         "purl_url": "https://purl.org/packagegraph/ontology/core",
#         "target_url": "https://packagegraph.github.io/ontology/downloads/core.ttl",
#         "namespace_uri": "https://purl.org/packagegraph/ontology/core#",
#         "ttl_file": "core.ttl",
#         "type": "302"
#       }
#     ]
#   }

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ONTOLOGY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PURL_DOMAIN="/packagegraph"
PURL_BASE="https://purl.org/packagegraph"
TARGET_BASE="https://packagegraph.github.io/ontology/downloads"
GENERATED=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

CHECK_MODE=false
if [[ "${1:-}" == "--check" ]]; then
    CHECK_MODE=true
fi

# Build mappings array by scanning TTL files for ontology declarations
mappings=""
first=true

# Also add the base domain redirect
mappings="$mappings{\"purl_path\":\"$PURL_DOMAIN\",\"purl_url\":\"$PURL_BASE\",\"target_url\":\"https://packagegraph.github.io/ontology/\",\"namespace_uri\":null,\"ttl_file\":null,\"type\":\"302\"}"
first=false

for ttl_file in "$ONTOLOGY_DIR"/core/*.ttl "$ONTOLOGY_DIR"/extensions/*/*.ttl "$ONTOLOGY_DIR"/ecosystems/*/*.ttl; do
    # Skip .shacl.ttl and .examples.ttl files
    [[ "$ttl_file" == *.shacl.ttl ]] && continue
    [[ "$ttl_file" == *.examples.ttl ]] && continue
    [[ ! -f "$ttl_file" ]] && continue
    filename=$(basename "$ttl_file")

    # Extract ontology namespace URI from near the owl:Ontology declaration
    # Handles both single-line and multi-line declarations
    ns_uri=$(grep -B2 'owl:Ontology' "$ttl_file" | grep -oE 'https://purl\.org/packagegraph/ontology/[^#]+#' | head -1 || true)

    # Fallback: check @prefix : <...> declaration (for files using default prefix like core.ttl)
    if [[ -z "$ns_uri" ]]; then
        ns_uri=$(grep '^@prefix :' "$ttl_file" | grep -oE 'https://purl\.org/packagegraph/ontology/[^#]+#' | head -1 || true)
    fi

    if [[ -z "$ns_uri" ]]; then
        continue
    fi

    # Extract module name from namespace: .../ontology/MODULE#
    module=$(echo "$ns_uri" | sed 's|.*ontology/||; s|#$||')

    purl_path="$PURL_DOMAIN/ontology/$module"
    purl_url="$PURL_BASE/ontology/$module"
    target_url="$TARGET_BASE/$filename"

    if [[ "$first" == "false" ]]; then
        mappings="$mappings,"
    fi
    first=false

    mappings="$mappings{\"purl_path\":\"$purl_path\",\"purl_url\":\"$purl_url\",\"target_url\":\"$target_url\",\"namespace_uri\":\"$ns_uri\",\"ttl_file\":\"$filename\",\"type\":\"302\"}"
done

if [[ "$CHECK_MODE" == "true" ]]; then
    # Validate each PURL redirect is live
    echo "Checking PURL redirects..."
    errors=0
    total=0

    for ttl_file in "$ONTOLOGY_DIR"/core/*.ttl "$ONTOLOGY_DIR"/extensions/*/*.ttl "$ONTOLOGY_DIR"/ecosystems/*/*.ttl; do
        # Skip .shacl.ttl and .examples.ttl files
        [[ "$ttl_file" == *.shacl.ttl ]] && continue
        [[ "$ttl_file" == *.examples.ttl ]] && continue
        [[ ! -f "$ttl_file" ]] && continue
        filename=$(basename "$ttl_file")
        ns_uri=$(grep -oE 'https://purl\.org/packagegraph/ontology/[^#]+#' "$ttl_file" | head -1 || true)
        [[ -z "$ns_uri" ]] && continue

        module=$(echo "$ns_uri" | sed 's|.*ontology/||; s|#$||')
        purl_url="$PURL_BASE/ontology/$module"
        expected_target="$TARGET_BASE/$filename"
        total=$((total + 1))

        # Check redirect with curl
        status=$(curl -s -o /dev/null -w "%{http_code}" -L --max-redirs 0 "$purl_url" 2>/dev/null || echo "000")
        location=$(curl -s -o /dev/null -w "%{redirect_url}" -L --max-redirs 0 "$purl_url" 2>/dev/null || echo "")

        if [[ "$status" == "302" ]] || [[ "$status" == "301" ]]; then
            if echo "$location" | grep -q "$filename"; then
                echo "  ✓ $module → $filename"
            else
                echo "  ✗ $module → redirects to $location (expected $expected_target)"
                errors=$((errors + 1))
            fi
        else
            echo "  ✗ $module → HTTP $status (expected 301/302). Register at: https://purl.org/admin/domain/packagegraph"
            echo "    Name: $PURL_DOMAIN/ontology/$module"
            echo "    Target: $expected_target"
            errors=$((errors + 1))
        fi
    done

    echo ""
    echo "$((total - errors))/$total PURL redirects OK"
    if [[ "$errors" -gt 0 ]]; then
        echo ""
        echo "To register missing PURLs:"
        echo "  1. Go to https://purl.org/admin/domain/packagegraph"
        echo "  2. Add each missing redirect with type '302'"
        exit 1
    fi
else
    # Output JSON
    cat <<EOF
{
  "purl_domain": "$PURL_DOMAIN",
  "purl_base": "$PURL_BASE",
  "target_base": "$TARGET_BASE",
  "generated": "$GENERATED",
  "mappings": [
    $(echo "$mappings" | sed 's/},{/},\n    {/g')
  ]
}
EOF
fi
