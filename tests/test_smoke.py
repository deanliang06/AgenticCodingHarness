"""Small offline smoke suite; all file operations use temporary directories."""
import os
from pathlib import Path
import subprocess
import shlex
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ToolHandler import DictError, ToolHandler as T


class ToolSmokeTests(unittest.TestCase):
    def setUp(self):
        self.original = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        os.chdir(self.original)
        self.tmp.cleanup()

    def test_write_read_overwrite(self):
        path = str(self.root / 'sample.txt')
        T.write_file(path, 'first')
        T.write_file(path, 'second')
        self.assertEqual(Path(path).read_text(), 'second')
        self.assertIn('second', T.read_file(path))

    def test_list_directory(self):
        (self.root / 'sample.txt').touch()
        self.assertIn('sample.txt', T.list_dir(str(self.root)))

    def test_nested_directory_and_repeat(self):
        path = str(self.root / 'a' / 'b')
        T.make_dir(path)
        self.assertTrue(Path(path).is_dir())
        self.assertIn('already existed', T.make_dir(path))

    def test_change_directory(self):
        T.change_dir(str(self.root))
        self.assertEqual(Path.cwd(), self.root.resolve())

    def test_exists_and_delete(self):
        path = str(self.root / 'sample.txt')
        Path(path).touch()
        self.assertIn('exists at path', T.file_exists(path))
        T.delete_file(path)
        self.assertFalse(Path(path).exists())
        self.assertIn("doesn't exist", T.file_exists(path))
        self.assertIn("doesn't exist", T.delete_file(path))

    def test_empty_required_arguments(self):
        for name in ('run_shell', 'read_file', 'list_dir', 'change_dir',
                     'file_exists', 'make_dir', 'delete_file'):
            with self.subTest(tool=name), self.assertRaises(DictError):
                getattr(T, name)('')

    def test_shell_stdout(self):
        quote = subprocess.list2cmdline if os.name == 'nt' else shlex.join
        command = quote([sys.executable, '-c', "print('smoke-ok')"])
        self.assertIn('smoke-ok', T.run_shell(command).split('the output was ', 1)[1])

    def test_web_search_with_fake_client(self):
        client = SimpleNamespace(responses=SimpleNamespace(create=Mock(
            return_value=SimpleNamespace(output_text='fake result'))))
        self.assertIn('fake result', T.web_search(client, 'sample query'))
        self.assertEqual(client.responses.create.call_args.kwargs['input'], 'sample query')

    def test_empty_file_content(self):
        path = str(self.root / 'empty.txt')
        T.write_file(path, '')
        self.assertEqual(Path(path).read_text(), '')

    def test_shell_failure_is_observable(self):
        quote = subprocess.list2cmdline if os.name == 'nt' else shlex.join
        command = quote([
            sys.executable, '-c', "import sys; sys.stderr.write('failure-marker'); sys.exit(7)"])
        result = T.run_shell(command)
        self.assertIn('failure-marker', result)
        self.assertRegex(result, r'(?i)(exit|return)[ _-]*code\D*7')


if __name__ == '__main__':
    unittest.main(verbosity=2)
