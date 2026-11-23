#!/usr/bin/env python3
"""Regression check for optional macOS BugSplat packaging."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "indra/newview/viewer_manifest.py"


class MacManifestOptionalDependencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = MANIFEST.read_text()

    def test_bugsplat_framework_rewrite_is_feature_guarded(self):
        marker = "# BugSplat is optional."
        marker_at = self.source.index(marker)
        guard_at = self.source.index("if self.args.get('bugsplat'):", marker_at)
        end_at = self.source.index("# NOTE: the -S argument", guard_at)
        guarded_block = self.source[guard_at:end_at]

        for required in (
            "HockeySDK.framework",
            "CrashReporter.framework",
            "BugsplatMac.framework",
            "objdump",
            "install_name_tool",
        ):
            self.assertIn(required, guarded_block)

        openal_at = self.source.rfind(
            "if self.args['openal'] == 'ON':", 0, marker_at
        )
        self.assertGreater(openal_at, 0)
        openal_block = self.source[openal_at:marker_at]
        self.assertIn("libopenal.dylib", openal_block)
        self.assertIn("libalut.dylib", openal_block)
        self.assertIn("self.path(libfile)", openal_block)
        self.assertNotIn("HockeySDK.framework", openal_block)
        self.assertNotIn("install_name_tool", openal_block)


if __name__ == "__main__":
    unittest.main(verbosity=2)
