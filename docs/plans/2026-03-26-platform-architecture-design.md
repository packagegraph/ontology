# PackageGraph Platform Architecture Design

## Context

The PackageGraph project provides OWL 2 ontologies for representing software packages across major package management systems (Debian, RPM, Arch, BSD, Chocolatey, Homebrew, Nix). The ontology repo exists at `packagegraph/ontology` on GitHub. A working ETL pipeline and graph database deployment are needed to make this ontology operational.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Graph database | Apache Jena Fuseki | RDF-native; ontologies are OWL 2/Turtle; SPARQL endpoint out of the box |
| Repository structure | Two repos (`ontology` + `platform`) | Ontology is a publishable artifact; ETL + deploy are operationally coupled |
| Persistence | S3/Minio-backed (stateless Fuseki) | Leverages existing Minio; no PVC management; pods are disposable |
| Data loading | Pre-built TDB2 snapshots | 1GB+ datasets make parse-on-start too slow; TDB2 indexes enable instant startup |
| ETL operations | Manual Jobs (dev) + CronJob (prod) | Kustomize overlays; iterate in dev, automate in prod |
| Container format | Containerfile | Project convention |

## Repository Layout

### `packagegraph/ontology` (existing)

OWL 2 ontology files, SHACL shapes, examples, validation tooling. No changes to structure.

### `packagegraph/platform` (new)

```
platform/
├── etl/
│   ├── packagegraph/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── collector.py
│   │   ├── debian_collector.py
│   │   ├── rpm_collector.py
│   │   └── profiler.py
│   ├── Containerfile
│   ├── pyproject.toml
│   └── uv.lock
├── fuseki/
│   ├── Containerfile
│   ├── config.ttl
│   └── entrypoint.sh
├── deploy/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   ├── fuseki/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── route.yaml
│   │   ├── etl/
│   │   │   └── job.yaml
│   │   └── minio/
│   │       └── secret.yaml
│   ├── overlays/
│   │   ├── dev/
│   │   │   ├── kustomization.yaml
│   │   │   └── patches/
│   │   └── prod/
│   │       ├── kustomization.yaml
│   │       ├── cronjob.yaml
│   │       └── patches/
├── Makefile
└── README.md
```

## Data Flow

```
Package Repos ──> ETL Job ──> Minio ──> Fuseki Init Container ──> Fuseki (SPARQL)
(Debian, RPM)     │                      (tdb2/latest/)           (emptyDir volume)
                  │
ontology/ TTLs ───┘
```

### ETL Job steps

1. Collect package metadata from upstream repos
2. Serialize as N-Triples using rdflib + ontology terms
3. Run `tdb2.tdbloader` to build TDB2 database (includes ontology TTLs)
4. Tar TDB2 directory, upload to Minio (`s3://packagegraph/tdb2/latest/`)

### Fuseki startup

1. Init container uses `mc` to pull `tdb2/latest/tdb2.tar.gz` from Minio
2. Extracts TDB2 into emptyDir volume shared with Fuseki container
3. Fuseki starts with pre-built indexes, serves SPARQL endpoint immediately

## Container Images

| Image | Base | Contents |
|-------|------|----------|
| `etl` | `python:3.12-slim` + Jena CLI tools | Collectors, ontology TTLs, `tdb2.tdbloader`, `mc` (Minio client) |
| `fuseki` | `stain/jena-fuseki:4` | + `mc` for init container, Fuseki dataset config |

## OpenShift Resources

### Base

| Resource | Kind | Purpose |
|----------|------|---------|
| `namespace.yaml` | Namespace | `packagegraph` |
| `fuseki/deployment.yaml` | Deployment | Fuseki + init container + emptyDir |
| `fuseki/service.yaml` | Service | ClusterIP :3030 |
| `fuseki/route.yaml` | Route | External SPARQL endpoint |
| `etl/job.yaml` | Job | ETL run template |
| `minio/secret.yaml` | Secret | Minio credentials (placeholder) |

### Dev overlay

- Reduced resource limits (512Mi/1cpu Fuseki, 1Gi/2cpu ETL)
- ETL targets single distro/component
- 1 Fuseki replica, no TLS

### Prod overlay

- CronJob wrapping ETL Job (weekly schedule)
- Higher resource limits (4Gi/4cpu ETL, 2Gi/2cpu Fuseki)
- ETL collects all configured distros
- Liveness/readiness probes

## Resource Estimates

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| Fuseki (serving) | 1-2 cores | 2-4Gi | emptyDir ~50-100Gi (TDB2 snapshot) |
| ETL Job (transient) | 2-4 cores | 2-4Gi | ephemeral ~150Gi during build |
| Minio | existing | existing | ~50-100Gi bucket |

## Ontology Integration

The ETL container image clones or copies `packagegraph/ontology` TTL files at build time. These are loaded into TDB2 alongside collected package data, so the SPARQL endpoint serves both schema and instance data.

## Status

- Approved: Yes
