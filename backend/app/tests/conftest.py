"""Test isolation: point the app at throwaway data/export dirs before any
app module reads its config, so tests never touch the repo's real files."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="curtainlen-test-")
os.environ.setdefault("DATA_DIR", os.path.join(_tmp, "data"))
os.environ.setdefault("EXPORTS_DIR", os.path.join(_tmp, "exports"))
