#!/usr/bin/env python3
"""Generate SHACL shapes for classes that lack them."""
import sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS

OWL = Namespace("http://www.w3.org/2002/07/owl#")
SH = Namespace("http://www.w3.org/ns/shacl#")

# VCS shapes to add
VCS_SHAPES = """
vcs:BranchShape a sh:NodeShape ;
    sh:property [ sh:datatype xsd:string ;
            sh:minCount 1 ; sh:maxCount 1 ;
            sh:message "A branch must have exactly one branch name."@en ;
            sh:path vcs:branchName ] ;
    sh:targetClass vcs:Branch .

vcs:TagShape a sh:NodeShape ;
    sh:property [ sh:datatype xsd:string ;
            sh:minCount 1 ; sh:maxCount 1 ;
            sh:message "A tag must have exactly one tag name."@en ;
            sh:path vcs:tagName ] ;
    sh:targetClass vcs:Tag .

vcs:ReleaseShape a sh:NodeShape ;
    sh:property [ sh:datatype xsd:dateTime ;
            sh:message "A release should have a release date."@en ;
            sh:path vcs:releaseDate ] ;
    sh:targetClass vcs:Release .

vcs:RepositoryShape a sh:NodeShape ;
    sh:property [ sh:datatype xsd:anyURI ;
            sh:message "A repository should have a repository URL."@en ;
            sh:path vcs:repositoryURL ] ;
    sh:targetClass vcs:Repository .

vcs:PullRequestShape a sh:NodeShape ;
    sh:property [ sh:datatype xsd:string ;
            sh:minCount 1 ;
            sh:message "A pull request must have at least one label."@en ;
            sh:path rdfs:label ] ;
    sh:targetClass vcs:PullRequest .

vcs:IssueShape a sh:NodeShape ;
    sh:property [ sh:datatype xsd:string ;
            sh:minCount 1 ;
            sh:message "An issue must have at least one label."@en ;
            sh:path rdfs:label ] ;
    sh:targetClass vcs:Issue .
"""

# SLSA shape
SLSA_SHAPES = """
slsa:BuildLevelShape a sh:NodeShape ;
    sh:property [ sh:datatype xsd:string ;
            sh:minCount 1 ;
            sh:message "A build level must have at least one label."@en ;
            sh:path rdfs:label ] ;
    sh:targetClass slsa:BuildLevel .
"""

# DQ shape
DQ_SHAPES = """@prefix dq: <https://purl.org/packagegraph/ontology/dq#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

dq:DataQualityIssueShape a sh:NodeShape ;
    sh:property [ sh:datatype xsd:string ;
            sh:minCount 1 ;
            sh:message "A data quality issue must have at least one label."@en ;
            sh:path rdfs:label ] ;
    sh:targetClass dq:DataQualityIssue .
"""

def append_shapes(file_path: Path, shapes_text: str):
    content = file_path.read_text()
    # Remove trailing whitespace/newlines
    content = content.rstrip()
    # Append shapes
    file_path.write_text(content + "\n\n" + shapes_text.strip() + "\n")
    print(f"✓ {file_path}")

# Add VCS shapes
append_shapes(Path("extensions/vcs/vcs.shacl.ttl"), VCS_SHAPES)

# Add SLSA shape
append_shapes(Path("extensions/slsa/slsa.shacl.ttl"), SLSA_SHAPES)

# Create DQ SHACL file
Path("extensions/dq/dq.shacl.ttl").write_text(DQ_SHAPES)
print("✓ extensions/dq/dq.shacl.ttl (created)")

print("\nDone - added 8 shapes across 3 modules")
