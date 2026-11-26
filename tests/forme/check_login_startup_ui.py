#!/usr/bin/env python3
# Copyright (C) 2026, ForMe.World contributors.
# SPDX-License-Identifier: LGPL-2.1-only
"""Validate UI resources instantiated before the first UDP login."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
NV = ROOT / 'indra/newview'


class LoginStartupUI(unittest.TestCase):
    def test_group_panel_has_no_retired_call_control(self):
        # postBuild is invoked by idle_startup even when the user never opens
        # Groups. The macOS report identifies the former null callback here.
        for filename in ('llpanelgroup.cpp', 'llpanelgroup.h'):
            source = (NV / filename).read_text()
            self.assertIsNone(re.search(r'\b(?:mButtonCall|onBtnGroupCallClicked|callGroup)\b', source), filename)
        self.assertIn('LLGroupActions::startIM(getID())', (NV / 'llpanelgroup.cpp').read_text())

    def test_layout_panels_can_be_created_by_their_parent_registry(self):
        for filename in ('floater_fs_nearby_chat.xml', 'floater_world_map.xml'):
            for path in (NV / 'skins').glob(f'*/xui/*/{filename}'):
                root = ET.parse(path).getroot()
                for parent in root.iter():
                    for child in parent.findall('layout_panel'):
                        with self.subTest(path=path.relative_to(NV), panel=child.get('name')):
                            self.assertEqual('layout_stack', parent.tag)

    def test_text_uses_supported_font_style_parameter(self):
        for path in (NV / 'skins').glob('*/xui/*/floater_fs_nearby_chat.xml'):
            root = ET.parse(path).getroot()
            title = root.find(".//*[@name='forme_chat_title'][@font_style]")
            self.assertIsNone(title, (path, 'unsupported font_style parameter'))
        for path in (NV / 'skins').glob('*/xui/*/floater_world_map.xml'):
            root = ET.parse(path).getroot()
            with self.subTest(path=path.relative_to(NV)):
                self.assertEqual([], [el.get('name') for el in root.findall('.//text[@font_style]')],
                                 'Use font.style for text font styles')

    def test_custom_font_sizes_exist_in_actual_installed_font_profiles(self):
        # LLFontGL tries install_dir/fonts first, not the skin fallback fonts.xml.
        fallback = ET.parse(NV / 'skins/default/xui/en/fonts.xml').getroot()
        expected = {n.get('name'): n.get('size') for n in fallback.findall('font_size')
                    if n.get('name', '').startswith('WMap')}
        self.assertTrue(expected)
        for path in (NV / 'fonts').glob('*.xml'):
            sizes = {n.get('name'): n.get('size') for n in ET.parse(path).getroot().findall('font_size')}
            for name, size in expected.items():
                self.assertEqual(size, sizes.get(name), (path, name))


if __name__ == '__main__':
    unittest.main()
