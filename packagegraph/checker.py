# Ontology validation utilities.
# ETL collectors (debian, rpm) have moved to https://github.com/packagegraph/platform

from pathlib import Path
from rdflib import Graph

def find_ttl_files():
    """Find all .ttl files in the current directory."""
    return list(Path('.').glob('*.ttl'))

def validate_ttl_file(file_path):
    """Validate a single TTL file and return validation results."""
    results = {'file': str(file_path), 'valid': False, 'triples_count': 0, 'errors': [], 'warnings': []}
    try:
        g = Graph()
        g.parse(file_path, format='turtle')
        results['valid'] = True
        results['triples_count'] = len(g)
        if results['triples_count'] == 0:
            results['warnings'].append("File contains no triples")
    except Exception as e:
        results['errors'].append(f"Unexpected error: {str(e)}")
    return results

def run_check():
    """Run the complete test suite for the ontology."""
    import click
    click.echo("🧪 Running Ontology Test Suite")
    click.echo("=" * 50)
    
    ttl_files = find_ttl_files()
    if not ttl_files:
        click.echo("❌ No TTL files found!")
        return False
    
    all_valid = True
    for file_path in ttl_files:
        result = validate_ttl_file(file_path)
        status = "✅" if result['valid'] else "❌"
        click.echo(f"{status} {result['file']}: {result['triples_count']} triples")
        if not result['valid']:
            all_valid = False
            for error in result['errors']:
                click.echo(f"   🚨 {error}")
    
    click.echo("\n" + "=" * 50)
    if all_valid:
        click.echo("🎉 All individual files are valid.")
    else:
        click.echo("❌ Some files failed validation.")

    # SHACL Validation
    if Path('shacl.ttl').exists():
        click.echo("\n🔍 Running SHACL Validation (using shacl.ttl)")
        try:
            from pyshacl import validate
            combined_g = Graph()
            for file_path in ttl_files:
                if file_path.name not in ['shacl.ttl', 'x.ttl']:
                    combined_g.parse(file_path, format='turtle')
            
            shacl_g = Graph()
            shacl_g.parse('shacl.ttl', format='turtle')
            
            conforms, results_graph, results_text = validate(
                combined_g,
                shacl_graph=shacl_g,
                inference='rdfs',
                serialize_report_graph=False
            )
            
            if conforms:
                click.echo("✅ SHACL validation successful! Data conforms to shapes.")
            else:
                click.echo("❌ SHACL validation failed!")
                click.echo(results_text)
                all_valid = False
        except ImportError:
            click.echo("⚠ pyshacl not installed, skipping SHACL validation.")
            click.echo("  Install with: uv add pyshacl")
        except Exception as e:
            click.echo(f"🚨 SHACL validation error: {str(e)}")
            all_valid = False

    return all_valid

if __name__ == "__main__":
    import sys
    if not run_check():
        sys.exit(1)
