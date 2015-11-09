import datetime


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
