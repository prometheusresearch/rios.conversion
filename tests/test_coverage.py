""" Specialized tests to insure complete coverage.
"""
from __future__ import print_function

from rios.conversion.utils.balanced_match import *
from rios.conversion.base.structures import *
from rios.conversion.utils.csv_reader import *
from rios.conversion.base.from_rios import FromRios
from rios.conversion.redcap.from_rios import RedcapFromRios
import collections
import json, yaml, os


print("\n====== COVERAGE TESTS ======")


DUMMY_ARGS = {
    'localization': None,
    'form': None,
    'instrument': None,
    'calculationset': None,
}


def test_add_field():
    type_object = TypeObject()
    field_object = FieldObject(id='test_field')
    type_object.add_field(field_object)
    assert type_object['record'][0]['id'] == 'test_field'

def test_add_parameter():
    web_form = WebForm()
    test_parameter = ParameterObject(type='test_type')
    web_form.add_parameter('test', test_parameter)
    assert web_form['parameters']['test']['type'] == 'test_type'

def test_add_type():
    instrument = Instrument()
    type_object = TypeObject(base='text')
    instrument.add_type('type_name', type_object)
    assert instrument['types']['type_name']['base'] == 'text'

def test_balanced_match():
    try:
        balanced_match('x', 0)
    except ValueError as e:
        assert True
    b, e = balanced_match('((a))+1', 0)
    assert (b, e) == (0, 5)

def test_convert_variables():
    rfr = RedcapFromRios
    answer = '[assessment_var] + [calculations_var] + [table][field]'
    assert answer == rfr.convert_variables(
            'assessment["assessment_var"] '
            '+ calculations["calculations_var"] '
            '+ table["field"]')

def test_csv_reader():
    csv_reader = CsvReader('tests/redcap/format_1.csv')
    csv_reader.load_reader()
    rows = [od for od in csv_reader]
    assert len(rows) == 24, len(rows)
