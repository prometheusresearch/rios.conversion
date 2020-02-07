#
# Copyright (c) 2016, Prometheus Research, LLC
#
# REDCap Function Routines
#

from __future__ import division


import datetime


__all__ = (
    'datediff',
    'mean',
    'median',
    'round_',
    'rounddown',
    'roundup',
    'stdev',
    'sum_',
)


def datediff(date1, date2, units, date_fmt="ymd"):
    def _datetime(date):
        return datetime.datetime(**dict(zip(
                [{'y': 'year', 'm': 'month', 'd': 'day'}[x]
                        for x in date_fmt],
                map(int, date.split('-')) )))

    def _timedelta(timedelta):
        days = timedelta.days
        if units == 'y':
            return days / 365
        elif units == 'M':
            return days / 30
        elif units == 'd':
            return days
        else:
            seconds = days * 24 * 3600 + timedelta.seconds
            if units == 'h':
                return seconds / 3600
            elif units == 'm':
                return seconds / 60
            elif units == 's':
                return seconds
            else:
                raise ValueError(units)

    if "today" in [date1, date2]:
        today = datetime.datetime.today()
    minuend = today if date1 == "today" else _datetime(date1)
    subtrahend = today if date2 == "today" else _datetime(date2)
    difference = minuend - subtrahend
    return _timedelta(difference)


def mean(*data):
    return sum(data) / float(len(data)) if data else 0.0


def median(*data):
    if data:
        sorted_data = sorted(data)
        n = len(sorted_data)
        if n % 2 == 1:
            return float(sorted_data[n // 2])
        else:
            m = n // 2
            return (sorted_data[m - 1] + sorted_data[m]) / 2.0
    else:
        return None


def round_(number, decimal_places):
    x = 10.0 ** decimal_places
    return round(x * number) / x


def rounddown(number, decimal_places):
    rounded = round_(number, decimal_places)
    if rounded <= number:
        return rounded
    else:
        x = 0.5 * 10 ** -decimal_places
        return round_(number - x, decimal_places)


def roundup(number, decimal_places):
    rounded = round_(number, decimal_places)
    if rounded >= number:
        return rounded
    else:
        x = 0.5 * 10 ** -decimal_places
        return round_(number + x, decimal_places)


def stdev(*data):
    """Calculates the population standard deviation."""
    n = len(data)
    if n < 2:
        return 0.0
    else:
        m = mean(*data)
        ss = sum((x - m) ** 2 for x in data)
        pvar = ss / n   # the population variance
        return pvar ** 0.5


def sum_(*data):
    return sum(data, 0)
