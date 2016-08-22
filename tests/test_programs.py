import glob
import os
from rios.conversion.redcap.to_rios import RedcapToRios as RedcapRios
from rios.conversion.redcap.from_rios import RedcapFromRios as RiosRedcap
from rios.conversion.qualtrics.to_rios import QualtricsToRios as QualtricsRios
from rios.conversion.qualtrics.from_rios import QualtricsFromRios as RiosQualtrics


DUMMY_ARGS_FROM_RIOS = {
    'outfile': None,
    'localization': None,
    'format': None,
    'verbose': None,
    'form': None,
    'instrument': None,
    'calculationset': None,
}


DUMMY_ARGS_TO_RIOS = {
    'outfile_prefix': None,
    'id': None,
    'instrument_version': None,
    'title': None,
    'localization': None,
    'format': None,
    'infile': None,
}


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
            'infile': './tests/redcap/%s.csv' % name,
            'outfile_prefix': './tests/sandbox/redcap/%s' % name,
            'localization': 'en',
    }
    test_json = dict({'format': 'json'}, **test_base)
    test_yaml = dict({'format': 'yaml'}, **test_base)
    return [test_json, test_yaml]
    
def rios_redcap_tst(name):
    calc_filename = './tests/redcap/%s_c.yaml' % name
    test_base = {
            'instrument': './tests/redcap/%s_i.yaml' % name,
            'form': './tests/redcap/%s_f.yaml' % name,
            'outfile': './tests/sandbox/redcap/%s.csv' % name,
            'verbose': True,
            'localization': None,
            
    }
    if os.access(calc_filename, os.F_OK):
        test_base = dict({'calculationset': calc_filename}, **test_base)
    else:
        test_base = dict({'calculationset': None}, **test_base)
        

    test_json = dict({'format': 'json'}, **test_base)
    test_yaml = dict({'format': 'yaml'}, **test_base)
    return [test_json, test_yaml]

rios_redcap_mismatch_tests = [
    {
        'calculationset': './tests/redcap/format_1_c.yaml',
        'instrument': './tests/redcap/matrix_1_i.yaml',
        'form': './tests/redcap/matrix_1_f.yaml',
        'outfile': './tests/sandbox/redcap/mismatch_tests.csv',
        'verbose': True,
        'localization': None,
        'format': 'yaml',
    },
    {
        'calculationset': './tests/redcap/format_1_c.yaml',
        'instrument': './tests/redcap/matrix_1_i.yaml',
        'form': './tests/redcap/format_1_f.yaml',
        'outfile': './tests/sandbox/redcap/mismatch_tests.csv',
        'verbose': True,
        'localization': None,
        'format': 'yaml',
    },
]
      
def qualtrics_rios_tst(name):
    test = [
            '--instrument-version', '1.0',
            '--infile', './tests/qualtrics/%s.qsf' % name,
            '--outfile-prefix', './tests/sandbox/qualtrics/%s' % name,
            ]
    if name.startswith('bad_'):
        return [test]
    else:
        return [test + ['--format', 'json'], test + ['--format', 'yaml']]

def rios_qualtrics_tst(name):
    calc_filename = './tests/qualtrics/%s_c.yaml' % name
    test = [
            '--verbose',
            '-i', './tests/qualtrics/%s_i.yaml' % name,
            '-f', './tests/qualtrics/%s_f.yaml' % name,
            '-o', './tests/sandbox/qualtrics/%s.txt' % name,
            ]
    if os.access(calc_filename, os.F_OK):
            test.extend(['-c', '%s' % calc_filename])
        
    return [test, test[1:]]
      
def show_tst(cls, test):
    name = repr(cls)
    print('\n%s\n\t%s' % (name, ' '.join(test)))

def tst_class(cls, tests):
    for test in tests:
        show_tst(cls, test)
        try:
            #print "++++"
            #print test
            #print "++++"
            program = cls(**test)
            #print "0000"
            program()
        except Exception, exc:
            print(exc)

csv_names = [
    os.path.basename(name)[:-4] 
    for name in glob.glob('./tests/redcap/*.csv')
]
rios_qualtrics_names = [
    os.path.basename(name)[:-7] 
    for name in glob.glob('./tests/qualtrics/*_i.yaml')
]
rios_redcap_names = [
    os.path.basename(name)[:-7] 
    for name in glob.glob('./tests/redcap/*_i.yaml')
]
qsf_names = [
    os.path.basename(name)[:-4] 
    for name in glob.glob('./tests/qualtrics/*.qsf')
]

print('%s: testing ...' % __file__)

#redcap_rios_tests = flatten([redcap_rios_tst(n) for n in csv_names])
rios_redcap_tests = flatten([rios_redcap_tst(n) for n in rios_redcap_names])
#qualtrics_rios_tests = flatten([qualtrics_rios_tst(n) for n in qsf_names])
#rios_qualtrics_tests = flatten([rios_qualtrics_tst(n) for n in rios_qualtrics_names])


#tst_class(RedcapRios, redcap_rios_tests)
tst_class(RiosRedcap, rios_redcap_tests + rios_redcap_mismatch_tests)
#tst_class(QualtricsRios(**DUMMY_ARGS_TO_RIOS), qualtrics_rios_tests)
#tst_class(RiosQualtrics(**DUMMY_ARGS_FROM_RIOS), rios_qualtrics_tests)

print('%s: OK' % __file__)
