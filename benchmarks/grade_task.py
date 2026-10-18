"""Grade an exercise with restored upstream tests; no model calls."""
import os
import subprocess
import sys

os.chdir(sys.argv[1])
result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-p', '*_test.py', '-v'],
                        capture_output=True, text=True, timeout=30)
print(result.stdout + result.stderr)
sys.exit(result.returncode)
