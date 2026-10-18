import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ToolHandler import ToolHandler


class WriteVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, 'solution.py')

    def test_write_verifies_saved_python_without_executing_it(self):
        result = ToolHandler.write_file(self.path, "raise RuntimeError('do not execute')\n")
        self.assertIn('Changes verified', result)
        self.assertIn('Python syntax passed', result)
        self.assertIn('still require tests', result)

    def test_write_reports_invalid_python(self):
        result = ToolHandler.write_file(self.path, 'def broken(:\n')
        self.assertIn('Python syntax verification failed', result)
        self.assertNotIn('Python syntax passed', result)

    def test_readback_detects_different_content(self):
        Path(self.path).write_text('actual = 1\n')
        result = ToolHandler.verify_file(self.path, 'expected = 2\n')
        self.assertIn('saved content does not match', result)

    def test_readback_failure_is_reported(self):
        result = ToolHandler.verify_file(self.path, 'value = 1\n')
        self.assertIn('could not read back the file', result)

    def test_other_files_do_not_claim_code_correctness(self):
        result = ToolHandler.write_file(self.path + '.txt', 'some text\r\n')
        self.assertIn('Changes verified', result)
        self.assertIn('code correctness was not checked', result)


if __name__ == '__main__':
    unittest.main()
