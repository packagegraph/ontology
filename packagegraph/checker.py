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
        return True
    else:
        click.echo("❌ Some files failed validation.")
        return False
