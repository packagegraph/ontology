"""Test that PURL redirects for all ontology namespaces are live.

Run with: uv run pytest tests/test_purl_redirects.py -v

These tests verify that the PURL redirects registered at purl.org/packagegraph
resolve correctly. If a test fails, the corresponding PURL redirect needs to be
created or updated at https://purl.org/admin/domain/packagegraph.
"""

import re
from pathlib import Path
import pytest
import requests

# All ontology modules and their expected PURL paths
ONTOLOGY_MODULES = [
    ("core", "core.ttl"),
    ("vcs", "vcs.ttl"),
    ("security", "security.ttl"),
    ("debian", "debian.ttl"),
    ("rpm", "rpm.ttl"),
    ("archlinux", "arch.ttl"),
    ("bsd", "bsd.ttl"),
    ("chocolatey", "chocolatey.ttl"),
    ("homebrew", "homebrew.ttl"),
    ("nix", "nix.ttl"),
    ("redhat", "redhat.ttl"),
    ("metrics", "metrics.ttl"),
    ("slsa", "slsa.ttl"),
    ("shacl", "shacl.ttl"),
]

PURL_BASE = "https://purl.org/packagegraph/ontology"
GITHUB_PAGES_BASE = "https://packagegraph.github.io/ontology/downloads"


@pytest.mark.integration
class TestPurlRedirects:
    """Verify PURL redirects resolve to the correct GitHub Pages URLs."""

    @pytest.mark.parametrize("module,ttl_file", ONTOLOGY_MODULES)
    def test_purl_redirect_resolves(self, module, ttl_file):
        """Each ontology module's PURL should redirect to its TTL file."""
        purl_url = f"{PURL_BASE}/{module}"
        response = requests.head(purl_url, allow_redirects=False, timeout=10)

        assert response.status_code in (301, 302), (
            f"PURL {purl_url} returned {response.status_code}, expected 301/302. "
            f"Register this redirect at https://purl.org/admin/domain/packagegraph"
        )

        location = response.headers.get("Location", "")
        assert ttl_file in location, (
            f"PURL {purl_url} redirects to {location}, "
            f"expected target to contain '{ttl_file}'"
        )

    def test_purl_domain_resolves(self):
        """The base PURL domain should redirect."""
        response = requests.head(
            "https://purl.org/packagegraph",
            allow_redirects=False,
            timeout=10,
        )
        assert response.status_code in (301, 302), (
            "Base PURL /packagegraph not registered"
        )


@pytest.mark.unit
class TestNamespacesUsePurl:
    """Verify all TTL files use purl.org namespaces, not packagegraph.github.io."""

    @pytest.mark.parametrize("module,ttl_file", ONTOLOGY_MODULES)
    def test_ttl_uses_purl_namespace(self, module, ttl_file):
        """Each TTL file's ontology declaration should use purl.org namespace."""
        ttl_path = Path(__file__).parent.parent / ttl_file
        if not ttl_path.exists():
            pytest.skip(f"{ttl_file} not found")

        content = ttl_path.read_text()

        # Check that the ontology declaration uses purl.org
        assert "purl.org/packagegraph/ontology/" in content, (
            f"{ttl_file} still uses old namespace — "
            f"should use https://purl.org/packagegraph/ontology/"
        )

        # Check that no github.io ontology namespace remains
        github_matches = re.findall(
            r"packagegraph\.github\.io/ontology/", content
        )
        assert len(github_matches) == 0, (
            f"{ttl_file} still has {len(github_matches)} references to "
            f"packagegraph.github.io/ontology/ — migrate to purl.org"
        )
