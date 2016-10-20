import traceback
import sys


from rios.conversion.exception import Error, ConversionFailureError
from rios.conversion.base import SUCCESS_MESSAGE
from rios.conversion import (
    redcap_to_rios,
    rios_to_redcap,
)
from utils import (
    show_tst, 
    redcap_to_rios_tsts,
    rios_tsts,
    no_error_tst_to_rios,
    no_error_tst_from_rios,
)


def to_rios_api_tst(api_func, tests):
    for test in tests:
        show_tst(api_func, test)
        try:
            package = api_func(**test)
        except Exception as exc:
            ex_type, ex, tb = sys.exc_info()
            if isinstance(exc, Error) \
                        or isinstance(exc, ConversionFailureError):
                print "Successful error handling (exception)"
                print "= EXCEPTION:"
                traceback.print_tb(tb)
                print str(exc)
            else:
                print "= EXCEPTION:"
                traceback.print_tb(tb)
                print repr(exc)
                raise exc
        else:
            if 'suppress' in test and test['suppress']:
                # Error output is suppressed
                if 'failure' in package:
                    # We have an error situation
                    if not package['failure']:
                        raise ValueError('Error output is empty')
                    elif ('instrument' in package
                                or 'form' in package
                                or 'calculationset' in package):
                        raise ValueError(
                            'Error output should not contain references'
                            ' to instrument, form, or calculationset'
                            ' configuration definitions')
                    else:
                        print "Successful error handling (logged)"
                else:
                    # We do NOT have an error situation
                    no_error_tst_to_rios(package)
            else:
                # Error output is NOT suppressed
                if 'failure' in package:
                    raise ValueError(
                        'Errors should only be logged if error suppression'
                        ' is set'
                    )
                else:
                    # We do NOT have an error situation
                    no_error_tst_to_rios(package)


def from_rios_api_tst(api_func, tests):
    for test in tests:
        show_tst(api_func, test)
        try:
            package = api_func(**test)
        except Exception as exc:
            ex_type, ex, tb = sys.exc_info()
            if isinstance(exc, Error) \
                        or isinstance(exc, ConversionFailureError):
                print "Successful error handling (exception)"
                print "= EXCEPTION:"
                traceback.print_tb(tb)
                print str(exc)
            else:
                print "= EXCEPTION:"
                traceback.print_tb(tb)
                print repr(exc)
                raise exc
        else:
            if 'suppress' in test and test['suppress']:
                # Error output is suppressed
                if 'failure' in package:
                    # We have an error situation
                    if not package['failure']:
                        raise ValueError('Error output is empty')
                    elif ('instrument' in package
                                or 'form' in package
                                or 'calculationset' in package):
                        raise ValueError(
                            'Error output should not contain references'
                            ' to instrument, form, or calculationset'
                            ' configuration definitions')
                    else:
                        print "Successful error handling (logged)"
                else:
                    # We do NOT have an error situation
                    no_error_tst_from_rios(package)
            else:
                # Error output is NOT suppressed
                if 'failure' in package:
                    raise ValueError(
                        'Errors should only be logged if error suppression'
                        ' is set'
                    )
                else:
                    # We do NOT have an error situation
                    no_error_tst_from_rios(package)

print "\n====== API TESTS ======"

def test_redcap_to_rios_api():
    to_rios_api_tst(redcap_to_rios, redcap_to_rios_tsts)

def test_rios_to_redcap_api():
    from_rios_api_tst(rios_to_redcap, rios_tsts)
