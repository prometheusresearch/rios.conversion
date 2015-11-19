PAIRS = ['()', ]
LEFTS = {p[0]: p[1] for p in PAIRS}
RIGHTS = {p[1]: p[0] for p in PAIRS}


def balanced_match(string, start):
    assert start >= 0
    limit = len(string)
    assert start < limit
    char = string[start]
    level = 1
    if char in LEFTS:
        delta = 1
        comp = LEFTS[char]
    elif char in RIGHTS:
        delta = -1
        limit = -1
        comp = RIGHTS[char]
    else:
        raise ValueError('unable to match: %s in %s' % (char, string))
    position = start + delta
    while level > 0 and position != limit:
        next = string[position]
        position += delta
        if next == char:
            level += 1
        elif next == comp:
            level -= 1
    if delta == 1:
        return start, position
    else:
        return position + 1, start + 1
