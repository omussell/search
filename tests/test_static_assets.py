import tempfile
import unittest
from pathlib import Path

from app import app
from core import static_assets


class TestStaticAssetsHelpers(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.static_folder = self._tmpdir.name
        css_dir = Path(self.static_folder) / "css"
        css_dir.mkdir()
        (css_dir / "base.css").write_text("body { color: black; }", encoding="utf-8")
        (css_dir / "bootstrap.min.css").write_text(".btn {}", encoding="utf-8")
        static_assets.build_static_manifest(self.static_folder)

    def tearDown(self):
        self._tmpdir.cleanup()
        static_assets.build_static_manifest(app.static_folder)

    def test_build_manifest_registers_hashed_names(self):
        hashed = static_assets._manifest["css/base.css"]
        self.assertTrue(hashed.startswith("css/base."))
        self.assertTrue(hashed.endswith(".css"))
        self.assertEqual(static_assets.resolve_hashed_filename(hashed), "css/base.css")

    def test_static_url_uses_manifest(self):
        hashed = static_assets._manifest["css/base.css"]
        self.assertTrue(static_assets.static_url("css/base.css").endswith(f"/static/{hashed}"))

    def test_strip_content_hash(self):
        self.assertEqual(
            static_assets.strip_content_hash("css/base.deadbeef00.css"),
            "css/base.css",
        )
        self.assertIsNone(static_assets.strip_content_hash("css/bootstrap.min.css"))
        self.assertIsNone(static_assets.strip_content_hash("font/fontawesome-webfont.woff"))


class TestServeStatic(unittest.TestCase):
    def setUp(self):
        static_assets.build_static_manifest(app.static_folder)
        self.client = app.test_client()

    def test_known_hash_long_cache(self):
        hashed = static_assets._manifest["css/base.css"]
        response = self.client.get(f"/static/{hashed}")
        self.assertEqual(response.status_code, 200)
        cache_control = response.headers.get("Cache-Control", "")
        self.assertIn("max-age=31536000", cache_control)
        self.assertIn("immutable", cache_control)

    def test_unknown_hash_fallback_short_cache(self):
        response = self.client.get("/static/css/base.deadbeef00.css")
        self.assertEqual(response.status_code, 200)
        cache_control = response.headers.get("Cache-Control", "")
        self.assertIn("max-age=3600", cache_control)
        self.assertNotIn("immutable", cache_control)

    def test_plain_name_short_cache(self):
        response = self.client.get("/static/font/fontawesome-webfont.woff")
        self.assertEqual(response.status_code, 200)
        cache_control = response.headers.get("Cache-Control", "")
        self.assertIn("max-age=3600", cache_control)
        self.assertNotIn("immutable", cache_control)


if __name__ == "__main__":
    unittest.main()
