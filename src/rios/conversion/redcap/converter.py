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

# Find database reference
# \1 => table name, \2 => field name
RE_database_ref = re.compile(r'\[([\w_]+)\]\[([\w_]+)\]')

# Find variable reference
# \1 => variable name
RE_variable_ref = re.compile(r'''\[([\w_]+)\]''')

# Find function call
# \1 => function name
RE_function = re.compile(r'([\w_]+\()')

class Csv2OrderedDict(Csv.CsvConverter):
    def get_name(self, name):
        return RE_strip_outer_underbars.sub(
                r'\1',
                RE_non_alphanumeric.sub('_', name.strip().lower()))

    def get_row(self, row):
        return collections.OrderedDict(zip(self.attributes, row))

class Csv2RedCapOrderedDict(Csv2OrderedDict):
    def get_name(self, name):
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
                title=Rios.LocalizedStringObject(
                        {self.localization: self.title}),
                )
                
        self.matrix_group_name = ''
        self.page_name = ''
        for od in Csv2RedCapOrderedDict(fname):
            if 'form_name' not in od:
                continue
            page_name = od['form_name']
            if self.page_name != page_name:
                self.page_name = page_name
                self.form.add_page(Rios.PageObject(id=page_name))
                
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

        self.create_instrument_file()
        self.create_calculation_file()
        self.create_form_file()
    
    def convert_calc(self, calc):
        """convert RedCap expression into Python

        - convert variables:  [a][b] => a.["b"]
                              [a] => a

        - convert function names
        """
        s = RE_database_ref.sub(r'assessment["\1"]["\2"]', calc)
        s = RE_variable_ref.sub(r'assessment["\1"]', s)
        s = RE_function.sub(r'prism.conversion.redcap.math.\1', s)
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

    def get_choices(self, od):
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
                bound_constraint = {}
                if val_min:
                    bound_constraint['min'] = val_min
                if val_max:
                    bound_constraint['max'] = val_max
                return {
                        'base': text_type,
                        'range': bound_constraint, 
                        }
            else:
                return text_type 
        elif field_type == 'notes':
            return 'text'
        elif field_type in ['dropdown', 'radio']:
              return {
                      'base': 'enumeration',
                      'enumerations': self.get_choices(od),
                      }
        elif field_type in ['checkbox', ]:
              return {
                      'base': 'enumerationSet',
                      'enumerations': self.get_choices(od),
                      }
        elif field_type == 'calc':
              form_name = od['form_name']
              if not self.calculations:
                  self.calculations = {
                          'instrument': {
                                  'id': self.instrument['id'],
                                  'version': self.instrument['version'],
                                  },
                          'calculations': []
                          }
              calc = self.convert_calc(od['choices_or_calculations'])
              self.calculations['calculations'].append({
                      'id': od['variable_field_name'],
                      'description': od['field_label'],
                      'type': 'float',
                      'method': 'python',
                      'options': {'expression': calc},
                      })
              return None
        elif field_type == 'slider':
              return {
                      'base': 'float',
                      'range': {'min': 0, 'max': 100}
                      }
        elif field_type in ['truefalse', 'yesno']:
              return 'boolean'
        else:
              return None

    def make_field(self, od):
        field = {}
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
        
    def make_instrument(self, version, od):
        instrument = {}
        instrument['id'] = 'urn:' + od['form_name']
        instrument['version'] = version
        instrument['title'] = od['form_name']
        instrument['record'] = []
        return instrument

    def make_matrix_field(self, od):
        field = {}
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
        
if __name__ == '__main__':
    Converter()

