#!/usr/bin/env bash
# sync-purls.sh — Register/update PURL redirects at purl.archive.org
#
# Uses playwright-cli with cookie-based auth to sync the PURLs defined in
# purl-mappings.json with the live PURL registry.
#
# Prerequisites:
#   - playwright-cli installed (npm install -g @anthropic/playwright-cli or via Pilot Shell)
#   - Cookie file at ../.purl-cookie (Netscape format, exported from browser)
#     Export from Firefox: about:config → devtools.chrome.enabled → true,
#     then Browser Console → copy(document.cookie) and format as Netscape.
#     Or use a cookie export extension.
#
# Usage:
#   cd ontology/
#   # First: regenerate mappings from current ontology
#   bash scripts/generate-purl-mappings.sh > purl-mappings.json
#
#   # Then: sync to purl.archive.org
#   bash scripts/sync-purls.sh
#
#   # Dry run (show what would be done):
#   bash scripts/sync-purls.sh --dry-run
#
# What it does:
#   1. Opens purl.archive.org and injects auth cookies
#   2. Reads existing PURLs from the /packagegraph domain page
#   3. Compares against purl-mappings.json
#   4. Adds missing PURLs
#   5. Updates PURLs with wrong target URLs
#   6. Reports results

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ONTOLOGY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COOKIE_FILE="${PURL_COOKIE_FILE:-$ONTOLOGY_DIR/../.purl-cookie}"
MAPPINGS_FILE="$ONTOLOGY_DIR/purl-mappings.json"
DOMAIN_URL="https://purl.archive.org/domain/packagegraph"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "DRY RUN — no changes will be made"
fi

if [[ ! -f "$COOKIE_FILE" ]]; then
    echo "ERROR: Cookie file not found: $COOKIE_FILE"
    echo "Export cookies from your browser session at purl.archive.org"
    echo "Set PURL_COOKIE_FILE env var or place at ../.purl-cookie"
    exit 1
fi

if [[ ! -f "$MAPPINGS_FILE" ]]; then
    echo "ERROR: purl-mappings.json not found. Run: bash scripts/generate-purl-mappings.sh > purl-mappings.json"
    exit 1
fi

# Parse cookie file and inject via playwright-cli
inject_cookies() {
    echo "Injecting auth cookies..."
    while IFS=$'\t' read -r domain _flag path secure _expiry name value; do
        [[ "$domain" == \#* ]] && continue
        [[ -z "$name" ]] && continue
        playwright-cli cookie-set "$name" "$value" --domain "$domain" --path "$path" 2>&1 | tail -0
    done < "$COOKIE_FILE"
}

echo "=== PURL Sync ==="
echo "  Mappings: $MAPPINGS_FILE"
echo "  Cookies:  $COOKIE_FILE"
echo ""

# Open browser and inject cookies
playwright-cli open "$DOMAIN_URL" 2>&1 | head -1
inject_cookies
playwright-cli goto "$DOMAIN_URL" 2>&1 | head -1

# Get currently registered PURLs
EXISTING=$(playwright-cli eval '
    Array.from(document.querySelectorAll("table")[0].querySelectorAll("tbody tr"))
        .map(r => {
            const cells = r.querySelectorAll("td");
            return cells[0]?.textContent?.trim() + "|" + cells[2]?.textContent?.trim();
        })
        .join("\n")
' 2>&1 | grep "^###" -A1 | tail -1 | tr -d '"')

echo "Currently registered:"
echo "$EXISTING" | sed 's/\\n/\n/g' | while read -r line; do
    [[ -n "$line" ]] && echo "  $line"
done
echo ""

# Parse desired state from purl-mappings.json
DESIRED=$(python3 -c "
import json
with open('$MAPPINGS_FILE') as f:
    data = json.load(f)
for m in data['mappings']:
    if m['ttl_file']:
        print(f\"{m['purl_path']}|{m['target_url']}\")
")

# Compute diff
added=0
updated=0
skipped=0

while IFS='|' read -r purl_path target_url; do
    name=$(echo "$purl_path" | sed 's|/packagegraph/ontology/||')

    if echo "$EXISTING" | sed 's/\\n/\n/g' | grep -q "^$purl_path|"; then
        # Already exists — check if target matches
        existing_target=$(echo "$EXISTING" | sed 's/\\n/\n/g' | grep "^$purl_path|" | cut -d'|' -f2)
        if [[ "$existing_target" == "$target_url" ]]; then
            skipped=$((skipped + 1))
        else
            echo "UPDATE: $name ($existing_target → $target_url)"
            if [[ "$DRY_RUN" == "false" ]]; then
                playwright-cli goto "https://purl.archive.org/purl$purl_path" 2>&1 | head -0
                playwright-cli run-code "async page => {
                    await page.getByRole('button', { name: 'edit' }).click();
                    await page.waitForLoadState('networkidle');
                    await page.getByRole('textbox', { name: 'target URL' }).fill('$target_url');
                    await Promise.all([
                        page.waitForNavigation({ timeout: 10000 }).catch(() => {}),
                        page.getByRole('button', { name: 'save' }).click()
                    ]);
                }" 2>&1 | head -0
                playwright-cli goto "$DOMAIN_URL" 2>&1 | head -0
            fi
            updated=$((updated + 1))
        fi
    else
        echo "ADD: $name → $target_url"
        if [[ "$DRY_RUN" == "false" ]]; then
            playwright-cli run-code "async page => {
                await page.locator('input[name=\"name\"]').fill('$purl_path');
                await page.locator('input[name=\"target\"]').fill('$target_url');
                await Promise.all([
                    page.waitForNavigation({ timeout: 10000 }).catch(() => {}),
                    page.locator('button:has-text(\"Add\")').click()
                ]);
            }" 2>&1 | head -0
        fi
        added=$((added + 1))
    fi
done <<< "$DESIRED"

echo ""
echo "=== Results ==="
echo "  Added:   $added"
echo "  Updated: $updated"
echo "  Skipped: $skipped (already correct)"

if [[ "$DRY_RUN" == "false" ]]; then
    # Verify final count
    final_count=$(playwright-cli eval 'Array.from(document.querySelectorAll("table")[0].querySelectorAll("tbody tr")).length' 2>&1 | grep "^###" -A1 | tail -1 | tr -d '"')
    echo "  Total registered: $final_count"
fi

playwright-cli close 2>&1 | head -0
echo "Done."
