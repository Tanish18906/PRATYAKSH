"""A cold hash cache must be safe to warm from separate benchmark workers."""

import subprocess
import sys
from pathlib import Path

import pytest


def test_concurrent_cold_cache(tmp_path):
    sketch = pytest.importorskip("app.common.sketch")
    if not getattr(sketch, "__file__", None):
        pytest.skip("requires the shared sketch on disk for child processes")
    backend = Path(__file__).resolve().parents[2]
    worker = """
import sys
from pathlib import Path
from app.sim import base_table
base_table.CACHE_DIR = Path(sys.argv[1])
base = base_table.warm_cache('bench')
print(int(base.hashes['email'][123]))
"""
    processes = [subprocess.Popen([sys.executable, "-c", worker, str(tmp_path)],
                                  cwd=backend, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True)
                 for _ in range(2)]
    try:
        results = [process.communicate(timeout=60) for process in processes]
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()
    assert all(process.returncode == 0 for process in processes), results
    assert results[0][0] == results[1][0]
    third = subprocess.run([sys.executable, "-c", worker, str(tmp_path)], cwd=backend,
                           capture_output=True, text=True, timeout=60, check=True)
    assert third.stdout == results[0][0]
