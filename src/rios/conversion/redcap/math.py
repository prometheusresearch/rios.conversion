"""REDCap math routines
"""


def mean(*data):
    return sum(data) / float(len(data)) if data else 0.0


def median(*data):
    if data:
        sorted_data = sorted(data)
        n = len(sorted_data)
        if n % 2 == 1:
            return float(sorted_data[n / 2])
        else:
            m = n / 2
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
