# PackageGraph Platform Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create the `packagegraph/platform` repository with ETL pipeline, Fuseki deployment, and OpenShift Kustomize manifests using content-addressable Minio storage.

**Architecture:** Python ETL collects package metadata, serializes N-Triples, builds TDB2 indexes via `tdb2.tdbloader`, and uploads content-addressed snapshots to Minio. Fuseki pods pull pre-built TDB2 snapshots on startup via init container. Kustomize overlays provide dev (manual Job) and prod (CronJob) configurations.

**Tech Stack:** Python 3.12, rdflib, Click, Apache Jena CLI tools, Minio (mc client), OpenShift/Kustomize, Podman/Containerfile

**Design doc:** `docs/plans/2026-03-26-platform-architecture-design.md`

---

## Task 1: Scaffold platform repository

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Create: `Makefile`

**Step 1: Initialize git repo and create .gitignore**

```bash
mkdir -p /Users/bharrington/Projects/packagegraph/platform
cd /Users/bharrington/Projects/packagegraph/platform
git init
```

Create `.gitignore`:
```
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
build/
.ruff_cache/
*.ttl.zst
*.tar.gz
output/
dead_letters/
```

**Step 2: Create top-level README**

Create `README.md` with project overview referencing the design doc. Describe the two-repo relationship (`ontology` for schemas, `platform` for ETL + deploy).

**Step 3: Create top-level Makefile**

```makefile
.PHONY: build-etl build-fuseki push-etl push-fuseki deploy-dev deploy-prod

REGISTRY ?= quay.io/packagegraph
ETL_IMAGE = $(REGISTRY)/etl
FUSEKI_IMAGE = $(REGISTRY)/fuseki
TAG ?= latest

build-etl:
	podman build -t $(ETL_IMAGE):$(TAG) -f etl/Containerfile etl/

build-fuseki:
	podman build -t $(FUSEKI_IMAGE):$(TAG) -f fuseki/Containerfile fuseki/

build: build-etl build-fuseki

push-etl:
	podman push $(ETL_IMAGE):$(TAG)

push-fuseki:
	podman push $(FUSEKI_IMAGE):$(TAG)

push: push-etl push-fuseki

deploy-dev:
	oc apply -k deploy/overlays/dev

deploy-prod:
	oc apply -k deploy/overlays/prod
```

**Step 4: Commit**

```bash
git add .gitignore README.md Makefile
git commit -m "chore: scaffold platform repository"
```

---

## Task 2: Migrate ETL Python package

**Files:**
- Create: `etl/pyproject.toml`
- Create: `etl/packagegraph/__init__.py`
- Create: `etl/packagegraph/cli.py`
- Create: `etl/packagegraph/collector.py`
- Create: `etl/packagegraph/debian_collector.py`
- Create: `etl/packagegraph/rpm_collector.py`
- Create: `etl/packagegraph/profiler.py`

Source: `/Users/bharrington/Projects/packagegraph/ontology/packagegraph/` and `/Users/bharrington/Projects/packagegraph/ontology/main.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "packagegraph-etl"
version = "0.1.0"
description = "ETL pipeline for PackageGraph - collects package metadata and builds RDF knowledge graphs"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "click>=8.2",
    "rdflib>=7.1",
    "requests>=2.32",
    "zstandard>=0.23",
]

[project.scripts]
packagegraph = "packagegraph.cli:cli"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.12",
]

[tool.ruff]
target-version = "py312"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 2: Copy and adapt Python modules**

Copy from `ontology/packagegraph/`:
- `collector.py` → `etl/packagegraph/collector.py` (no changes)
- `debian_collector.py` → `etl/packagegraph/debian_collector.py` (no changes)
- `rpm_collector.py` → `etl/packagegraph/rpm_collector.py` (no changes)
- `profiler.py` → `etl/packagegraph/profiler.py` (no changes)
- `__init__.py` → `etl/packagegraph/__init__.py` (no changes)

Copy `ontology/main.py` → `etl/packagegraph/cli.py` with these changes:
- Remove the `convert` command (will be replaced by TDB2 build + Minio upload in Task 3)
- Remove `rdf2g`/`tqdm` imports (not used)
- Remove `checker` import and `check` command (belongs to ontology repo)

**Step 3: Initialize venv and verify**

```bash
cd /Users/bharrington/Projects/packagegraph/platform/etl
uv sync
uv run packagegraph --help
```

Expected: CLI shows `collect` command with options.

**Step 4: Commit**

```bash
cd /Users/bharrington/Projects/packagegraph/platform
git add etl/
git commit -m "feat(etl): migrate Python ETL package from ontology repo"
```

---

## Task 3: Add Minio upload and TDB2 build to ETL CLI

**Files:**
- Create: `etl/packagegraph/minio.py`
- Create: `etl/packagegraph/tdb.py`
- Modify: `etl/packagegraph/cli.py`
- Create: `etl/tests/__init__.py`
- Create: `etl/tests/test_minio.py`
- Create: `etl/tests/test_tdb.py`

**Step 1: Write failing test for content-addressable Minio upload**

Create `etl/tests/test_minio.py`:

```python
import hashlib
from unittest.mock import patch, MagicMock
from packagegraph.minio import MinioStore


