import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("profile_update", ROOT / "scripts/update_profile.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def repo(name, **fields):
    return {"name": name, "owner": {"login": "Joacoorandom"}, "private": False, **fields}


class PublicProfileTests(unittest.TestCase):
    def test_public_only_across_pages(self):
        batch = [repo("Joacoorandom"), repo("secret", private=True), repo("hidden", visibility="private"), repo("foreign", owner={"login": "elsewhere"})]
        batch += [repo(f"public-{i}") for i in range(96)]
        pages = iter([batch, [repo("last")]])
        result = p.public_repos("Joacoorandom", lambda _: next(pages))
        self.assertEqual(len(result), 97)
        self.assertIn("last", [r["name"] for r in result])

    def test_failures_do_not_look_like_empty_catalog(self):
        with self.assertRaises(ValueError):
            p.public_repos("Joacoorandom", lambda _: {"message": "rate limited"})

    def test_escaping_and_marker_preservation(self):
        config = {"owner": "Joacoorandom"}
        generated = p.catalog([repo("safe", description='<img src=x onerror="x"> | test')], config)
        self.assertNotIn('<img src=x', generated)
        original = "intro\n" + p.START + "old" + p.END + "\nfooter"
        result = p.replace_catalog(original, generated)
        self.assertTrue(result.startswith("intro\n"))
        self.assertTrue(result.endswith("\nfooter"))
        self.assertEqual(result, p.replace_catalog(result, generated))
        with self.assertRaises(ValueError):
            p.replace_catalog("missing markers", generated)

    def test_modules_are_valid_svg(self):
        import json
        config = json.loads((ROOT / "profile.json").read_text())
        ET.fromstring(p.modules([repo("own"), repo("fork", fork=True)], config))


if __name__ == "__main__":
    unittest.main()
