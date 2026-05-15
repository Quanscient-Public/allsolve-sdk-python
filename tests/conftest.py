from pathlib import Path
import os
import pytest

import allsolve

_TESTS_DIR = str(Path(__file__).parent)


@pytest.fixture(scope="session")
def allsolve_client():
    try:
        client = allsolve.Client(
            dotenv_file=os.path.join(_TESTS_DIR, ".env"), cache_base_dir=_TESTS_DIR
        )
    except ValueError as exc:
        pytest.skip(f"Allsolve credentials not available: {exc}")
    yield client
    try:
        client.clean_cache()
    except Exception as exc:
        print(f"WARNING: clean_cache failed: {exc}")


@pytest.fixture
def smoke_project(allsolve_client):
    project = allsolve_client.create_project(
        name="sdk_smoke_test_bending_beam",
        description="SDK Smoke test -- auto-deleted after test",
    )
    yield project
    try:
        project.delete()
    except Exception as exc:
        print(f"WARNING: project delete failed: {exc}")
