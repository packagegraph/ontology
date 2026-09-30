"""Cross-language URI recipe vectors, independent of collector implementation."""
import importlib.util
import unittest


class RpmUriTests(unittest.TestCase):
    def api(self):
        # An explicit missing-contract assertion, not an unrelated import error.
        self.assertIsNotNone(importlib.util.find_spec("packagegraph.rpm_contract"))
        from packagegraph import rpm_contract
        return rpm_contract

    def test_capability_percent_encoding_is_reversible_and_case_sensitive(self):
        api = self.api()
        for token, suffix in (
            ("libssl.so.3()(64bit)", "libssl.so.3%28%29%2864bit%29"),
            ("/bin/sh", "%2Fbin%2Fsh"), ("foo%2Fbar", "foo%252Fbar"),
            ("café", "caf%C3%A9"), ("a > b", "a%20%3E%20b"),
            (" foo ", "%20foo%20"), ("Foo", "Foo"),
        ):
            with self.subTest(token=token):
                self.assertEqual(api.capability_uri(token),
                                 "https://packagegraph.github.io/d/capability/rpm/" + suffix)
        self.assertNotEqual(api.capability_uri("é"), api.capability_uri("e\u0301"))

    def test_occurrence_vectors(self):
        api = self.api()
        vectors = (
            ("https://example.org/package/1", "requires", 0,
             "c8cc209329892ecabebe17fb3985a0d92de4ca52c73dbc64782355d7a0a48ea7"),
            ("https://example.org/package/1", "requires", 1,
             "52d63a2446c3c26bf54851157eff30499181c0f3eb3f9bdd0cea148b0a9c4394"),
            ("https://example.org/é", "provides", 0,
             "91a3e57f528d571bea4e4c7e4991ca23e3809cdcf6e6cb8da35ba80ec8d645e3"),
        )
        for package, kind, ordinal, digest in vectors:
            with self.subTest(package=package, kind=kind, ordinal=ordinal):
                self.assertEqual(api.declaration_uri(package, "a" * 64, 0, kind, ordinal),
                                 "https://packagegraph.github.io/d/rpm-declaration/" + digest)

    def test_changed_context_changes_identity_and_rerun_is_stable(self):
        api = self.api()
        original = ("https://example.org/package/1", "a" * 64, 0, "requires", 0)
        result = api.declaration_uri(*original)
        self.assertEqual(result, api.declaration_uri(*original))
        for position, replacement in enumerate(("https://example.org/package/2", "b" * 64, 1, "provides", 1)):
            changed = list(original)
            changed[position] = replacement
            self.assertNotEqual(result, api.declaration_uri(*changed))

    def test_invalid_identifiers_are_rejected_not_normalized(self):
        api = self.api()
        original = ["https://example.org/package/1", "a" * 64, 0, "requires", 0]
        for position, replacement in ((0, "relative/path"), (0, "https://example.org/a b"),
                                      (1, "A" * 64), (1, "bad"), (2, -1),
                                      (2, True), (2, 0.5), (3, "Requires"),
                                      (3, "recommends"), (4, -1), (4, 2**64)):
            with self.subTest(position=position, replacement=replacement):
                changed = original.copy()
                changed[position] = replacement
                with self.assertRaises(ValueError):
                    api.declaration_uri(*changed)
        for token in ("", "(foo or bar)"):
            with self.assertRaises(ValueError):
                api.capability_uri(token)
        with self.assertRaises(ValueError):
            api.capability_uri("foo", data_base="https://example.org/")


if __name__ == "__main__":
    unittest.main()
