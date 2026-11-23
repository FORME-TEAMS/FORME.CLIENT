#!/usr/bin/env python3
"""Validate the ForMe login welcome hub geometry and locale overlay."""
from pathlib import Path
import xml.etree.ElementTree as ET
import re

ROOT = Path(__file__).resolve().parents[2]
XUI = ROOT / "indra/newview/skins/default/xui"

en = ET.parse(XUI / "en/panel_forme_login.xml").getroot()
ru = ET.parse(XUI / "ru/panel_forme_login.xml").getroot()

def child(root, name):
    node = root.find(".//*[@name='%s']" % name)
    assert node is not None, name
    return node

hub = child(en, "forme_welcome_hub")
assert hub.get("follows") == "right|top"
width, height = int(hub.get("width")), int(hub.get("height"))
cards = [child(hub, name) for name in (
    "forme_hub_explore_card", "forme_hub_connect_card", "forme_hub_create_card")]
rects = []
for card in cards:
    x, y = int(card.get("left")), int(card.get("top"))
    w, h = int(card.get("width")), int(card.get("height"))
    assert x >= 0 and y >= 0 and x + w <= width and y + h <= height
    rects.append((x, y, x + w, y + h))
for i, a in enumerate(rects):
    for b in rects[i + 1:]:
        assert a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]

for name in ("forme_hub_eyebrow", "forme_hub_title", "forme_hub_intro",
             "forme_hub_explore_title", "forme_hub_explore_copy",
             "forme_hub_connect_title", "forme_hub_connect_copy",
             "forme_hub_create_title", "forme_hub_create_copy", "forme_hub_footer"):
    child(hub, name)
    child(ru, name)

# The welcome area is informational; native credential and login controls remain intact.
for name in ("username_combo", "password_edit", "start_location_combo", "connect_btn"):
    child(en, name)
# The workspace rail is a new native XUI surface, not a recolored legacy toolbar.
sidebar_en = ET.parse(XUI / "en/panel_forme_sidebar.xml").getroot()
sidebar_ru = ET.parse(XUI / "ru/panel_forme_sidebar.xml").getroot()
main_view = ET.parse(XUI / "en/main_view.xml").getroot()
mounted = child(main_view, "forme_workspace_sidebar")
assert mounted.get("filename") == "panel_forme_sidebar.xml"
for name in ("forme_sidebar_world", "forme_sidebar_people", "forme_sidebar_inventory",
             "forme_sidebar_community", "forme_sidebar_market", "forme_sidebar_preferences"):
    child(sidebar_en, name)
    child(sidebar_ru, name)
for name in ("forme_sidebar_world_label", "forme_sidebar_people_label",
             "forme_sidebar_inventory_label", "forme_sidebar_community_label",
             "forme_sidebar_market_label"):
    child(sidebar_en, name)
    child(sidebar_ru, name)

# The Home side tray is now a native ForMe dashboard, not an embedded web page.
home_en = ET.parse(XUI / "en/panel_sidetray_home_tab.xml").getroot()
home_ru = ET.parse(XUI / "ru/panel_sidetray_home_tab.xml").getroot()
assert home_en.find(".//web_browser") is None
assert home_ru.find(".//web_browser") is None
for name in ("forme_home_title", "forme_home_section_world",
             "forme_home_section_social", "forme_home_section_tools",
             "forme_home_open_map", "forme_home_open_destinations",
             "forme_home_open_people", "forme_home_open_groups",
             "forme_home_open_inventory", "forme_home_open_market",
             "forme_home_open_preferences"):
    child(home_en, name)
    child(home_ru, name)
# Keep the dashboard honest: no fabricated wallet, visitor, friend or event totals.
for node in home_en.iter():
    if node.tag == "text":
        label = (node.text or "").lower()
        assert not any(token in label for token in ("visitors:", "friends online:", "balance:"))

# Keep the in-world navigation surfaces on the same ForMe theme.
nav = ET.parse(XUI / "en/panel_navigation_bar.xml").getroot()
assert nav.get("background_visible") == "true"
assert nav.get("bg_opaque_color") == "MenuBarBgColor"
nav_main = child(nav, "navigation_bar_visibility_panel")
assert nav_main.get("background_visible") == "true"
favorites = child(nav, "favorites_bar_visibility_panel")
assert favorites.get("background_visible") == "true"

topinfo = ET.parse(XUI / "en/panel_topinfo_bar.xml").getroot()
assert topinfo.get("background_opaque") == "true"
assert topinfo.get("bg_opaque_color") == "floater_bg_color"

toolbar_ru = ET.parse(XUI / "ru/panel_status_bar.xml").getroot()
for name in ("forme_tools_map", "forme_tools_people", "forme_tools_inventory",
             "forme_tools_market", "forme_tools_build", "forme_tools_move",
             "forme_tools_rotate", "forme_tools_settings"):
    child(toolbar_ru, name)

