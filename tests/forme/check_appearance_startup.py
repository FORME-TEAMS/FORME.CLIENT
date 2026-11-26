#!/usr/bin/env python3
# Copyright (C) 2026, ForMe.World contributors.
# SPDX-License-Identifier: LGPL-2.1-only
"""Run the production COF admission/fetch code against incomplete login inventory.

Only the inventory/network boundary is stubbed. The resolver, update admission
and fetch dispatcher are extracted from the viewer, rather than reimplemented.
This is not a substitute for linking/running the complete macOS viewer.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
NV = ROOT / 'indra/newview'


def function(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


class AppearanceStartup(unittest.TestCase):
    def test_production_admission_and_fetch(self):
        source = (NV / 'llappearancemgr.cpp').read_text()
        # Execute everything before the first appearance traversal/mutation.
        update = function(source, 'void LLAppearanceMgr::updateAppearanceFromCOF(')
        admission = update[:update.index('    LL_DEBUGS("Avatar")')]
        self.assertIn('if (!ensureCOF())', admission)
        code = STUBS + '\n'.join((
            function(source, 'void LLAppearanceMgr::initCOFID()'),
            function(source, 'bool LLAppearanceMgr::ensureCOF()'),
            admission + '''
    (void)enforce_item_restrictions; (void)enforce_ordering; (void)post_update_func;
    ++accepted_updates;
}
''',
            function(source, 'void callAfterCOFFetch(nullary_func_t cb)'),
        )) + SCENARIOS
        with tempfile.TemporaryDirectory() as directory:
            cpp = Path(directory) / 'appearance.cpp'
            exe = Path(directory) / 'appearance'
            cpp.write_text(code)
            subprocess.run(['c++', '-std=c++20', '-Wall', '-Wextra', '-Werror',
                            '-fsanitize=undefined', '-fno-sanitize-recover=all',
                            str(cpp), '-o', str(exe)], check=True)
            subprocess.run([str(exe)], check=True)

    def test_startup_binds_existing_cof_before_system_folder_wait(self):
        source = (NV / 'llstartup.cpp').read_text()
        build = source.index('        gInventory.buildParentChildMap();')
        common = source.index('        gInventory.createCommonSystemCategories();', build)
        self.assertIn('LLAppearanceMgr::instance().initCOFID();', source[build:common])
        # Normal initial appearance replay remains after inventory initialization.
        self.assertIn('callAfterCOFFetch(set_flags_and_update_appearance)', source[common:])

    def test_disappeared_category_diagnostic_is_safe(self):
        source = (NV / 'llappearancemgr.cpp').read_text()
        update = function(source, 'void LLAppearanceMgr::updateAppearanceFromCOF(')
        start = update.index('LLViewerInventoryCategory *cof =')
        diagnostic = update.index('cof->getVersion()', start)
        self.assertIn('if (!cof)', update[start:diagnostic])
        self.assertIn('return;', update[start:diagnostic])


STUBS = r'''
#include <cassert>
#include <functional>
#include <iostream>
#include <map>
using nullary_func_t = std::function<void()>;
struct LLUUID {
    int value = 0;
    bool notNull() const { return value != 0; }
    bool operator==(const LLUUID&) const = default;
    bool operator<(const LLUUID& other) const { return value < other.value; }
};
namespace LLFolderType { enum EType { FT_CURRENT_OUTFIT = 46, FT_NONE = -1 }; }
struct LLViewerInventoryCategory {
    enum { FETCH_NONE = 0 };
    LLFolderType::EType type = LLFolderType::FT_CURRENT_OUTFIT;
    LLUUID owner{1}, parent{10};
    int fetch_resets = 0;
    auto getPreferredType() const { return type; }
    auto getOwnerID() const { return owner; }
    auto getParentUUID() const { return parent; }
    void setFetching(int) { ++fetch_resets; }
};
struct Agent { LLUUID getID() const { return {1}; } } gAgent;
struct Inventory {
    bool usable = true;
    LLUUID selected{20};
    std::map<LLUUID, LLViewerInventoryCategory> categories;
    int lookups = 0, searches = 0;
    bool isInventoryUsable() const { return usable; }
    LLUUID getRootFolderID() const { return {10}; }
    LLViewerInventoryCategory* getCategory(LLUUID id) {
        ++lookups;
        auto it = categories.find(id);
        return it == categories.end() ? nullptr : &it->second;
    }
    LLUUID findCategoryUUIDForType(LLFolderType::EType) {
        ++searches;
        return selected;
    }
} gInventory;
int accepted_updates = 0, category_fetches = 0;
#define LL_INFOS(...) std::clog
#define LL_WARNS(...) std::clog
#define LL_ENDL '\n'
class LLAppearanceMgr {
public:
    LLUUID mCOFID;
    bool mIsInUpdateAppearanceFromCOF = false;
    static LLAppearanceMgr& instance() { static LLAppearanceMgr mgr; return mgr; }
    LLUUID getCOF() const { return mCOFID; }
    void initCOFID();
    bool ensureCOF();
    void updateAppearanceFromCOF(bool = true, bool = true, nullary_func_t = {});
};
namespace AISAPI {
    bool available = false;
    bool isAvailable() { return available; }
}
class LLInventoryModelBackgroundFetch {
public:
    int cof_fetches = 0;
    static LLInventoryModelBackgroundFetch* getInstance() {
        static LLInventoryModelBackgroundFetch fetch; return &fetch;
    }
    void fetchCOF(nullary_func_t cb) { ++cof_fetches; if (cb) cb(); }
};
void callAfterCategoryFetch(LLUUID id, nullary_func_t cb) {
    assert(id.notNull()); assert(gInventory.getCategory(id));
    ++category_fetches; if (cb) cb();
}
'''

SCENARIOS = r'''
int main() {
    auto& mgr = LLAppearanceMgr::instance();
    // Regression: idle callback arrives before the manager's COF was initialized.
    // An existing folder is resolved, without waiting for unrelated folders.
    gInventory.categories[{20}] = {};
    mgr.updateAppearanceFromCOF();
    assert(mgr.getCOF() == LLUUID{20}); assert(accepted_updates == 1);
    int searches = gInventory.searches;
    mgr.updateAppearanceFromCOF(false, false);
    assert(gInventory.searches == searches); assert(accepted_updates == 2);

    // Cached folder removed: no inventory traversal/mutation, no null dereference.
    gInventory.categories.clear();
    mgr.updateAppearanceFromCOF(); assert(accepted_updates == 2);
    // Once delivered, the normal initial appearance callback can proceed.
    gInventory.categories[{20}] = {};
    mgr.updateAppearanceFromCOF(); assert(accepted_updates == 3);

    // Stale cached UUID must resolve to the current root's folder.
    mgr.mCOFID = {999};
    assert(mgr.ensureCOF()); assert(mgr.mCOFID == LLUUID{20});
    // A folder from another account/library, a non-COF, or nested COF is refused.
    gInventory.categories[{20}].owner = {2};
    assert(!mgr.ensureCOF());
    gInventory.categories[{20}] = {};
    gInventory.categories[{20}].type = LLFolderType::FT_NONE;
    assert(!mgr.ensureCOF());
    gInventory.categories[{20}] = {};
    gInventory.categories[{20}].parent = {30};
    assert(!mgr.ensureCOF());
    gInventory.categories[{20}] = {};
    gInventory.usable = false;
    int lookups = gInventory.lookups;
    mgr.updateAppearanceFromCOF();
    assert(gInventory.lookups == lookups); assert(accepted_updates == 3);
    gInventory.usable = true;

    // Legacy fetch also resolves the category and preserves completion semantics.
    int completed = 0;
    mgr.mCOFID = {};
    callAfterCOFFetch([&] { ++completed; });
    assert(completed == 1); assert(category_fetches == 1);
    assert(gInventory.categories[{20}].fetch_resets == 1);
    gInventory.categories.clear();
    callAfterCOFFetch([&] { ++completed; mgr.updateAppearanceFromCOF(); });
    assert(completed == 2); assert(category_fetches == 1);
    assert(accepted_updates == 3);
    callAfterCOFFetch({}); // empty completion is legal on failure too

    // AIS can fetch a COF not present locally yet; the guard must not block it.
    AISAPI::available = true;
    callAfterCOFFetch([&] { ++completed; });
    assert(completed == 3);
    assert(LLInventoryModelBackgroundFetch::getInstance()->cof_fetches == 1);
    std::cout << "COF startup admission/fetch scenarios passed\n";
}
'''

if __name__ == '__main__':
    unittest.main()
