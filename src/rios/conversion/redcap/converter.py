"""
Converts a redcap csv file into a series of json blobs
stored in files:

    - %(prefix)s.i.json   rios instrument
    - %(prefix)s.c.json   rios calculation
    - %(prefix)s.f.json   rios web form
"""

import argparse
import collections
import csv
import json
import re
import rios.conversion.csv as Csv
import rios.conversion.classes as Rios
import sys
import os

# Consecutive non-alpha chars.
RE_non_alphanumeric = re.compile(r'\W+')

# Remove leading and trailing underbars.
# result available as: \1
RE_strip_outer_underbars = re.compile(r'^_*(.*[^_])_*$')

# Remove leading integer comma.
# result available as: \1
RE_strip_integer_comma = re.compile('\d+,\s*(.*)')

# Find database reference:  [table_name][field_name]
# \1 => table_name, \2 => field_name
RE_database_ref = re.compile(r'\[([\w_]+)\]\[([\w_]+)\]')

# Find variable reference
# \1 => variable name
RE_variable_ref = re.compile(r'''\[([\w_]+)\]''')

# Find function call
# \1 => function name
RE_function = re.compile(r'([\w_]+\()')

# Find carat function: (base)^(exponent)
# \1 => base, \2 => exponent
RE_carat_function = re.compile(r'\((.+)\)^\((.+)\)')

FUNCTION_TO_PYTHON = {
        'min': 'min',
        'max': 'max',
        'mean': 'rios.conversion.redcap.math.mean',
        'median': 'rios.conversion.redcap.math.median',
        'sum': 'rios.conversion.redcap.math.sum_',
        'stdev': 'rios.conversion.redcap.math.stdev',

        'round': 'round',
        'roundup': 'rios.conversion.redcap.math.roundup',
        'rounddown': 'rios.conversion.redcap.math.rounddown',
        'sqrt': 'math.sqrt',
        'abs': 'abs',
        'datediff': 'rios.conversion.redcap.math.datediff',
        }
        
RE_funcs = {
        k: re.compile(r'(%s\()' % k) 
        for k in FUNCTION_TO_PYTHON.keys()}

class Csv2OrderedDict(Csv.CsvConverter):
    def get_name(self, name):
        return RE_strip_outer_underbars.sub(
                r'\1',
                RE_non_alphanumeric.sub('_', name.strip().lower()))

    def get_row(self, row):
        return collections.OrderedDict(zip(self.attributes, row))

class Csv2RedCapOrderedDict(Csv2OrderedDict):
    def get_name(self, name):
        """REDCap has several names for the 'choices' field
        but they all begin with 'choices'
        """
        x = super(Csv2RedCapOrderedDict, self).get_name(name)
        if x.startswith('choices'):
          x = 'choices_or_calculations'
        return x
        
