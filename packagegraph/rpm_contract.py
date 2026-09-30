"""Reference URI recipes for the bounded RPM primary.xml declaration profile.

These functions consume already XML-decoded values. They neither parse RPM
expressions nor resolve providers. The platform must independently compare its
output and source occurrences before publication.
"""
import hashlib
import json
import re
from urllib.parse import quote

DATA_BASE = "https://packagegraph.github.io/d/"
DATA_BASES = (DATA_BASE, "https://purl.org/packagegraph/d/")


def _base(data_base: str) -> str:
    if data_base not in DATA_BASES:
        raise ValueError("data_base must be a documented PackageGraph data base")
    return data_base


def capability_uri(token: str, *, data_base: str = DATA_BASE) -> str:
    """Identify an exact, nonempty simple token in the RPM naming system."""
    if not isinstance(token, str) or not token or token.startswith("("):
        raise ValueError("expected a nonempty simple RPM capability token")
    return _base(data_base) + "capability/rpm/" + quote(token, safe="")


def declaration_uri(package_iri: str, source_sha256: str, package_ordinal: int,
                    section_kind: str, entry_ordinal: int, *,
                    data_base: str = DATA_BASE) -> str:
    """Identify an occurrence, using the SHA-256 of the uncompressed XML bytes.

The positional key preserves exact duplicate entries. It is stable on rereading
the same source/context and recompression, not across changed XML snapshots.
"""
    if (not isinstance(package_iri, str)
            or not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", package_iri)
            or any(ord(char) <= 32 or char in '<>"{}|\\^`' for char in package_iri)):
        raise ValueError("package_iri must be an absolute IRI without forbidden characters")
    if not isinstance(source_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
        raise ValueError("source_sha256 must be 64 lowercase hexadecimal characters")
    for ordinal in (package_ordinal, entry_ordinal):
        if type(ordinal) is not int or not 0 <= ordinal < 2**64:
            raise ValueError("ordinals must be unsigned 64-bit integers, not booleans")
    if section_kind not in ("provides", "requires", "conflicts", "obsoletes"):
        raise ValueError("unsupported primary.xml section kind")
    key = [1, package_iri, source_sha256, package_ordinal, section_kind, entry_ordinal]
    encoded = json.dumps(key, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return _base(data_base) + "rpm-declaration/" + hashlib.sha256(encoded).hexdigest()
