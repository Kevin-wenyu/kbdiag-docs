import importlib.util
from pathlib import Path
import tempfile
import unittest
spec = importlib.util.spec_from_file_location('check_site', Path(__file__).with_name('check-site.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ValidationTests(unittest.TestCase):
    def check(self, html, files=None, required=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'index.html').write_text(html)
            for name, text in (files or {}).items():
                path=root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
            return module.validate(root,'https://example.com/site/',{} if required is None else required)[0]

    def test_valid_anchor(self):
        self.assertEqual(self.check('<a href="#ok">link</a><h1 id="ok">Hi</h1>'), [])

    def test_missing_file(self):
        self.assertTrue(any('missing target' in e for e in self.check('<a href="absent/">link</a>')))

    def test_missing_anchor(self):
        self.assertTrue(any('missing anchor' in e for e in self.check('<a href="#absent">link</a>')))

    def test_outside_base(self):
        self.assertTrue(any('outside baseURL' in e for e in self.check('<a href="/docs/">link</a>')))

    def test_missing_translation(self):
        errors=self.check('hello',{'docs/index.html':'hello'}, {'docs/':()})
        self.assertIn('Missing required page: zh/docs/',errors)

    def test_evidence_marker(self):
        errors=self.check('hello',{'docs/index.html':'hello','zh/docs/index.html':'hello'}, {'docs/':('LSN',)})
        self.assertTrue(any('missing evidence marker' in e for e in errors))

    def test_missing_search_target(self):
        errors=self.check('<div data-td-index-src="search.json"></div>',{'search.json':'[{"ref":"https://example.com/site/absent/"}]'})
        self.assertTrue(any('Search index' in e for e in errors))

if __name__=='__main__':
    unittest.main()
