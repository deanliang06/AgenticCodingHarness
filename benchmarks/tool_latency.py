"""Offline write/read round-trip latency, excluding imports and setup."""
import json
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ToolHandler import ToolHandler as T

with tempfile.TemporaryDirectory() as directory:
    path = str(Path(directory) / 'sample.txt')
    payload = 'x' * 1024
    samples = []
    for index in range(110):
        start = time.perf_counter()
        T.write_file(path, payload)
        result = T.read_file(path)
        elapsed = (time.perf_counter() - start) * 1000
        assert result.endswith(payload)
        if index >= 10:
            samples.append(elapsed)
    print(json.dumps({
        'python': platform.python_version(), 'platform': platform.platform(),
        'iterations': len(samples), 'warmup': 10, 'payload_bytes': len(payload),
        'median_ms': round(statistics.median(samples), 3),
        'p95_ms': round(sorted(samples)[94], 3),
    }, indent=2))
