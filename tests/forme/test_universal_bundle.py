#!/usr/bin/env python3
"""Regression tests for universal macOS app and architecture-specific VLC plugins."""
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from forme_client import verify_universal_app


class UniversalBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Path(self.temp.name) / "ForMe.World.app"
        self.main = self.app / "Contents/MacOS/Firestorm"
        self.plugin = (
            self.app / "Contents/Resources/SLPlugin.app/Contents/Frameworks/"
            "plugins/libi420_rgb_mmx_plugin.dylib"
        )
        self.main.parent.mkdir(parents=True)
        self.plugin.parent.mkdir(parents=True)
        self.main.touch()
        self.plugin.touch()

    def run_verifier(self, architectures):
        def fake_run(args, **kwargs):
            if args[0] == "file":
                return SimpleNamespace(stdout="Mach-O 64-bit dynamically linked shared library")
            if args[0] == "lipo":
                archs = architectures[str(args[-1])]
                return SimpleNamespace(returncode=0, stdout=archs, stderr="")
            raise AssertionError(args)

        with patch("forme_client.subprocess.run", side_effect=fake_run):
            verify_universal_app(self.app)

    def test_thin_intel_vlc_plugin_does_not_reject_universal_app(self):
        self.run_verifier({
            str(self.main): "arm64 x86_64",
            str(self.plugin): "x86_64",
        })

    def test_universal_vlc_plugin_is_accepted(self):
        self.run_verifier({
            str(self.main): "arm64 x86_64",
            str(self.plugin): "arm64 x86_64",
        })

    def test_thin_required_viewer_binary_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "обязательном бинарнике"):
            self.run_verifier({
                str(self.main): "x86_64",
                str(self.plugin): "x86_64",
            })

    def test_vlc_plugin_with_unsupported_architecture_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "не поддерживает arm64 или x86_64"):
            self.run_verifier({
                str(self.main): "arm64 x86_64",
                str(self.plugin): "i386",
            })

    def test_non_utf8_file_metadata_is_decoded_without_crashing(self):
        calls = []

        def fake_run(args, **kwargs):
            calls.append((args[0], kwargs))
            if args[0] == "file":
                return SimpleNamespace(
                    stdout="Mach-O 64-bit dynamically linked shared library \ufffd"
                )
            if args[0] == "lipo":
                return SimpleNamespace(returncode=0, stdout="arm64 x86_64", stderr="")
            raise AssertionError(args)

        with patch("forme_client.subprocess.run", side_effect=fake_run):
            verify_universal_app(self.app)

        file_calls = [kwargs for command, kwargs in calls if command == "file"]
        lipo_calls = [kwargs for command, kwargs in calls if command == "lipo"]
        self.assertEqual(len(file_calls), 2)
        self.assertEqual(len(lipo_calls), 2)
        for kwargs in file_calls + lipo_calls:
            self.assertEqual(kwargs.get("encoding"), "utf-8")
            self.assertEqual(kwargs.get("errors"), "replace")


if __name__ == "__main__":
    unittest.main(verbosity=2)
