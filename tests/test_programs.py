import glob
import os
from rios.conversion.redcap.to_rios import ToRios as RedcapRios
from rios.conversion.redcap.from_rios import FromRios as RiosRedcap
from rios.conversion.qualtrics.to_rios import ToRios as QualtricsRios

def flatten(array):
    result = []
    for x in array:
        (result.append if isinstance(x, str) else result.extend)(x)
    return result

def redcap_rios_tst(name):
    test = [
            '--title', '%s' % name,
            '--id', 'urn:%s' % name,
            '--instrument-version', '1.0',
            '--infile', './tests/redcap/%s.csv' % name,
            '--outfile-prefix', './tests/sandbox/redcap/%s' % name,
            ]
    return [test + ['--format', 'json'], test + ['--format', 'yaml']]
    
def rios_redcap_tst(name):
    calc_filename = './tests/redcap/%s_c.yaml' % name
    test = [
            '-i', './tests/redcap/%s_i.yaml' % name,
            '-f', './tests/redcap/%s_f.yaml' % name,
            '-o', './tests/sandbox/redcap/%s.csv' % name,
            ]
    if os.access(calc_filename, os.F_OK):
            test = ['-c', '%s' % calc_filename] + test
        
    return [test]
      
def qualtrics_rios_tst(name):
    test = [
            '--instrument-version', '1.0',
            '--infile', './tests/qualtrics/%s.qsf' % name,
            '--outfile-prefix', './tests/sandbox/qualtrics/%s' % name,
            ]
    return [test + ['--format', 'json'], test + ['--format', 'yaml']]

def show_tst(cls, test):
    name = str(cls).split("'")[1]
    print('\n%s\n\t%s' % (name, ' '.join(test)))

def tst_class(cls, tests):
    program = cls()
    for test in boilerplate_tests + tests:
        show_tst(cls, test)
        try:
            program(test)
        except Exception, exc:
            print(exc)

csv_names = [
        os.path.basename(name)[:-4] 
        for name in glob.glob('./tests/redcap/*.csv') ]
rios_redcap_names = [
        os.path.basename(name)[:-7] 
        for name in glob.glob('./tests/redcap/*_i.yaml') ]
qsf_names = [
        os.path.basename(name)[:-4] 
        for name in glob.glob('./tests/qualtrics/*.qsf') ]

boilerplate_tests = [
        ['--help', ],
        ['-h', ],
        ['--version', ],
        ['-v', ], ]

print('%s: testing ...' % __file__)

rios_redcap_mismatch_tests = [
        [
        '-c', './tests/redcap/redcap_1_c.yaml',
        '-i', './tests/redcap/redcap_matrix_1_i.yaml',
        '-f', './tests/redcap/redcap_matrix_1_f.yaml',
        '-o', './tests/sandbox/redcap/mismatch_tests.csv',
        ],
        [
        '-c', './tests/redcap/redcap_1_c.yaml',
        '-i', './tests/redcap/redcap_matrix_1_i.yaml',
        '-f', './tests/redcap/redcap_1_f.yaml',
        '-o', './tests/sandbox/redcap/mismatch_tests.csv',
        ], ]
redcap_rios_tests = flatten([redcap_rios_tst(n) for n in csv_names])
rios_redcap_tests = flatten([rios_redcap_tst(n) for n in rios_redcap_names])
qualtrics_rios_tests = flatten([qualtrics_rios_tst(n) for n in qsf_names])

tst_class(RedcapRios, redcap_rios_tests)
tst_class(RiosRedcap, rios_redcap_tests + rios_redcap_mismatch_tests)
tst_class(QualtricsRios, qualtrics_rios_tests)

print('%s: OK' % __file__)
