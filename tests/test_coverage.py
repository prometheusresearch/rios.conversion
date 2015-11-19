from rios.conversion.balanced_match import *
from rios.conversion.classes import *
from rios.conversion.csv_reader import *

print('%s: testing ...' % __file__)

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
    except ValueError, e:
        assert True
    b, e = balanced_match('((a))+1', 0)
    assert (b, e) == (0, 5)

def test_csv_reader():
    csv_reader = CsvReader('tests/redcap/redcap_1.csv')
    csv_reader.load_reader()
    rows = [od for od in csv_reader]
    assert len(rows) == 30, len(rows)
 
print('%s: OK' % __file__)
