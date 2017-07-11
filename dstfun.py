#!/usr/bin/python
#
# Copyright (C) 2017 Boris Dimitrov, dimiroll@gmail.com
#
# Utilities and tests for the fun subtleties of daylight savigns time.
#
# For example, computing the number of seconds since midnight is
# a deceptively simple question, which requires substantial machinery
# to do correctly for every point in time.  Fortunately, this machinery
# is already part of the C and Python standard libraries, and the
# function most_recent_midnight() below illustrates how to use it.
#
# The local timezone rules for changes to/from summer time are
# deliciously different in American and European time zones.
# In the US, the changes occur at 2am local time in each timezone.
# In Europe, the changes occurs at the same instant, at 1am GMT, in
# all timezones.  The function find_prev_and_next_dst_change computes
# the exact unixtime of the next time change in the local timezone.
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
    Of all unixtimes U that correspond to midnight in the local timezone, return the greatest U <= t.
    The default for t is now.
    """
    if t == None:
        t = time.time()
    ts = time.localtime(t)
    tsl = list(ts)
    # The tm_hour, tm_min, and tm_sec fields of a struct_time are read-only.
    # To clear those fields, we convert the struct_time to a list, zero out
    # liast elements 3, 4, 5, then convert the list back to a struct_time,
    # and we do that once for standard time and once for dst because we don't
    # know whether the most recent midnight is in standard or dst.
    tsl[3] = tsl[4] = tsl[5] = 0
    dst_options = (0, 1)
    if ts.tm_isdst not in dst_options:
        dst_options = (ts.tm_isdst,)
    for dst in dst_options:
        tsl[8] = dst
        ts = time.struct_time(tsl)
        assert ts.tm_hour == 0
        assert ts.tm_min == 0
        assert ts.tm_sec == 0
        assert ts.tm_isdst == dst
        mt = time.mktime(ts)
        mts = time.localtime(mt)
        if mts.tm_hour == 0 and mts.tm_min == 0 and mts.tm_sec == 0:
            return mt
    assert False


def find_dst_change(ta, tb):
    """
    Return unixtime t such that ta < t <= tb and is_dst differs at t-1 and t.
    If no such t exists, return None.
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

def find_prev_and_next_dst_change(tnow=None):
    if tnow == None:
        tnow = time.time()
    # there is 1 time change within any 7 month interval
    m7 = 7*30*24*3600
    last = find_dst_change(tnow - m7, tnow)
    next = find_dst_change(tnow, tnow + m7)
    return (last, next)

# ----------- The rest is fun test code ----------------
#

def fmt_time(t):
    t_fmt = "%A %X %Y-%m-%d %Z"
    return time.strftime(t_fmt, time.localtime(t))


def test(tnow=None):
    """
    Check that the most recent midnight is less than 25 hours in the past
    (almost 25 can happen during the transition from DST to standard time).
    
    Check that if there was a shorter/longer night within the last 7 months,
    the night was longer if the transition was to standard time, and shorter
    if the transition was to daylight savings time.
    
    Make sure to compute the most recent midnight for the moment immediately
    before and after a DST transition occurs, for both the most recent DST
    transition, and the one that's about to occur in the nearest future.

    """
    if tnow == None:
        tnow = time.time()
    lt = time.localtime(tnow)
    if 4 <= lt.tm_hour <= 11:
        print "Good morning!"
    elif 12 <= lt.tm_hour <= 16:
        print "Good afternoon."
    else:
        print "Good evening."
    print "It is {},".format(fmt_time(tnow)),
    mrm = most_recent_midnight(tnow)
    mrm_7mo = most_recent_midnight(tnow - 7*30*24*3600)  # mrm ~6 months ago
    # The 48, 46, and 2 below (as contrasted with 24, 23, 1) support
    # daylight savings time offset by 30 minutes from standard time.
    delta = int((mrm - mrm_7mo) / 1800.0) % 48
    if delta == 0:
        print "local timezone does not have daylight savings time."
        assert time.localtime(tnow).tm_isdst != 1
    elif delta >= 46:
        print "daylight savings time."
        assert time.localtime(tnow).tm_isdst == 1
    elif delta <= 2:
        print "standard time."
        assert time.localtime(tnow).tm_isdst == 0
    else:
        offset = (int(mrm - mrm_7mo) % (24 * 3600)) / 3600.0
        assert False, \
            "Unexpected offset {} hours between summer time and standard time.".format(offset)
    print "The most recent midnight was {}.".format(fmt_time(mrm))
    assert 0 <= int(tnow - mrm) < 25*3600
    assert list(time.localtime(mrm))[3:6] == [0, 0, 0]
    assert list(time.localtime(mrm_7mo))[3:6] == [0, 0, 0]
    last, next = find_prev_and_next_dst_change()
    print "Most recent time change:\n    from {}\n      to {}".format(
        fmt_time(last - 1), fmt_time(last))
    print "Next time change:\n    from {}\n      to {}".format(
        fmt_time(next - 1), fmt_time(next))
    # last and next will be None in timezones without DST, like Arizona
    if last != None and next != None:
        # These will fail an assert in the computation if something is wrong.
        print fmt_time(most_recent_midnight(next - 1)), fmt_time(most_recent_midnight(next))
        print fmt_time(most_recent_midnight(last - 1)), fmt_time(most_recent_midnight(last))


if __name__ == "__main__":
    test()