def test_upload_snapshot_uses_content_hash():
    """Snapshot is stored at hash-based path, latest pointer is updated."""
    store = MinioStore(
        endpoint="minio.example.com",
        bucket="packagegraph",
        access_key="test",
        secret_key="test",
    )
    with patch("packagegraph.minio.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = store.upload_snapshot("/tmp/tdb2.tar.gz")

    # Should have called mc cp with hash-based path
    calls = [str(c) for c in mock_run.call_args_list]
    assert any("tdb2/sha256-" in str(c) for c in mock_run.call_args_list)
    # Should have updated latest pointer
    assert any("tdb2/latest" in str(c) for c in mock_run.call_args_list)
    assert result.startswith("sha256-")


def test_upload_snapshot_skips_if_hash_exists():
    """If snapshot with same hash already exists, skip upload."""
    store = MinioStore(
        endpoint="minio.example.com",
        bucket="packagegraph",
        access_key="test",
        secret_key="test",
    )
    with patch("packagegraph.minio.subprocess.run") as mock_run:
        # First call (mc stat) succeeds = object exists
        mock_run.return_value = MagicMock(returncode=0)
        result = store.upload_snapshot("/tmp/tdb2.tar.gz")

    assert result.startswith("sha256-")
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/bharrington/Projects/packagegraph/platform/etl
uv run pytest tests/test_minio.py -q
```

Expected: FAIL - `ModuleNotFoundError: No module named 'packagegraph.minio'`

**Step 3: Implement MinioStore**

Create `etl/packagegraph/minio.py`:

```python
import hashlib
import subprocess
from pathlib import Path


class MinioStore:
    def __init__(self, endpoint: str, bucket: str, access_key: str, secret_key: str):
        self.endpoint = endpoint
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.alias = "pgraph"

    def _mc(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["mc", *args],
            capture_output=True,
            text=True,
            env={
                "MC_HOST_" + self.alias: f"https://{self.access_key}:{self.secret_key}@{self.endpoint}",
            },
        )

    def _hash_file(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return f"sha256-{h.hexdigest()}"

    def _object_exists(self, remote_path: str) -> bool:
        result = self._mc("stat", f"{self.alias}/{self.bucket}/{remote_path}")
        return result.returncode == 0

    def upload_snapshot(self, tar_path: str) -> str:
        content_hash = self._hash_file(tar_path)
        remote_path = f"tdb2/{content_hash}/tdb2.tar.gz"

        if not self._object_exists(remote_path):
            result = self._mc("cp", tar_path, f"{self.alias}/{self.bucket}/{remote_path}")
            if result.returncode != 0:
                raise RuntimeError(f"mc cp failed: {result.stderr}")

        # Update latest pointer (small file containing the hash)
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content_hash)
            pointer_path = f.name
        self._mc("cp", pointer_path, f"{self.alias}/{self.bucket}/tdb2/latest")
        Path(pointer_path).unlink()

        return content_hash

    def download_latest(self, dest_dir: str) -> str:
        # Read latest pointer
        result = self._mc("cat", f"{self.alias}/{self.bucket}/tdb2/latest")
        if result.returncode != 0:
            raise RuntimeError(f"No latest snapshot found: {result.stderr}")
        content_hash = result.stdout.strip()

        # Download snapshot
        remote_path = f"tdb2/{content_hash}/tdb2.tar.gz"
        local_path = f"{dest_dir}/tdb2.tar.gz"
        result = self._mc("cp", f"{self.alias}/{self.bucket}/{remote_path}", local_path)
        if result.returncode != 0:
            raise RuntimeError(f"mc cp failed: {result.stderr}")
        return local_path
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_minio.py -q
```

Expected: PASS

**Step 5: Write failing test for TDB2 builder**

Create `etl/tests/test_tdb.py`:

```python
from unittest.mock import patch, MagicMock
from packagegraph.tdb import TDB2Builder


def test_build_creates_tdb2_from_ntriples():
    """tdb2.tdbloader is called with correct arguments."""
    builder = TDB2Builder(jena_home="/opt/jena")
    with patch("packagegraph.tdb.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        builder.build(
            input_files=["/data/packages.nt", "/data/ontology.nt"],
            output_dir="/tmp/tdb2",
        )
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "tdb2.tdbloader" in cmd[0]
    assert "--loc=/tmp/tdb2" in cmd
    assert "/data/packages.nt" in cmd
    assert "/data/ontology.nt" in cmd


def test_build_raises_on_failure():
    """Raises RuntimeError if tdb2.tdbloader exits non-zero."""
    builder = TDB2Builder(jena_home="/opt/jena")
    with patch("packagegraph.tdb.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        try:
            builder.build(input_files=["/data/test.nt"], output_dir="/tmp/tdb2")
            assert False, "Should have raised"
        except RuntimeError:
            pass
```

**Step 6: Run test to verify it fails**

```bash
uv run pytest tests/test_tdb.py -q
```

Expected: FAIL - `ModuleNotFoundError: No module named 'packagegraph.tdb'`

**Step 7: Implement TDB2Builder**

Create `etl/packagegraph/tdb.py`:

```python
import subprocess
import tarfile
from pathlib import Path


class TDB2Builder:
    def __init__(self, jena_home: str = "/opt/jena"):
        self.tdbloader = f"{jena_home}/bin/tdb2.tdbloader"

    def build(self, input_files: list[str], output_dir: str) -> None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        cmd = [self.tdbloader, f"--loc={output_dir}", *input_files]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"tdb2.tdbloader failed: {result.stderr}")

    def package(self, tdb_dir: str, output_path: str) -> str:
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(tdb_dir, arcname="tdb2")
        return output_path
```

**Step 8: Run test to verify it passes**

```bash
uv run pytest tests/test_tdb.py -q
```

Expected: PASS

**Step 9: Add `build` command to CLI**

Modify `etl/packagegraph/cli.py` — add a `build` command that:
1. Collects N-Triples from a directory of TTL files (ontology + collected data)
2. Runs TDB2Builder to create indexes
3. Packages as tar.gz
4. Uploads to Minio via MinioStore

```python
@cli.command()
@click.option("--input-dir", "-i", default=".", help="Directory containing TTL/NT files.")
@click.option("--ontology-dir", help="Directory containing ontology TTL files.")
@click.option("--output-dir", "-o", default="/tmp/tdb2", help="TDB2 output directory.")
@click.option("--minio-endpoint", envvar="MINIO_ENDPOINT", help="Minio endpoint.")
@click.option("--minio-bucket", envvar="MINIO_BUCKET", default="packagegraph", help="Minio bucket.")
@click.option("--minio-access-key", envvar="MINIO_ACCESS_KEY", help="Minio access key.")
@click.option("--minio-secret-key", envvar="MINIO_SECRET_KEY", help="Minio secret key.")
@click.option("--jena-home", envvar="JENA_HOME", default="/opt/jena", help="Jena installation path.")
def build(input_dir, ontology_dir, output_dir, minio_endpoint, minio_bucket,
          minio_access_key, minio_secret_key, jena_home):
    """Build TDB2 index from collected data and upload to Minio."""
    from .tdb import TDB2Builder
    from .minio import MinioStore

    # Gather input files
    input_path = Path(input_dir)
    files = list(input_path.glob("*.nt")) + list(input_path.glob("*.ttl"))
    if ontology_dir:
        files += list(Path(ontology_dir).glob("*.ttl"))

    if not files:
        click.echo("No input files found.", err=True)
        sys.exit(1)

    click.echo(f"Building TDB2 from {len(files)} files...")
    builder = TDB2Builder(jena_home=jena_home)
    builder.build([str(f) for f in files], output_dir)

    tar_path = f"{output_dir}.tar.gz"
    click.echo(f"Packaging TDB2 to {tar_path}...")
    builder.package(output_dir, tar_path)

    if minio_endpoint:
        click.echo("Uploading to Minio...")
        store = MinioStore(minio_endpoint, minio_bucket, minio_access_key, minio_secret_key)
        content_hash = store.upload_snapshot(tar_path)
        click.echo(f"Uploaded as {content_hash}")
    else:
        click.echo("No Minio endpoint configured, skipping upload.")
```

**Step 10: Run all tests**

```bash
uv run pytest -q
```

Expected: All tests pass.

**Step 11: Commit**

```bash
git add etl/
git commit -m "feat(etl): add TDB2 builder and content-addressable Minio upload"
```

---

## Task 4: Create ETL Containerfile

**Files:**
- Create: `etl/Containerfile`
- Create: `etl/entrypoint.sh`

**Step 1: Create Containerfile**

```dockerfile
FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install Apache Jena CLI tools
ARG JENA_VERSION=5.3.0
RUN curl -fsSL https://archive.apache.org/dist/jena/binaries/apache-jena-${JENA_VERSION}.tar.gz \
    | tar -xz -C /opt \
    && mv /opt/apache-jena-${JENA_VERSION} /opt/jena
ENV JENA_HOME=/opt/jena
ENV PATH="${JENA_HOME}/bin:${PATH}"

# Install mc (Minio client)
RUN curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc \
    && chmod +x /usr/local/bin/mc

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY packagegraph/ packagegraph/

# Copy ontology files (added at build time from ontology repo)
COPY ontology/ /app/ontology/

COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
```

**Step 2: Create entrypoint.sh**

```bash
#!/bin/bash
set -euo pipefail

# Default: run the full ETL pipeline
# 1. Collect from configured repos
# 2. Build TDB2
# 3. Upload to Minio

COLLECT_ARGS="${COLLECT_ARGS:-}"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/output}"
TDB2_DIR="${TDB2_DIR:-/tmp/tdb2}"
ONTOLOGY_DIR="${ONTOLOGY_DIR:-/app/ontology}"

