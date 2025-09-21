from abc import ABC, abstractmethod
import tempfile
import os
from concurrent.futures import ProcessPoolExecutor
from rdflib import Graph

class BaseCollector(ABC):
    """Abstract base class for repository collectors."""

    def __init__(self, g, repo_url, parallel=True, chunk_size=1000, workers=4):
        self.g = g
        self.repo_url = repo_url
        self.parallel = parallel
        self.chunk_size = chunk_size
        self.workers = workers

    @abstractmethod
    def collect(self):
        """
        The main method to collect data from the repository and add it to the graph.
        This method must be implemented by subclasses.
        """
        pass

    def collect_parallel(self, packages, process_chunk_func):
        """Generic parallel processing for any package format."""
        if not self.parallel or len(packages) < self.chunk_size:
            from .profiler import profiler
            profiler.log(f"Using single-threaded processing (parallel={self.parallel}, packages={len(packages)}, chunk_size={self.chunk_size})")
            # For single-threaded processing, we'll process directly without chunking
            # The caller should handle this case separately
            return len(packages)
        
        from .profiler import profiler
        profiler.log(f"Using parallel processing with {self.workers} workers, {len(packages)} packages, chunk_size={self.chunk_size}")
        
        chunks = [packages[i:i+self.chunk_size] for i in range(0, len(packages), self.chunk_size)]
        temp_files = []
        
        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            futures = [executor.submit(process_chunk_func, chunk, i) for i, chunk in enumerate(chunks)]
            for future in futures:
                temp_file = future.result()
                if temp_file:
                    temp_files.append(temp_file)
        
        # Merge temp files into main graph
        for temp_file in temp_files:
            self.g.parse(temp_file, format='turtle')
            os.unlink(temp_file)
        
        return len(packages)

    @staticmethod
    def merge_turtle_files(temp_files, output_file):
        """Efficiently merge multiple turtle files without loading into memory."""
        with open(output_file, 'w') as outf:
            for i, temp_file in enumerate(temp_files):
                with open(temp_file, 'r') as inf:
                    if i > 0:
                        # Skip prefixes after first file
                        for line in inf:
                            if not line.startswith('@prefix') and line.strip():
                                outf.write(line)
                                break
                        # Copy rest of file
                        outf.writelines(inf)
                    else:
                        outf.writelines(inf)
                os.unlink(temp_file)

    @staticmethod
    def create_chunk_graph(repo_url):
        """Create a new graph for chunk processing."""
        return Graph()

    def save_chunk_to_temp(self, chunk_graph, chunk_id):
        """Save a chunk graph to temporary file."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=f'_chunk_{chunk_id}.ttl', delete=False)
        chunk_graph.serialize(destination=temp_file.name, format='turtle')
        temp_file.close()
        return temp_file.name
