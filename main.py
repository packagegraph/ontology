import sys
from pathlib import Path
import click
from rdflib import Graph

try:
    import rdf2g
    from tqdm import tqdm
except ImportError:
    rdf2g = None
    tqdm = None

from packagegraph.checker import run_check
from packagegraph.debian_collector import DebianCollector
from packagegraph.rpm_collector import RpmCollector
from packagegraph.profiler import profiler

@click.group()
def cli():
    """A CLI for managing and inspecting the package graph ontology."""
    pass

@cli.command()
def check():
    """Run the complete test suite for the ontology."""
    if not run_check():
        sys.exit(1)

@cli.command()
@click.argument('repo_url')
@click.option('--repo-type', type=click.Choice(['debian', 'rpm'], case_sensitive=False), default='debian', help="Type of the repository.")
@click.option('--distribution', '-d', default='stable', help="[Debian] The distribution to collect (e.g., stable, bookworm).")
@click.option('--component', default='main', help="[Debian] The component to collect (e.g., main).")
@click.option('--arch', default='binary-amd64', help="[Debian] The architecture to collect.")
@click.option('--output-file', '-o', help="Path to save the graph to.")
@click.option('--input-file', '-i', help="Path to an existing graph to load.")
@click.option('--parallel/--no-parallel', default=True, help="Enable parallel processing.")
@click.option('--chunk-size', default=1000, help="Number of packages per chunk for parallel processing.")
@click.option('--workers', default=4, help="Number of worker processes.")
@click.option('--profile/--no-profile', default=False, help="Enable detailed timing profiling.")
def collect(repo_url, repo_type, distribution, component, arch, output_file, input_file, parallel, chunk_size, workers, profile):
    """Downloads package information from a repository and creates a linked data graph."""
    
    # Enable profiling if requested
    profiler.enabled = profile
    
    with profiler.step("Total Collection Time"):
        g = Graph()
        
        if input_file and Path(input_file).exists():
            with profiler.step("Load Existing Graph"):
                click.echo(f"Loading existing graph from {input_file}")
                g.parse(input_file)
                click.echo(f"Loaded {len(g)} triples.")

        try:
            with profiler.step("Initialize Collector"):
                if repo_type == 'debian':
                    collector = DebianCollector(g, repo_url, distribution, component, arch, parallel, chunk_size, workers)
                elif repo_type == 'rpm':
                    collector = RpmCollector(g, repo_url, parallel, chunk_size, workers)
            
            with profiler.step("Collect Package Data"):
                parsed_count = collector.collect()
            
            click.echo(f"Successfully processed {parsed_count} packages.")
            click.echo(f"Graph now contains {len(g)} triples.")
            
            if output_file:
                with profiler.step("Serialize Graph"):
                    click.echo(f"Serializing graph to {output_file}")
                    g.serialize(destination=output_file, format='turtle')
                    click.echo("Graph saved.")

        except Exception as e:
            click.echo(f"An unexpected error occurred: {e}", err=True)
            sys.exit(1)
    
    # Print profiling summary
    profiler.print_summary()

@cli.command()
@click.option('--input-dir', '-i', default='.', help="Directory containing TTL files to process.")
@click.option('--output-file', '-o', required=True, help="Path to save the consolidated N-Triples file.")
def convert(input_dir, output_file):
    """Consolidates, links, and de-duplicates TTL files into a single N-Triples file for bulk loading."""
    
    g = Graph()
    input_path = Path(input_dir)
    
    if not input_path.is_dir():
        click.echo(f"Error: Input directory '{input_dir}' not found.", err=True)
        sys.exit(1)
        
    click.echo(f"Searching for .ttl files in {input_path.resolve()}...")
    
    ttl_files = list(input_path.rglob('*.ttl'))
    
    if not ttl_files:
        click.echo("No .ttl files found.", err=True)
        sys.exit(0)
        
    click.echo(f"Found {len(ttl_files)} files to consolidate.")
    
    for ttl_file in ttl_files:
        click.echo(f"  -> Loading {ttl_file}")
        try:
            g.parse(ttl_file, format='turtle')
        except Exception as e:
            click.echo(f"    Warning: Could not parse {ttl_file}. Error: {e}", err=True)
            
    click.echo(f"Consolidated graph contains {len(g)} triples.")
    
    click.echo(f"Serializing to N-Triples format at {output_file}...")
    g.serialize(destination=output_file, format='nt')
    
    click.echo("Conversion complete.")

if __name__ == "__main__":
    cli()
