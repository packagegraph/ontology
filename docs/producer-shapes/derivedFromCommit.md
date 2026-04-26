# Producer Shape: pkg:derivedFromCommit

**Date:** 2026-04-26
**Consumer CQ:** VCS-02 (Commit-to-Release Tracing)
**Status:** No producer exists — shape defined for specfile collector targeting

---

## Purpose

Link a distribution package to the specific VCS commit it was built from. This is the key provenance join that enables commit-to-release tracing (VCS-02).

## Expected Triple Patterns

The producer should emit at minimum:

```turtle
# 1. The derivedFromCommit link (REQUIRED)
<d/pkg/fedora/43/x86_64/openssl> pkg:derivedFromCommit <d/commit/abc123def456> .

# 2. The commit entity with hash (REQUIRED)
<d/commit/abc123def456> a vcs:Commit ;
    vcs:commitHash "abc123def456789012345678901234567890abcd" ;
    vcs:commitTimestamp "2026-04-01T12:00:00Z"^^xsd:dateTime .

# 3. The commit's repository link (REQUIRED for VCS-02 join)
<d/repo/github.com/openssl/openssl> vcs:hasCommit <d/commit/abc123def456> .
```

## Minimal Join Path for VCS-02

```
Package → derivedFromCommit → Commit → commitHash
```

## Full Join Path (with branch, if available)

```
Package → derivedFromCommit → Commit ← hasCommit ← Repository
                                ↑
                          (branch linkage —
                           requires vcs:onBranch or similar,
                           not yet defined in vcs.ttl)
```

## URI Patterns

| Entity | Pattern | Example |
|--------|---------|---------|
| Commit | `d/commit/{short-hash}` | `d/commit/abc123def456` |
| Repository | `d/repo/{forge}/{owner}/{name}` | `d/repo/github.com/openssl/openssl` |

## Source of Truth

For RPM packages: the `%commit` or `%git_commit` macro in the spec file, or the `Source0` tarball URL containing a commit hash.

For Debian packages: `debian/changelog` entries referencing upstream tags/commits, or `debian/watch` file patterns.

## Missing Ontology Vocabulary

VCS-02's frozen query uses `vcs:onBranch` which is **not defined in vcs.ttl**. If branch-level tracing is needed, the ontology team needs to add:

```
vcs:onBranch a owl:ObjectProperty ;
    rdfs:domain vcs:Commit ;
    rdfs:range vcs:Branch .
```

Without this, VCS-02 can only trace to commit level, not branch level. The simpler version of VCS-02 (commit tracing without branch filter) is achievable with just `derivedFromCommit`.

## Validation Probe

```sparql
ASK {
  ?package a pkg:Package ;
           pkg:derivedFromCommit ?commit .
  ?commit a vcs:Commit ;
          vcs:commitHash ?hash .
}
```
