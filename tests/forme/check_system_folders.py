#!/usr/bin/env python3
# Copyright (C) 2026 ForMe.World contributors.
# SPDX-License-Identifier: LGPL-2.1-only
"""Run the system-folder startup code with the inventory transport stubbed."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from check_appearance_startup import function

ROOT = Path(__file__).resolve().parents[2]
NEWVIEW = ROOT / 'indra/newview'


class SystemFolderStartup(unittest.TestCase):
    def test_creation_and_startup_gate(self):
        inventory = (NEWVIEW / 'llinventorymodel.cpp').read_text()
        startup = (NEWVIEW / 'llstartup.cpp').read_text()
        functions = (
            'void LLInventoryModel::ensureCategoryForTypeExists(',
            'LLUUID LLInventoryModel::findExistingCategoryUUIDForTypeInRoot(',
            'void LLInventoryModel::createCommonSystemCategories()',
            'LLInventoryModel::SystemFolders::Status LLInventoryModel::getSystemFolderStatus()',
            'void LLInventoryModel::resetSystemFolderTracking()',
        )
        gate = function(startup, 'if (STATE_INVENTORY_CALLBACKS  == LLStartUp::getStartupState())')
        ready = gate.index('        LLInventoryModelBackgroundFetch::instance().start();')
        gate = 'bool pollStartup() {\n' + gate[:ready] + '        return true;\n    }\n    return false;\n}\n'
        program = STUBS + '\n'.join(function(inventory, name) for name in functions) + gate + SCENARIOS
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'system_folders.cpp'
            binary = Path(directory) / 'system_folders'
            source.write_text(program)
            subprocess.run(['c++', '-std=c++20', '-Wall', '-Wextra', '-Werror',
                            '-fsanitize=undefined', '-fno-sanitize-recover=all',
                            '-I', str(NEWVIEW), str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

    def test_reset_and_localized_disconnect(self):
        startup = (NEWVIEW / 'llstartup.cpp').read_text()
        # Skip the forward declaration.
        self.assertIn('gInventory.resetSystemFolderTracking();', function(startup, 'void reset_login()\n'))
        for locale in ('en', 'ru'):
            strings = ET.parse(NEWVIEW / 'skins/default/xui' / locale / 'strings.xml')
            for key in ('LoginSystemFoldersFailed', 'LoginSystemFoldersTimedOut'):
                self.assertTrue(strings.findtext(f"string[@name='{key}']").strip())


STUBS = r'''
#include "formesystemfolders.h"
#include <cassert>
#include <functional>
#include <iostream>
#include <map>
#include <string>
#include <utility>
#include <vector>

struct LLUUID {
    int value{};
    static const LLUUID null;
    bool isNull() const { return value == 0; }
    bool notNull() const { return !isNull(); }
    bool operator==(const LLUUID&) const = default;
    bool operator<(const LLUUID& other) const { return value < other.value; }
};
const LLUUID LLUUID::null{};
std::ostream& operator<<(std::ostream& stream, const LLUUID& id) { return stream << id.value; }
namespace LLFolderType {
    enum EType { FT_ROOT_INVENTORY, FT_TRASH, FT_FAVORITE, FT_CALLINGCARD, FT_MY_OUTFITS,
                 FT_CURRENT_OUTFIT, FT_LANDMARK, FT_SETTINGS, FT_MATERIAL, FT_INBOX,
                 FT_MARKETPLACE_LISTINGS };
}
struct Category {
    LLFolderType::EType type;
    LLUUID id;
    auto getPreferredType() const { return type; }
    const LLUUID& getUUID() const { return id; }
};
namespace LLStringUtil { const std::string null; }
using inventory_func_type = std::function<void(const LLUUID&)>;
template<typename Map, typename Key>
auto get_ptr_in_map(const Map& map, const Key& key) {
    auto iter = map.find(key);
    return iter == map.end() ? nullptr : iter->second;
}
class LLInventoryModel {
public:
    using SystemFolders = forme::SystemFolders<LLFolderType::EType>;
    using cat_array_t = std::vector<const Category*>;
    std::map<LLUUID, cat_array_t*> mParentChildCategoryTree;
    cat_array_t root_children;
    LLUUID root{1};
    bool usable = true;
    SystemFolders mSystemFolders;
    std::vector<std::pair<LLFolderType::EType, inventory_func_type>> requests;

    LLUUID getRootFolderID() const { return root; }
    bool isInventoryUsable() const { return usable && root.notNull(); }
    void createNewCategory(const LLUUID&, LLFolderType::EType type, const std::string&,
                           inventory_func_type callback) {
        if (isInventoryUsable()) requests.emplace_back(type, std::move(callback));
        else callback(LLUUID::null);
    }
    void ensureCategoryForTypeExists(LLFolderType::EType, inventory_func_type = nullptr);
    LLUUID findExistingCategoryUUIDForTypeInRoot(LLFolderType::EType, const LLUUID&) const;
    void createCommonSystemCategories();
    SystemFolders::Status getSystemFolderStatus() const;
    void resetSystemFolderTracking();
} gInventory;
struct Agent {
    LLUUID session{2};
    const LLUUID& getSessionID() const { return session; }
} gAgent;

#define LL_WARNS(...) std::clog
#define LL_INFOS(...) std::clog
#define LL_ENDL '\n'
bool gDoDisconnect = false;
std::string reason;
int frames = 0;
int logout_requests = 0;
enum { STATE_INVENTORY_CALLBACKS };
struct LLStartUp { static auto getStartupState() { return STATE_INVENTORY_CALLBACKS; } };
struct LLTrans { static std::string getString(const char* key) { return key; } };
struct LLAppViewer {
    static LLAppViewer* instance() { static LLAppViewer viewer; return &viewer; }
    void sendSimpleLogoutRequest() { assert(!gDoDisconnect); ++logout_requests; }
    void forceDisconnect(const std::string& why) { assert(!gDoDisconnect); reason = why; gDoDisconnect = true; }
};
void do_startup_frame() { ++frames; }
'''

SCENARIOS = r'''
int main() {
    using namespace LLFolderType;
    using Folders = LLInventoryModel::SystemFolders;
    using Status = Folders::Status;
    const auto now = Folders::Clock::now();
    Folders tracker;
    auto generation = tracker.begin({FT_TRASH}, now);
    assert(tracker.status(now + std::chrono::seconds(119)) == Status::Pending);
    const auto deadline = now + std::chrono::seconds(120);
    assert(!tracker.complete(generation, FT_TRASH, true, deadline));
    assert(tracker.status(deadline) == Status::TimedOut);
    assert(tracker.complete(tracker.begin({FT_TRASH}, now), FT_TRASH, true, now));
    assert(tracker.status(deadline) == Status::Ready);

    auto& inventory = gInventory;
    const Category folders[] = {{FT_TRASH, {10}}, {FT_FAVORITE, {11}}, {FT_CALLINGCARD, {12}},
        {FT_MY_OUTFITS, {13}}, {FT_CURRENT_OUTFIT, {14}}, {FT_LANDMARK, {15}},
        {FT_SETTINGS, {16}}, {FT_MATERIAL, {17}}, {FT_INBOX, {18}}};
    inventory.mParentChildCategoryTree[inventory.root] = &inventory.root_children;
    for (const auto& folder : folders) inventory.root_children.push_back(&folder);
    inventory.createCommonSystemCategories();
    assert(inventory.requests.empty());
    assert(pollStartup());

    // Only an actual root folder satisfies startup. Duplicate callbacks and a
    // non-startup request cannot consume other folders' completions.
    inventory.root_children.resize(7);
    inventory.createCommonSystemCategories();
    assert(inventory.requests.size() == 2);
    assert(!pollStartup() && frames == 1 && !gDoDisconnect);
    auto material = inventory.requests[0].second;
    auto inbox = inventory.requests[1].second;
    inventory.root_children.push_back(&folders[7]);
    material({17});
    material(LLUUID::null);
    inventory.ensureCategoryForTypeExists(FT_MARKETPLACE_LISTINGS);
    inventory.requests.back().second({30});
    assert(inventory.getSystemFolderStatus() == Status::Pending);
    inventory.root_children.push_back(&folders[8]);
    inbox({18});
    assert(pollStartup());

    // A callback from an earlier attempt cannot complete even the same folder
    // for the same agent and root. The current attempt must hear its own reply.
    inventory.root_children.pop_back();
    inventory.resetSystemFolderTracking();
    inbox(LLUUID::null);
    assert(inventory.getSystemFolderStatus() == Status::Inactive);
    inventory.createCommonSystemCategories();
    inventory.root_children.push_back(&folders[8]);
    inbox({18});
    assert(inventory.getSystemFolderStatus() == Status::Pending);
    inventory.requests.back().second({18});
    assert(pollStartup());
    assert(logout_requests == 0);

    // A successful transport reply with no usable folder must fail startup.
    inventory.root_children.pop_back();
    inventory.createCommonSystemCategories();
    inventory.requests.back().second({18});
    assert(inventory.getSystemFolderStatus() == Status::Failed);
    assert(!pollStartup() && reason == "LoginSystemFoldersFailed");
    assert(!pollStartup() && gDoDisconnect);
    assert(logout_requests == 1);

    // A null reply fails immediately. It does not become ready after a
    // subsequent duplicate callback, even if the folder has appeared locally.
    gDoDisconnect = false;
    inventory.createCommonSystemCategories();
    inventory.requests.back().second(LLUUID::null);
    inventory.root_children.push_back(&folders[8]);
    inventory.requests.back().second({18});
    assert(inventory.getSystemFolderStatus() == Status::Failed);

    inventory.root = LLUUID::null;
    const auto request_count = inventory.requests.size();
    inventory.createCommonSystemCategories();
    assert(inventory.requests.size() == request_count);
    assert(inventory.getSystemFolderStatus() == Status::Failed);

    // The production startup gate surfaces an expired callback separately.
    inventory.mSystemFolders.begin({FT_TRASH}, Folders::Clock::now() - Folders::TIMEOUT);
    assert(!pollStartup() && reason == "LoginSystemFoldersTimedOut");
    assert(!pollStartup() && gDoDisconnect);
    assert(logout_requests == 2);
    assert(inventory.getSystemFolderStatus() == Status::Inactive);
    std::cout << "System-folder startup scenarios passed\n";
}
'''

if __name__ == '__main__':
    unittest.main()
