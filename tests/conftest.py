import pytest
from pathlib import Path

VALID_YAML = """
groups:
  dev:
    description: Local development
    commands:
      start:
        description: Start the server
        run: "uvicorn app.main:app --reload"
      reset:
        description: Reset the DB
        run: "python scripts/reset_db.py"
  test:
    description: Test suite
    commands:
      run:
        description: Run all tests
        run: "pytest"
"""

@pytest.fixture
def tmp_config(tmp_path):
    """Write ordo.yaml to a temp dir and return a factory."""
    def _make(content: str = VALID_YAML) -> Path:
        config_file = tmp_path / "ordo.yaml"
        config_file.write_text(content)
        return config_file
    return _make