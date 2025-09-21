import click
import requests
import gzip
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote
try:
    import zstandard as zstd
except ImportError:
    zstd = None
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS
from .collector import BaseCollector
from .profiler import profiler

class RpmCollector(BaseCollector):
    """Collects data from an RPM repository."""

    def __init__(self, g, repo_url, parallel=True, chunk_size=1000, workers=4):
        super().__init__(g, repo_url, parallel, chunk_size, workers)

    def collect(self):
        with profiler.step("Download Primary Metadata"):
            # Get package data from primary metadata
            packages_data = self._get_primary_packages_data()
            click.echo(f"Found {len(packages_data)} package entries in primary metadata.")
        
        with profiler.step("Process Packages (Parallel)"):
            # Process packages in parallel
            processed_count = self.collect_parallel(
                packages_data,
                RpmCollector._process_package_chunk
            )
        
        with profiler.step("Build Package Map"):
            # Process filelists and other metadata in parallel
            pkg_map = self._build_package_map(packages_data)
            
        with profiler.step("Process Filelists"):
            self._process_filelists_parallel(pkg_map)
            
        with profiler.step("Process Other Metadata"):
            self._process_other_parallel(pkg_map)
        
        return processed_count

    def _get_metadata_url(self, metadata_type):
        """Finds the metadata URL for a given type from repomd.xml."""
        repomd_url = f"{self.repo_url.rstrip('/')}/repodata/repomd.xml"
        click.echo(f"Fetching repomd.xml from {repomd_url}")
        response = requests.get(repomd_url)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        ns = {'repo': 'http://linux.duke.edu/metadata/repo'}
        
        location = root.find(f"repo:data[@type='{metadata_type}']/repo:location", ns)
        if location is not None:
            return f"{self.repo_url.rstrip('/')}/{location.get('href')}"
        click.echo(f"Warning: Could not find '{metadata_type}' metadata location in repomd.xml", err=True)
        return None

    def _download_and_decompress(self, url):
        click.echo(f"Downloading metadata from {url}")
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            if url.endswith('.gz'):
                return gzip.decompress(response.content)
            elif url.endswith('.zst'):
                if not zstd:
                    raise click.ClickException("'zstandard' library is required for .zst decompression.")
                dctx = zstd.ZstdDecompressor()
                with dctx.stream_reader(response.raw) as reader:
                    return reader.read()
            else:
                return response.content

    def _process_primary_metadata(self):
        primary_url = self._get_metadata_url('primary')
        if not primary_url:
            raise click.ClickException("Could not find primary metadata, cannot proceed.")
        
        content = self._download_and_decompress(primary_url)
        
        root = ET.fromstring(content)
        ns = {'common': 'http://linux.duke.edu/metadata/common', 'rpm': 'http://linux.duke.edu/metadata/rpm'}
        RPM = "http://packagegraph.github.io/ontology/rpm#"
        
        packages = root.findall('common:package', ns)
        click.echo(f"Found {len(packages)} package entries in primary metadata.")
        
        pkg_map = {}
        for pkg in packages:
            name = pkg.find('common:name', ns).text
            arch = pkg.find('common:arch', ns).text
            version_info = pkg.find('common:version', ns)
            ver = version_info.get('ver')
            rel = version_info.get('rel')
            
            pkg_id = f"{name}-{ver}-{rel}.{arch}"
            pkg_uri = URIRef(f"{RPM}{quote(pkg_id)}")
            self.g.add((pkg_uri, RDF.type, URIRef(f"{RPM}RPMPackage")))
            
            # Add core properties as literals for easier querying
            self.g.add((pkg_uri, URIRef(f"{RPM}name"), Literal(name)))
            self.g.add((pkg_uri, URIRef(f"{RPM}version"), Literal(ver)))
            self.g.add((pkg_uri, URIRef(f"{RPM}release"), Literal(rel)))
            self.g.add((pkg_uri, URIRef(f"{RPM}arch"), Literal(arch)))

            pkgid_checksum = pkg.find('common:checksum', ns).text
            pkg_map[pkgid_checksum] = pkg_uri

            summary = pkg.find('common:summary', ns)
            if summary is not None: self.g.add((pkg_uri, URIRef(f"{RPM}summary"), Literal(summary.text)))
                
            description = pkg.find('common:description', ns)
            if description is not None: self.g.add((pkg_uri, URIRef(f"{RPM}description"), Literal(description.text)))

            format_element = pkg.find('common:format', ns)
            if format_element is not None:
                for dep_entry in format_element.findall('rpm:requires/rpm:entry', ns):
                    dep_name = dep_entry.get('name')
                    dep_bnode = BNode()
                    self.g.add((pkg_uri, URIRef(f"{RPM}requires"), dep_bnode))
                    self.g.add((dep_bnode, RDF.type, URIRef(f"{RPM}Dependency")))
                    self.g.add((dep_bnode, URIRef(f"{RPM}onPackage"), URIRef(f"{RPM}package/{quote(dep_name)}")))
        return pkg_map

    def _process_filelists(self, pkg_map):
        filelists_url = self._get_metadata_url('filelists')
        if filelists_url:
            content = self._download_and_decompress(filelists_url)
            file_root = ET.fromstring(content)
            file_ns = {'filelists': 'http://linux.duke.edu/metadata/filelists'}
            for pkg in file_root.findall('filelists:package', file_ns):
                pkgid = pkg.get('pkgid')
                if pkgid in pkg_map:
                    pkg_uri = pkg_map[pkgid]
                    for file_entry in pkg.findall('filelists:file', file_ns):
                        if file_entry.text:
                            self.g.add((pkg_uri, URIRef(f"http://packagegraph.github.io/ontology/rpm#fileName"), Literal(file_entry.text)))

    def _process_other(self, pkg_map):
        other_url = self._get_metadata_url('other')
        if other_url:
            content = self._download_and_decompress(other_url)
            other_root = ET.fromstring(content)
            other_ns = {'other': 'http://linux.duke.edu/metadata/other'}
            for pkg in other_root.findall('other:package', other_ns):
                pkgid = pkg.get('pkgid')
                if pkgid in pkg_map:
                    pkg_uri = pkg_map[pkgid]
                    for changelog in pkg.findall('other:changelog', other_ns):
                        cl_bnode = BNode()
                        self.g.add((pkg_uri, URIRef(f"http://packagegraph.github.io/ontology/rpm#hasChangelog"), cl_bnode))
                        self.g.add((cl_bnode, RDF.type, URIRef(f"http://packagegraph.github.io/ontology/rpm#Changelog")))
                        if changelog.text:
                            self.g.add((cl_bnode, URIRef(f"http://packagegraph.github.io/ontology/rpm#changelogText"), Literal(changelog.text)))
                        if changelog.get('author'):
                            self.g.add((cl_bnode, URIRef(f"http://packagegraph.github.io/ontology/rpm#changelogAuthor"), Literal(changelog.get('author'))))
                        if changelog.get('date'):
                            self.g.add((cl_bnode, URIRef(f"http://packagegraph.github.io/ontology/rpm#changelogTime"), Literal(changelog.get('date'), datatype=RDFS.Literal)))
    
    def _get_primary_packages_data(self):
        """Download and parse primary metadata into structured format."""
        primary_url = self._get_metadata_url('primary')
        if not primary_url:
            return []
        
        content = self._download_and_decompress(primary_url)
        root = ET.fromstring(content)
        ns = {'common': 'http://linux.duke.edu/metadata/common', 'rpm': 'http://linux.duke.edu/metadata/rpm'}
        
        packages = root.findall('common:package', ns)
        packages_data = []
        
        for pkg in packages:
            pkg_data = {
                'name': pkg.find('common:name', ns).text if pkg.find('common:name', ns) is not None else '',
                'version': pkg.find('common:version', ns).get('ver') if pkg.find('common:version', ns) is not None else '',
                'release': pkg.find('common:version', ns).get('rel') if pkg.find('common:version', ns) is not None else '',
                'arch': pkg.find('common:arch', ns).text if pkg.find('common:arch', ns) is not None else '',
                'summary': pkg.find('common:summary', ns).text if pkg.find('common:summary', ns) is not None else '',
                'description': pkg.find('common:description', ns).text if pkg.find('common:description', ns) is not None else '',
                'pkgid': pkg.find('common:checksum', ns).text if pkg.find('common:checksum', ns) is not None else '',
                'format_element': pkg.find('common:format', ns)
            }
            packages_data.append(pkg_data)
        
        return packages_data
    
    def _build_package_map(self, packages_data):
        """Build package pkgid to URI mapping."""
        RPM = "http://packagegraph.github.io/ontology/rpm#"
        pkg_map = {}
        for pkg_data in packages_data:
            pkg_id = f"{pkg_data['name']}-{pkg_data['version']}-{pkg_data['release']}.{pkg_data['arch']}"
            pkg_uri = URIRef(f"{RPM}{quote(pkg_id)}")
            pkg_map[pkg_data['pkgid']] = pkg_uri
        return pkg_map
    
    def _process_filelists_parallel(self, pkg_map):
        """Process filelists metadata in parallel."""
        filelists_url = self._get_metadata_url('filelists')
        if not filelists_url:
            return
        
        content = self._download_and_decompress(filelists_url)
        file_root = ET.fromstring(content)
        file_ns = {'filelists': 'http://linux.duke.edu/metadata/filelists'}
        packages = file_root.findall('filelists:package', file_ns)
        
        # Convert to serializable data
        filelists_data = []
        for pkg in packages:
            pkgid = pkg.get('pkgid')
            files = [file_entry.text for file_entry in pkg.findall('filelists:file', file_ns) if file_entry.text]
            if pkgid and files:
                filelists_data.append({'pkgid': pkgid, 'files': files})
        
        # Process in parallel
        self.collect_parallel(
            [(data, pkg_map) for data in filelists_data],
            RpmCollector._process_filelists_chunk_wrapper
        )
    
    def _process_other_parallel(self, pkg_map):
        """Process other metadata in parallel."""
        other_url = self._get_metadata_url('other')
        if not other_url:
            return
        
        content = self._download_and_decompress(other_url)
        other_root = ET.fromstring(content)
        other_ns = {'other': 'http://linux.duke.edu/metadata/other'}
        packages = other_root.findall('other:package', other_ns)
        
        # Convert to serializable data
        other_data = []
        for pkg in packages:
            pkgid = pkg.get('pkgid')
            changelogs = []
            for changelog in pkg.findall('other:changelog', other_ns):
                cl_data = {
                    'text': changelog.text,
                    'author': changelog.get('author'),
                    'date': changelog.get('date')
                }
                changelogs.append(cl_data)
            if pkgid and changelogs:
                other_data.append({'pkgid': pkgid, 'changelogs': changelogs})
        
        # Process in parallel
        self.collect_parallel(
            [(data, pkg_map) for data in other_data],
            RpmCollector._process_other_chunk_wrapper
        )
    
    @staticmethod
    def _process_filelists_chunk_wrapper(data_chunk, chunk_id):
        """Wrapper for parallel processing of filelists chunks."""
        filelists_data = [item[0] for item in data_chunk]
        pkg_map = data_chunk[0][1]
        return RpmCollector._process_filelists_chunk(filelists_data, chunk_id, pkg_map)
    
    @staticmethod
    def _process_other_chunk_wrapper(data_chunk, chunk_id):
        """Wrapper for parallel processing of other chunks."""
        other_data = [item[0] for item in data_chunk]
        pkg_map = data_chunk[0][1]
        return RpmCollector._process_other_chunk(other_data, chunk_id, pkg_map)

    @staticmethod
    def _process_package_chunk(packages_chunk, chunk_id):
        """Process a chunk of packages in a separate process."""
        import tempfile
        from rdflib import Graph, URIRef, Literal, BNode
        from rdflib.namespace import RDF, RDFS
        from urllib.parse import quote
        import xml.etree.ElementTree as ET
        
        chunk_graph = Graph()
        RPM = "http://packagegraph.github.io/ontology/rpm#"
        
        for pkg_data in packages_chunk:
            pkg_id = f"{pkg_data['name']}-{pkg_data['version']}-{pkg_data['release']}.{pkg_data['arch']}"
            pkg_uri = URIRef(f"{RPM}{quote(pkg_id)}")
            
            chunk_graph.add((pkg_uri, RDF.type, URIRef(f"{RPM}RpmPackage")))
            chunk_graph.add((pkg_uri, URIRef(f"{RPM}name"), Literal(pkg_data['name'])))
            chunk_graph.add((pkg_uri, URIRef(f"{RPM}version"), Literal(pkg_data['version'])))
            chunk_graph.add((pkg_uri, URIRef(f"{RPM}release"), Literal(pkg_data['release'])))
            chunk_graph.add((pkg_uri, URIRef(f"{RPM}arch"), Literal(pkg_data['arch'])))
            
            if pkg_data['summary']:
                chunk_graph.add((pkg_uri, URIRef(f"{RPM}summary"), Literal(pkg_data['summary'])))
            if pkg_data['description']:
                chunk_graph.add((pkg_uri, URIRef(f"{RPM}description"), Literal(pkg_data['description'])))
            
            # Process dependencies from format_element if available
            if pkg_data['format_element'] is not None:
                ns = {'rpm': 'http://linux.duke.edu/metadata/rpm'}
                for dep_entry in pkg_data['format_element'].findall('rpm:requires/rpm:entry', ns):
                    dep_bnode = BNode()
                    chunk_graph.add((pkg_uri, URIRef(f"{RPM}requires"), dep_bnode))
                    if dep_entry.get('name'):
                        chunk_graph.add((dep_bnode, URIRef(f"{RPM}dependencyName"), Literal(dep_entry.get('name'))))
                    if dep_entry.get('ver'):
                        chunk_graph.add((dep_bnode, URIRef(f"{RPM}dependencyVersion"), Literal(dep_entry.get('ver'))))
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=f'_rpm_chunk_{chunk_id}.ttl', delete=False)
        chunk_graph.serialize(destination=temp_file.name, format='turtle')
        temp_file.close()
        return temp_file.name
    
    @staticmethod
    def _process_filelists_chunk(filelists_chunk, chunk_id, pkg_map):
        """Process a chunk of filelists data in a separate process."""
        import tempfile
        from rdflib import Graph, URIRef, Literal
        
        chunk_graph = Graph()
        RPM = "http://packagegraph.github.io/ontology/rpm#"
        
        for pkg_data in filelists_chunk:
            pkgid = pkg_data['pkgid']
            if pkgid in pkg_map:
                pkg_uri = pkg_map[pkgid]
                for filename in pkg_data['files']:
                    chunk_graph.add((pkg_uri, URIRef(f"{RPM}fileName"), Literal(filename)))
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=f'_rpm_filelists_chunk_{chunk_id}.ttl', delete=False)
        chunk_graph.serialize(destination=temp_file.name, format='turtle')
        temp_file.close()
        return temp_file.name
    
    @staticmethod
    def _process_other_chunk(other_chunk, chunk_id, pkg_map):
        """Process a chunk of other metadata in a separate process."""
        import tempfile
        from rdflib import Graph, URIRef, Literal, BNode
        from rdflib.namespace import RDF, RDFS
        
        chunk_graph = Graph()
        RPM = "http://packagegraph.github.io/ontology/rpm#"
        
        for pkg_data in other_chunk:
            pkgid = pkg_data['pkgid']
            if pkgid in pkg_map:
                pkg_uri = pkg_map[pkgid]
                for cl_data in pkg_data['changelogs']:
                    cl_bnode = BNode()
                    chunk_graph.add((pkg_uri, URIRef(f"{RPM}hasChangelog"), cl_bnode))
                    chunk_graph.add((cl_bnode, RDF.type, URIRef(f"{RPM}Changelog")))
                    if cl_data['text']:
                        chunk_graph.add((cl_bnode, URIRef(f"{RPM}changelogText"), Literal(cl_data['text'])))
                    if cl_data['author']:
                        chunk_graph.add((cl_bnode, URIRef(f"{RPM}changelogAuthor"), Literal(cl_data['author'])))
                    if cl_data['date']:
                        chunk_graph.add((cl_bnode, URIRef(f"{RPM}changelogTime"), Literal(cl_data['date'], datatype=RDFS.Literal)))
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=f'_rpm_other_chunk_{chunk_id}.ttl', delete=False)
        chunk_graph.serialize(destination=temp_file.name, format='turtle')
        temp_file.close()
        return temp_file.name
