#!/usr/bin/env python3
"""Fix owl:imports to use namespace URIs instead of relative file paths."""

import re
from pathlib import Path

# Map relative file paths to namespace URIs
IMPORT_MAP = {
    "<core.ttl>": "<https://purl.org/packagegraph/ontology/core#>",
    "<vcs.ttl>": "<https://purl.org/packagegraph/ontology/vcs#>",
    "<security.ttl>": "<https://purl.org/packagegraph/ontology/security#>",
    "<rpm.ttl>": "<https://purl.org/packagegraph/ontology/rpm#>",
}

count = 0
for ttl in sorted(Path(".").rglob("*.ttl")):
    if ".venv" in str(ttl):
        continue
    content = ttl.read_text()
    new_content = content
    for old, new in IMPORT_MAP.items():
        new_content = new_content.replace(old, new)
    if new_content != content:
        ttl.write_text(new_content)
        count += 1
        print(f"  Fixed: {ttl}")

print(f"\nUpdated {count} files")
