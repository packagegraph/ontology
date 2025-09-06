import os
import sys
from pathlib import Path
from rdflib import Graph, Namespace, URIRef
from rdflib.exceptions import ParserError
import traceback

def find_ttl_files():
    """Find all .ttl files in the current directory."""
    return list(Path('.').glob('*.ttl'))

def validate_ttl_file(file_path):
    """Validate a single TTL file and return validation results."""
    results = {
        'file': str(file_path),
        'valid': False,
        'triples_count': 0,
        'errors': [],
        'warnings': []
    }
    
    try:
        g = Graph()
        g.parse(file_path, format='turtle')
        results['valid'] = True
        results['triples_count'] = len(g)
        
        # Check for common issues
        if results['triples_count'] == 0:
            results['warnings'].append("File contains no triples")
            
    except ParserError as e:
        results['errors'].append(f"Parser error: {str(e)}")
    except Exception as e:
        results['errors'].append(f"Unexpected error: {str(e)}")
    
    return results

def test_ontology_consistency():
    """Test that all TTL files can be loaded together without conflicts."""
    combined_graph = Graph()
    loaded_files = []
    errors = []
    
    ttl_files = find_ttl_files()
    
    for file_path in ttl_files:
        try:
            combined_graph.parse(file_path, format='turtle')
            loaded_files.append(str(file_path))
        except Exception as e:
            errors.append(f"Failed to load {file_path}: {str(e)}")
    
    return {
        'loaded_files': loaded_files,
        'total_triples': len(combined_graph),
        'errors': errors,
        'success': len(errors) == 0
    }

def test_namespace_definitions():
    """Test that namespace prefixes are properly defined."""
    results = []
    ttl_files = find_ttl_files()
    
    for file_path in ttl_files:
        try:
            g = Graph()
            g.parse(file_path, format='turtle')
            
            # Get all namespaces defined in the file
            namespaces = list(g.namespaces())
            
            results.append({
                'file': str(file_path),
                'namespaces': [(prefix, str(namespace)) for prefix, namespace in namespaces],
                'namespace_count': len(namespaces)
            })
        except Exception as e:
            results.append({
                'file': str(file_path),
                'error': str(e),
                'namespaces': [],
                'namespace_count': 0
            })
    
    return results

def test_class_and_property_definitions():
    """Test for proper class and property definitions."""
    from rdflib import RDF, RDFS, OWL
    
    combined_graph = Graph()
    ttl_files = find_ttl_files()
    
    # Load all files into combined graph
    for file_path in ttl_files:
        try:
            combined_graph.parse(file_path, format='turtle')
        except:
            continue
    
    # Find classes and properties
    classes = list(combined_graph.subjects(RDF.type, RDFS.Class)) + \
              list(combined_graph.subjects(RDF.type, OWL.Class))
    
    properties = list(combined_graph.subjects(RDF.type, RDF.Property)) + \
                 list(combined_graph.subjects(RDF.type, OWL.ObjectProperty)) + \
                 list(combined_graph.subjects(RDF.type, OWL.DatatypeProperty))
    
    return {
        'classes': [str(cls) for cls in classes],
        'properties': [str(prop) for prop in properties],
        'class_count': len(classes),
        'property_count': len(properties)
    }

def run_test_suite():
    """Run the complete test suite."""
    print("🧪 Running Ontology Test Suite")
    print("=" * 50)
    
    # Test 1: Individual file validation
    print("\n📁 Test 1: Individual TTL File Validation")
    print("-" * 40)
    
    ttl_files = find_ttl_files()
    if not ttl_files:
        print("❌ No TTL files found!")
        return False
    
    all_valid = True
    total_triples = 0
    
    for file_path in ttl_files:
        result = validate_ttl_file(file_path)
        status = "✅" if result['valid'] else "❌"
        print(f"{status} {result['file']}: {result['triples_count']} triples")
        
        if result['errors']:
            for error in result['errors']:
                print(f"   🚨 {error}")
            all_valid = False
        
        if result['warnings']:
            for warning in result['warnings']:
                print(f"   ⚠️  {warning}")
        
        total_triples += result['triples_count']
    
    print(f"\nTotal triples across all files: {total_triples}")
    
    # Test 2: Combined loading consistency
    print("\n🔗 Test 2: Combined Loading Consistency")
    print("-" * 40)
    
    consistency_result = test_ontology_consistency()
    if consistency_result['success']:
        print(f"✅ All files loaded successfully")
        print(f"   📊 Combined graph: {consistency_result['total_triples']} triples")
        print(f"   📁 Files loaded: {len(consistency_result['loaded_files'])}")
    else:
        print("❌ Consistency test failed:")
        for error in consistency_result['errors']:
            print(f"   🚨 {error}")
        all_valid = False
    
    # Test 3: Namespace definitions
    print("\n🏷️  Test 3: Namespace Definitions")
    print("-" * 40)
    
    namespace_results = test_namespace_definitions()
    for result in namespace_results:
        if 'error' in result:
            print(f"❌ {result['file']}: {result['error']}")
            all_valid = False
        else:
            print(f"✅ {result['file']}: {result['namespace_count']} namespaces")
            for prefix, uri in result['namespaces']:
                print(f"   📎 {prefix}: {uri}")
    
    # Test 4: Class and property definitions
    print("\n🏗️  Test 4: Class and Property Definitions")
    print("-" * 40)
    
    definitions = test_class_and_property_definitions()
    print(f"✅ Found {definitions['class_count']} classes")
    print(f"✅ Found {definitions['property_count']} properties")
    
    if definitions['classes']:
        print("\n📋 Classes:")
        for cls in sorted(definitions['classes']):
            print(f"   🏷️  {cls}")
    
    if definitions['properties']:
        print("\n📋 Properties:")
        for prop in sorted(definitions['properties']):
            print(f"   🔗 {prop}")
    
    # Final result
    print("\n" + "=" * 50)
    if all_valid:
        print("🎉 All tests passed! Ontology is valid.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

def main():
    """Main entry point."""
    success = run_test_suite()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
