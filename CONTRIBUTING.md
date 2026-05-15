# Contributing to Allsolve SDK

Thank you for your interest in contributing to the Allsolve SDK!

## Local Setup

1. Clone the repository:

```bash
git clone https://github.com/Quanscient-Public/allsolve-sdk-python.git
cd allsolve-sdk-python
```

2. Create a virtual environment and install dependencies:

**Using pip:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements_dev.txt
```

**Using [uv](https://docs.astral.sh/uv/):**

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
uv pip install -r requirements_dev.txt
```

## Testing

Create a `.env` file in the `tests/` directory with your API credentials:

```
ALLSOLVE_ACCESS_KEY=your-access-key-here
ALLSOLVE_SECRET_KEY=your-secret-key-here
ALLSOLVE_HOST=https://allsolve.quanscient.com/
```

Run the test suite:

```bash
pytest
```

## Code Standards

- **Formatting:** [Black](https://github.com/psf/black) with default settings
- **Type checking:** [Pyright](https://github.com/microsoft/pyright) and [mypy](https://mypy-lang.org/)

Check your code before submitting:

```bash
black --check src/allsolve/
pyright src/allsolve/
mypy --follow-imports=silent src/allsolve/
```

## Contributor License Agreement

Before your first pull request can be merged, you must agree to the
[Contributor License Agreement (CLA)](CLA.md). The CLA is a lightweight
agreement that confirms you have the right to contribute your code and that
you grant Quanscient Oy a license to use it. Every pull request includes a
checkbox to confirm your agreement.

## Pull Request Guidelines

1. Create a feature branch from `main`
2. Make your changes and ensure all checks pass
3. Write a clear description of what your PR does and why
4. Confirm the CLA checkbox in the pull request template
5. Submit the pull request for review
