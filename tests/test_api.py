import glob
import os
import traceback
import sys


from rios.core import (
    validate_instrument,
    validate_form,
    validate_calculationset,
)
from rios.conversion.exception import Error
from rios.conversion.convert import (
    redcap_to_rios,
    qualtrics_to_rios,
    #rios_to_redcap,
    #rios_to_qualtrics,
)


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


def show_tst(api_func, test):
    func_name = "= TEST FUNCTION: " + str(api_func.__name__)
    filename = "= TEST FILENAME: " + str(test['stream'].name)
    print '\n%s\n%s' % (func_name, filename)


def api_tst(api_func, tests):
    for test in tests:
        show_tst(api_func, test)
        try:
            package = api_func(**test)
        except Exception as exc:
            ex_type, ex, tb = sys.exc_info()
            if isinstance(exc, Error):
                print "Successful error handling (exception)"
            else:
                print "= EXCEPTION:"
                traceback.print_tb(tb)
                print repr(exc)
                raise exc
        else:
            if 'suppress' in test and test['suppress']:
                # Error output is suppressed
                if 'error' in package:
                    # We have an error situation
                    if not package['error']:
                        ValueError('Error output is empty')
                    elif ('instrument' in package
                                or 'form' in package
                                or 'calculationset' in package):
                        ValueError(
                            'Error output should not contain references'
                            ' to instrument, form, or calculationset'
                            ' configuration definitions')
                    else:
                        print "Successful error handling (logged)"
                else:
                    # We do NOT have an error situation
                    no_error_tst(package)
            else:
                # Error output is NOT suppressed
                if 'error' in package:
                    raise ValueError(
                        'Errors should only be logged if error suppression'
                        ' is set'
                    )
                else:
                    # We do NOT have an error situation
                    no_error_tst(package)


def no_error_tst(package):
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


csv_names = [
    os.path.basename(name)[:-4] 
    for name in glob.glob('./tests/redcap/*.csv')
]
qsf_names = [
    os.path.basename(name)[:-4] 
    for name in glob.glob('./tests/qualtrics/*.qsf')
]


redcap_to_rios_tsts = flatten(
    [redcap_to_rios_tsts(name) for name in csv_names]
)
qualtrics_to_rios_tsts = flatten(
    [qualtrics_to_rios_tsts(name) for name in qsf_names]
)

def test_api():
    print "\n====== API TESTS ======"
    api_tst(redcap_to_rios, redcap_to_rios_tsts)
    api_tst(qualtrics_to_rios, qualtrics_to_rios_tsts)
