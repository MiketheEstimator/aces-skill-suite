---
name: structured-xml-export
description: "Use this skill when producing .xml files. Covers schema-driven XML generation, namespace handling, XSD validation, pretty-printing, and industry-standard XML formats. Trigger on any XML export, data interchange, config file, or format requiring XML structure."
---

# Structured XML Export SKILL

## Quick Reference

| Task | Tool |
|------|------|
| Generate XML | `xml.etree.ElementTree` (stdlib) or `lxml` |
| Pretty-print | `lxml` with `pretty_print=True` |
| XSD validation | `lxml.etree.XMLSchema` |
| Namespaces | `lxml` recommended |
| XPath queries | `lxml` |
| Large files | `lxml.etree.iterparse` |

---

## Standard XML Generation (stdlib)

```python
import xml.etree.ElementTree as ET
from xml.dom import minidom

def build_xml():
    root = ET.Element("ProjectExport")
    root.set("version", "1.0")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

    project = ET.SubElement(root, "Project")
    ET.SubElement(project, "Name").text = "Main Tower"
    ET.SubElement(project, "Date").text = "2024-03-15"
    ET.SubElement(project, "Budget").text = "1250000.00"

    phases = ET.SubElement(project, "Phases")
    for phase_data in [("Foundation", True), ("Structure", False)]:
        phase = ET.SubElement(phases, "Phase")
        ET.SubElement(phase, "Name").text = phase_data[0]
        ET.SubElement(phase, "Complete").text = str(phase_data[1]).lower()

    return root

def pretty_print_xml(root):
    raw = ET.tostring(root, encoding="unicode")
    reparsed = minidom.parseString(raw)
    return reparsed.toprettyxml(indent="  ")

root = build_xml()
with open("output.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write(pretty_print_xml(root))
```

---

## lxml (Recommended for Production)

```python
# pip install lxml --break-system-packages
from lxml import etree

root = etree.Element("ProjectExport", version="1.0")

project = etree.SubElement(root, "Project")
etree.SubElement(project, "Name").text = "Main Tower"
etree.SubElement(project, "Date").text = "2024-03-15"

tree = etree.ElementTree(root)

# Write with declaration and pretty-print
tree.write(
    "output.xml",
    xml_declaration=True,
    encoding="UTF-8",
    pretty_print=True
)
```

---

## Namespace Handling

```python
from lxml import etree

# Define namespaces
nsmap = {
    None: "http://example.com/schema/v1",      # default namespace
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "ifc": "http://www.buildingsmart-tech.org/ifc"
}

root = etree.Element("Export", nsmap=nsmap)
root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
         "http://example.com/schema/v1 schema.xsd")
```

---

## XSD Validation

```python
from lxml import etree

def validate_xml(xml_path, xsd_path):
    with open(xsd_path, 'rb') as f:
        schema_doc = etree.parse(f)
    schema = etree.XMLSchema(schema_doc)
    
    with open(xml_path, 'rb') as f:
        doc = etree.parse(f)
    
    is_valid = schema.validate(doc)
    if not is_valid:
        for error in schema.error_log:
            print(f"Line {error.line}: {error.message}")
    return is_valid
```

---

## CLI Verification

```bash
# Validate well-formed XML
python -c "
import xml.etree.ElementTree as ET
ET.parse('output.xml')
print('Well-formed XML ✓')
"

# Pretty-print with xmllint
xmllint --format output.xml | head -50

# Validate against XSD
xmllint --schema schema.xsd output.xml --noout

# Count elements
python -c "
from lxml import etree
tree = etree.parse('output.xml')
print('Total elements:', len(tree.findall('.//*')))
"

# XPath query
python -c "
from lxml import etree
tree = etree.parse('output.xml')
results = tree.xpath('//Phase[Complete=\"true\"]/Name/text()')
print(results)
"
```

---

## QA Checklist

- [ ] XML is well-formed (parses without error)
- [ ] XML declaration present (`<?xml version="1.0" encoding="UTF-8"?>`)
- [ ] Encoding is UTF-8
- [ ] All tags properly opened and closed
- [ ] Special characters escaped (`&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`)
- [ ] Namespace declarations correct and consistent
- [ ] Validates against XSD (if schema provided)
- [ ] No empty required elements
- [ ] Consistent date format (ISO 8601)

---

## Character Escaping Reference

| Character | Escaped Form |
|-----------|-------------|
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |
| `"` | `&quot;` |
| `'` | `&apos;` |

> Note: `lxml` and `ElementTree` handle escaping automatically when using `.text` assignment. Only manually escape when building raw XML strings.

---

## Common Mistakes to Avoid

- Building XML by string concatenation (never do this — use a library)
- Forgetting XML declaration encoding attribute
- Mixing namespace prefixes inconsistently
- Using element names starting with numbers or containing spaces
- Forgetting to escape `&` in text content
- Attribute values without quotes (invalid XML)

---

## Dependencies

```bash
pip install lxml --break-system-packages
# xml.etree.ElementTree, xml.dom.minidom: Python stdlib
```
