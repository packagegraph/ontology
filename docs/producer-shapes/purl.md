# PURL placement and collection profiles

`pkg:purl` has the single domain `pkg:PackageEntity`. Identities carry at most
one canonical **versionless** PURL; concrete packages carry at most one canonical
**versioned** PURL. Asserting this property alone must not infer either subtype.
The [PURL specification](https://github.com/package-url/purl-spec) permits an
absent version. A matching name or PURL does not create an OWL identity axiom.

There are three independent validation layers:

1. `core/core.shacl.ttl` checks literal datatype, cardinality, basic structure,
   and placement of the version delimiter. Its pattern is deliberately not a
   complete syntax validator.
2. `python -m packagegraph.purls FILE...` checks canonical serialization with
   `packageurl-python==0.17.6`, known ecosystem conventions, entity roles and
   agreement between linked package and identity PURLs. RPM epoch is a package
   qualifier and is excluded from the versionless identity PURL. Qualifiers such
   as architecture remain on both. The parser rejects malformed encoding,
   duplicate/unsorted qualifiers and noncanonical ecosystem names. Unknown PURL
   types receive general syntax checks, without claiming ecosystem validation.
3. `--profile rpm`, `--profile deb`, or `--profile maven` additionally requires
   one PURL of the matching type on the following graph-local entities:

| Profile | Collected class | Additional required subjects |
| --- | --- | --- |
| `rpm` | `rpm:BinaryRPM`, `rpm:SourceRPM`, `pkg:SourcePackage` | binary `isVersionOf` identities and `builtFromSource` sources |
| `deb` | `deb:BinaryPackage`, `pkg:SourcePackage` | binary `isVersionOf` identities and `builtFromSource` sources |
| `maven` | `maven:MavenArtifact` | its `isVersionOf` identities and resolved `directlyDependsOn` identities |

Run profiles on complete collector graph exports, never a union of unrelated
graphs or a truncated sample. RPM/Debian capability and virtual dependency
targets are excluded. Other collectors are not declared PURL-complete. Do not
invent PURLs from incomplete identities merely to satisfy a coverage gate.
The global identity shape therefore has no PURL `minCount` requirement.

## Coordinated rollout and regeneration

The ontology change and companion platform collector change must ship together.
Pin the platform ontology input to the ontology commit containing this contract;
the old domain would infer every newly annotated package to be an identity.
RPM, Debian and Maven collectors must regenerate their graph artifacts. Cache
entries containing emitted RDF and retained checkpoint generations require
regeneration; replaying old RDF is not migration. Preserve raw source caches and
previous graph artifacts for audit/rollback. Preserve original snapshot metadata,
and let a new collection record its own `DataSnapshot` through the normal uploader.

For an existing **single named graph** export, a conservative offline migration
is also available:

```bash
python -m packagegraph.purl_migration graph-before.nt graph-after.nt
python -m packagegraph.purls --profile rpm graph-after.nt
```

The output path must be new. This command does not contact production. It moves
versioned identity PURLs only when the graph's linked packages and recorded
`versionString` values supply an exact match, derives package PURLs from a known
identity mapping plus recorded version, and normalizes legacy RPM epochs. It
refuses unmatched versions, conflicting identity coordinates and conflicting
package identifiers. It changes only PURL statements; every other triple,
including snapshot provenance, package IRIs and version facts, is retained.
Missing identity mappings stay missing and can still fail a supported profile.
Missing source mappings require recollection. Large graphs should be recollected
through the streaming collectors; this offline utility loads one export in memory.

`tests/fixtures/purls/two-versions.ttl` and its legacy/regenerated N-Triples
counterparts demonstrate lossless migration of two versions. The companion
platform fixtures regenerate complete RPM, Debian and Maven collector outputs.

Before production replacement, retain each original artifact and graph URI,
validate the regenerated artifact with its profile, run SHACL and forbidden-type
inference checks, and compare all non-PURL facts for offline migrations. Publish
through the existing graph replacement/index pipeline; appending regenerated RDF
would leave the old identity PURLs in place. A production rollout also needs the
platform's coordinated collector release procedure and host maintenance window.
Re-run `scripts/measure_purls.py` after the new index is serving, retaining the
before/after reports. Acceptance requires zero misplaced/multiple PURLs in each
supported graph and profile completeness, not merely a better global percentage.

The pre-change shapes can accept one versioned PURL, so they are not formally
unsatisfiable. Their requirements are inconsistent with the intended identity
semantics when versions accumulate. Missing identifiers are a separate coverage
problem; changing the domain or pattern does not populate them. See the
[fresh graph-scoped baseline](../reports/2026-09-23-purl-baseline.md).
