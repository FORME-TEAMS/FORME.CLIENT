#!/usr/bin/env python3
# Copyright (C) 2026, ForMe.World contributors.
# SPDX-License-Identifier: LGPL-2.1-only
"""Exercise marketplace catalog callbacks across same-URL region changes."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from check_appearance_startup import function

ROOT = Path(__file__).resolve().parents[2]


class MarketCatalogContext(unittest.TestCase):
    def test_region_changes_retire_catalog_requests(self):
        source = (ROOT / 'indra/newview/fsmarketbrowser.cpp').read_text()
        build = function(source, 'bool FSMarketBrowser::postBuild(')
        registration = build[build.index('if (mMode == "catalog")'):build.index('getChild<LLSearchEditor>("query")')]
        region_change_signature = 'void FSMarketBrowser::onCatalogRegionChange('
        region_change = function(source, region_change_signature) if region_change_signature in source else ''
        request = function(source, 'void FSMarketBrowser::request(')
        # Suspend the actual request before its response guard. The fixture
        # controls response order and deliberately reuses the same capability.
        code = STUBS + '\nvoid FSMarketBrowser::bindCatalog() {\n' + registration + '}\n}\n' + region_change
        code += '\n' + request[:request.index('        LLSD result;')]
        code += request[request.index('        auto* view ='):request.index('        const auto status =')]
        code += '        (void)data;\n        done(view, LLSD());\n    });\n}\n' + SCENARIOS
        with tempfile.TemporaryDirectory() as directory:
            cpp = Path(directory) / 'market_catalog_context.cpp'
            binary = Path(directory) / 'market_catalog_context'
            cpp.write_text(code)
            subprocess.run(['c++', '-std=c++20', '-Wall', '-Wextra', '-Werror',
                            '-fsanitize=undefined', '-fno-sanitize-recover=all',
                            str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


STUBS = r'''
#include <cassert>
#include <functional>
#include <string>
#include <utility>
#include <vector>
using U64 = unsigned long long;
using LLUUID = int;
struct LLSD {
    int rows = 0;
    static LLSD emptyArray() { return {}; }
};
struct Region {
    U64 handle;
    U64 getHandle() const { return handle; }
};
struct {
    Region region{1};
    std::function<void()> boundary;
    LLUUID getID() const { return 11; }
    LLUUID getSessionID() const { return 12; }
    const Region* getRegion() const { return &region; }
    int addRegionChangedCallback(std::function<void()> callback) { boundary = std::move(callback); return 1; }
    void enter(U64 handle) { region.handle = handle; if (boundary) boundary(); }
} gAgent;
std::string capability() { return "shared-market-capability"; }
enum { STATE_STARTED };
struct LLStartUp { static auto getStartupState() { return STATE_STARTED; } };
struct LLCoros {
    std::vector<std::function<void()>> replies;
    static LLCoros& instance() { static LLCoros coros; return coros; }
    void launch(const char*, std::function<void()> callback) { replies.push_back(std::move(callback)); }
    void reply(std::size_t index) { replies.at(index)(); }
};
class FSMarketBrowser {
public:
    std::string mMode = "catalog";
    LLUUID mAgent = gAgent.getID();
    LLUUID mSession = gAgent.getSessionID();
    std::string mCap = capability();
    U64 mRevision = 0;
    U64 mCatalogRegionHandle = 0;
    int mCatalogRegionChange = 0;
    bool mBusy = false;
    int mPage = 0;
    int mTotal = 0;
    int rendered = 0;
    LLSD mItems;
    struct Handle { FSMarketBrowser* ptr; FSMarketBrowser* get() const { return ptr; } };
    Handle getHandle() { return {this}; }
    bool isDead() const { return false; }
    bool getVisible() const { return true; }
    void status(const std::string&) {}
    void render() { ++rendered; }
    void bindCatalog();
    void onCatalogRegionChange();
    void request(LLSD data, std::function<void(FSMarketBrowser*, const LLSD&)> done);
};
'''

SCENARIOS = r'''
int main() {
    FSMarketBrowser catalog;
    catalog.bindCatalog();
    catalog.mItems.rows = 3;
    catalog.mPage = 3;
    catalog.mTotal = 12;
    int accepted = 0;
    auto callback = [&](FSMarketBrowser*, const LLSD&) { ++accepted; };

    catalog.request({}, callback);
    assert(catalog.mBusy);
    gAgent.enter(2);
    gAgent.enter(1); // The return to the same URL occurs before a draw.
    auto& coros = LLCoros::instance();
    coros.reply(0);
    assert(accepted == 0);
    assert(!catalog.mBusy && catalog.mTotal == 0 && catalog.mPage == 0 && catalog.mItems.rows == 0);

    catalog.request({}, callback);
    gAgent.enter(1); // A second signal for the same region does not retire a request.
    coros.reply(1);
    assert(accepted == 1 && !catalog.mBusy);

    gAgent.boundary = {};
    FSMarketBrowser product;
    product.mMode = "item";
    product.bindCatalog();
    assert(!gAgent.boundary);
}
'''

if __name__ == '__main__':
    unittest.main()