# Full ForMe home dashboard mirrors the supplied 1672x941 desktop composition.
home_dashboard_en = ET.parse(XUI / "en/floater_forme_home.xml").getroot()
home_dashboard_ru = ET.parse(XUI / "ru/floater_forme_home.xml").getroot()
assert home_dashboard_en.get("width") == "1672"
assert home_dashboard_en.get("height") == "941"
assert home_dashboard_en.get("min_width") == "1672"
assert home_dashboard_en.get("min_height") == "941"
assert home_dashboard_ru.get("width") == "1672"
assert home_dashboard_ru.get("height") == "941"
assert home_dashboard_ru.get("min_width") == "1672"
assert home_dashboard_ru.get("min_height") == "941"
# Russian locale is a complete native dashboard, not a text-only placeholder.
for name in ("home_topbar", "home_sidebar", "home_main_content", "home_hero",
             "home_hero_art", "home_world_stats", "home_online_stat",
             "home_server_stat", "home_world_stat", "home_season_stat",
             "home_feature_explore", "home_feature_connect", "home_feature_create",
             "home_feature_progress", "home_feature_earn", "home_event_panel",
             "home_event_art", "home_news_panel", "home_news_riverside_art",
             "home_news_housing_art", "home_quick_panel", "home_quick_access",
             "home_profile_card", "home_community_card", "home_footer_card"):
    child(home_dashboard_ru, name)
for name in ("home_nav_play", "home_nav_world", "home_nav_map",
             "home_nav_inventory", "home_nav_people", "home_nav_groups",
             "home_nav_events", "home_nav_market", "home_profile_button",
             "home_side_home", "home_side_avatar", "home_side_inventory",
             "home_side_map", "home_side_community", "home_side_events",
             "home_side_market", "home_side_settings", "home_side_style",
             "home_start_game", "home_choose_server", "home_event_open_map",
             "home_news_open", "home_quick_play", "home_quick_friends",
             "home_quick_chat", "home_quick_tasks", "home_quick_style",
             "home_quick_collection", "home_quick_achievements", "home_quick_clans"):
    en_button, ru_button = child(home_dashboard_en, name), child(home_dashboard_ru, name)
    en_callback = en_button.find("button.commit_callback")
    ru_callback = ru_button.find("button.commit_callback")
    assert (en_callback is None) == (ru_callback is None), name
    if en_callback is not None:
        assert en_callback.attrib == ru_callback.attrib, name
main = child(home_dashboard_en, "home_main_content")
main_width, main_height = int(main.get("width")), int(main.get("height"))
feature_names = ("explore", "connect", "create", "progress", "earn")
feature_bottom = 0
for feature in feature_names:
    card = child(home_dashboard_en, "home_feature_" + feature)
    x, y = int(card.get("left")), int(card.get("top"))
    w, h = int(card.get("width")), int(card.get("height"))
    art = child(card, "feature_" + feature + "_art")
    title = child(card, "feature_" + feature + "_title")
    copy = child(card, "feature_" + feature + "_copy")
    assert x >= 0 and y >= 0 and x + w <= main_width
    assert int(art.get("top")) + int(art.get("height")) <= int(title.get("top"))
    assert int(title.get("top")) + int(title.get("height")) <= int(copy.get("top"))
    assert int(copy.get("top")) + int(copy.get("height")) <= h
    feature_bottom = max(feature_bottom, y + h)
for name in ("home_event_panel", "home_news_panel"):
    panel = child(home_dashboard_en, name)
    assert int(panel.get("top")) >= feature_bottom
    assert int(panel.get("top")) + int(panel.get("height")) <= main_height
assert child(home_dashboard_en, "home_quick_tasks").find("button.commit_callback") is not None
assert child(home_dashboard_en, "home_quick_achievements").find("button.commit_callback") is not None
for name in ("home_footer_card", "home_quick_tasks", "home_quick_achievements"):
    child(home_dashboard_en, name)
assert "Демо-контент" in child(home_dashboard_ru, "home_event_note").text

for name in ("home_topbar", "home_sidebar", "home_main_content",
             "home_hero", "home_world_stats", "home_feature_explore",
             "home_feature_connect", "home_feature_create",
             "home_feature_progress", "home_feature_earn",
             "home_event_panel", "home_news_panel", "home_quick_panel",
             "home_quick_access", "home_profile_card", "home_community_card"):
    child(home_dashboard_en, name)
for name in ("home_nav_play", "home_nav_world", "home_nav_map",
             "home_nav_inventory", "home_nav_people", "home_nav_groups",
             "home_nav_events", "home_nav_market", "home_side_inventory",
             "home_side_map", "home_side_community", "home_side_settings",
             "home_start_game", "home_choose_server", "home_event_open_map",
             "home_news_open", "home_quick_collection", "home_profile_inventory"):
    child(home_dashboard_en, name)
