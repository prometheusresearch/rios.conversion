import glob
import os
import re
import simplejson
import yaml
import six


def flatten(array):
    result = []
    for x in array:
        (result.append if isinstance(x, dict) else result.extend)(x)
    return result


def redcap_to_rios_tsts(name):
    test_base = {
            'title': name,
            'id': 'urn:%s' % name,
            'instrument_version': '1.0',
            'stream': open('./tests/redcap/%s.csv' % name, 'r'),
            'description': '',
            'localization': 'en',
    }
    test_suppress = dict(test_base, **{'suppress': True})
    return [test_base, test_suppress]

def qualtrics_to_rios_tsts(name):
    test_base = {
            'title': name,
            'id': 'urn:%s' % name,
            'instrument_version': '1.0',
            'stream': open('./tests/qualtrics/%s.qsf' % name, 'r'),
            'description': '',
            'localization': 'en',
    }
    test_suppress = dict(test_base, **{'suppress': True})
    test_filemetadata = dict(test_base, **{'filemetadata': True})
    test_combined = dict(test_suppress, **test_filemetadata)
    return [
        test_base,
        dict(test_base, **test_suppress),
        dict(test_base, **test_filemetadata),
        dict(test_base, **test_combined)
    ]

rios_redcap_mismatch_tests = [
    {
        'calculationset': open('./tests/rios/format_1_c.yaml', 'r'),
        'instrument': open('./tests/rios/matrix_1_i.yaml', 'r'),
        'form': open('./tests/rios/matrix_1_f.yaml', 'r'),
        'localization': None,
    },
    {
        'calculationset': open('./tests/rios/format_1_c.yaml', 'r'),
        'instrument': open('./tests/rios/matrix_1_i.yaml', 'r'),
        'form': open('./tests/rios/format_1_f.yaml', 'r'),
        'localization': None,
    },
]

def rios_tst(name):
    calc_filename = './tests/rios/%s_c.yaml' % name
    test_base = {
        'instrument': yaml.load(open('./tests/rios/%s_i.yaml' % name, 'r')),
        'form': yaml.load(open('./tests/rios/%s_f.yaml' % name, 'r')),
        'localization': None,
    }

    if os.access(calc_filename, os.F_OK):
        test = dict(
            {'calculationset': yaml.load(open(calc_filename, 'r'))},
            **test_base
        )
    else:
        test = dict(
            {'calculationset': None},
            **test_base
        )

    return [test,]

def show_tst(cls, test):
    class_name = "= TEST CLASS: " + str(cls.__name__)
    if 'stream' in test:
        if isinstance(test['stream'], dict):
            filenames = "= TEST INSTRUMENT TITLE: " + str(test['title'])
        elif isinstance(test['stream'], file):
            filenames = "= TEST FILENAME: " + str(test['stream'].name)
        else:
            filenames = None
    else:
        if isinstance(test['instrument'], dict):
            filenames = "= TEST INSTRUMENT TITLE: " \
                + str(test.get('title', 'No title available'))
        elif isinstance(test['instrument'], file):
            filenames = "= TEST FILENAMES:\n    " + "\n    ".join([
                test['instrument'].get('name', 'No instrument name'),
                test['form'].get('name', 'No form name'),
                (test['calculationset'].name if 'calculationset' in test \
                            else "No calculationset file"),
            ])
        else:
            filenmes = None
        
    print '\n{}'.format(class_name) \
        + ('\n{}'.format(filenames) if filenames else "")

def no_error_tst_to_rios(package):
    if 'instrument' not in package or not package['instrument']:
        raise ValueError('Missing instrument definition')
    elif 'form' not in package or not package['form']:
        raise ValueError('Missing form definition')
    elif 'calculationset' in package and not package['calculationset']:
        raise ValueError('Calculationset is missing definition data')
    elif 'logs' in package and not package['logs']:
        raise ValueError('Logs are missing logging data')
    else:
        print "Successful conversion test"


def no_error_tst_from_rios(package):
    if 'instrument' not in package or not package['instrument']:
        raise ValueError('Missing instrument definition')
    else:
        print "Successful conversion test"


csv_names = [
    os.path.basename(name)[:-4] 
    for name in glob.glob('./tests/redcap/*.csv')
]
qsf_names = [
    os.path.basename(name)[:-4] 
    for name in glob.glob('./tests/qualtrics/*.qsf')
]
rios_names = [
    os.path.basename(name)[:-7] 
    for name in glob.glob('./tests/rios/*_i.yaml')
]


redcap_to_rios_tsts = flatten(
    [redcap_to_rios_tsts(name) for name in csv_names]
)
qualtrics_to_rios_tsts = flatten(
    [qualtrics_to_rios_tsts(name) for name in qsf_names]
)
rios_tsts = flatten(
    [rios_tst(name) for name in rios_names]
)
