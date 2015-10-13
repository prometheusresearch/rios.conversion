"""
Converts a redcap csv file into a series of output files

    - <prefix>_i.<format>   rios instrument
    - <prefix>_c.<format>   rios calculation
    - <prefix>_f.<format>   rios web form
"""

import argparse
import csv
import json
import re
import rios.conversion.csv_reader
import rios.conversion.classes as Rios
import sys
import os
import yaml

# Consecutive non-alpha chars.
RE_non_alphanumeric = re.compile(r'\W+')

# Remove leading and trailing underbars.
# result available as: \1
RE_strip_outer_underbars = re.compile(r'^_*(.*[^_])_*$')

# Find database reference:  [table_name][field_name]
# \1 => table_name, \2 => field_name
RE_database_ref = re.compile(r'\[([\w_]+)\]\[([\w_]+)\]')

# Find variable reference
# \1 => variable name
RE_variable_ref = re.compile(r'''\[([\w_]+)\]''')

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
        'round': 'rios.conversion.redcap.math.round_',
        'roundup': 'rios.conversion.redcap.math.roundup',
        'rounddown': 'rios.conversion.redcap.math.rounddown',
        'sqrt': 'math.sqrt',
        'abs': 'abs',
        'datediff': 'rios.conversion.redcap.date.datediff',
        }

# dict of function name: pattern which finds "name("
RE_funcs = {
        k: re.compile(r'%s\(' % k) 
        for k in FUNCTION_TO_PYTHON.keys()}

OPERATOR_TO_PYTHON = [
        # = (but not !=, <= or >=) to ==
        (r'([^!<>])=', r'\1=='),

        # <> to !=
        (r'<>', r'!='),
        ]

RE_ops = [(re.compile(pat), repl) for pat, repl in OPERATOR_TO_PYTHON]
                