mkdir -p "$OUTPUT_DIR"

echo "=== PackageGraph ETL Pipeline ==="

# Step 1: Collect package data
if [ -n "${REPO_URL:-}" ]; then
    echo "Collecting from ${REPO_URL}..."
    uv run packagegraph collect "$REPO_URL" \
        --repo-type "${REPO_TYPE:-debian}" \
        --output-file "$OUTPUT_DIR/packages.ttl" \
        $COLLECT_ARGS
fi

# Step 2: Build TDB2 and upload to Minio
echo "Building TDB2 index..."
uv run packagegraph build \
    --input-dir "$OUTPUT_DIR" \
    --ontology-dir "$ONTOLOGY_DIR" \
    --output-dir "$TDB2_DIR" \
    --jena-home "$JENA_HOME"

echo "=== ETL Pipeline Complete ==="
```

**Step 3: Verify Containerfile builds**

```bash
cd /Users/bharrington/Projects/packagegraph/platform

# Copy ontology TTLs for build context
mkdir -p etl/ontology
cp /Users/bharrington/Projects/packagegraph/ontology/*.ttl etl/ontology/

podman build -t packagegraph-etl:test -f etl/Containerfile etl/
```

Expected: Image builds successfully.

**Step 4: Commit**

```bash
git add etl/Containerfile etl/entrypoint.sh
git commit -m "feat(etl): add Containerfile with Jena, mc, and Python ETL"
```

---

## Task 5: Create Fuseki Containerfile and config

**Files:**
- Create: `fuseki/Containerfile`
- Create: `fuseki/config.ttl`
- Create: `fuseki/entrypoint.sh`

**Step 1: Create Fuseki dataset config**

Create `fuseki/config.ttl`:

```turtle
@prefix fuseki:  <http://jena.apache.org/fuseki#> .
@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix ja:      <http://jena.hpl.hp.com/2005/11/Assembler#> .
@prefix tdb2:    <http://jena.apache.org/2016/tdb#> .

<#service> rdf:type fuseki:Service ;
    fuseki:name "packagegraph" ;
    fuseki:endpoint [ fuseki:operation fuseki:query ; fuseki:name "sparql" ] ;
    fuseki:endpoint [ fuseki:operation fuseki:query ; fuseki:name "query" ] ;
    fuseki:endpoint [ fuseki:operation fuseki:gsp-r ; fuseki:name "get" ] ;
    fuseki:dataset <#dataset> .

<#dataset> rdf:type tdb2:DatasetTDB2 ;
    tdb2:location "/data/tdb2" .
```

**Step 2: Create Fuseki entrypoint**

Create `fuseki/entrypoint.sh`:

```bash
#!/bin/bash
set -euo pipefail

TDB2_DIR="/data/tdb2"
MINIO_ALIAS="pgraph"

echo "=== Fuseki Init: Loading TDB2 from Minio ==="

# Configure mc
export MC_HOST_${MINIO_ALIAS}="https://${MINIO_ACCESS_KEY}:${MINIO_SECRET_KEY}@${MINIO_ENDPOINT}"

# Read latest pointer
CONTENT_HASH=$(mc cat "${MINIO_ALIAS}/${MINIO_BUCKET}/tdb2/latest")
echo "Latest snapshot: ${CONTENT_HASH}"

# Download and extract TDB2 snapshot
REMOTE_PATH="tdb2/${CONTENT_HASH}/tdb2.tar.gz"
echo "Downloading ${REMOTE_PATH}..."
mc cp "${MINIO_ALIAS}/${MINIO_BUCKET}/${REMOTE_PATH}" /tmp/tdb2.tar.gz

echo "Extracting TDB2..."
mkdir -p "$TDB2_DIR"
tar -xzf /tmp/tdb2.tar.gz -C /data/
rm /tmp/tdb2.tar.gz

echo "TDB2 ready at ${TDB2_DIR}"
echo "=== Starting Fuseki ==="

# Hand off to Fuseki
exec /docker-entrypoint.sh /jena-fuseki/fuseki-server \
    --config /fuseki/config.ttl \
    --port 3030
```

**Step 3: Create Fuseki Containerfile**

```dockerfile
FROM stain/jena-fuseki:5.3.0

USER root

# Install mc (Minio client)
RUN curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc \
    && chmod +x /usr/local/bin/mc

# Copy config and entrypoint
COPY config.ttl /fuseki/config.ttl
COPY entrypoint.sh /fuseki/entrypoint.sh
RUN chmod +x /fuseki/entrypoint.sh

# TDB2 data volume (populated by init container or entrypoint)
VOLUME /data/tdb2

EXPOSE 3030

ENTRYPOINT ["/fuseki/entrypoint.sh"]
```

**Step 4: Verify Containerfile builds**

```bash
podman build -t packagegraph-fuseki:test -f fuseki/Containerfile fuseki/
```

Expected: Image builds successfully.

**Step 5: Commit**

```bash
git add fuseki/
git commit -m "feat(fuseki): add Containerfile with Minio-backed TDB2 loading"
```

---

## Task 6: Create Kustomize base manifests

**Files:**
- Create: `deploy/base/kustomization.yaml`
- Create: `deploy/base/namespace.yaml`
- Create: `deploy/base/minio/secret.yaml`
- Create: `deploy/base/fuseki/deployment.yaml`
- Create: `deploy/base/fuseki/service.yaml`
- Create: `deploy/base/fuseki/route.yaml`
- Create: `deploy/base/etl/job.yaml`

**Step 1: Create namespace**

```yaml
# deploy/base/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: packagegraph
```

**Step 2: Create Minio secret template**

```yaml
# deploy/base/minio/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: minio-credentials
  namespace: packagegraph
type: Opaque
stringData:
  MINIO_ENDPOINT: "minio.example.com"
  MINIO_BUCKET: "packagegraph"
  MINIO_ACCESS_KEY: "CHANGEME"
  MINIO_SECRET_KEY: "CHANGEME"
```

**Step 3: Create Fuseki deployment**

```yaml
# deploy/base/fuseki/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fuseki
  namespace: packagegraph
  labels:
    app: fuseki
    app.kubernetes.io/name: fuseki
    app.kubernetes.io/part-of: packagegraph
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fuseki
  template:
    metadata:
      labels:
        app: fuseki
    spec:
      initContainers:
        - name: load-tdb2
          image: packagegraph/fuseki:latest
          command: ["/fuseki/entrypoint.sh"]
          args: ["--init-only"]
          envFrom:
            - secretRef:
                name: minio-credentials
          volumeMounts:
            - name: tdb2-data
              mountPath: /data
      containers:
        - name: fuseki
          image: stain/jena-fuseki:5.3.0
          args:
            - --config
            - /fuseki/config.ttl
            - --port
            - "3030"
          ports:
            - containerPort: 3030
              name: http
          volumeMounts:
            - name: tdb2-data
              mountPath: /data
            - name: fuseki-config
              mountPath: /fuseki/config.ttl
              subPath: config.ttl
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: "2"
              memory: 4Gi
          livenessProbe:
            httpGet:
              path: /$/ping
              port: 3030
            initialDelaySeconds: 30
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /$/ping
              port: 3030
            initialDelaySeconds: 10
            periodSeconds: 10
      volumes:
        - name: tdb2-data
          emptyDir:
            sizeLimit: 100Gi
        - name: fuseki-config
          configMap:
            name: fuseki-config
```

**Step 4: Create Fuseki service and route**

```yaml
# deploy/base/fuseki/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: fuseki
  namespace: packagegraph
  labels:
    app: fuseki
spec:
  selector:
    app: fuseki
  ports:
    - port: 3030
      targetPort: 3030
      name: http
```

```yaml
# deploy/base/fuseki/route.yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: fuseki
  namespace: packagegraph
  labels:
    app: fuseki
spec:
  to:
    kind: Service
    name: fuseki
  port:
    targetPort: http
  tls:
    termination: edge
```

**Step 5: Create ETL Job**

```yaml
# deploy/base/etl/job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: etl-collect
  namespace: packagegraph
  labels:
    app: etl
    app.kubernetes.io/name: etl
    app.kubernetes.io/part-of: packagegraph
spec:
  backoffLimit: 2
  template:
    metadata:
      labels:
        app: etl
    spec:
      restartPolicy: Never
      containers:
        - name: etl
          image: packagegraph/etl:latest
          envFrom:
            - secretRef:
                name: minio-credentials
          env:
            - name: REPO_URL
              value: "http://deb.debian.org/debian"
            - name: REPO_TYPE
              value: "debian"
            - name: COLLECT_ARGS
              value: "--distribution stable --component main"
          resources:
            requests:
              cpu: "1"
              memory: 2Gi
            limits:
              cpu: "4"
              memory: 4Gi
```

**Step 6: Create ConfigMap for Fuseki config**

```yaml
# deploy/base/fuseki/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fuseki-config
  namespace: packagegraph
data:
  config.ttl: |
    @prefix fuseki:  <http://jena.apache.org/fuseki#> .
    @prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix ja:      <http://jena.hpl.hp.com/2005/11/Assembler#> .
    @prefix tdb2:    <http://jena.apache.org/2016/tdb#> .

    <#service> rdf:type fuseki:Service ;
        fuseki:name "packagegraph" ;
        fuseki:endpoint [ fuseki:operation fuseki:query ; fuseki:name "sparql" ] ;
        fuseki:endpoint [ fuseki:operation fuseki:query ; fuseki:name "query" ] ;
        fuseki:endpoint [ fuseki:operation fuseki:gsp-r ; fuseki:name "get" ] ;
        fuseki:dataset <#dataset> .

    <#dataset> rdf:type tdb2:DatasetTDB2 ;
        tdb2:location "/data/tdb2" .
```

**Step 7: Create base kustomization.yaml**

```yaml
# deploy/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: packagegraph

resources:
  - namespace.yaml
  - minio/secret.yaml
  - fuseki/configmap.yaml
  - fuseki/deployment.yaml
  - fuseki/service.yaml
  - fuseki/route.yaml
  - etl/job.yaml
```

**Step 8: Validate with kustomize**

```bash
oc kustomize deploy/base/
```

Expected: Valid YAML output with all resources.

**Step 9: Commit**

```bash
git add deploy/base/
git commit -m "feat(deploy): add Kustomize base manifests for Fuseki, ETL Job, and Minio"
```

---

## Task 7: Create dev overlay

**Files:**
- Create: `deploy/overlays/dev/kustomization.yaml`
- Create: `deploy/overlays/dev/patches/fuseki-resources.yaml`
- Create: `deploy/overlays/dev/patches/etl-single-distro.yaml`

**Step 1: Create dev kustomization**

```yaml
# deploy/overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

patches:
  - path: patches/fuseki-resources.yaml
  - path: patches/etl-single-distro.yaml
```

**Step 2: Create dev patches**

```yaml
# deploy/overlays/dev/patches/fuseki-resources.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fuseki
spec:
  template:
    spec:
      containers:
        - name: fuseki
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: "1"
              memory: 1Gi
```

```yaml
# deploy/overlays/dev/patches/etl-single-distro.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: etl-collect
spec:
  template:
    spec:
      containers:
        - name: etl
          env:
            - name: COLLECT_ARGS
              value: "--distribution stable --component main --arch binary-amd64 --no-parallel"
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: "2"
              memory: 2Gi
```

**Step 3: Validate**

```bash
oc kustomize deploy/overlays/dev/
```

Expected: Valid YAML with reduced resource limits.

**Step 4: Commit**

```bash
git add deploy/overlays/dev/
git commit -m "feat(deploy): add dev overlay with reduced resources"
```

---

## Task 8: Create prod overlay with CronJob

**Files:**
- Create: `deploy/overlays/prod/kustomization.yaml`
- Create: `deploy/overlays/prod/cronjob.yaml`
- Create: `deploy/overlays/prod/patches/fuseki-resources.yaml`

**Step 1: Create prod CronJob**

```yaml
# deploy/overlays/prod/cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: etl-scheduled
  namespace: packagegraph
  labels:
    app: etl
    app.kubernetes.io/name: etl
    app.kubernetes.io/part-of: packagegraph
spec:
  schedule: "0 2 * * 0"  # Weekly: Sunday at 2 AM
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        metadata:
          labels:
            app: etl
        spec:
          restartPolicy: Never
          containers:
            - name: etl
              image: packagegraph/etl:latest
              envFrom:
                - secretRef:
                    name: minio-credentials
              env:
                - name: REPO_URL
                  value: "http://deb.debian.org/debian"
                - name: REPO_TYPE
                  value: "debian"
                - name: COLLECT_ARGS
                  value: "--distribution stable --component main --parallel --workers 4"
              resources:
                requests:
                  cpu: "2"
                  memory: 2Gi
                limits:
                  cpu: "4"
                  memory: 4Gi
```

**Step 2: Create prod kustomization**

```yaml
# deploy/overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base
  - cronjob.yaml

patches:
  - path: patches/fuseki-resources.yaml

# Remove the manual Job in prod (CronJob handles scheduling)
# The base Job is kept for ad-hoc runs via: oc create job --from=cronjob/etl-scheduled etl-manual
```

**Step 3: Create prod Fuseki patch**

```yaml
# deploy/overlays/prod/patches/fuseki-resources.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fuseki
spec:
  template:
    spec:
      containers:
        - name: fuseki
          resources:
            requests:
              cpu: "1"
              memory: 2Gi
            limits:
              cpu: "2"
              memory: 4Gi
```

**Step 4: Validate**

```bash
oc kustomize deploy/overlays/prod/
```

Expected: Valid YAML including CronJob and production resource limits.

**Step 5: Commit**

```bash
git add deploy/overlays/prod/
git commit -m "feat(deploy): add prod overlay with weekly CronJob"
```

---

## Task 9: Wire up Fuseki init container for Minio pull

**Files:**
- Modify: `fuseki/entrypoint.sh`
- Modify: `deploy/base/fuseki/deployment.yaml`

**Step 1: Update entrypoint to support init-only mode**

Update `fuseki/entrypoint.sh` to support `--init-only` flag (used by init container) vs full startup (used by standalone):

```bash
#!/bin/bash
set -euo pipefail

TDB2_DIR="/data/tdb2"
MINIO_ALIAS="pgraph"

echo "=== Fuseki: Loading TDB2 from Minio ==="

# Configure mc
export MC_HOST_${MINIO_ALIAS}="https://${MINIO_ACCESS_KEY}:${MINIO_SECRET_KEY}@${MINIO_ENDPOINT}"

# Read latest pointer
CONTENT_HASH=$(mc cat "${MINIO_ALIAS}/${MINIO_BUCKET}/tdb2/latest")
echo "Latest snapshot: ${CONTENT_HASH}"

# Check if TDB2 already loaded with this hash
HASH_FILE="/data/.content-hash"
if [ -f "$HASH_FILE" ] && [ "$(cat "$HASH_FILE")" = "$CONTENT_HASH" ]; then
    echo "TDB2 already loaded with ${CONTENT_HASH}, skipping download."
else
    # Download and extract TDB2 snapshot
    REMOTE_PATH="tdb2/${CONTENT_HASH}/tdb2.tar.gz"
    echo "Downloading ${REMOTE_PATH}..."
    mc cp "${MINIO_ALIAS}/${MINIO_BUCKET}/${REMOTE_PATH}" /tmp/tdb2.tar.gz

    echo "Extracting TDB2..."
    rm -rf "$TDB2_DIR"
    mkdir -p "$TDB2_DIR"
    tar -xzf /tmp/tdb2.tar.gz -C /data/
    rm /tmp/tdb2.tar.gz
    echo "$CONTENT_HASH" > "$HASH_FILE"
fi

echo "TDB2 ready at ${TDB2_DIR} (${CONTENT_HASH})"

# If --init-only, exit here (used as init container)
if [ "${1:-}" = "--init-only" ]; then
    echo "Init complete."
    exit 0
fi

echo "=== Starting Fuseki ==="
exec /docker-entrypoint.sh /jena-fuseki/fuseki-server \
    --config /fuseki/config.ttl \
    --port 3030
```

**Step 2: Verify Containerfile still builds**

```bash
podman build -t packagegraph-fuseki:test -f fuseki/Containerfile fuseki/
```

**Step 3: Commit**

```bash
git add fuseki/entrypoint.sh
git commit -m "feat(fuseki): support init-only mode and content-hash caching"
```

---

## Task 10: Add GitHub remote and verify complete structure

**Files:**
- None (verification only)

**Step 1: Verify full directory structure**

```bash
cd /Users/bharrington/Projects/packagegraph/platform
find . -not -path './.git/*' -not -path './.venv/*' -not -path './__pycache__/*' | sort
```

Expected structure:
```
.
./deploy/base/etl/job.yaml
./deploy/base/fuseki/configmap.yaml
./deploy/base/fuseki/deployment.yaml
./deploy/base/fuseki/route.yaml
./deploy/base/fuseki/service.yaml
./deploy/base/kustomization.yaml
./deploy/base/minio/secret.yaml
./deploy/base/namespace.yaml
./deploy/overlays/dev/kustomization.yaml
./deploy/overlays/dev/patches/etl-single-distro.yaml
./deploy/overlays/dev/patches/fuseki-resources.yaml
./deploy/overlays/prod/cronjob.yaml
./deploy/overlays/prod/kustomization.yaml
./deploy/overlays/prod/patches/fuseki-resources.yaml
./etl/Containerfile
./etl/entrypoint.sh
./etl/packagegraph/__init__.py
./etl/packagegraph/cli.py
./etl/packagegraph/collector.py
./etl/packagegraph/debian_collector.py
./etl/packagegraph/minio.py
./etl/packagegraph/profiler.py
./etl/packagegraph/rpm_collector.py
./etl/packagegraph/tdb.py
./etl/pyproject.toml
./etl/tests/__init__.py
./etl/tests/test_minio.py
./etl/tests/test_tdb.py
./fuseki/Containerfile
./fuseki/config.ttl
./fuseki/entrypoint.sh
./.gitignore
./Makefile
./README.md
```

**Step 2: Run all tests**

```bash
cd /Users/bharrington/Projects/packagegraph/platform/etl
uv run pytest -q
```

Expected: All tests pass.

**Step 3: Validate all Kustomize overlays**

```bash
cd /Users/bharrington/Projects/packagegraph/platform
oc kustomize deploy/base/
oc kustomize deploy/overlays/dev/
oc kustomize deploy/overlays/prod/
```

Expected: Valid YAML for all three.

**Step 4: Lint Python code**

```bash
cd etl
ruff check .
ruff format --check .
```

Expected: Clean.

**Step 5: Create GitHub repo and push**

```bash
cd /Users/bharrington/Projects/packagegraph/platform
# User creates repo on GitHub, then:
git remote add origin git@github.com:packagegraph/platform.git
git push -u origin main
```

---

## Summary

| Task | Description | Depends On |
|------|-------------|------------|
| 1 | Scaffold platform repo | — |
| 2 | Migrate ETL Python package | 1 |
| 3 | Add Minio upload + TDB2 builder | 2 |
| 4 | ETL Containerfile | 3 |
| 5 | Fuseki Containerfile + config | 1 |
| 6 | Kustomize base manifests | 4, 5 |
| 7 | Dev overlay | 6 |
| 8 | Prod overlay with CronJob | 6 |
| 9 | Fuseki init container wiring | 5, 6 |
| 10 | Verify complete structure | 7, 8, 9 |

Tasks 4 and 5 can run in parallel. Tasks 7 and 8 can run in parallel.
