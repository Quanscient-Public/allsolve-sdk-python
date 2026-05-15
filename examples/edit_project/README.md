# Introduction

This example opens an Allsolve project and lets you export it to YAML, edit the file
locally, import changes back, reset data, or delete the project—while keeping the
project open in the browser.

# Running

Create an Organization API key via Allsolve web UI
("Settings" / "Organization" / "API keys" / "Create key").

Configure credentials using `example/.env` (recommended) or environment variables:

```
(venv) $ export ALLSOLVE_ACCESS_KEY=<your key id>
(venv) $ export ALLSOLVE_SECRET_KEY=<your secret key>
(venv) $ python edit_project.py
```

Alternatively, use a `.env` file in `example/` with:

```
ALLSOLVE_ACCESS_KEY=<your key id>
ALLSOLVE_SECRET_KEY=<your secret key>
```

Then run:

```
(venv) $ python edit_project.py
```

See `edit_project.py` for optional settings (`PROJECT_ID`, `PROJECT_NAME`, `YAML_FILE`, etc.).