class Csv2OrderedDict(rios.conversion.csv_reader.CsvReader):
    def get_name(self, name):
        """ Return canonical name.
        - replace non-alphanumeric with underbars.
        - strip leading and trailing underbars.
        - ensure 'choices' field is 'choices_or_calculations' 
          (REDCap has several names for the 'choices' field
          but they all begin with 'choices')
        - convert to lowercase.
        """
        x = RE_strip_outer_underbars.sub(
                r'\1',
                RE_non_alphanumeric.sub('_', name.strip().lower()))
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
        self.format = args.format
        self(args.infile)
        
    def _get_args(self):
        parser = argparse.ArgumentParser(
                prog=os.path.basename(sys.argv[0]),
                formatter_class=argparse.RawTextHelpFormatter,
                description=__doc__)
        parser.add_argument(
                '--format',
                default='yaml',
                choices=['yaml', 'json'],
                help='The format for the output files.  '
                        'The default is "yaml".')
        parser.add_argument(
                '--id',
                required=True,
                help='The instrument id to output.')
        parser.add_argument(
                '--infile',
                required=True,
                type=argparse.FileType('r'),            
                help="The csv input file to process.  Use '-' for stdin.")
        parser.add_argument(
                '--localization',
                default='en',
                help='The default localization for the web form.  '
                        'The default is "en"')
        parser.add_argument(
                '--prefix',
                required=True,
                help='The prefix for the output files')
        parser.add_argument(
                '--title',
                required=True,
                help='The instrument title to output.')
        parser.add_argument(
                '--version',
                required=True,
                help='The instrument version to output.')
        return parser.parse_args()
    
    def __call__(self, fname):
        """process the csv input, and create output files.
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
        for od in Csv2OrderedDict(fname):
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
        variables = RE_variable_ref.findall(s)
        s = RE_variable_ref.sub(r'calculations["\1"]', s)
        for var in variables:
            if var not in self.calculation_variables:
                s = s.replace(
                        'calculations["%s"]' % var, 
                        'assessment["%s"]' % var)
        for name, pattern in RE_funcs.items():
            # the matched pattern includes the '('
            s = pattern.sub('%s(' % FUNCTION_TO_PYTHON[name], s)
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

    def convert_trigger(self, trigger):
        s = self.convert_calc(trigger)
        for pattern, replacement in RE_ops:
            s = pattern.sub(replacement, s)
        return 'rios.conversion.redcap.math.not_(%s)' % s
        
    def convert_value(self, value, text_type):
        if text_type == 'integer':
            return int(value)
        elif text_type == 'float':
            return float(value)
        else:
            return value

    def create__file(self, kind, obj):
        if obj:
            obj.clean()
            with open(self.filename(kind), 'w') as fo:
                if self.format == 'json':
                    json.dump(obj, fo, indent=1)
                elif self.format == 'yaml':
                    yaml.safe_dump(
                            json.loads(json.dumps(obj)), 
                            fo, 
                            default_flow_style=False)

    def create_calculation_file(self):
        self.create__file('c', self.calculations)

    def create_instrument_file(self):
        self.create__file('i', self.instrument)
        
    def create_form_file(self):
        self.create__file('f', self.form)

    def filename(self, kind):
        return '%(prefix)s_%(kind)s.%(extension)s' % {
                'prefix':self.prefix,
                'kind': kind, 
                'extension': self.format, }

    def get_choices_form(self, od):
        """ returns array of DescriptorObject
        Expecting: choices_or_calculations to be pipe separated list 
        of (comma delimited) tuples: internal, external
        """
        return [
                Rios.DescriptorObject(
                        id=x.strip().split(',')[0].lower(),
                        text=self.localized_string_object(
                                ','.join(x.strip().split(',')[1:])),)
                for x in od['choices_or_calculations'].split('|') ]

    def get_choices_instrument(self, od):
        """ returns EnumerationCollectionObject
        Expecting: choices_or_calculations to be pipe separated list 
        of (comma delimited) tuples: internal, external
        """
        return Rios.EnumerationCollectionObject(**{
                x.strip().split(',')[0].lower(): None
                for x in od['choices_or_calculations'].split('|') })
                
    def get_type(self, od):
        """returns the computed instrument field type.
        Also has side effects.
        - can initialize self.calculations.
        - can append a calculation.
        - updates self.question: 
            enumerations, questions, rows, widget, events
        """
        def get_widget(type):
            return Rios.WidgetConfigurationObject(type=type)

        def get_widget_type(text_type):
            if text_type == 'text':
                return 'inputText'
            elif text_type in ['integer', 'float']:
                return 'inputNumber'
            elif text_type == 'dateTime':
                return 'dateTimePicker'
            else:
                raise ValueError, ('unexpected text type', text_type)
                 
        def process_calculation():
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
                    options={'expression': calc}, ))
            assert field_name not in self.calculation_variables
            self.calculation_variables.add(field_name)
            return None # not an instrument field

        def process_checkbox():
            self.question.set_widget(get_widget(type='checkGroup'))
            self.question['enumerations'] = self.get_choices_form(od)
            return Rios.TypeObject(
                    base='enumerationSet',
                    enumerations=self.get_choices_instrument(od), )

        def process_dropdown():
            self.question.set_widget(get_widget(type='dropDown'))
            self.question['enumerations'] = self.get_choices_form(od)
            return Rios.TypeObject(
                    base='enumeration',
                    enumerations=self.get_choices_instrument(od), )

        def process_notes():
            self.question.set_widget(get_widget(type='textArea'))
            return 'text'

        def process_radio():
            self.question.set_widget(get_widget(type='radioGroup'))
            self.question['enumerations'] = self.get_choices_form(od)
            return Rios.TypeObject(
                    base='enumeration',
                    enumerations=self.get_choices_instrument(od), )

        def process_slider():
            self.question.set_widget(get_widget(type='inputNumber'))
            return Rios.TypeObject(
                    base='float',
                    range=Rios.BoundConstraintObject(
                            min=0.0, 
                            max=100.0), )

        def process_text():
            val_min = od['text_validation_min']
            val_max = od['text_validation_max']
            text_type = self.convert_text_type(
                    od['text_validation_type_or_show_slider_number'])
            self.question.set_widget(get_widget(
                    type=get_widget_type(text_type)))
            if val_min or val_max:
                bound_constraint = Rios.BoundConstraintObject()
                if val_min:
                    bound_constraint['min'] = self.convert_value(
                            val_min, 
                            text_type)
                if val_max:
                    bound_constraint['max'] = self.convert_value(
                            val_max, 
                            text_type)
                return Rios.TypeObject(
                        base=text_type, 
                        range=bound_constraint)
            else:
                return text_type 

        def process_truefalse():        
            self.question.set_widget(get_widget(type='radioGroup'))
            self.question.add_enumeration(Rios.DescriptorObject(
                    id="True",
                    text=self.localized_string_object("True"),))
            self.question.add_enumeration(Rios.DescriptorObject(
                    id="False",
                    text=self.localized_string_object("False"),))
            return Rios.TypeObject(
                    base='boolean',
                    enumerations=Rios.EnumerationCollectionObject(
                            yes=Rios.EnumerationObject(description="True"),
                            no=Rios.EnumerationObject(description="False"),
                            ), )

        def process_yesno():
            self.question.set_widget(get_widget(type='radioGroup'))
            self.question.add_enumeration(Rios.DescriptorObject(
                    id="Yes",
                    text=self.localized_string_object("Yes"),))
            self.question.add_enumeration(Rios.DescriptorObject(
                    id="No",
                    text=self.localized_string_object("No"),))
            return Rios.TypeObject(
                    base='boolean',
                    enumerations=Rios.EnumerationCollectionObject(
                            yes=Rios.EnumerationObject(description="Yes"),
                            no=Rios.EnumerationObject(description="No"), 
                            ), )

        field_type = od['field_type']
        if field_type == 'text':
            return process_text()
        elif field_type == 'notes':
            return process_notes()
        elif field_type == 'dropdown':
            return process_dropdown()
        elif field_type == 'radio':
            return process_radio()
        elif field_type == 'checkbox':
            return process_checkbox()
        elif field_type == 'calc':
            return process_calculation()
        elif field_type == 'slider':
            return process_slider()
        elif field_type == 'truefalse':
            return process_truefalse()
        elif field_type == 'yesno':
            return process_yesno()
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
        if od['field_type'] == 'calc':
            del elements[-1] # not a form field.
        else:
            element['type'] = 'question'
            element['options'] = Rios.QuestionObject(
                    fieldId=od['variable_field_name'],
                    text=self.localized_string_object(od['field_label']),
                    help=self.localized_string_object(od['field_note']), )
        return elements 

    def make_field(self, od):
        field = Rios.FieldObject()
        field_type = self.get_type(od)
        if field_type:
            field['id'] = od['variable_field_name']
            field['description'] = od['field_label']
            field['type'] = field_type
            field['required'] = bool(od['required_field'])
            field['identifiable'] = bool(od['identifier'])
        return field
        
    def make_matrix_field(self, od):
        field = Rios.FieldObject()
        field_type = self.get_type(od)
        field['id'] = od['matrix_group_name']
        field['description'] = od.get('section_header', '')
        field['type'] = Rios.TypeObject(base='matrix', )
        return field

    def process_od(self, od):
        page_name = od['form_name']
        if self.page_name != page_name:
            self.page_name = page_name
            self.page = Rios.PageObject(id=page_name)
            self.form.add_page(self.page)
            
        elements = self.make_elements(od)
        self.page.add_element(elements)
        if elements and elements[-1]['type'] == 'question':
            self.question = elements[-1]['options']

        if od['branching_logic_show_field_only_if']:
            self.question.add_event(Rios.EventObject(
                    trigger=self.convert_trigger(
                            od['branching_logic_show_field_only_if']),
                    action='disable', ))

        """ assessment[m][r][c]
        m = matrix_group_name
        r = variable_field_name
        c = field_type
        """
        matrix_group_name = od.get('matrix_group_name', '')
        if matrix_group_name:
            if self.matrix_group_name != matrix_group_name:
                # Start a new matrix.
                self.matrix_group_name = matrix_group_name
                field = self.make_matrix_field(od)
                self.field_type = field['type']
                # Append the only column.
                # Use the field_type (checkbox or radiobutton) as the id.
                self.field_type.add_column(Rios.ColumnObject(
                        id=od['field_type'],
                        description=od['field_label'],
                        type=field_type,
                        required=bool(od['required_field']),
                        identifiable=bool(od['identifier']), ))
                # Append the first row.
                self.field_type.add_row(Rios.RowObject(
                        id=od['variable_field_name'],
                        description=od['field_label'],
                        required=bool(od['required_field']), ))
                # add the column to the form
                self.question.add_question(Rios.QuestionObject(
                        fieldId=od['variable_field_name'],
                        text=self.localized_string_object(od['field_label']),
                        enumerations=self.get_choices_form(od), ))
                # add the row to the form
                self.question.add_row(Rios.DescriptorObject(
                        id=od['variable_field_name'],
                        text=self.localized_string_object(od['field_label']),
                        ))
            else:
                # Append row to existing matrix.
                self.field_type.add_row(Rios.RowObject(
                        id=od['variable_field_name'],
                        description=od['field_label'],
                        required=bool(od['required_field']), ))
                field = Rios.FieldObject()
                # add the row to the form      
                self.question.add_row(Rios.DescriptorObject(
                        id=od['variable_field_name'],
                        text=self.localized_string_object(od['field_label']),
                        ))
        else:
            self.matrix_group_name = ''
            self.field_type = None
            field = self.make_field(od)

        if field['id']:
            self.instrument.add_field(field) 

def main():
    Converter()
    sys.exit(0)

