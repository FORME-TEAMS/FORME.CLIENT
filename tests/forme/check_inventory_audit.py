#!/usr/bin/env python3
# Copyright (C) 2026 ForMe.World contributors.
# SPDX-License-Identifier: LGPL-2.1-only
"""Compile production inventory decisions against a small model and deferred transport."""
from pathlib import Path
import subprocess
import tempfile

from check_appearance_startup import function

NEWVIEW = Path(__file__).resolve().parents[2] / 'indra/newview'


def main():
    sources = {
        'llappearancemgr.cpp': (
            'void LLAppearanceMgr::initCOFID()',
            'bool LLAppearanceMgr::ensureCOF()',
            'const LLViewerInventoryItem* LLAppearanceMgr::getBaseOutfitLink()',
            'LLInventoryModel::item_array_t LLAppearanceMgr::findCOFItemLinks(',
            'void LLAppearanceMgr::removeCOFItemLinks(const LLUUID& item_id, LLPointer<LLInventoryCallback> cb, bool',
            'void callAfterCategoryLinksFetch(',
        ),
        'llinventorymodelbackgroundfetch.cpp': ('void LLInventoryModelBackgroundFetch::fetchCOF(',),
        'fsforme_fittingroom.cpp': (
            'LLUUID findMyOutfits()',
            'LLViewerInventoryCategory* findSavedOutfit(',
            'bool isSavedOutfitComplete(',
            'void FSForMeFittingRoom::wearSavedOutfit(',
        ),
        'fsformeinventory.cpp': (
            'std::string lowercaseInventoryText(',
            'bool FSForMeInventoryBrowser::matches(',
        ),
    }
    code = [STUBS]
    for filename, signatures in sources.items():
        source = (NEWVIEW / filename).read_text()
        code.extend(function(source, signature) for signature in signatures)
    code.append(SCENARIOS)
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / 'inventory_audit.cpp'
        binary = Path(directory) / 'inventory_audit'
        source.write_text('\n'.join(code))
        subprocess.run(['c++', '-std=c++20', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=undefined', '-fno-sanitize-recover=all',
                        str(source), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


STUBS = r'''
#include <algorithm>
#include <cassert>
#include <clocale>
#include <cwctype>
#include <functional>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <vector>

using S32 = int;
using nullary_func_t = std::function<void()>;
struct LLUUID {
    int value{};
    static const LLUUID null;
    bool isNull() const { return value == 0; }
    bool notNull() const { return !isNull(); }
    bool operator==(const LLUUID&) const = default;
    bool operator<(const LLUUID& other) const { return value < other.value; }
};
const LLUUID LLUUID::null{};
namespace LLFolderType { enum EType { FT_MY_OUTFITS, FT_CURRENT_OUTFIT, FT_OUTFIT, FT_TRASH }; }
namespace LLAssetType { enum EType { AT_CATEGORY, AT_LINK, AT_CLOTHING, AT_BODYPART, AT_OBJECT,
                                      AT_ANIMATION, AT_GESTURE }; }
namespace LLWearableType { enum EType { WT_SHOES, WT_HAIR, WT_SKIN, WT_TATTOO }; }
namespace LLInventoryType { enum EType { IT_WEARABLE, IT_ATTACHMENT, IT_OBJECT }; }
struct LLViewerInventoryCategory {
    enum { FETCH_NONE, FETCH_RECURSIVE, VERSION_UNKNOWN = -1 };
    LLFolderType::EType type = LLFolderType::FT_OUTFIT;
    LLUUID owner{1}, parent{10}, id{};
    bool complete = true;
    int fetching = FETCH_NONE;
    LLFolderType::EType getPreferredType() const { return type; }
    LLUUID getOwnerID() const { return owner; }
    LLUUID getParentUUID() const { return parent; }
    LLUUID getUUID() const { return id; }
    std::string getName() const { return "Saved outfit"; }
    int getVersion() const { return complete ? 0 : VERSION_UNKNOWN; }
    void setFetching(int value) { fetching = value; }
};
struct LLViewerInventoryItem {
    LLUUID id{20}, linked_id{21};
    LLViewerInventoryCategory* category = nullptr;
    LLViewerInventoryItem* linked_item = nullptr;
    LLAssetType::EType type = LLAssetType::AT_CLOTHING;
    LLInventoryType::EType inventory_type = LLInventoryType::IT_WEARABLE;
    LLWearableType::EType wearable_type = LLWearableType::WT_TATTOO;
    std::string name = "ЁЖ и КОТ";
    bool link = true, complete = true;
    LLUUID getUUID() const { return id; }
    LLUUID getLinkedUUID() const { return linked_id; }
    LLAssetType::EType getType() const { return type; }
    LLAssetType::EType getActualType() const { return link ? LLAssetType::AT_LINK : type; }
    LLInventoryType::EType getInventoryType() const { return inventory_type; }
    LLWearableType::EType getWearableType() const { return wearable_type; }
    const std::string& getName() const { return name; }
    LLViewerInventoryCategory* getLinkedCategory() const { return category; }
    LLViewerInventoryItem* getLinkedItem() const { return linked_item; }
    bool getIsLinkType() const { return link; }
    bool isFinished() const { return complete; }
};
template<typename T> struct LLPointer {
    T* pointer{};
    T* get() const { return pointer; }
    operator T*() const { return pointer; }
    T* operator->() const { return pointer; }
    bool isNull() const { return !pointer; }
};
struct LLIsType { explicit LLIsType(LLAssetType::EType) {} };
namespace LLInventoryObserver { enum { LABEL }; }
class LLInventoryModel {
public:
    using cat_array_t = std::vector<LLPointer<LLViewerInventoryCategory>>;
    using item_array_t = std::vector<LLPointer<LLViewerInventoryItem>>;
    enum { EXCLUDE_TRASH };
    std::map<LLUUID, LLViewerInventoryCategory> categories;
    std::map<LLUUID, cat_array_t> subfolders;
    std::map<LLUUID, item_array_t> items;
    bool usable = true;
    int traversals = 0, changed = 0;
    bool isInventoryUsable() const { return usable; }
    LLUUID getRootFolderID() const { return {10}; }
    LLUUID findExistingCategoryUUIDForTypeInRoot(LLFolderType::EType type, const LLUUID& root) {
        for (const auto& [id, cat] : categories)
            if (cat.type == type && cat.parent == root) return id;
        return {};
    }
    LLViewerInventoryCategory* getCategory(LLUUID id) {
        auto found = categories.find(id);
        return found == categories.end() ? nullptr : &found->second;
    }
    LLUUID getLinkedItemID(const LLUUID& id) const { return id; }
    bool isCategoryComplete(LLUUID id) { auto* cat = getCategory(id); return cat && cat->complete; }
    void collectDescendents(const LLUUID& id, cat_array_t&, item_array_t& result, bool) {
        ++traversals;
        result = items[id];
    }
    void collectDescendentsIf(const LLUUID& id, cat_array_t& cats, item_array_t& result, bool include, LLIsType&) {
        collectDescendents(id, cats, result, include);
    }
    void getDirectDescendentsOf(const LLUUID& id, cat_array_t*& cats, item_array_t*& out) {
        auto found = items.find(id);
        cats = getCategory(id) ? &subfolders[id] : nullptr;
        out = found == items.end() ? nullptr : &found->second;
    }
    void addChangedMask(int, const LLUUID&) { ++changed; }
} gInventory;
struct Agent {
    LLUUID session{55};
    LLUUID getSessionID() const { return session; }
    LLUUID getID() const { return {1}; }
} gAgent;
struct LLInventoryCallback {};
struct rlv_handler_t { static bool isEnabled() { return false; } };
#define RLV_ASSERT(...) assert(true)
std::vector<LLUUID> removed;
void remove_inventory_item(LLUUID id, LLPointer<LLInventoryCallback>, bool) { removed.push_back(id); }

class LLAppearanceMgr {
public:
    LLUUID mCOFID;
    int applied = 0;
    static LLAppearanceMgr& instance() { static LLAppearanceMgr value; return value; }
    static LLAppearanceMgr* getInstance() { return &instance(); }
    LLUUID getCOF() const { return mCOFID; }
    LLUUID getBaseOutfitUUID() { return {}; }
    void initCOFID();
    bool ensureCOF();
    const LLViewerInventoryItem* getBaseOutfitLink();
    LLInventoryModel::item_array_t findCOFItemLinks(const LLUUID&);
    void removeCOFItemLinks(const LLUUID&, LLPointer<LLInventoryCallback>, bool);
    void wearInventoryCategoryOnAvatar(LLViewerInventoryCategory*, bool append) { assert(!append); ++applied; }
};
namespace AISAPI {
    bool available = true;
    bool isAvailable() { return available; }
    std::function<void(const LLUUID&)> pending;
    void FetchCOF(std::function<void(const LLUUID&)> callback) { pending = callback; }
}
void no_op() {}
struct IdleCallbacks { void addFunction(void (*)(void*), void*) {} } gIdleCallbacks;
bool gDisconnected = false;
using uuid_vec_t = std::vector<LLUUID>;
std::vector<nullary_func_t> fetch_callbacks;
uuid_vec_t linked_fetch_ids;
nullary_func_t linked_fetch_callback;
void callAfterCategoryFetch(const LLUUID&, nullary_func_t callback) { fetch_callbacks.push_back(callback); }
void callAfterInventoryItemsFetch(const uuid_vec_t& ids, nullary_func_t callback) {
    linked_fetch_ids = ids;
    linked_fetch_callback = callback;
}
class LLInventoryModelBackgroundFetch {
public:
    enum { FT_DEFAULT };
    bool mFolderFetchActive = false;
    int fetches = 0;
    std::vector<LLUUID> mExpectedFolderIds;
    static LLInventoryModelBackgroundFetch* getInstance() {
        static LLInventoryModelBackgroundFetch fetcher; return &fetcher;
    }
    static void backgroundFetchCB(void*) {}
    void incrFetchFolderCount(int n) { fetches += n; }
    void markFetchStarted() {}
    void fetchFolderAndLinks(const LLUUID&, nullary_func_t callback) { fetch_callbacks.push_back(callback); }
    void onAISFolderCalback(const LLUUID& expected, const LLUUID&, int) {
        assert(mExpectedFolderIds.size() == 1 && mExpectedFolderIds.front() == expected);
        mExpectedFolderIds.clear();
        --fetches;
    }
    void fetchCOF(nullary_func_t callback);
};

bool isAgentAvatarValid() { return true; }
struct LLTextBox {
    std::string text;
    void setText(std::string value) { text = value; }
};
struct Floater {};
struct Handle { Floater** ptr; Floater* get() const { return *ptr; } };
class FSForMeFittingRoom : public Floater {
public:
    int mWearRequest = 0;
    LLTextBox status;
    Floater* self = this;
    Handle getHandle() { return {&self}; }
    template<typename T> T* getChild(const char*) { return &status; }
    void wearSavedOutfit(const LLUUID&);
};
class FSForMeInventoryBrowser {
public:
    std::string mCategory = "all", mQuery;
    std::vector<LLUUID> mRecentItems;
    bool matches(const LLViewerInventoryItem*) const;
};
bool get_is_favorite(const LLUUID&) { return false; }
using llwchar = char32_t;
using LLWString = std::u32string;
struct LLWStringUtil {
    static void toLower(LLWString& value) { for (auto& c : value) c = std::towlower(c); }
};
LLWString utf8str_to_wstring(const std::string& text) {
    LLWString result;
    for (std::size_t i = 0; i < text.size(); ++i) {
        const unsigned char first = text[i];
        if (first < 0x80) result.push_back(first);
        else {
            assert(first < 0xe0 && i + 1 < text.size());
            const unsigned char second = text[++i];
            result.push_back(((first & 0x1f) << 6) | (second & 0x3f));
        }
    }
    return result;
}
std::string wstring_to_utf8str(const LLWString& value) {
    std::string result;
    for (auto c : value) {
        assert(c < 0x800);
        if (c < 0x80) result.push_back(static_cast<char>(c));
        else {
            result.push_back(static_cast<char>(0xc0 | (c >> 6)));
            result.push_back(static_cast<char>(0x80 | (c & 0x3f)));
        }
    }
    return result;
}
'''

SCENARIOS = r'''
int main() {
    auto& appearance = LLAppearanceMgr::instance();
    auto& inventory = gInventory;
    inventory.categories[{11}] = {.type = LLFolderType::FT_MY_OUTFITS};
    inventory.categories[{12}] = {.parent = {11}};
    LLViewerInventoryItem link{.category = inventory.getCategory({12})};
    inventory.items[LLUUID::null] = {{&link}};
    inventory.items[{99}] = {{&link}};

    // A missing or foreign COF must not read or delete another folder's links.
    assert(!appearance.getBaseOutfitLink());
    assert(appearance.findCOFItemLinks(link.linked_id).empty());
    appearance.mCOFID = {99};
    inventory.categories[{99}] = {.type = LLFolderType::FT_CURRENT_OUTFIT, .owner = {2}};
    appearance.removeCOFItemLinks(link.linked_id, {}, true);
    assert(removed.empty() && inventory.traversals == 0 && inventory.changed == 0);
    inventory.categories.erase({99});

    // AIS can deliver a COF that wasn't present when the request was queued.
    auto* fetcher = LLInventoryModelBackgroundFetch::getInstance();
    int completed = 0;
    fetcher->fetchCOF([&] { ++completed; });
    assert(fetcher->mExpectedFolderIds.front().isNull());
    inventory.categories[{13}] = {.type = LLFolderType::FT_CURRENT_OUTFIT};
    inventory.items[{13}] = {{&link}};
    AISAPI::pending({13});
    assert(completed == 1 && fetcher->fetches == 0 && fetcher->mExpectedFolderIds.empty());
    assert(appearance.getBaseOutfitLink() == &link);
    assert(appearance.findCOFItemLinks(link.linked_id).size() == 1);
    appearance.removeCOFItemLinks(link.linked_id, {}, true);
    assert(removed == std::vector<LLUUID>{link.id});

    // Cached link rows are insufficient until their target items have arrived.
    const LLUUID outfit{12};
    inventory.items[outfit] = {{&link}};
    FSForMeFittingRoom fitting;
    fitting.wearSavedOutfit(outfit);
    assert(appearance.applied == 0 && fetch_callbacks.size() == 1);
    fetch_callbacks.back()();
    assert(appearance.applied == 0);
    LLViewerInventoryItem target;
    link.linked_item = &target;

    // An older fetch answer cannot overtake the user's latest request.
    fitting.wearSavedOutfit(outfit);
    fitting.wearSavedOutfit(outfit);
    fetch_callbacks[1]();
    assert(appearance.applied == 0);
    fetch_callbacks[2]();
    fetch_callbacks[2]();
    assert(appearance.applied == 1);

    fitting.wearSavedOutfit(outfit);
    gAgent.session = {56};
    fetch_callbacks.back()();
    fitting.wearSavedOutfit(outfit);
    inventory.categories[outfit].parent = {42};
    fetch_callbacks.back()();
    inventory.categories[outfit].parent = {11};
    fitting.wearSavedOutfit(outfit);
    inventory.categories[outfit].complete = false;
    fetch_callbacks.back()();
    inventory.categories[outfit].complete = true;
    inventory.categories[{14}] = {.parent = outfit, .id = {14}, .complete = false};
    inventory.subfolders[outfit] = {{inventory.getCategory({14})}};
    fitting.wearSavedOutfit(outfit);
    fetch_callbacks.back()();
    assert(appearance.applied == 1);
    inventory.subfolders[outfit].clear();

    // With the legacy fetch, linked target IDs are requested after the folder.
    AISAPI::available = false;
    link.linked_item = nullptr;
    fitting.wearSavedOutfit(outfit);
    fetch_callbacks.back()();
    assert(appearance.applied == 1 && linked_fetch_ids == uuid_vec_t{link.linked_id});
    link.linked_item = &target;
    linked_fetch_callback();
    assert(appearance.applied == 2);
    AISAPI::available = true;
    fitting.wearSavedOutfit(outfit);
    fitting.self = nullptr;
    fetch_callbacks.back()();
    assert(appearance.applied == 2);

    // Default C-locale matching still folds Cyrillic names and search text.
    assert(std::setlocale(LC_CTYPE, "C"));
    FSForMeInventoryBrowser browser;
    browser.mCategory = "tattoos";
    browser.mQuery = lowercaseInventoryText("ёЖ");
    assert(browser.matches(&link));
    link.type = LLAssetType::AT_BODYPART;
    link.wearable_type = LLWearableType::WT_SKIN;
    assert(!browser.matches(&link));
    browser.mCategory = "accessories";
    link.type = LLAssetType::AT_OBJECT;
    link.inventory_type = LLInventoryType::IT_ATTACHMENT;
    assert(browser.matches(&link));
    browser.mCategory = "objects";
    assert(!browser.matches(&link));
    link.inventory_type = LLInventoryType::IT_OBJECT;
    assert(browser.matches(&link));
    std::cout << "Inventory workspace and outfit regression scenarios passed\n";
}
'''


if __name__ == '__main__':
    main()
