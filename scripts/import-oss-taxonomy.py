#!/usr/bin/env python3
"""Convert ecosyste.ms OSS Taxonomy combined-taxonomy.json to SKOS Turtle.

Usage:
    python import-oss-taxonomy.py --input combined-taxonomy.json --output taxonomy-concepts.ttl

The input JSON is expected to have facet keys (domain, role, function, audience,
layer, technology) each containing an array of term objects with name, description,
optional aliases, related terms, and example projects.

Output is appended-ready SKOS Turtle with concepts linked to the TaxonomyScheme
and facet collections defined in extensions/taxonomy/taxonomy.ttl.
"""

import argparse
import json
import re
import sys
from pathlib import Path


PREFIXES = """\
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix tax: <https://purl.org/packagegraph/ontology/taxonomy#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

"""

FACETS = {
    "domain": "DomainFacet",
    "role": "RoleFacet",
    "function": "FunctionFacet",
    "audience": "AudienceFacet",
    "layer": "LayerFacet",
    "technology": "TechnologyFacet",
}


def slugify(name: str) -> str:
    """Convert a term name to a URI-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def escape_turtle(s: str) -> str:
    """Escape a string for Turtle literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def main():
    parser = argparse.ArgumentParser(description="Convert OSS Taxonomy JSON to SKOS Turtle")
    parser.add_argument("--input", required=True, help="Path to combined-taxonomy.json")
    parser.add_argument("--output", required=True, help="Output Turtle file path")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(input_path) as f:
        taxonomy = json.load(f)

    all_concept_uris: dict[str, str] = {}
    lines: list[str] = [PREFIXES]
    facet_members: dict[str, list[str]] = {k: [] for k in FACETS}

    for facet_key, facet_collection in FACETS.items():
        if facet_key not in taxonomy:
            print(f"Warning: facet '{facet_key}' not found in input", file=sys.stderr)
            continue

        terms = taxonomy[facet_key]
        if not isinstance(terms, list):
            print(f"Warning: facet '{facet_key}' is not an array, skipping", file=sys.stderr)
            continue

        for term in terms:
            name = term.get("name", "").strip()
            if not name:
                continue

            slug = slugify(name)
            concept_uri = f"tax:{facet_key}-{slug}"
            all_concept_uris[f"{facet_key}:{slug}"] = concept_uri
            facet_members[facet_key].append(concept_uri)

            lines.append(f'{concept_uri} a skos:Concept ;')
            lines.append(f'    skos:inScheme tax:TaxonomyScheme ;')
            lines.append(f'    skos:prefLabel "{escape_turtle(name)}"@en ;')

            description = term.get("description", "").strip()
            if description:
                lines.append(f'    skos:definition "{escape_turtle(description)}"@en ;')

            aliases = term.get("aliases", [])
            for alias in aliases:
                alias = alias.strip()
                if alias:
                    lines.append(f'    skos:altLabel "{escape_turtle(alias)}"@en ;')

            examples = term.get("examples", [])
            for example in examples:
                example = example.strip()
                if example:
                    lines.append(f'    skos:example "{escape_turtle(example)}" ;')

            # Close the concept (replace trailing ; with .)
            if lines[-1].endswith(" ;"):
                lines[-1] = lines[-1][:-2] + " ."
            else:
                lines.append("    .")
            lines.append("")

    # Emit skos:related links (second pass to resolve cross-facet references)
    related_triples: list[str] = []
    for facet_key in FACETS:
        if facet_key not in taxonomy:
            continue
        for term in taxonomy[facet_key]:
            name = term.get("name", "").strip()
            if not name:
                continue
            slug = slugify(name)
            source_key = f"{facet_key}:{slug}"
            source_uri = all_concept_uris.get(source_key)
            if not source_uri:
                continue

            for related in term.get("related", []):
                related = related.strip()
                if not related:
                    continue
                related_slug = slugify(related)
                # Try to find the related term in any facet
                target_uri = None
                for other_facet in FACETS:
                    candidate_key = f"{other_facet}:{related_slug}"
                    if candidate_key in all_concept_uris:
                        target_uri = all_concept_uris[candidate_key]
                        break
                if target_uri:
                    related_triples.append(f"{source_uri} skos:related {target_uri} .")

    if related_triples:
        lines.append("# Cross-facet related links")
        lines.extend(related_triples)
        lines.append("")

    # Emit facet collection membership
    lines.append("# Facet collection membership")
    for facet_key, facet_collection in FACETS.items():
        members = facet_members.get(facet_key, [])
        if members:
            member_list = " ,\n        ".join(members)
            lines.append(f"tax:{facet_collection} skos:member {member_list} .")
            lines.append("")

    output_path = Path(args.output)
    output_path.write_text("\n".join(lines))
    print(f"Generated {len(all_concept_uris)} concepts across {len(FACETS)} facets → {output_path}")


if __name__ == "__main__":
    main()
