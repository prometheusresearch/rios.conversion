import glob
import os
import sys
import traceback


from rios.conversion.exception import Error
from rios.conversion.base import SUCCESS_MESSAGE
from rios.conversion.redcap.to_rios import RedcapToRios
from rios.conversion.redcap.from_rios import RedcapFromRios
from rios.conversion.qualtrics.to_rios import QualtricsToRios
from rios.conversion.qualtrics.from_rios import QualtricsFromRios


def flatten(array):
    result = []
    for x in array:
        (result.append if isinstance(x, dict) else result.extend)(x)
    return result

def redcap_rios_tst(name):
    test_base = {
            'title': name,
            'id': 'urn:%s' % name,
            'instrument_version': '1.0',
            'stream': open('./tests/redcap/%s.csv' % name, 'r'),
            'description': '',
            'localization': 'en',
    }
    return [test_base,]

def qualtrics_rios_tst(name):
    test_base = {
            'title': name,
            'id': 'urn:%s' % name,
            'instrument_version': '1.0',
            'stream': open('./tests/qualtrics/%s.qsf' % name, 'r'),
            'description': '',
            'localization': 'en',
    }
    return [test_base,]
    
def rios_redcap_tst(name):
    calc_filename = './tests/rios/%s_c.yaml' % name
    test_base = {
            'instrument': open('./tests/redcap/%s_i.yaml' % name, 'r'),
            'form': open('./tests/redcap/%s_f.yaml' % name, 'r'),
            'localization': None,
            
    }
    if os.access(calc_filename, os.F_OK):
        test = dict(
            test_base,
            **{'calculationset': open(calc_filename, 'r')}
        )
    else:
        test = dict(test_base, **{'calculationset': None})
        
    return [test,]


def rios_tst(name):
    calc_filename = './tests/rios/%s_c.yaml' % name
    test_base = {
        'instrument': open('./tests/rios/%s_i.yaml' % name, 'r'),
        'form': open('./tests/rios/%s_f.yaml' % name, 'r'),
        'localization': None,
    }
    if os.access(calc_filename, os.F_OK):
        test = dict(test_base, **{'calculationset': open(calc_filename, 'r')})
    else:
        test = dict(test_base, **{'calculationset': None})

    return [test,]

def show_tst(cls, test):
    class_name = "= TEST CLASS: " + str(cls.__name__)
    filename = "= TEST FILENAME: " + str(test['stream'].name)
    print('\n%s\n%s' % (class_name, filename))

def tst_class(cls, tests):
    for test in tests:
        tb = None
        exc = None
        show_tst(cls, test)
        converter = cls(**test)
        try:
            converter()
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
            if SUCCESS_MESSAGE in converter.pplogs:
                print "Successful conversion test"
            else:
                raise ValueError(
                    "Logged extraneous messages for a successful conversion"
                )

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


redcap_rios_tests = flatten([redcap_rios_tst(n) for n in csv_names])
qualtrics_rios_tests = flatten([qualtrics_rios_tst(n) for n in qsf_names])
###rios_redcap_tests = flatten([rios_tst(n) for n in rios_names])
rios_qualtrics_tests = flatten([rios_tst(n) for n in rios_names])


def test_classes():
    print "\n====== CLASS TESTS ======"
    tst_class(RedcapToRios, redcap_rios_tests)
    tst_class(QualtricsToRios, qualtrics_rios_tests)
    ###tst_class(RedcapFromRios, rios_redcap_tests)
    tst_class(QualtricsFromRios, rios_qualtrics_tests)
