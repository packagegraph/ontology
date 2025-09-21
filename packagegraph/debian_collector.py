import sys
import click
import requests
import gzip
import re
from urllib.parse import quote
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL
from .collector import BaseCollector
from .profiler import profiler

class DebianCollector(BaseCollector):
    """Collects data from a Debian repository."""

    def __init__(self, g, repo_url, distribution, component, arch, parallel=True, chunk_size=1000, workers=4):
        super().__init__(g, repo_url, parallel, chunk_size, workers)
        self.distribution = distribution
        self.component = component
        self.arch = arch

    def collect(self):
        with profiler.step("Get Release Info"):
            release_info = self._get_release_info()
            if not release_info:
                click.echo(f"Could not determine release information for '{self.distribution}'. Aborting.", err=True)
                sys.exit(1)

        codename, suite, origin = release_info['Codename'], release_info['Suite'], release_info['Origin']
        click.echo(f"Resolved '{self.distribution}' to Origin='{origin}', Suite='{suite}', Codename='{codename}'.")

        with profiler.step("Add Distribution Metadata"):
            # Add distribution metadata to main graph
            self._add_distribution_metadata(codename, suite, origin)
        
        with profiler.step("Download Package Metadata"):
            # Get package data
            packages_data = self._get_packages_data()
            click.echo(f"Found {len(packages_data)} package entries.")
        
        with profiler.step("Process Packages (Parallel)"):
            # Process packages in parallel or single-threaded
            if not self.parallel or len(packages_data) < self.chunk_size:
                # Single-threaded processing directly into main graph
                processed_count = self._process_packages_single_threaded(packages_data, codename, suite, origin)
            else:
                # Parallel processing with chunks
                processed_count = self.collect_parallel(
                    [(pkg_data, codename, suite, origin) for pkg_data in packages_data],
                    DebianCollector._process_package_chunk_wrapper
                )
        
        with profiler.step("Process Contents File"):
            # Process contents file in parallel chunks
            pkg_map = self._build_package_map(packages_data)
            self._process_contents_parallel(pkg_map)
        
        return processed_count

    def _get_release_info(self):
        """Fetches the Release file and extracts Codename, Suite, and Origin."""
        release_url = f"{self.repo_url.rstrip('/')}/dists/{self.distribution}/Release"
        click.echo(f"Fetching Release info from {release_url}")
        release_info = {}
        try:
            response = requests.get(release_url)
            response.raise_for_status()
            for line in response.text.splitlines():
                if line.startswith('Codename:'):
                    release_info['Codename'] = line.split(':', 1)[1].strip()
                elif line.startswith('Suite:'):
                    release_info['Suite'] = line.split(':', 1)[1].strip()
                elif line.startswith('Origin:'):
                    release_info['Origin'] = line.split(':', 1)[1].strip()
            if 'Codename' in release_info and 'Suite' in release_info and 'Origin' in release_info:
                return release_info
        except requests.exceptions.RequestException as e:
            click.echo(f"Error: Could not fetch or parse Release file: {e}", err=True)
            sys.exit(1)
        return None

    def _process_packages(self, codename, suite, origin):
        packages_url = f"{self.repo_url.rstrip('/')}/dists/{self.distribution}/{self.component}/{self.arch}/Packages.gz"
        click.echo(f"Downloading {packages_url}")
        response = requests.get(packages_url)
        response.raise_for_status()
        content = gzip.decompress(response.content).decode('utf-8')
        
        DEB = "http://packagegraph.github.io/ontology/debian#"
        dist_uri = URIRef(f"{DEB}{origin}")
        suite_uri = URIRef(f"{DEB}{suite}")
        codename_uri = URIRef(f"{DEB}{codename}")
        
        self.g.add((dist_uri, RDF.type, URIRef(f"{DEB}Distribution")))
        self.g.add((codename_uri, RDF.type, URIRef(f"{DEB}Suite")))
        self.g.add((codename_uri, URIRef(f"{DEB}partOfDistribution"), dist_uri))
        if suite != codename:
            self.g.add((suite_uri, OWL.sameAs, codename_uri))

        packages = content.strip().split('\n\n')
        click.echo(f"Found {len(packages)} package entries.")
        
        pkg_map = {}
        for pkg_info in packages:
            pkg_data = {k.strip(): v.strip() for k, v in (line.split(':', 1) for line in pkg_info.strip().split('\n') if ':' in line)}
            if 'Package' in pkg_data and 'Version' in pkg_data:
                pkg_name, pkg_version = pkg_data['Package'], pkg_data['Version']
                pkg_id = f"{pkg_name}-{pkg_version}"
                pkg_uri = URIRef(f"{DEB}{quote(pkg_id)}")
                pkg_map[pkg_name] = pkg_uri
                
                self.g.add((pkg_uri, RDF.type, URIRef(f"{DEB}DebianPackage")))
                self.g.add((pkg_uri, URIRef(f"{DEB}inSuite"), codename_uri))
                
                # Add core properties as literals for easier querying
                self.g.add((pkg_uri, URIRef(f"{DEB}name"), Literal(pkg_name)))
                self.g.add((pkg_uri, URIRef(f"{DEB}version"), Literal(pkg_version)))

                for key, value in pkg_data.items():
                    prop_name = key.lower().replace('-', '')
                    if prop_name in ['depends', 'recommends', 'suggests', 'breaks', 'enhances', 'predepends']:
                        continue
                    self.g.add((pkg_uri, URIRef(f"{DEB}{prop_name}"), Literal(value)))

                dep_fields = ['Depends', 'Recommends', 'Suggests', 'Breaks', 'Enhances', 'Pre-Depends']
                for field in dep_fields:
                    if field in pkg_data:
                        prop_uri = URIRef(f"{DEB}{field.lower().replace('-', '')}")
                        dependencies = self._parse_dependency_string(pkg_data[field])
                        for dep_name, version_constraint in dependencies:
                            dep_bnode = BNode()
                            self.g.add((pkg_uri, prop_uri, dep_bnode))
                            self.g.add((dep_bnode, RDF.type, URIRef(f"{DEB}Dependency")))
                            self.g.add((dep_bnode, URIRef(f"{DEB}onPackage"), URIRef(f"{DEB}package/{quote(dep_name)}")))
                            if version_constraint:
                                self.g.add((dep_bnode, URIRef(f"{DEB}versionConstraint"), Literal(version_constraint)))
        return pkg_map

    def _process_contents(self, pkg_map):
        contents_arch = self.arch.split('-')[-1]
        contents_url = f"{self.repo_url.rstrip('/')}/dists/{self.distribution}/Contents-{contents_arch}.gz"
        click.echo(f"Downloading {contents_url}")
        try:
            with requests.get(contents_url, stream=True) as response:
                response.raise_for_status()
                contents_content = gzip.decompress(response.content).decode('utf-8', errors='ignore')
                
                click.echo("Processing file lists...")
                for line in contents_content.splitlines():
                    parts = line.strip().split()
                    if len(parts) < 2: continue
                    
                    file_path, pkg_names_str = parts[0], parts[-1]
                    for pkg_name in pkg_names_str.split(','):
                        clean_pkg_name = pkg_name.split('/')[-1]
                        if clean_pkg_name in pkg_map:
                            self.g.add((pkg_map[clean_pkg_name], URIRef(f"http://packagegraph.github.io/ontology/debian#fileName"), Literal(file_path)))
        except requests.exceptions.HTTPError as e:
            click.echo(f"Warning: Could not download Contents file at {contents_url}: {e}", err=True)

    def _parse_dependency_string(self, dep_string):
        """Parses a Debian dependency string into a list of tuples."""
        dep_pattern = re.compile(r'([\w.-]+)(?:\s+\(([^)]+)\))?')
        dependencies = []
        for part in dep_string.split(','):
            alternatives = [d.strip() for d in part.split('|')]
            first_alternative = alternatives[0]
            match = dep_pattern.match(first_alternative)
            if match:
                dependencies.append((match.group(1), match.group(2)))
        return dependencies
    
    def _add_distribution_metadata(self, codename, suite, origin):
        """Add distribution metadata to main graph."""
        DEB = "http://packagegraph.github.io/ontology/debian#"
        dist_uri = URIRef(f"{DEB}{origin}")
        suite_uri = URIRef(f"{DEB}{suite}")
        codename_uri = URIRef(f"{DEB}{codename}")
        
        self.g.add((dist_uri, RDF.type, URIRef(f"{DEB}Distribution")))
        self.g.add((codename_uri, RDF.type, URIRef(f"{DEB}Suite")))
        self.g.add((codename_uri, URIRef(f"{DEB}partOfDistribution"), dist_uri))
        if suite != codename:
            self.g.add((suite_uri, OWL.sameAs, codename_uri))
    
    def _get_packages_data(self):
        """Download and parse package data into structured format."""
        packages_url = f"{self.repo_url.rstrip('/')}/dists/{self.distribution}/{self.component}/{self.arch}/Packages.gz"
        
        with profiler.step("Download Packages.gz"):
            click.echo(f"Downloading {packages_url}")
            response = requests.get(packages_url)
            response.raise_for_status()
            profiler.log(f"Downloaded {len(response.content)} bytes")
        
        with profiler.step("Decompress Packages.gz"):
            content = gzip.decompress(response.content).decode('utf-8')
            profiler.log(f"Decompressed to {len(content)} characters")
        
        with profiler.step("Parse Package Entries"):
            packages = content.strip().split('\n\n')
            packages_data = []
            
            for pkg_info in packages:
                pkg_data = {k.strip(): v.strip() for k, v in (line.split(':', 1) for line in pkg_info.strip().split('\n') if ':' in line)}
                if 'Package' in pkg_data and 'Version' in pkg_data:
                    packages_data.append(pkg_data)
            
            profiler.log(f"Parsed {len(packages_data)} valid packages")
        
        return packages_data
    
    def _build_package_map(self, packages_data):
        """Build package name to URI mapping for contents processing."""
        DEB = "http://packagegraph.github.io/ontology/debian#"
        pkg_map = {}
        for pkg_data in packages_data:
            pkg_name = pkg_data['Package']
            pkg_version = pkg_data['Version']
            pkg_id = f"{pkg_name}-{pkg_version}"
            pkg_uri = URIRef(f"{DEB}{quote(pkg_id)}")
            pkg_map[pkg_name] = pkg_uri
        return pkg_map
    
    def _process_contents_parallel(self, pkg_map):
        """Download and process contents file in parallel chunks."""
        contents_arch = self.arch.split('-')[-1]
        contents_url = f"{self.repo_url.rstrip('/')}/dists/{self.distribution}/Contents-{contents_arch}.gz"
        
        try:
            with profiler.step("Download Contents File"):
                click.echo(f"Downloading {contents_url}")
                with requests.get(contents_url, stream=True) as response:
                    response.raise_for_status()
                    profiler.log(f"Downloaded {len(response.content)} bytes")
                    
            with profiler.step("Decompress Contents File"):
                contents_content = gzip.decompress(response.content).decode('utf-8', errors='ignore')
                profiler.log(f"Decompressed to {len(contents_content)} characters")
                
            with profiler.step("Parse Contents Lines"):
                click.echo("Processing file lists...")
                lines = contents_content.splitlines()
                profiler.log(f"Split into {len(lines)} lines")
                
            with profiler.step("Process Contents (Parallel)"):
                # Process contents in parallel or single-threaded
                if not self.parallel or len(lines) < self.chunk_size:
                    # Single-threaded processing directly into main graph
                    self._process_contents_single_threaded(lines, pkg_map)
                else:
                    # Process contents in chunks
                    self.collect_parallel(
                        [(line, pkg_map) for line in lines],
                        DebianCollector._process_contents_chunk_wrapper
                    )
        except requests.exceptions.HTTPError as e:
            click.echo(f"Warning: Could not download Contents file at {contents_url}: {e}", err=True)
    
    def _process_packages_single_threaded(self, packages_data, codename, suite, origin):
        """Process packages directly into main graph (single-threaded)."""
        DEB = "http://packagegraph.github.io/ontology/debian#"
        codename_uri = URIRef(f"{DEB}{codename}")
        
        for pkg_data in packages_data:
            pkg_name, pkg_version = pkg_data['Package'], pkg_data['Version']
            pkg_id = f"{pkg_name}-{pkg_version}"
            pkg_uri = URIRef(f"{DEB}{quote(pkg_id)}")
            
            self.g.add((pkg_uri, RDF.type, URIRef(f"{DEB}DebianPackage")))
            self.g.add((pkg_uri, URIRef(f"{DEB}inSuite"), codename_uri))
            self.g.add((pkg_uri, URIRef(f"{DEB}name"), Literal(pkg_name)))
            self.g.add((pkg_uri, URIRef(f"{DEB}version"), Literal(pkg_version)))
            
            # Add package properties
            for key, value in pkg_data.items():
                prop_name = key.lower().replace('-', '')
                if prop_name not in ['package', 'version']:
                    self.g.add((pkg_uri, URIRef(f"{DEB}{prop_name}"), Literal(value)))
            
            # Process dependencies
            for dep_key in ['Depends', 'Recommends', 'Suggests', 'Conflicts', 'Replaces', 'Provides']:
                if dep_key in pkg_data:
                    dependencies = self._parse_dependency_string(pkg_data[dep_key])
                    for dep_name, version_constraint in dependencies:
                        dep_bnode = BNode()
                        self.g.add((pkg_uri, URIRef(f"{DEB}{dep_key.lower()}"), dep_bnode))
                        self.g.add((dep_bnode, URIRef(f"{DEB}packageName"), Literal(dep_name)))
                        if version_constraint:
                            self.g.add((dep_bnode, URIRef(f"{DEB}versionConstraint"), Literal(version_constraint)))
        
        return len(packages_data)
    
    def _process_contents_single_threaded(self, lines, pkg_map):
        """Process contents lines directly into main graph (single-threaded)."""
        DEB = "http://packagegraph.github.io/ontology/debian#"
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) < 2: 
                continue
            
            file_path, pkg_names_str = parts[0], parts[-1]
            for pkg_name in pkg_names_str.split(','):
                clean_pkg_name = pkg_name.split('/')[-1]
                if clean_pkg_name in pkg_map:
                    self.g.add((pkg_map[clean_pkg_name], URIRef(f"{DEB}fileName"), Literal(file_path)))
    
    @staticmethod
    def _process_package_chunk_wrapper(data_chunk, chunk_id):
        """Wrapper for parallel processing of package chunks."""
        packages_data = [item[0] for item in data_chunk]
        codename, suite, origin = data_chunk[0][1], data_chunk[0][2], data_chunk[0][3]
        return DebianCollector._process_package_chunk(packages_data, chunk_id, codename, suite, origin)
    
    @staticmethod
    def _process_contents_chunk_wrapper(data_chunk, chunk_id):
        """Wrapper for parallel processing of contents chunks."""
        lines = [item[0] for item in data_chunk]
        pkg_map = data_chunk[0][1]
        return DebianCollector._process_contents_chunk(lines, chunk_id, pkg_map)

    @staticmethod
    def _process_package_chunk(packages_chunk, chunk_id, codename, suite, origin):
        """Process a chunk of packages in a separate process."""
        import tempfile
        from rdflib import Graph, URIRef, Literal, BNode
        from rdflib.namespace import RDF, RDFS, OWL
        from urllib.parse import quote
        import re
        
        def _parse_dependency_string_static(dep_string):
            """Static version of dependency parsing for multiprocessing."""
            dep_pattern = re.compile(r'([\w.-]+)(?:\s+\(([^)]+)\))?')
            dependencies = []
            for part in dep_string.split(','):
                alternatives = [d.strip() for d in part.split('|')]
                first_alternative = alternatives[0]
                match = dep_pattern.match(first_alternative)
                if match:
                    dependencies.append((match.group(1), match.group(2)))
            return dependencies
        
        chunk_graph = Graph()
        DEB = "http://packagegraph.github.io/ontology/debian#"
        codename_uri = URIRef(f"{DEB}{codename}")
        
        for pkg_data in packages_chunk:
            pkg_name, pkg_version = pkg_data['Package'], pkg_data['Version']
            pkg_id = f"{pkg_name}-{pkg_version}"
            pkg_uri = URIRef(f"{DEB}{quote(pkg_id)}")
            
            chunk_graph.add((pkg_uri, RDF.type, URIRef(f"{DEB}DebianPackage")))
            chunk_graph.add((pkg_uri, URIRef(f"{DEB}inSuite"), codename_uri))
            chunk_graph.add((pkg_uri, URIRef(f"{DEB}name"), Literal(pkg_name)))
            chunk_graph.add((pkg_uri, URIRef(f"{DEB}version"), Literal(pkg_version)))
            
            # Add package properties
            for key, value in pkg_data.items():
                prop_name = key.lower().replace('-', '')
                if prop_name not in ['package', 'version']:
                    chunk_graph.add((pkg_uri, URIRef(f"{DEB}{prop_name}"), Literal(value)))
            
            # Process dependencies
            for dep_key in ['Depends', 'Recommends', 'Suggests', 'Conflicts', 'Replaces', 'Provides']:
                if dep_key in pkg_data:
                    dependencies = _parse_dependency_string_static(pkg_data[dep_key])
                    for dep_name, version_constraint in dependencies:
                        dep_bnode = BNode()
                        chunk_graph.add((pkg_uri, URIRef(f"{DEB}{dep_key.lower()}"), dep_bnode))
                        chunk_graph.add((dep_bnode, URIRef(f"{DEB}packageName"), Literal(dep_name)))
                        if version_constraint:
                            chunk_graph.add((dep_bnode, URIRef(f"{DEB}versionConstraint"), Literal(version_constraint)))
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=f'_chunk_{chunk_id}.ttl', delete=False)
        chunk_graph.serialize(destination=temp_file.name, format='turtle')
        temp_file.close()
        return temp_file.name
    
    @staticmethod
    def _process_contents_chunk(lines_chunk, chunk_id, pkg_map):
        """Process a chunk of contents file lines in a separate process."""
        import tempfile
        from rdflib import Graph, URIRef, Literal
        
        chunk_graph = Graph()
        DEB = "http://packagegraph.github.io/ontology/debian#"
        
        for line in lines_chunk:
            parts = line.strip().split()
            if len(parts) < 2: 
                continue
            
            file_path, pkg_names_str = parts[0], parts[-1]
            for pkg_name in pkg_names_str.split(','):
                clean_pkg_name = pkg_name.split('/')[-1]
                if clean_pkg_name in pkg_map:
                    chunk_graph.add((pkg_map[clean_pkg_name], URIRef(f"{DEB}fileName"), Literal(file_path)))
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=f'_contents_chunk_{chunk_id}.ttl', delete=False)
        chunk_graph.serialize(destination=temp_file.name, format='turtle')
        temp_file.close()
        return temp_file.name
