import glob
import os
import sys
import traceback
import yaml
import simplejson
import re


from rios.conversion.redcap.to_rios import RedcapToRios
from rios.conversion.redcap.from_rios import RedcapFromRios
from rios.conversion.qualtrics.to_rios import QualtricsToRios
from rios.conversion.qualtrics.from_rios import QualtricsFromRios
from rios.conversion.base import SUCCESS_MESSAGE
from rios.conversion.exception import Error


def flatten(array):
    result = []
    for x in array:
        (result.append if isinstance(x, dict) else result.extend)(x)
    return result

def redcap_to_rios_tst(name):
    test_base = {
        'title': name,
        'id': 'urn:%s' % name,
        'instrument_version': '1.0',
        'stream': open('./tests/redcap/%s.csv' % name, 'r'),
        'description': '',
        'localization': 'en',
    }
    return [test_base,]

def qualtrics_to_rios_tst(name):
    test_base = {
        'title': name,
        'id': 'urn:%s' % name,
        'instrument_version': '1.0',
        'stream': simplejson.load(
            open('./tests/qualtrics/%s.qsf' % name, 'r')
        ),
        'description': '',
        'localization': 'en',
    }
    return [test_base,]
    
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
    name = "= TEST CLASS: " + str(cls.__name__)
    if 'stream' in test:
        filenames = "= TEST FILENAME: " + str(test['stream'].name)
    else:
        filenames = "= TEST FILENAMES:\n    " + "\n    ".join([
            test['instrument'].name,
            test['form'].name,
            (test['calculationset'].name if 'calculationset' in test \
                        else "No calculationset file"),
        ])
    print('\n%s\n%s' % (name, filenames))

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
rios_names = [
    os.path.basename(name)[:-7] 
    for name in glob.glob('./tests/rios/*_i.yaml')
]
qsf_names = [
    os.path.basename(name)[:-4] 
    for name in glob.glob('./tests/qualtrics/*.qsf')
    if not re.match('bad_json', os.path.basename(name)[:-4])
]


redcap_to_rios_tsts = flatten([redcap_to_rios_tst(n) for n in csv_names])
qualtrics_to_rios_tsts = flatten([qualtrics_to_rios_tst(n) for n in qsf_names])
rios_tsts = flatten([rios_tst(n) for n in rios_names])


print "\n====== TEST PROGRAMS ======"
def test_redcap_to_rios():
    tst_class(RedcapToRios, redcap_to_rios_tsts)
def test_qualtrics_to_rios():
    tst_class(QualtricsToRios, qualtrics_to_rios_tsts)
###def test_redcap_from_rios():
###    tst_class(RedcapFromRios, rios_tests)
def test_qualtrics_from_rios():
    tst_class(QualtricsFromRios, rios_tsts)
