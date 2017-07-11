#!/usr/bin/python
#
# Copyright (C) 2017 Boris Dimitrov, dimiroll@gmail.com
#
# Utilities and tests for the fun subtleties of daylight savigns time.
#
# Example execution results:
"""
Good evening. It is Tuesday 02:28:37 2017-07-11 PDT, daylight savings time.
Most recent time change:
    from Sunday 01:59:59 2017-03-12 PST
      to Sunday 03:00:00 2017-03-12 PDT
Next time change:
    from Sunday 01:59:59 2017-11-05 PDT
      to Sunday 01:00:00 2017-11-05 PST
"""

import time


def most_recent_midnight(t=None):
    """
    Without arg, return the number of seconds elapsed between the unix epoch start
    at 00:00 on Jan 1, 1970 UTC and the most recent midnight in the local timezone.

    With arg t, return the max unixtime <= t that corresponds to a midnight in the
    local timezone.
    """
    if t == None:
        t = time.time()
    ts = time.localtime(t)
    # The tm_hour, tm_min, and tm_sec fields of a struct_time are read-only.
    # To clear those fields, we convert the struct_time to a list, zero out
    # list elements 3, 4, 5, then convert the list back to a struct_time.
    ts = list(ts)
    ts[3] = ts[4] = ts[5] = 0
    ts = time.struct_time(ts)
    assert(ts.tm_hour == 0)
    assert(ts.tm_min == 0)
    assert(ts.tm_sec == 0)
    # Now ts represents the most recent midnight in the local timezone.
    # Convert back to unixtime, and return.
    return time.mktime(ts)


def find_dst_change(ta, tb):
    """
    Return unixtime t such that ta < t <= tb and is_dst differs at t-1 and t,
    or None.
    """
    # Sometimes it's just fun to reimplement binary search.
    # Other times there is the bisect package.
    ta = int(ta)
    tb = int(tb)
    la = time.localtime(ta)
    lb = time.localtime(tb)
    if la.tm_isdst != lb.tm_isdst:
        while (ta + 1) < tb:
            tc = int((ta + tb) / 2)
            lc = time.localtime(tc)
            if la.tm_isdst != lc.tm_isdst:
                tb, lb = tc, lc
            else:
                ta, la = tc, lc
        if (ta + 1) == tb:
            return tb
    return None


# ----------- The rest is fun test code ----------------
#

def fmt_time(t):
    t_fmt = "%A %X %Y-%m-%d %Z"
    return time.strftime(t_fmt, time.localtime(t))


def test_most_recent_midnight(tnow=None):
    """
    Check that the most recent midnight is less than 25 hours in the past
    (almost 25 can happen during the transition from DST to standard time).
    
    Check that if there was a shorter/longer night within the last 6 months,
    the night was longer if the transition was to standard time, and shorter
    if the transition was to daylight savings time.
    
    This is a horrible test because it runs on different numbers every time.
    """
    if tnow == None:
        tnow = time.time()
    lt = time.localtime(tnow)
    if 4 <= lt.tm_hour <= 11:
        print "Good morning!",
    elif 12 <= lt.tm_hour <= 16:
        print "Good afternoon.",
    else:
        print "Good evening.",
    print "It is {},".format(fmt_time(tnow)),
    mrm = most_recent_midnight(tnow)
    mrm_6mo = most_recent_midnight(tnow - 6*30*24*3600)  # mrm ~6 months ago
    # The 48, 46, and 2 below (as contrasted with 24, 23, 1) support
    # daylight savings time offset by 30 minutes from standard time.
    delta = int((mrm - mrm_6mo) / 1800.0) % 48
    if delta == 0:
        print "Our timezone does not have daylight savings time, or our OS does not support it."
        assert time.localtime(tnow).tm_isdst != 1
    elif delta >= 46:
        print "daylight savings time."
        assert time.localtime(tnow).tm_isdst == 1
    elif delta <= 2:
        print "standard time."
        assert time.localtime(tnow).tm_isdst == 0
    else:
        offset = (int(mrm - mrm_6mo) % (24 * 3600)) / 3600.0
        assert False, \
            "Unexpected offset {} hours between summer time and standard time.".format(offset)
    assert 0 <= int(tnow - mrm) < 25*3600
    assert list(time.localtime(mrm))[3:6] == [0, 0, 0]
    assert list(time.localtime(mrm_6mo))[3:6] == [0, 0, 0]


def test_find_dst_change(tnow=None):
    if tnow == None:
        tnow = time.time()
    # there is 1 time change within any 7 month interval
    m7 = 7*30*24*3600
    last = find_dst_change(tnow - m7, tnow)
    next = find_dst_change(tnow, tnow + m7)
    print "Most recent time change:\n    from {}\n      to {}".format(
        fmt_time(last - 1), fmt_time(last))
    print "Next time change:\n    from {}\n      to {}".format(
        fmt_time(next - 1), fmt_time(next))


if __name__ == "__main__":
    tnow = time.time()
    test_most_recent_midnight(tnow)
    test_find_dst_change(tnow)
