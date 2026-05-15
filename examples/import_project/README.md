# Introduction

This is an example for creating a project from a declarative YAML or JSON file,
and exporting projects back to YAML/JSON format.

# Import-Export Cycle

You can also run the import-export example to see how projects can be exported:

```
(venv) $ python import_export_example.py
```

This demonstrates:

- Importing a project from YAML
- Exporting it back to YAML and JSON
- Getting export data as a Python dictionary

The exported file will be semantically equivalent to the original, though
formatting may differ slightly.