assert child(home_dashboard_en, "home_quick_chat").find("button.commit_callback").get("parameter") == "fs_nearby_chat"
registry_source = (ROOT / "indra/newview/llviewerfloaterreg.cpp").read_text()
registered_floaters = set(re.findall(r'LLFloaterReg::add[(]"([^"]+)"', registry_source))
for locale_root in (home_dashboard_en, home_dashboard_ru):
    for callback in locale_root.findall(".//button.commit_callback"):
        if callback.get("function") == "Floater.Toggle":
            assert callback.get("parameter") in registered_floaters, callback.get("parameter")
assert child(home_dashboard_en, "home_nav_groups").find("button.commit_callback").get("parameter") == "forme_groups"
assert child(home_dashboard_en, "home_side_community").find("button.commit_callback").get("parameter") == "forme_groups"
assert child(home_dashboard_en, "home_news_open").find("button.commit_callback").get("parameter") == "forme_groups"
for name in ("home_hero_title", "home_features_title", "home_event_heading",
             "home_news_heading", "home_quick_heading", "home_profile_heading"):
    child(home_dashboard_ru, name)
# Match the full-width desktop reference: one hero, five feature tiles and a three-panel footer.
home_main = child(home_dashboard_en, "home_main_content")
assert home_main.get("width") == "1398"
assert child(home_dashboard_en, "home_hero").get("width") == "1398"
assert child(home_dashboard_en, "home_world_stats").get("left") == "282"
feature_positions = {"explore": 116, "connect": 372, "create": 628, "progress": 884, "earn": 1140}
for feature, x in feature_positions.items():
    card = child(home_dashboard_en, "home_feature_" + feature)
    assert int(card.get("left")) == x and card.get("width") == "242"
    assert int(card.get("top")) == 340 and card.get("height") == "156"
    art = child(card, "feature_" + feature + "_art")
    title = child(card, "feature_" + feature + "_title")
    copy = child(card, "feature_" + feature + "_copy")
    assert int(art.get("top")) + int(art.get("height")) <= int(title.get("top"))
    assert int(title.get("top")) + int(title.get("height")) <= int(copy.get("top"))
for name, x in (("home_event_panel", 20), ("home_news_panel", 558), ("home_quick_panel", 1012)):
    panel = child(home_dashboard_en, name)
    assert int(panel.get("left")) == x and int(panel.get("top")) == 520
assert child(home_dashboard_en, "home_quick_access").get("width") == "386"
for name in ("home_profile_card", "home_community_card", "home_footer_card"):
    assert child(home_dashboard_en, name).get("visible") == "false"

# Dashboard counters are deliberately placeholders until backed by live server/account APIs.
for name in ("home_online_stat", "home_server_stat", "home_world_stat",
             "home_season_stat", "home_currency_label"):
    assert "—" in child(home_dashboard_en, name).text

# Generated demo artwork is bundled locally in the viewer texture tree.
texture_root = ROOT / "indra/newview/skins/default/textures"
textures = ET.parse(texture_root / "textures.xml").getroot()
texture_names = {node.get("name"): node for node in textures.findall("texture")}
for name in ("ForMe_Home_Hero", "Forme_Home_Explore", "Forme_Home_Connect",
             "Forme_Home_Create", "Forme_Home_Progress", "Forme_Home_Earn",
             "Forme_Home_Event", "Forme_Home_News_Riverside",
             "Forme_Home_News_Housing"):
    assert name in texture_names, name
assert texture_names["ForMe_Home_Hero"].get("file_name") == "forme_home/home_hero.jpg"
assert texture_names["Forme_Home_Explore"].get("file_name") == "forme_home/cards_atlas.jpg"
assert (texture_root / "forme_home/home_hero.jpg").is_file()
assert (texture_root / "forme_home/cards_atlas.jpg").is_file()
for name in ("home_hero_art", "feature_explore_art", "feature_connect_art",
             "feature_create_art", "feature_progress_art", "feature_earn_art",
             "home_event_art", "home_news_riverside_art", "home_news_housing_art"):
    child(home_dashboard_en, name)
assert child(home_dashboard_en, "home_hero_art").get("image_name") == "ForMe_Home_Hero"
assert child(home_dashboard_en, "home_event_art").get("image_name") == "Forme_Home_Event"
for name in ("home_news_riverside_title", "home_news_riverside_copy",
             "home_news_housing_title", "home_news_housing_copy"):
    child(home_dashboard_en, name)
    child(home_dashboard_ru, name)

print("PASS ForMe ForMe login hub and in-world navigation: layout, locale, theme surfaces and native controls")
