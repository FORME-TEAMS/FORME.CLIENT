#!/usr/bin/env python3
"""Regression test for optional macOS BugSplat packaging.

The viewer can be configured with OpenAL enabled and BugSplat disabled.
In that configuration the manifest must not inspect, copy, or rewrite any
BugSplat framework. This test parses the real manifest instead of matching
indentation or comments, so moving the code outside the feature guard fails.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "indra/newview/viewer_manifest.py"


def is_self_args_get(node, key):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and isinstance(node.func.value, ast.Attribute)
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "self"
        and node.func.value.attr == "args"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == key
    )


def call_name(node):
    if not isinstance(node, ast.Call):
        return ""
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


class MacManifestOptionalDependencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(MANIFEST.read_text(), filename=str(MANIFEST))
        cls.parents = {
            child: parent
            for parent in ast.walk(cls.tree)
            for child in ast.iter_child_nodes(parent)
        }
        cls.bugsplat_guards = [
            node for node in ast.walk(cls.tree)
            if isinstance(node, ast.If) and is_self_args_get(node.test, "bugsplat")
        ]
        cls.openal_guards = [
            node for node in ast.walk(cls.tree)
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Subscript)
            and isinstance(node.test.left.value, ast.Attribute)
            and isinstance(node.test.left.value.value, ast.Name)
            and node.test.left.value.value.id == "self"
            and node.test.left.value.attr == "args"
            and isinstance(node.test.left.slice, ast.Constant)
            and node.test.left.slice.value == "openal"
        ]

    def has_guard_ancestor(self, node, guards):
        parent = self.parents.get(node)
        while parent is not None:
            if parent in guards:
                return True
            parent = self.parents.get(parent)
        return False

    def test_bugsplat_framework_operations_are_feature_guarded(self):
        self.assertTrue(self.bugsplat_guards, "manifest must have an explicit BugSplat guard")
        relevant = []
        for node in ast.walk(self.tree):
            name = call_name(node)
            rendered = ast.dump(node)
            if name == "check_output" and "objdump" in rendered:
                relevant.append(node)
            elif name == "run_command" and "install_name_tool" in rendered:
                relevant.append(node)
            elif name == "path2basename" and any(
                framework in rendered
                for framework in ("HockeySDK.framework", "CrashReporter.framework",
                                  "BugsplatMac.framework")
            ):
                relevant.append(node)
        self.assertTrue(relevant, "expected BugSplat framework packaging operations")
        for node in relevant:
            self.assertTrue(
                self.has_guard_ancestor(node, self.bugsplat_guards),
                "BugSplat framework operation is reachable when USE_BUGSPLAT is OFF",
            )

    def test_openal_libraries_remain_independent_of_bugsplat(self):
        self.assertTrue(self.openal_guards, "manifest must retain an OpenAL option guard")
        openal_loops = []
        for guard in self.openal_guards:
            for node in ast.walk(guard):
                if not isinstance(node, ast.For) or not isinstance(node.iter, ast.Tuple):
                    continue
                values = {
                    item.value for item in node.iter.elts
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                }
                if {"libopenal.dylib", "libalut.dylib"}.issubset(values):
                    openal_loops.append((guard, node))
        self.assertTrue(openal_loops, "both OpenAL runtime libraries must be staged")
        for guard, loop in openal_loops:
            self.assertTrue(self.has_guard_ancestor(loop, self.openal_guards))
            self.assertFalse(
                self.has_guard_ancestor(loop, self.bugsplat_guards),
                "OpenAL must not depend on the optional BugSplat SDK",
            )
            self.assertTrue(
                any(call_name(node) == "path" for node in ast.walk(loop)),
                "OpenAL libraries must be copied into the app bundle",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
