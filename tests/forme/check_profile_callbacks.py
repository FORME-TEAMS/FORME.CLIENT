#!/usr/bin/env python3
# Copyright (C) 2026, ForMe.World contributors.
# SPDX-License-Identifier: LGPL-2.1-only
"""Exercise profile prompts with the viewer's window and notification APIs stubbed."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from check_appearance_startup import function

NV = Path(__file__).resolve().parents[2] / 'indra/newview'


class ProfileCallbacks(unittest.TestCase):
    def test_prompt_responses_are_bound_to_the_window_and_session(self):
        permissions = (NV / 'llpanelprofile.cpp').read_text()
        profile = (NV / 'llfloaterprofile.cpp').read_text()
        callbacks = (
            function(permissions, 'void LLFloaterProfilePermissions::confirmModifyRights('),
            function(permissions, 'void LLFloaterProfilePermissions::rightsConfirmationCallback('),
            function(profile, 'void LLFloaterProfile::onClickCloseBtn('),
            function(profile, 'void LLFloaterProfile::onUnsavedChangesCallback('),
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'profile_callbacks.cpp'
            binary = Path(directory) / 'profile_callbacks'
            source.write_text(STUBS + '\n'.join(callbacks) + SCENARIOS)
            subprocess.run(['c++', '-std=c++20', '-Wall', '-Wextra', '-Werror',
                            '-Wno-unused-parameter', '-fsanitize=undefined',
                            '-fno-sanitize-recover=all', str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


STUBS = r'''
#include <cassert>
#include <functional>
#include <memory>
#include <string>
#include <utility>
namespace boost { using std::bind; }
using namespace std::placeholders;
using LLUUID = int;
using S32 = int;
struct LLSD {
    int option = 0;
    bool asBoolean() const { return option != 0; }
    LLSD& operator[](const char*) { return *this; }
    LLSD& operator=(const std::string&) { return *this; }
};
struct { LLUUID session = 21; LLUUID getSessionID() const { return session; } } gAgent;
struct LLSLURL {
    LLSLURL(const char*, LLUUID, const char*) {}
    std::string getSLURLString() const { return {}; }
};
namespace LLNotificationsUtil {
    using Callback = std::function<void(const LLSD&, const LLSD&)>;
    Callback pending;
    std::string prompt;
    void add(const char* name, const LLSD&, const LLSD&, Callback callback) {
        prompt = name;
        pending = std::move(callback);
    }
    int getSelectedOption(const LLSD&, const LLSD& response) { return response.option; }
}
void answer(int choice) {
    auto callback = std::move(LLNotificationsUtil::pending);
    assert(callback);
    callback({}, {choice});
}
class LLFloater {
    std::shared_ptr<LLFloater*> target = std::make_shared<LLFloater*>(this);
public:
    virtual ~LLFloater() { *target = nullptr; }
    bool dead = false;
    bool visible = true;
    bool isDead() const { return dead; }
    bool getVisible() const { return visible; }
    void closeFloater() { dead = true; visible = false; }
    template<typename T> struct Handle {
        std::shared_ptr<LLFloater*> target;
        T* get() const { return static_cast<T*>(*target); }
    };
    template<typename T> Handle<T> getDerivedHandle() { return {target}; }
};
struct CheckBox {
    bool checked = true;
    LLSD getValue() const { return {checked}; }
    void setValue(bool value) { checked = value; }
};
class LLFloaterProfilePermissions : public LLFloater {
public:
    void confirmModifyRights(bool);
    void rightsConfirmationCallback(const LLSD&, const LLSD&);
    bool mHasUnsavedPermChanges = false;
    const LLUUID mAvatarID = 1;
    CheckBox editRights;
    CheckBox* mEditObjectRights = &editRights;
};
class LLFloaterProfile : public LLFloater {
public:
    void onClickCloseBtn(bool);
    void onUnsavedChangesCallback(const LLSD&, const LLSD&, bool);
    struct Panel {
        bool unpublished = false;
        int saves = 0;
        bool hasUnpublishedClassifieds() const { return unpublished; }
        bool hasUnsavedChanges() const { return true; }
        void commitUnsavedChanges() { ++saves; }
    } panel;
    Panel* mPanelProfile = &panel;
};
'''

SCENARIOS = r'''
int main() {
    LLFloaterProfile active_profile;
    active_profile.onClickCloseBtn(false);
    assert(LLNotificationsUtil::prompt == "ProfileUnsavedChanges");
    answer(2);
    assert(active_profile.getVisible() && active_profile.panel.saves == 0);
    active_profile.onClickCloseBtn(false);
    answer(0);
    assert(active_profile.isDead() && active_profile.panel.saves == 1);

    LLFloaterProfilePermissions active_permissions;
    active_permissions.confirmModifyRights(true);
    assert(LLNotificationsUtil::prompt == "GrantModifyRights");
    answer(1);
    assert(!active_permissions.editRights.checked && !active_permissions.mHasUnsavedPermChanges);
    active_permissions.confirmModifyRights(false);
    assert(LLNotificationsUtil::prompt == "RevokeModifyRights");
    answer(0);
    assert(active_permissions.mHasUnsavedPermChanges);

    // Closing a permissions window during friend removal marks it dead before
    // its handle expires at the end of the frame.
    LLFloaterProfilePermissions closing_permissions;
    closing_permissions.confirmModifyRights(true);
    closing_permissions.closeFloater();
    answer(1);
    assert(closing_permissions.editRights.checked);

    LLFloaterProfile hidden_profile;
    hidden_profile.onClickCloseBtn(false);
    hidden_profile.visible = false;
    answer(0);
    assert(hidden_profile.panel.saves == 0);

    LLFloaterProfile previous_session_profile;
    previous_session_profile.onClickCloseBtn(false);
    ++gAgent.session;
    answer(0);
    assert(previous_session_profile.getVisible() && previous_session_profile.panel.saves == 0);

    LLFloaterProfilePermissions previous_session_permissions;
    previous_session_permissions.confirmModifyRights(true);
    ++gAgent.session;
    answer(0);
    assert(!previous_session_permissions.mHasUnsavedPermChanges);

    auto old_profile = std::make_unique<LLFloaterProfile>();
    old_profile->panel.unpublished = true;
    old_profile->onClickCloseBtn(false);
    assert(LLNotificationsUtil::prompt == "ProfileUnpublishedClassified");
    old_profile.reset();
    LLFloaterProfile replacement;
    answer(0);
    assert(replacement.getVisible() && replacement.panel.saves == 0);
}
'''

if __name__ == '__main__':
    unittest.main()
