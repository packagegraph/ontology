#!/usr/bin/env python3
"""Measure explicit, graph-local PURL coverage using read-only SPARQL SELECTs.

Requires Python 3 and curl. No RDF inference or full PURL syntax validation is
performed. A version marker is an unescaped @ after the last path slash and
before qualifiers/subpath; its presence alone does not establish validity.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ENDPOINT = "https://packagegraph.di.riseproject.dev/"
PREFIX = "PREFIX pkg: <https://purl.org/packagegraph/ontology/core#>\n"
POPULATIONS = ("identity", "package")
METRICS = ("denominator", "with_purl", "missing_purl", "multiple_purls",
           "with_version_marker", "without_version_marker")
TYPES = """VALUES (?type ?population) {
    (pkg:PackageIdentity "identity")
    (pkg:Package "package")
    (pkg:BinaryPackage "package")
    (pkg:SourcePackage "package")
}"""
DISCOVERY_QUERY = PREFIX + """SELECT DISTINCT ?graph WHERE {
    GRAPH ?graph {
        """ + TYPES + """
        ?subject a ?type .
    }
} ORDER BY ?graph
"""


def count_query(graph=None):
    """Return the actual counting query, optionally restricted to one graph."""
    graph_values = ""
    if graph is not None:
        if (not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", graph)
                or re.search(r'[\s<>"{}|^`\\]', graph)):
            raise ValueError("Graph must be an absolute IRI without SPARQL delimiters")
        graph_values = f"VALUES ?graph {{ <{graph}> }}"
    return PREFIX + """SELECT ?graph ?population
    (COUNT(*) AS ?denominator)
    (SUM(IF(?purl_count > 0, 1, 0)) AS ?with_purl)
    (SUM(IF(?purl_count = 0, 1, 0)) AS ?missing_purl)
    (SUM(IF(?purl_count > 1, 1, 0)) AS ?multiple_purls)
    (SUM(?has_version_marker) AS ?with_version_marker)
    (SUM(?has_no_version_marker) AS ?without_version_marker)
WHERE {
    {
        SELECT ?graph ?population ?subject
            (COUNT(DISTINCT ?purl) AS ?purl_count)
            (MAX(?version_marker) AS ?has_version_marker)
            (MAX(?no_version_marker) AS ?has_no_version_marker)
        WHERE {
            """ + graph_values + """
            GRAPH ?graph {
                """ + TYPES + """
                ?subject a ?type .
                OPTIONAL { ?subject pkg:purl ?purl . }
            }
            BIND(COALESCE(REGEX(STR(?purl),
                "^pkg:[^/?#]+/([^?#]*/)?[^/?#@]+@"), false) AS ?marker)
            BIND(IF(BOUND(?purl), IF(?marker, 1, 0), 0) AS ?version_marker)
            BIND(IF(BOUND(?purl), IF(?marker, 0, 1), 0) AS ?no_version_marker)
        }
        GROUP BY ?graph ?population ?subject
    }
}
GROUP BY ?graph ?population
ORDER BY ?graph ?population
"""


def bindings(response, variables):
    """Reject malformed/incomplete SELECT responses instead of inventing zeros."""
    try:
        rows = response["results"]["bindings"]
        actual_variables = response["head"]["vars"]
        total = response.get("meta", {}).get("result-size-total", len(rows))
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("Response is not SPARQL SELECT JSON") from exc
    if (not isinstance(rows, list) or not isinstance(actual_variables, list)
            or not set(variables).issubset(actual_variables) or total != len(rows)):
        raise ValueError("Response has missing variables or truncated results")
    return rows


def decode_counts(response, graph):
    """Decode a successful graph response; absent populations then mean zero."""
    result = {population: dict.fromkeys(METRICS, 0) for population in POPULATIONS}
    seen = set()
    for row in bindings(response, ("graph", "population", *METRICS)):
        try:
            population = row["population"]["value"]
            if (row["graph"]["value"] != graph or population not in POPULATIONS
                    or population in seen):
                raise ValueError("Unexpected graph or duplicate/unknown population")
            counts = {metric: int(row[metric]["value"]) for metric in METRICS}
        except (KeyError, TypeError) as exc:
            raise ValueError("Response has missing count bindings") from exc
        if (any(value < 0 or value > counts["denominator"] for value in counts.values())
                or counts["with_purl"] + counts["missing_purl"] != counts["denominator"]):
            raise ValueError("Response has inconsistent counts")
        seen.add(population)
        result[population] = counts
    return result


def query_endpoint(endpoint, query, timeout):
    """Use a bounded curl request; only SELECT queries generated here are sent."""
    process = subprocess.run(
        ["curl", "--fail-with-body", "--silent", "--show-error", "--max-time", str(timeout),
         "--connect-timeout", str(min(timeout, 10)), "--get", endpoint,
         "--header", "Accept: application/sparql-results+json",
         "--data-urlencode", "query=" + query],
        capture_output=True, text=True, check=False, timeout=timeout + 2,
    )
    if process.returncode:
        raise RuntimeError(f"curl exit {process.returncode}: "
                           f"{process.stderr.strip()} {process.stdout[:500].strip()}")
    return json.loads(process.stdout)


def timestamp():
    return datetime.now(UTC).isoformat()


def measure(endpoint, timeout, graphs=None):
    """Measure graphs sequentially and retain query failures as unknown counts."""
    report = {
        "endpoint": endpoint, "started_at": timestamp(), "timeout_seconds": timeout,
        "query_source": "scripts/measure_purls.py", "inference": "none requested",
        "scope": "selected named graphs" if graphs is not None else "discovered named graphs",
        "population_types": {
            "identity": ["pkg:PackageIdentity"],
            "package": ["pkg:Package", "pkg:BinaryPackage", "pkg:SourcePackage"],
        },
        "complete": True, "graphs": [],
    }
    if graphs is None:
        discovery = {"query": DISCOVERY_QUERY, "started_at": timestamp()}
        report["discovery"] = discovery
        try:
            response = query_endpoint(endpoint, DISCOVERY_QUERY, timeout)
            discovery["response"] = response
            graphs = sorted({row["graph"]["value"] for row in bindings(response, ("graph",))})
            discovery["status"] = "ok"
        except (RuntimeError, ValueError, KeyError, TypeError, OSError,
                subprocess.TimeoutExpired) as exc:
            discovery.update(status="error", error=str(exc))
            report["complete"] = False
            graphs = []
        discovery["finished_at"] = timestamp()
    for graph in dict.fromkeys(graphs):
        entry = {"graph": graph, "started_at": timestamp(), "counts": None}
        report["graphs"].append(entry)
        print(f"Measuring {graph}", file=sys.stderr, flush=True)
        try:
            entry["query"] = count_query(graph)
            response = query_endpoint(endpoint, entry["query"], timeout)
            entry["response"] = response
            entry["counts"] = decode_counts(response, graph)
            entry["status"] = "ok"
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
            entry.update(status="error", error=str(exc))
            report["complete"] = False
            print(f"  Unknown: {exc}", file=sys.stderr, flush=True)
        entry["finished_at"] = timestamp()
    report["finished_at"] = timestamp()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default=ENDPOINT)
    parser.add_argument("--timeout", type=float, default=30, help="Seconds per request (default 30)")
    parser.add_argument("--graph", action="append", help="Named graph IRI; repeat to select several")
    parser.add_argument("--output", type=Path, required=True, help="JSON evidence file")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    report = measure(args.endpoint, args.timeout, args.graph)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}; complete={report['complete']}", file=sys.stderr)
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
