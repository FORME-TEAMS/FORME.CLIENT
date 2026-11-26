// Copyright (C) 2026, ForMe.World contributors.
// SPDX-License-Identifier: LGPL-2.1-only
#ifndef FORME_SYSTEM_FOLDERS_H
#define FORME_SYSTEM_FOLDERS_H

#include <chrono>
#include <cstdint>
#include <initializer_list>
#include <set>

namespace forme
{
// Tracks one login's system-folder requests. Each folder can complete once;
// callbacks from a previous login cannot complete a new login's requests.
template<typename FolderType>
class SystemFolders
{
public:
    using Clock = std::chrono::steady_clock;
    using Generation = std::uint64_t;
    static constexpr auto TIMEOUT = std::chrono::seconds(120);

    enum class Status { Inactive, Pending, Ready, Failed, TimedOut };

    Generation begin(std::initializer_list<FolderType> types, Clock::time_point now)
    {
        reset();
        mPending = types;
        mDeadline = now + TIMEOUT;
        mStatus = mPending.empty() ? Status::Ready : Status::Pending;
        return mGeneration;
    }

    void reset()
    {
        ++mGeneration;
        mPending.clear();
        mStatus = Status::Inactive;
    }

    Status status(Clock::time_point now) const
    {
        if (mStatus == Status::Pending && now >= mDeadline)
        {
            return Status::TimedOut;
        }
        return mStatus;
    }

    bool complete(Generation generation, FolderType type, bool success, Clock::time_point now)
    {
        if (generation != mGeneration || status(now) != Status::Pending || !mPending.erase(type))
        {
            return false;
        }

        if (!success)
        {
            mStatus = Status::Failed;
        }
        else if (mPending.empty())
        {
            mStatus = Status::Ready;
        }
        return true;
    }

private:
    Generation mGeneration{0};
    std::set<FolderType> mPending;
    Clock::time_point mDeadline;
    Status mStatus{Status::Inactive};
};
}
#endif
