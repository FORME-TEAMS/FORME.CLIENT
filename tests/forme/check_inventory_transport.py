#!/usr/bin/env python3
# Copyright (C) 2026 ForMe.World contributors.
# SPDX-License-Identifier: LGPL-2.1-only
"""Exercise the production AIS and category-capability transport decisions."""
from pathlib import Path
import subprocess
import tempfile

from check_appearance_startup import function

NEWVIEW = Path(__file__).resolve().parents[2] / 'indra/newview'


def main():
    inventory = (NEWVIEW / 'llinventorymodel.cpp').read_text()
    ais = (NEWVIEW / 'llaisapi.cpp').read_text()
    program = '\n'.join((
        STUBS,
        function(inventory, 'bool LLInventoryModel::isInventoryRequestCurrent('),
        function(inventory, 'void LLInventoryModel::createNewCategoryCoro('),
        function(ais, 'struct StaleAISResponse') + ';',
        function(ais, 'void AISAPI::EnqueueAISCommand('),
        function(ais, 'void AISAPI::InvokeAISCommandCoro('),
        function(ais, 'void AISUpdate::checkTimeout()'),
        SCENARIOS,
    ))
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / 'inventory_transport.cpp'
        binary = Path(directory) / 'inventory_transport'
        source.write_text(program)
        subprocess.run(['c++', '-std=c++20', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=undefined', '-fno-sanitize-recover=all',
                        str(source), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


STUBS = r'''
#include <cassert>
#include <functional>
#include <iostream>
#include <list>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

struct LLUUID {
    int value{};
    static const LLUUID null;
    bool isNull() const { return value == 0; }
    bool notNull() const { return !isNull(); }
    bool operator==(const LLUUID&) const = default;
    bool operator<(const LLUUID& other) const { return value < other.value; }
};
const LLUUID LLUUID::null;
struct LLSD {
    enum Kind { Undefined, Map, Array, Integer, Uuid, String } kind = Undefined;
    std::map<std::string, LLSD> fields;
    std::vector<LLSD> elements;
    int number{};
    std::string value;
    LLSD() = default;
    LLSD(int n) : kind(Integer), number(n) {}
    LLSD(LLUUID id) : kind(Uuid), number(id.value) {}
    LLSD(const char* str) : kind(String), value(str) {}
    LLSD(std::initializer_list<LLUUID> ids) : kind(Array) {
        for (const auto& id : ids) elements.emplace_back(id);
    }
    LLSD& operator[](const std::string& key) { kind = Map; return fields[key]; }
    const LLSD& operator[](const std::string& key) const {
        static const LLSD undefined;
        auto it = fields.find(key);
        return it == fields.end() ? undefined : it->second;
    }
    bool has(const std::string& key) const { return fields.contains(key); }
    bool isMap() const { return kind == Map; }
    bool isInteger() const { return kind == Integer; }
    bool isString() const { return kind == String; }
    LLUUID asUUID() const { return {kind == Uuid ? number : 0}; }
    int asInteger() const { return kind == Integer ? number : 0; }
    std::string asString() const { return value; }
    operator LLUUID() const { return asUUID(); }
    auto beginArray() const { return elements.begin(); }
    auto endArray() const { return elements.end(); }
};
std::ostream& operator<<(std::ostream& out, const LLSD&) { return out; }
std::string ll_pretty_print_sd(const LLSD&) { return {}; }
#define LL_INFOS(...) std::clog
#define LL_WARNS(...) std::clog
#define LL_DEBUGS(...) std::clog
#define LL_ENDL '\n'

namespace LLCore {
    class HttpRequest {
    public:
        using ptr_t = std::shared_ptr<HttpRequest>;
        using policy_t = int;
        enum { DEFAULT_POLICY_ID };
    };
    class HttpOptions {
    public:
        using ptr_t = std::shared_ptr<HttpOptions>;
        void setWantHeaders(bool) {}
        void setTimeout(int) {}
    };
    struct HttpHeaders { using ptr_t = std::shared_ptr<HttpHeaders>; };
    struct HttpStatus {
        int code;
        explicit HttpStatus(int code = 0, const char* = nullptr) : code(code) {}
        explicit operator bool() const { return code == 0 || (code >= 200 && code <= 299); }
        bool operator==(const HttpStatus&) const = default;
        int getType() const { return code; }
        std::string toString() const { return std::to_string(code); }
    };
}
enum { HTTP_FORBIDDEN = 403, HTTP_INTERNAL_ERROR = 500 };

LLSD reply;
std::function<void()> during_http;
int http_requests = 0;
namespace LLCoreHttpUtil {
    class HttpCoroutineAdapter {
    public:
        using ptr_t = std::shared_ptr<HttpCoroutineAdapter>;
        static constexpr auto HTTP_RESULTS = "http_result";
        static constexpr auto HTTP_RESULTS_CONTENT = "content";
        HttpCoroutineAdapter(const char*, int) {}
        LLSD postAndSuspend(LLCore::HttpRequest::ptr_t, const std::string&, LLSD,
                            LLCore::HttpOptions::ptr_t) {
            ++http_requests;
            if (during_http) during_http();
            return reply;
        }
        static LLCore::HttpStatus getStatusFromLLSD(const LLSD& response) {
            return LLCore::HttpStatus(response["status"].asInteger());
        }
    };
}
using Adapter = LLCoreHttpUtil::HttpCoroutineAdapter;
namespace LLFolderType { enum EType { FT_NONE = -1, FT_OUTFIT = 47 }; }
struct LLViewerInventoryCategory {
    enum { VERSION_INITIAL = 1, DESCENDENT_COUNT_UNKNOWN = -1 };
    LLUUID id, parent, owner;
    LLFolderType::EType type = LLFolderType::FT_NONE;
    std::string name;
    int version = VERSION_INITIAL, count = DESCENDENT_COUNT_UNKNOWN;
    LLViewerInventoryCategory() = default;
    LLViewerInventoryCategory(LLUUID id, LLUUID parent, LLFolderType::EType type, std::string name, LLUUID owner)
        : id(id), parent(parent), owner(owner), type(type), name(name) {}
    std::string getName() const { return name; }
    LLUUID getUUID() const { return id; }
    LLUUID getParentUUID() const { return parent; }
    int getVersion() const { return version; }
    int getDescendentCount() const { return count; }
    int getViewerDescendentCount() const { return count; }
    void setVersion(int v) { version = v; }
    void setDescendentCount(int c) { count = c; }
};
std::ostream& operator<<(std::ostream& out, const LLUUID& id) { return out << id.value; }
struct LLViewerInventoryItem {
    LLUUID getParentUUID() const { return {31}; }
    std::string getName() const { return "Item"; }
};
template<typename T> struct LLPointer {
    std::shared_ptr<T> pointer;
    LLPointer(T* p) : pointer(p) {}
    T* operator->() const { return pointer.get(); }
};
struct Agent {
    LLUUID session{1};
    bool region = true;
    LLUUID getID() const { return {19}; }
    LLUUID getSessionID() const { return session; }
    const bool* getRegion() const { return region ? &region : nullptr; }
} gAgent;
bool gDisconnected = false, gDoDisconnect = false;
using inventory_func_type = std::function<void(const LLUUID&)>;

class LLInventoryModel {
public:
    struct LLCategoryUpdate { LLCategoryUpdate(LLUUID, int) {} };
    std::map<LLUUID, LLViewerInventoryCategory> categories;
    LLViewerInventoryItem item;
    bool usable = true;
    int accounting = 0, writes = 0, refreshes = 0, removals = 0;
    LLViewerInventoryCategory* getCategory(LLUUID id) {
        auto found = categories.find(id);
        return found == categories.end() ? nullptr : &found->second;
    }
    LLViewerInventoryItem* getItem(LLUUID id) { return id == LLUUID{24} ? &item : nullptr; }
    bool isInventoryUsable() const { return usable; }
    void accountForUpdate(const LLCategoryUpdate&) { ++accounting; }
    void updateCategory(LLPointer<LLViewerInventoryCategory> cat) {
        if (cat->id.isNull()) return;
        ++writes;
        categories[cat->id] = *cat.pointer;
    }
    void fetchDescendentsOf(LLUUID) { ++refreshes; }
    void onObjectDeletedFromServer(LLUUID) { ++removals; }
    static bool isInventoryRequestCurrent(const LLUUID&);
    void createNewCategoryCoro(std::string, LLSD, inventory_func_type, LLUUID);
} gInventory;
namespace LLNotificationsUtil { void add(const char*) {} }
struct LLCoprocedureManager {
    using CoProcedure_t = std::function<void(Adapter::ptr_t&, const LLUUID&)>;
    CoProcedure_t queued;
    static LLCoprocedureManager& instance() { static LLCoprocedureManager manager; return manager; }
    int countPending(const char*) { return 0; }
    void enqueueCoprocedure(const char*, const std::string&, CoProcedure_t fn) { queued = fn; }
};
struct IdleCallbacks { void addFunction(void (*)(void*), void*) {} } gIdleCallbacks;
constexpr int MAX_SIMULTANEOUS_COROUTINES = 2048;

class AISAPI {
public:
    using completion_t = inventory_func_type;
    using invokationFn_t = std::function<LLSD(Adapter::ptr_t, LLCore::HttpRequest::ptr_t, std::string, LLSD,
                                            LLCore::HttpOptions::ptr_t, LLCore::HttpHeaders::ptr_t)>;
    enum COMMAND_TYPE { COPYINVENTORY, CREATEINVENTORY, COPYLIBRARYCATEGORY, FETCHCATEGORYCATEGORIES,
        FETCHCATEGORYCHILDREN, FETCHCATEGORYSUBSET, FETCHCATEGORYLINKS, FETCHCOF, FETCHITEM,
        UPDATECATEGORY, REMOVEITEM, REMOVECATEGORY };
    using ais_query_item_t = std::pair<std::string, LLCoprocedureManager::CoProcedure_t>;
    static inline std::list<ais_query_item_t> sPostponedQuery;
    enum { HTTP_TIMEOUT = 180 };
    static inline int applied = 0;
    static void onIdle(void*) {}
    static void onUpdateReceived(const LLSD&, COMMAND_TYPE, const LLSD&, const LLUUID&);
    static void InvokeAISCommandCoro(Adapter::ptr_t, invokationFn_t, std::string, LLUUID, LLSD,
                                    completion_t, COMMAND_TYPE, const LLUUID&);
    static void EnqueueAISCommand(const std::string&, invokationFn_t, const std::string&, const LLUUID&,
                                 const LLSD&, const completion_t&, COMMAND_TYPE);
};
using U32 = unsigned int;
struct Timer {
    bool expired = false;
    bool hasExpired() { return expired; }
    void setTimerExpirySec(float) {}
};
struct LLFrameTimer { static U32 getFrameCount() { return 1; } };
struct LLCoros { static void checkStop() {} };
std::function<void()> during_update;
namespace llcoro { void suspendUntilNextFrame() { if (during_update) during_update(); } }
struct AISUpdate {
    LLUUID mSessionID;
    Timer mTaskTimer;
    static inline Timer sBatchTimer;
    static inline U32 sBatchFrameCount = 1;
    static constexpr float AIS_TASK_EXPIRY_SECONDS = 0.008f, AIS_BATCH_EXPIRY_SECONDS = 0.010f;
    void checkTimeout();
};
void AISAPI::onUpdateReceived(const LLSD&, COMMAND_TYPE, const LLSD&, const LLUUID& session) {
    AISUpdate update{session, Timer{static_cast<bool>(during_update)}};
    update.checkTimeout();
    ++applied;
}
'''

SCENARIOS = r'''
int main() {
    const LLUUID session{1}, created{41}, parent{31};
    LLSD request;
    request["type"] = static_cast<int>(LLFolderType::FT_OUTFIT);
    request["parent_id"] = parent;
    reply["http_result"]["status"] = 200;
    reply["folder_id"] = created;
    reply["parent_id"] = parent;
    reply["type"] = request["type"];
    reply["name"] = "Outfit";

    std::vector<LLUUID> results;
    auto completed = [&](const LLUUID& id) { results.push_back(id); };
    auto assert_failed = [&] { assert(results == std::vector<LLUUID>{LLUUID::null}); results.clear(); };
    auto create = [&] { gInventory.createNewCategoryCoro("cap", request, completed, session); };

    // The legacy endpoint used to increment parent accounting for this malformed response.
    reply["folder_id"] = "bad UUID";
    create();
    assert_failed();
    assert(gInventory.accounting == 0 && gInventory.writes == 0);
    reply["folder_id"] = created;
    reply["parent_id"] = LLUUID{99};
    create();
    assert_failed();
    assert(gInventory.accounting == 0 && gInventory.writes == 0);
    reply["parent_id"] = parent;

    during_http = [] { gAgent.session = {2}; };
    create();
    assert_failed();
    const int sent = http_requests;
    create();
    assert_failed();
    assert(http_requests == sent && gInventory.accounting == 0 && gInventory.writes == 0);
    gAgent.session = session;
    during_http = {};
    create();
    assert(results == std::vector<LLUUID>{created});
    assert(gInventory.accounting == 1 && gInventory.writes == 1);
    results.clear();

    Adapter::ptr_t adapter = std::make_shared<Adapter>("fixture", 0);
    auto invoke = [](auto transport, auto request, auto url, auto body, auto options, auto) {
        return transport->postAndSuspend(request, url, body, options);
    };
    auto queue = [&](AISAPI::COMMAND_TYPE type) {
        AISAPI::EnqueueAISCommand("test", invoke, "cap", {24}, {}, completed, type);
    };
    auto run = [&] { LLCoprocedureManager::instance().queued(adapter, {}); };

    // Queue time, HTTP completion, and an in-update yield can each cross sessions.
    queue(AISAPI::FETCHITEM);
    gAgent.session = {2};
    const int before_queue = http_requests;
    run();
    assert_failed();
    assert(http_requests == before_queue && AISAPI::applied == 0);
    gAgent.session = session;
    during_http = [] { gDoDisconnect = true; };
    queue(AISAPI::FETCHITEM);
    run();
    assert_failed();
    assert(AISAPI::applied == 0);
    gDoDisconnect = false;
    during_http = {};
    during_update = [] { gAgent.region = false; };
    queue(AISAPI::FETCHITEM);
    run();
    assert_failed();
    assert(AISAPI::applied == 0);
    gAgent.region = true;
    during_update = {};

    // HTTP failures can echo an item ID or include update-like fields.
    reply["item_id"] = LLUUID{24};
    reply["http_result"]["status"] = 404;
    queue(AISAPI::FETCHITEM);
    run();
    assert_failed();
    assert(AISAPI::applied == 0);

    reply["http_result"]["status"] = 410;
    queue(AISAPI::REMOVEITEM);
    run();
    assert_failed();
    assert(gInventory.refreshes == 1 && gInventory.removals == 1 && AISAPI::applied == 0);

    reply["http_result"]["status"] = 200;
    reply["content"] = "non-map body";
    queue(AISAPI::FETCHITEM);
    run();
    assert_failed();
    assert(AISAPI::applied == 0);

    reply.fields.erase("content");
    queue(AISAPI::FETCHITEM);
    run();
    assert(results == std::vector<LLUUID>{LLUUID{24}} && AISAPI::applied == 1);
    results.clear();
    reply["_created_items"] = {LLUUID::null, LLUUID{70}, LLUUID{70}, LLUUID{71}};
    queue(AISAPI::CREATEINVENTORY);
    run();
    const std::vector<LLUUID> expected{{70}, {71}};
    assert(results == expected && AISAPI::applied == 2);
    results.clear();
    reply["_created_items"] = {LLUUID::null};
    queue(AISAPI::CREATEINVENTORY);
    run();
    assert_failed();
    std::cout << "Inventory transport response scenarios passed\n";
}
'''


if __name__ == '__main__':
    main()
