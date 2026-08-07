"""Content-hashed static URLs for cache busting.

1. Startup — build_static_manifest()
   Build / rebuild the manifest. Changed files get new hashes; unchanged keep
   the same hash; new files are added.
2. Page render — static_url()
3. Asset request — resolve_hashed_filename() (via _serve_static in app.py)
"""

import hashlib
import os

from settings import STATIC_CDN_BASE_URL

HASH_LENGTH = 10

_manifest = {}          # original -> hashed (step 2)
_reverse_manifest = {}  # hashed -> original (step 3)


def _relative_static_path(absolute_path, static_folder):
    """1.c Turn each absolute path into a URL-style relative path."""
    return os.path.relpath(absolute_path, static_folder).replace(os.sep, "/")


def _file_digest(absolute_path):
    """1.d Hash the file contents into a short digest."""
    with open(absolute_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:HASH_LENGTH]


def _hashed_filename(relative_path, digest):
    """1.e Build a hashed filename (insert digest before the extension)."""
    base, ext = os.path.splitext(relative_path)
    return f"{base}.{digest}{ext}"


def _register_static_file(relative_path, hashed_relative_path):
    """1.f Register both mapping directions (original <-> hashed)."""
    _manifest[relative_path] = hashed_relative_path
    _reverse_manifest[hashed_relative_path] = relative_path


def build_static_manifest(static_folder):
    """1. Build / rebuild filename maps from static_folder.

    1.a Clear any previous maps.
    1.b Walk every file under the static folder.
    1.c Turn each absolute path into a URL-style relative path.
    1.d Hash the file contents into a short digest.
    1.e Build a hashed filename (insert digest before the extension).
    1.f Register both mapping directions (original <-> hashed).
    """
    # 1.a
    _manifest.clear()
    _reverse_manifest.clear()
    # 1.b
    for root, _dirs, files in os.walk(static_folder):
        for name in files:
            absolute_path = os.path.join(root, name)
            relative_path = _relative_static_path(absolute_path, static_folder)  # 1.c
            digest = _file_digest(absolute_path)  # 1.d
            hashed_relative_path = _hashed_filename(relative_path, digest)  # 1.e
            _register_static_file(relative_path, hashed_relative_path)  # 1.f
    return _manifest


def static_url(filename):
    """2. Build hashed CDN/local URL from a stable filename (Jinja).

    2.a Look up hashed name in _manifest.
    2.b Return CDN/local URL for the HTML.
    """
    hashed = _manifest.get(filename, filename)  # 2.a
    return f"{STATIC_CDN_BASE_URL}/static/{hashed}"  # 2.b


def resolve_hashed_filename(requested_filename):
    """3.a Look up real filename on disk from a hashed URL path."""
    return _reverse_manifest.get(requested_filename)
