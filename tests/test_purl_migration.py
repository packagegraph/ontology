"""Offline migration must preserve all non-PURL facts and refuse guesses."""
import unittest
import subprocess
import sys
import tempfile
from pathlib import Path

from rdflib import Literal
from rdflib.namespace import XSD

from test_purl_contract import EX, PKG, fixture
from packagegraph.purl_migration import migrate_graph
from packagegraph.purls import validate_graph


def legacy():
    graph = fixture()
    graph.remove((None, PKG.purl, None))
    for value in ("pkg:rpm/almalinux/acl@2.3.2-4.el10?arch=aarch64",
                  "pkg:rpm/almalinux/acl@2.4.0-1.el10_2?arch=aarch64"):
        graph.add((EX.identity, PKG.purl, Literal(value, datatype=XSD.anyURI)))
    return graph


class MigrationTests(unittest.TestCase):
    def test_cli_preserves_snapshot_timestamp_lexical_form(self):
        with tempfile.TemporaryDirectory() as directory:
            before, after = Path(directory) / "before.nt", Path(directory) / "after.nt"
            graph = legacy()
            graph.add((EX.snapshot, PKG.snapshotTimestamp, Literal("2026-09-15T04:04:21Z", datatype=XSD.dateTime, normalize=False)))
            graph.serialize(before, format="nt")
            result = subprocess.run([sys.executable, "-m", "packagegraph.purl_migration", str(before), str(after)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('"2026-09-15T04:04:21Z"', after.read_text())

    def test_two_version_regeneration_preserves_every_other_fact(self):
        before = legacy()
        original = set(before)
        after = migrate_graph(before)
        self.assertEqual(set(before), original)
        self.assertEqual(set(after), set(fixture()))
        self.assertEqual({t for t in before if t[1] != PKG.purl},
                         {t for t in after if t[1] != PKG.purl})
        self.assertEqual(validate_graph(after, "rpm"), [])
        self.assertEqual(set(migrate_graph(after)), set(after))

    def test_unmatched_version_is_refused_without_mutation(self):
        graph = legacy()
        graph.set((EX.v2, PKG.versionString, Literal("unknown")))
        original = set(graph)
        with self.assertRaisesRegex(ValueError, "matching package"):
            migrate_graph(graph)
        self.assertEqual(set(graph), original)

    def test_conflicting_identity_coordinates_are_refused(self):
        graph = legacy()
        graph.add((EX.identity, PKG.purl, Literal("pkg:rpm/almalinux/other@2.3.2-4.el10?arch=aarch64", datatype=XSD.anyURI)))
        with self.assertRaisesRegex(ValueError, "identity coordinates"):
            migrate_graph(graph)

    def test_rpm_epoch_moves_to_qualifier_without_changing_version_facts(self):
        graph = legacy()
        graph.remove((EX.identity, PKG.purl, None))
        graph.add((EX.identity, PKG.purl, Literal("pkg:rpm/almalinux/acl@1%3A2.3.2-4.el10?arch=aarch64", datatype=XSD.anyURI)))
        graph.add((EX.identity, PKG.purl, Literal("pkg:rpm/almalinux/acl@2.4.0-1.el10_2?arch=aarch64", datatype=XSD.anyURI)))
        graph.set((EX.v1, PKG.versionString, Literal("1:2.3.2-4.el10")))
        after = migrate_graph(graph)
        self.assertIn((EX.old, PKG.purl, Literal("pkg:rpm/almalinux/acl@2.3.2-4.el10?arch=aarch64&epoch=1", datatype=XSD.anyURI)), after)
        self.assertIn((EX.v1, PKG.versionString, Literal("1:2.3.2-4.el10")), after)
        self.assertEqual(validate_graph(after, "rpm"), [])

    def test_collector_rpm_version_string_uses_recorded_release_arch_and_epoch(self):
        graph = legacy()
        graph.remove((EX.identity, PKG.purl, None))
        graph.add((EX.identity, PKG.purl, Literal("pkg:rpm/almalinux/acl@1%3A2.3.2-4.el10?arch=aarch64", datatype=XSD.anyURI)))
        graph.add((EX.identity, PKG.purl, Literal("pkg:rpm/almalinux/acl@2.4.0-1.el10_2?arch=aarch64", datatype=XSD.anyURI)))
        graph.set((EX.v1, PKG.versionString, Literal("2.3.2-4.el10.aarch64")))
        graph.add((EX.v1, PKG.release, Literal("4.el10")))
        graph.add((EX.v1, PKG.epoch, Literal("1")))
        graph.set((EX.v2, PKG.versionString, Literal("2.4.0-1.el10_2.aarch64")))
        graph.add((EX.v2, PKG.release, Literal("1.el10_2")))
        after = migrate_graph(graph)
        self.assertIn((EX.old, PKG.purl, Literal("pkg:rpm/almalinux/acl@2.3.2-4.el10?arch=aarch64&epoch=1", datatype=XSD.anyURI)), after)
        self.assertEqual({t for t in graph if t[1] != PKG.purl},
                         {t for t in after if t[1] != PKG.purl})

    def test_existing_package_purl_conflict_is_refused(self):
        graph = legacy()
        graph.add((EX.old, PKG.purl, Literal("pkg:rpm/almalinux/other@1", datatype=XSD.anyURI)))
        with self.assertRaises(ValueError):
            migrate_graph(graph)

    def test_ambiguous_or_lossy_legacy_syntax_is_refused(self):
        for value in (
            "pkg:rpm/almalinux/acl@2.3.2-4.el10?arch=x86_64&arch=aarch64",
            "pkg:rpm/almalinux/acl@2.3.2-4.el10?arch=aarch64&epoch=1&epoch=2",
            "pkg:rpm/almalinux/acl%FF@2.3.2-4.el10?arch=aarch64",
            "pkg:rpm/almalinux/acl@2.3.2-4.el10?arch=aarch64#../src",
        ):
            graph = legacy()
            graph.set((EX.identity, PKG.purl, Literal(value, datatype=XSD.anyURI)))
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "legacy syntax"):
                migrate_graph(graph)


if __name__ == "__main__":
    unittest.main()
