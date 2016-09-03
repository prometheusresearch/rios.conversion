import sys
import traceback


from rios.conversion.redcap.to_rios import RedcapToRios
from rios.conversion.redcap.from_rios import RedcapFromRios
from rios.conversion.qualtrics.to_rios import QualtricsToRios
from rios.conversion.qualtrics.from_rios import QualtricsFromRios
from rios.conversion.exception import Error
from rios.conversion.base import SUCCESS_MESSAGE
from utils import (
    show_tst, 
    redcap_to_rios_tsts,
    qualtrics_to_rios_tsts,
    rios_tsts,
)


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

print "\n====== CLASS TESTS ======"

def test_redcap_to_rios_tsts():
    tst_class(RedcapToRios, redcap_to_rios_tsts)

def test_qualtrics_to_rios_tsts():
    tst_class(QualtricsToRios, qualtrics_to_rios_tsts)

#def test_redcap_to_rios_tsts():
#    tst_class(RedcapFromRios, rios_tsts)

def test_rios_to_qualtrics_tsts():
    tst_class(QualtricsFromRios, rios_tsts)
