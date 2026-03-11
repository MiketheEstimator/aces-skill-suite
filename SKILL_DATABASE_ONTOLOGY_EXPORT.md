---
name: SKILL_DATABASE_ONTOLOGY_EXPORT
description: "Semantic web graph creation and taxonomic definitions. Use when producing .owl, .rdf, .ttl (Turtle), or .n3 files for knowledge graphs, taxonomies, linked data, or ontology-based data exchange. Triggers: 'OWL', 'RDF', 'ontology', '.owl file', '.ttl file', 'Turtle RDF', 'knowledge graph', 'semantic web', 'taxonomy', 'linked data'."
---

# SKILL_DATABASE_ONTOLOGY_EXPORT — OWL / RDF Ontology Skill

## Quick Reference

| Task | Section |
|------|---------|
| Format overview | [Format Overview](#format-overview) |
| Turtle (.ttl) syntax | [Turtle Syntax](#turtle-syntax) |
| OWL class hierarchy | [OWL Classes & Properties](#owl-classes--properties) |
| Python (rdflib) | [Python Integration](#python-integration) |
| SPARQL queries | [SPARQL Queries](#sparql-queries) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Format Overview

| Format | Extension | Notes |
|--------|-----------|-------|
| Turtle | `.ttl` | Human-readable; preferred for hand-authoring |
| RDF/XML | `.rdf`, `.owl` | XML-based; tool interchange standard |
| N-Triples | `.nt` | One triple per line; simple streaming |
| JSON-LD | `.jsonld` | JSON-compatible linked data |
| N3 | `.n3` | Notation3; superset of Turtle |

**Recommendation:** Author in Turtle (`.ttl`); export to RDF/XML (`.owl`) for OWL-based tools.

---

## Turtle Syntax

### Base Structure

```turtle
# Prefixes
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix ex:   <https://example.com/ontology#> .

# Ontology declaration
<https://example.com/ontology>
    a owl:Ontology ;
    rdfs:label "Example Ontology"@en ;
    owl:versionInfo "1.0.0" .
```

### Triples

```turtle
# Basic triple: Subject — Predicate — Object
ex:Alice  rdf:type   ex:Person .
ex:Alice  ex:hasName "Alice Smith"^^xsd:string .
ex:Alice  ex:age     30^^xsd:integer .

# Semicolon shorthand (same subject, multiple predicates)
ex:Alice
    a              ex:Person ;
    ex:hasName     "Alice Smith" ;
    ex:age         30 ;
    ex:worksFor    ex:AcmeCorp .

# Comma shorthand (same subject + predicate, multiple objects)
ex:Alice ex:hasRole ex:Architect, ex:ProjectLead .

# Blank nodes
ex:Alice ex:hasAddress [
    ex:street "123 Main St" ;
    ex:city   "London" ;
    ex:country "UK"
] .
```

### Data Types

```turtle
"plain string"
"English string"@en
"German string"@de
42^^xsd:integer
3.14^^xsd:decimal
true^^xsd:boolean
"2024-03-15"^^xsd:date
"2024-03-15T14:30:00Z"^^xsd:dateTime
```

---

## OWL Classes & Properties

### Class Hierarchy

```turtle
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix aec:  <https://example.com/aec-ontology#> .

# ── Classes ──────────────────────────────────────────────────────────────────

aec:Asset
    a owl:Class ;
    rdfs:label "Asset"@en ;
    rdfs:comment "A physical or virtual asset in a construction project."@en .

aec:Space
    a owl:Class ;
    rdfs:subClassOf aec:Asset ;
    rdfs:label "Space"@en .

aec:BuildingElement
    a owl:Class ;
    rdfs:subClassOf aec:Asset ;
    rdfs:label "Building Element"@en .

aec:StructuralElement
    a owl:Class ;
    rdfs:subClassOf aec:BuildingElement ;
    rdfs:label "Structural Element"@en .

aec:Beam
    a owl:Class ;
    rdfs:subClassOf aec:StructuralElement ;
    rdfs:label "Beam"@en .

aec:Column
    a owl:Class ;
    rdfs:subClassOf aec:StructuralElement ;
    rdfs:label "Column"@en .

aec:Project
    a owl:Class ;
    rdfs:label "Project"@en .

# ── Object Properties ─────────────────────────────────────────────────────────

aec:containsElement
    a owl:ObjectProperty ;
    rdfs:label "contains element"@en ;
    rdfs:domain aec:Project ;
    rdfs:range  aec:Asset .

aec:locatedIn
    a owl:ObjectProperty ;
    rdfs:label "located in"@en ;
    rdfs:domain aec:BuildingElement ;
    rdfs:range  aec:Space ;
    owl:inverseOf aec:contains .

aec:connectedTo
    a owl:ObjectProperty, owl:SymmetricProperty ;
    rdfs:label "connected to"@en ;
    rdfs:domain aec:BuildingElement ;
    rdfs:range  aec:BuildingElement .

# ── Datatype Properties ────────────────────────────────────────────────────────

aec:hasIFCGuid
    a owl:DatatypeProperty, owl:FunctionalProperty ;
    rdfs:label "IFC GUID"@en ;
    rdfs:domain aec:Asset ;
    rdfs:range  xsd:string .

aec:hasLength
    a owl:DatatypeProperty ;
    rdfs:label "length (m)"@en ;
    rdfs:domain aec:Beam ;
    rdfs:range  xsd:decimal .

aec:hasStatus
    a owl:DatatypeProperty ;
    rdfs:label "status"@en ;
    rdfs:domain aec:Asset ;
    rdfs:range  xsd:string .

# ── Individuals ────────────────────────────────────────────────────────────────

aec:Project_2401
    a aec:Project ;
    rdfs:label "Project 2401 — Office Tower"@en ;
    aec:hasStatus "Active" .

aec:Beam_B001
    a aec:Beam ;
    rdfs:label "Steel Beam B001"@en ;
    aec:hasIFCGuid "3D8ZkKnZH9fBzRi_l8kIaA" ;
    aec:hasLength 6.0 ;
    aec:hasStatus "Installed" .

aec:Project_2401 aec:containsElement aec:Beam_B001 .
```

---

## Python Integration

```bash
pip install rdflib
```

### Create Graph and Write Files

```python
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD
from pathlib import Path

# Namespaces
AEC = Namespace("https://example.com/aec-ontology#")

def build_graph() -> Graph:
    g = Graph()

    # Bind prefixes (appears in serialisation)
    g.bind("rdf",  RDF)
    g.bind("rdfs", RDFS)
    g.bind("owl",  OWL)
    g.bind("xsd",  XSD)
    g.bind("aec",  AEC)

    # Ontology declaration
    ontology_uri = URIRef("https://example.com/aec-ontology")
    g.add((ontology_uri, RDF.type, OWL.Ontology))
    g.add((ontology_uri, RDFS.label, Literal("AEC Ontology", lang="en")))

    # Class
    g.add((AEC.BuildingElement, RDF.type,         OWL.Class))
    g.add((AEC.BuildingElement, RDFS.label,       Literal("Building Element", lang="en")))
    g.add((AEC.Beam,            RDF.type,         OWL.Class))
    g.add((AEC.Beam,            RDFS.subClassOf,  AEC.BuildingElement))

    # Datatype property
    g.add((AEC.hasIFCGuid, RDF.type,    OWL.DatatypeProperty))
    g.add((AEC.hasIFCGuid, RDFS.domain, AEC.BuildingElement))
    g.add((AEC.hasIFCGuid, RDFS.range,  XSD.string))

    # Individual
    beam = AEC.Beam_B001
    g.add((beam, RDF.type,        AEC.Beam))
    g.add((beam, RDFS.label,      Literal("Beam B001", lang="en")))
    g.add((beam, AEC.hasIFCGuid,  Literal("3D8ZkKnZH9fBzRi_l8kIaA", datatype=XSD.string)))
    g.add((beam, AEC.hasLength,   Literal(6.0, datatype=XSD.decimal)))

    return g


def save_graph(g: Graph, base_path: str) -> None:
    """Save graph in multiple formats."""
    # Turtle (human-readable)
    g.serialize(f"{base_path}.ttl", format="turtle")
    print(f"Written: {base_path}.ttl")

    # RDF/XML (OWL tools)
    g.serialize(f"{base_path}.owl", format="xml")
    print(f"Written: {base_path}.owl")

    # JSON-LD
    g.serialize(f"{base_path}.jsonld", format="json-ld", indent=2)
    print(f"Written: {base_path}.jsonld")

    # N-Triples (simple streaming format)
    g.serialize(f"{base_path}.nt", format="nt")
    print(f"Written: {base_path}.nt")


g = build_graph()
print(f"Total triples: {len(g)}")
save_graph(g, "aec_ontology")
```

### Load and Query

```python
from rdflib import Graph
from rdflib.namespace import RDF, RDFS

g = Graph()
g.parse("aec_ontology.ttl", format="turtle")

# All triples
for subj, pred, obj in g:
    print(f"{subj} | {pred} | {obj}")

# Subjects of a specific type
for beam in g.subjects(RDF.type, AEC.Beam):
    label = g.value(beam, RDFS.label)
    guid  = g.value(beam, AEC.hasIFCGuid)
    print(f"Beam: {label} — GUID: {guid}")
```

---

## SPARQL Queries

```python
from rdflib import Graph

g = Graph()
g.parse("aec_ontology.ttl")

# Basic SELECT
results = g.query("""
    PREFIX aec:  <https://example.com/aec-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?element ?label ?guid
    WHERE {
        ?element a aec:Beam ;
                 rdfs:label ?label ;
                 aec:hasIFCGuid ?guid .
    }
    ORDER BY ?label
""")

for row in results:
    print(f"{row.label} — {row.guid}")

# CONSTRUCT (build new graph from pattern)
new_graph = g.query("""
    PREFIX aec: <https://example.com/aec-ontology#>

    CONSTRUCT { ?e aec:hasIFCGuid ?guid }
    WHERE     { ?e a aec:Beam ; aec:hasIFCGuid ?guid }
""")

# ASK (boolean check)
has_beams = bool(g.query("""
    PREFIX aec: <https://example.com/aec-ontology#>
    ASK { ?e a aec:Beam }
"""))
print(f"Graph has beams: {has_beams}")
```

---

## Validation & QA

```bash
# Validate Turtle syntax
pip install rdflib

python3 -c "
from rdflib import Graph
g = Graph()
g.parse('ontology.ttl', format='turtle')
print(f'PASS: {len(g)} triples loaded')
"

# OWL reasoning / consistency check
pip install owlready2

python3 -c "
import owlready2
onto = owlready2.get_ontology('file:///path/to/ontology.owl').load()
owlready2.sync_reasoner()
print('PASS: Consistent')
"
```

```python
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL

def validate_ontology(path: str, format: str = "turtle") -> bool:
    errors = []

    try:
        g = Graph()
        g.parse(path, format=format)
    except Exception as e:
        print(f"PARSE ERROR: {e}")
        return False

    triple_count = len(g)
    classes      = list(g.subjects(RDF.type, OWL.Class))
    properties   = list(g.subjects(RDF.type, OWL.ObjectProperty)) + \
                   list(g.subjects(RDF.type, OWL.DatatypeProperty))
    individuals  = list(g.subjects(RDF.type, OWL.NamedIndividual))

    print(f"Total triples:     {triple_count}")
    print(f"Classes:           {len(classes)}")
    print(f"Properties:        {len(properties)}")
    print(f"Named individuals: {len(individuals)}")

    # Check: classes have labels
    for cls in classes:
        if not list(g.objects(cls, RDFS.label)):
            errors.append(f"WARNING: Class has no rdfs:label — {cls}")

    # Check: ontology declaration present
    if not list(g.subjects(RDF.type, OWL.Ontology)):
        errors.append("WARNING: No owl:Ontology declaration found")

    if errors:
        for e in errors: print(e)
        return False

    print("PASS: Ontology is valid")
    return True


validate_ontology("aec_ontology.ttl")
```

### QA Checklist

- [ ] File parses without error (Turtle / RDF/XML)
- [ ] All classes have `rdfs:label` and `rdfs:comment`
- [ ] All properties have `rdfs:domain` and `rdfs:range`
- [ ] Ontology URI declared as `owl:Ontology`
- [ ] No duplicate individual URIs
- [ ] `owl:FunctionalProperty` used for single-value properties (e.g. IFC GUID)
- [ ] Namespace prefixes are bound and consistent
- [ ] OWL reasoner passes consistency check (no unsatisfiable classes)
- [ ] Round-trip: Turtle → RDF/XML → Turtle produces equivalent graph

### QA Loop

1. Author in Turtle
2. Parse with rdflib — fix syntax errors
3. Run `validate_ontology()` — label and declaration checks
4. Export to RDF/XML for OWL tool compatibility
5. Load in Protégé — run reasoner — fix inconsistencies
6. **Do not publish until reasoner passes with zero errors**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `Expected '.' but got ...` | Missing period at end of triple | Every triple block must end with `.` |
| Prefix not recognised | Missing `@prefix` declaration | Add prefix at top of file |
| Unsatisfiable class | Conflicting axioms | Check `owl:disjointWith` and domain/range constraints |
| Blank node not resolving | Blank node ID reused across files | Use named individuals with URIs |
| `rdflib` loses comments | RDF formats don't preserve comments | Use version control; comments are author-side only |
| Reasoner slow | Large ABox (many individuals) | Separate TBox (schema) and ABox (data) files |

---

## Dependencies

```bash
pip install rdflib          # graph, parsing, SPARQL, serialisation
pip install owlready2       # OWL reasoning
pip install pyshacl         # SHACL constraint validation

# GUI ontology editor
# Protégé: https://protege.stanford.edu (free, recommended)
```
