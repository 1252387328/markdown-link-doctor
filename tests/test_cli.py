import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(project):
    spec = importlib.util.spec_from_file_location(project.replace('-', '_'), ROOT / 'cli.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProjectTests(unittest.TestCase):
    def test_all_help_and_invalid_arguments(self):
        for path in [ROOT / 'cli.py']:
            with self.subTest(project=path.parent.name):
                result = subprocess.run([sys.executable, str(path), '--help'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                result = subprocess.run([sys.executable, str(path), '--not-a-real-option'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('Traceback', result.stderr)

    def test_markdown_valid_fixture(self):
        module = load('markdown-link-doctor')
        result = module.check(ROOT / 'examples/demo.md')
        self.assertEqual(result['issues'], [])
        self.assertEqual(result['external_links_skipped'], 1)

    def test_markdown_missing_file_and_anchor(self):
        module = load('markdown-link-doctor')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.md'
            path.write_text('# Hi\n[bad](missing.txt)\n[bad anchor](#absent)\n')
            self.assertEqual([i['reason'] for i in module.check(path)['issues']], ['missing target', 'missing heading anchor'])

if __name__ == '__main__':
    unittest.main()
