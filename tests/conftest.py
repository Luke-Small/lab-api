import os
import tempfile
from pathlib import Path

test_database = Path(tempfile.gettempdir()) / "lab_api_workflow_test.db"
if test_database.exists():
    test_database.unlink()
os.environ["LAB_DATABASE_URL"] = f"sqlite+pysqlite:///{test_database}"
