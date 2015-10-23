import rios.conversion.redcap.math as M

a = [i for i in range(1, 1 + 100)]
print('sum', M.sum_(*a))
print('mean', M.mean(*a))
print('median 1-100', M.median(*a))
print('median 1-99', M.median(*a[:-1]))
print('stddev', M.stdev(*a))
up = [0.1235, 0.2235, 0.3235, 0.4235, 0.5235]
dn = [0.1234, 0.2234, 0.3234, 0.4234, 0.5234]
p = 3
print('roundup')
for x in up:
    r = M.round_(x, p)
    u = M.roundup(x, p)
    d = M.rounddown(x, p)
    print(x, p, r, u, d)
    assert r == u
    assert u > d
print('rounddown')
for x in dn:
    r = M.round_(x, p)
    u = M.roundup(x, p)
    d = M.rounddown(x, p)
    print(x, p, r, u, d)
    assert r == d
    assert u > d