class Converter(object):
    def __init__(self):
        args = self._get_args()
        self.prefix = args.prefix
        self.id = args.id
        self.version = args.version
        self.title = args.title
        self.localization = args.localization
        self.matrix_id = 0
        self(args.infile)
        
    def _get_args(self):
        parser = argparse.ArgumentParser(
                prog=os.path.basename(sys.argv[0]),
                formatter_class=argparse.RawTextHelpFormatter,
                description=__doc__)
        parser.add_argument(
                '--infile',
                required=True,
                type=argparse.FileType('r'),            
                help="The csv input file to process.  Use '-' for stdin.")
        parser.add_argument(
                '--prefix',
                required=True,
                help='The prefix for the output files')
        parser.add_argument(
                '--id',
                required=True,
                help='The instrument id to output.')
        parser.add_argument(
                '--version',
                required=True,
                help='The instrument version to output.')
        parser.add_argument(
                '--title',
                required=True,
                help='The instrument title to output.')
        parser.add_argument(
                '--localization',
                default='en',
                help='The default localization for the web form.')
        return parser.parse_args()
    
    def __call__(self, fname):
        """process the csv input and create output files.
        ``fname`` is a filename, file, (or anything accepted by csv.reader)
        """
        self.instrument = Rios.Instrument(
                id=self.id,
                version=self.version,
                title=self.title)
        self.calculations = Rios.CalculationSetObject(
                instrument=Rios.InstrumentReferenceObject(self.instrument),
                )
        self.form = Rios.WebForm(
                instrument=Rios.InstrumentReferenceObject(self.instrument),
                defaultLocalization=self.localization,
                title=self.localized_string_object(self.title),
                )
        self.calculation_variables = set()
        self.matrix_group_name = ''
        self.page_name = ''
        for od in Csv2RedCapOrderedDict(fname):
            if 'form_name' not in od:
                continue
            self.process_od(od)                
        self.create_instrument_file()
        self.create_calculation_file()
        self.create_form_file()
    
    def convert_calc(self, calc):
        """convert RedCap expression into Python

        - convert database reference:  [a][b] => assessment["a"]["b"]
        - convert assessment variable reference: [a] => assessment["a"]
        - convert calculation variable reference: [c] => calculations["c"]
        - convert redcap function names to python
        - convert caret to pow
        """
        s = RE_database_ref.sub(r'assessment["\1"]["\2"]', calc)
        s = RE_variable_ref.sub(
                r'%s["\1"]' % (
                        'calculations' 
                        if variable in self.variables 
                        else 'assessment'),
                s)
        for name, pattern in RE_funcs.items():
            s = pattern.sub(FUNCTION_TO_PYTHON[name], s)
        s = RE_carat_function.sub(r'math.pow(\1, \2)', s)
        return s
        
    def convert_text_type(self, text_type):
        if text_type.startswith('date'):
            return 'dateTime'
        elif text_type == 'integer':
            return 'integer'
        elif text_type == 'number':
            return 'float'
        else:
            return 'text'

    def create_calculation_file(self):
        if self.calculations:
            with open(self.filename('c'), 'w') as fo:
                json.dump(self.calculations, fo)

    def create_instrument_file(self):
        if self.instrument:
            with open(self.filename('i'), 'w') as fo:
                json.dump(self.instrument, fo)
        
    def create_form_file(self):
        if self.form:
            with open(self.filename('f'), 'w') as fo:
                json.dump(self.form, fo)

    def filename(self, kind):
        return '%(prefix)s.%(kind)s.json' % {
                'prefix':self.prefix,
                'kind': kind,
                }

    def get_choices_internal(self, od):
        return {
                x.strip().split(',')[0]: None
                for x in od['choices_or_calculations'].split('|') }
                
    def get_choices_external(self, od):
        return {
                RE_strip_integer_comma.sub(r'\1', x.strip()): None
                for x in od['choices_or_calculations'].split('|')
                }  

    def get_type(self, od):
        field_type = od['field_type']
        if field_type == 'text':
            val_min = od['text_validation_min']
            val_max = od['text_validation_max']
            text_type = self.convert_text_type(
                    od['text_validation_type_or_show_slider_number'])
            if val_min or val_max:
                bound_constraint = Rios.BoundConstraintObject()
                if val_min:
                    bound_constraint['min'] = val_min
                if val_max:
                    bound_constraint['max'] = val_max
                return Rios.TypeObject(
                        base=text_type, 
                        range=bound_constraint)
            else:
                return text_type 
        elif field_type == 'notes':
            return 'text'
        elif field_type in ['dropdown', 'radio']:
            return Rios.TypeObject(
                    base='enumeration',
                    enumerations=self.get_choices_internal(od), )
        elif field_type in ['checkbox', ]:
            return Rios.TypeObject(
                    base='enumerationSet',
                    enumerations=self.get_choices_internal(od), )
        elif field_type == 'calc':
            form_name = od['form_name']
            field_name = od['variable_field_name']
            if not self.calculations:
                self.calculations = Rios.CalculationSetObject(
                        instrument=Rios.InstrumentReferenceObject(
                                **self.instrument), )
            calc = self.convert_calc(od['choices_or_calculations'])
            self.calculations.add(Rios.CalculationObject(
                    id=field_name,
                    description=od['field_label'],
                    type='float',
                    method='python',
                    options={'expression': calc},
                    })
            assert field_name not in self.calculation_variables
            self.calculation_variables.add(field_name)
            return None
        elif field_type == 'slider':
            return Rios.TypeObject(
                    base='float',
                    range=Rios.BoundConstraintObject(min=0.0, max=100.0), )
        elif field_type == 'truefalse':
            return Rios.TypeObject(
                    base='boolean',
                    enumerations=Rios.EnumerationCollectionObject(
                            yes=Rios.EnumerationObject(description="True"),
                            no=Rios.EnumerationObject(description="False"),
                            ), )
        elif field_type == 'yesno':
            return Rios.TypeObject(
                    base='boolean',
                    enumerations=Rios.EnumerationCollectionObject(
                            yes=Rios.EnumerationObject(description="Yes"),
                            no=Rios.EnumerationObject(description="No"), ))
        else:
            return None

    def localized_string_object(self, string):
        return Rios.LocalizedStringObject({self.localization: string})

    def make_elements(self, od):
        element = Rios.ElementObject()
        elements = [element]
        section_header = od['section_header']
        if section_header:
            element['type'] = 'header'
            element['options'] = {
                    'text': 
                    self.localized_string_object(section_header)}
            element = Rios.ElementObject()
            elements.append(element)
        element['type'] = 'question'
        element['options'] = self.make_question(od)
        return elements 

    def make_field(self, od):
        field = Rios.FieldObject()
        field_type = self.get_type(od)
        if field_type:
            field['id'] = od['variable_field_name']
            field['description'] = od['field_label']
            field['type'] = field_type
            field['required'] = bool(od['required_field'])
            field['annotation'] = None
            field['explanation'] = None
            field['identifiable'] = bool(od['identifier'])
        return field
        
    def make_matrix_field(self, od):
        field = Rios.FieldObject()
        # Construct a unique name for this matrix
        field['id'] = 'matrix_%02d' * self.matrix_id
        self.matrix_id += 1
        field['description'] = od.get('section_header', '')
        field['type'] = {
                'base': 'matrix',
                'columns': [],
                'rows': [],
                }
        # Append the only column (a checkbox or radiobutton)
        # Use the matrix_group_name as the id.
        field['type']['columns'].append({
                'id': od['matrix_group_name'],
                'description': od['field_label'],
                'type': self.get_type(od),
                'required': bool(od['required_field']),
                'identifiable': bool(od['identifier']),
                })
        # Append the first row.
        field['type']['rows'].append({
                'id': od['variable_field_name'],
                'description': od['field_label'],
                'required': bool(od['required_field']),
                })
        return field

    def make_question(self, od):
        question = Rios.QuestionObject(fieldId=od['variable_field_name'])
        question['text'] = self.localized_string_object(od['field_label'])
        question['help'] = self.localized_string_object(od['field_note'])
        field_type = od['field_type']
        if field_type == 'truefalse':
            question.add_enumeration(Rios.DescriptorObject(
                    id=True,
                    text=self.localized_string_object("True"),))
            question.add_enumeration(Rios.DescriptorObject(
                    id=False,
                    text=self.localized_string_object("False"),))
        elif field_type == 'yesno':
            question.add_enumeration(Rios.DescriptorObject(
                    id=True,
                    text=self.localized_string_object("Yes"),))
            question.add_enumeration(Rios.DescriptorObject(
                    id=False,
                    text=self.localized_string_object("No"),))
        question['widget'] = self.make_widget(od)

        return question

    def process_od(self, od)
        page_name = od['form_name']
        if self.page_name != page_name:
            self.page_name = page_name
            self.page = Rios.PageObject(id=page_name)
            self.form.add_page(self.page)
            
        matrix_group_name = od.get('matrix_group_name', '')
        if matrix_group_name:
            if self.matrix_group_name != matrix_group_name:
                # Start a new matrix.
                self.matrix_group_name = matrix_group_name
                field = self.make_matrix_field(od)
                self.matrix_rows = field['type']['rows']
            else:
                # Append row to existing matrix.
                self.matrix_rows.append({
                        'id': od['variable_field_name'],
                        'description': od['field_label'],
                        'required': bool(od['required_field']),
                        })
                field = {}       
        else:
            self.matrix_group_name = ''
            field = self.make_field(od)
        if field:
            self.instrument.add_field(field)    

        elements = self.make_elements(od)
        if elements:
            self.page.add_element(elements)
        
if __name__ == '__main__':
    Converter()

