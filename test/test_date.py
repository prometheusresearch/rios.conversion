import rios.conversion.redcap.date as D

def ndays(year):
    d = ['%02d-01-%04d' % (m, year) for m in range(1,1 + 12)]
    d.append('01-01-%04d' % (year + 1))
    return [D.datediff(d[i + 1], d[i], 'd', 'mdy') for i in range(12)]

leap = [31.0, 29.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]
year = [31.0, 28.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]

assert ndays(2000) == leap
assert ndays(2001) == year     
