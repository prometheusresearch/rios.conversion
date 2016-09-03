import sys
import traceback


from rios.conversion.redcap.to_rios import RedcapToRios
from rios.conversion.redcap.from_rios import RedcapFromRios
from rios.conversion.qualtrics.to_rios import QualtricsToRios
from rios.conversion.qualtrics.from_rios import QualtricsFromRios
from rios.conversion.exception import Error, ConversionFailureError
from rios.conversion.base import SUCCESS_MESSAGE
from utils import (
    show_tst, 
    redcap_to_rios_tsts,
    qualtrics_to_rios_tsts,
    rios_tsts,
)


def to_rios_tst_class(cls, tests):
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
                traceback.print_tb(tb)
                print repr(exc)
                print exc
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


def from_rios_tst_class(cls, tests):
    for test in tests:
        tb = None
        exc = None
        show_tst(cls, test)
        converter = cls(**test)
        try:
            converter()
        except Exception as exc:
            ex_type, ex, tb = sys.exc_info()
            if isinstance(exc, Error) \
                        or isinstance(exc, ConversionFailureError):
                print "= EXCEPTION:"
                traceback.print_tb(tb)
                print str(exc)
                print "Successful error handling (exception)"
            else:
                print "= EXCEPTION:"
                traceback.print_tb(tb)
                print repr(exc)
                raise exc
        else:
            if SUCCESS_MESSAGE in converter.pplogs:
                print SUCCESS_MESSAGE
            else:
                print "Successful conversion test"


print "\n====== CLASS TESTS ======"


def test_redcap_to_rios_tsts():
    to_rios_tst_class(RedcapToRios, redcap_to_rios_tsts)

def test_qualtrics_to_rios_tsts():
    to_rios_tst_class(QualtricsToRios, qualtrics_to_rios_tsts)

def test_redcap_from_rios_tsts():
    from_rios_tst_class(RedcapFromRios, rios_tsts)

def test_rios_from_qualtrics_tsts():
    from_rios_tst_class(QualtricsFromRios, rios_tsts)
