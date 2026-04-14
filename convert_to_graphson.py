import click
from rdflib import Graph, URIRef, Literal
import json
from tqdm import tqdm

def convert_rdf_to_graphson(input_file, output_file):
    """Converts an N-Triples file to GraphSON format for TinkerPop bulk loading."""
    
    g = Graph()
    click.echo(f"Parsing RDF data from {input_file}...")
    g.parse(input_file, format='nt')
    click.echo(f"Found {len(g)} triples.")

    vertices = {}
    edges = []
    vertex_id_counter = 0

    click.echo("Processing triples and building in-memory graph...")
    
    # First pass: create all vertices
    all_nodes = set(g.subjects()) | set(g.objects(predicate=None, unique=True))
    for node in tqdm(all_nodes, desc="Creating Vertices"):
        if isinstance(node, URIRef):
            if node not in vertices:
                vertices[node] = {
                    "id": vertex_id_counter,
                    "label": "vertex",
                    "properties": {
                        "uri": [{"id": f"{vertex_id_counter}-uri", "value": str(node)}]
                    }
                }
                vertex_id_counter += 1

    # Second pass: create edges and add literal properties
    for s, p, o in tqdm(g, desc="Creating Edges & Properties"):
        if s in vertices:
            source_vertex = vertices[s]
            
            # Get the short name for the property/edge label
            prop_name = p.split('#')[-1] if '#' in p else p.split('/')[-1]

            if isinstance(o, Literal):
                # It's a property of the source vertex
                if prop_name not in source_vertex["properties"]:
                    source_vertex["properties"][prop_name] = []
                
                prop_id = f"{source_vertex['id']}-{prop_name}-{len(source_vertex['properties'][prop_name])}"
                source_vertex["properties"][prop_name].append({"id": prop_id, "value": str(o)})

            elif isinstance(o, URIRef) and o in vertices:
                # It's an edge to another vertex
                target_vertex = vertices[o]
                
                edges.append({
                    "id": f"{source_vertex['id']}-{prop_name}-{target_vertex['id']}",
                    "label": prop_name,
                    "inV": target_vertex["id"],
                    "outV": source_vertex["id"]
                })

    click.echo(f"Writing {len(vertices)} vertices and {len(edges)} edges to {output_file}...")
    with open(output_file, 'w') as f:
        for vertex in tqdm(vertices.values(), desc="Writing Vertices"):
            f.write(json.dumps(vertex) + '\n')
        for edge in tqdm(edges, desc="Writing Edges"):
            f.write(json.dumps(edge) + '\n')
            
    click.echo("GraphSON conversion complete.")

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def main(input_file, output_file):
    """Converts a consolidated N-Triples file to GraphSON for TinkerPop."""
    convert_rdf_to_graphson(input_file, output_file)

if __name__ == '__main__':
    main()
