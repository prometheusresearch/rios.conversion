"""
Converts a redcap csv file into a series of output files

    <OUTFILE_PREFIX>_c.<format> RIOS calculation
    <OUTFILE_PREFIX>_i.<format> RIOS instrument
    <OUTFILE_PREFIX>_f.<format> RIOS web form

The RIOS calculation file is only created when there are
calculation fields in the input.
However if there are no calculation fields
and the calculation file already exists,
it will be deleted.
"""
#
"""
RIOS imposes restrictions on the range of strings which can be used for IDs.
This program quietly converts input IDs using Csv2OrderedDict.get_name()
in the hopes of obtaining a valid RIOS ID.
"""

import argparse
import json
import pkg_resources
import re
import rios.conversion.balanced_match as balanced_match
import rios.conversion.csv_reader
import rios.conversion.classes as Rios
from rios.conversion.to_rios import ToRios
import sys

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

# dict: each item => REDCap name: rios.conversion name
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
        k: re.compile(r'\b%s\(' % k)
        for k in FUNCTION_TO_PYTHON.keys()}

# Array of tuples: (REDCap operator, rios.conversion operator)
OPERATOR_TO_REXL = [
        (r'<>', r'!='),
        ]

# array of (regex pattern, replacement)
RE_ops = [(re.compile(redcap), rexl) for redcap, rexl in OPERATOR_TO_REXL]


class Csv2OrderedDict(rios.conversion.csv_reader.CsvReader):
    def get_name(self, name):
        """ Return canonical name, a valid RIOS Identifier.

        - replace (one or more) non-alphanumeric with underbar.
        - strip leading and trailing underbars.
        - convert to lowercase.
        - ensure 'choices' field is 'choices_or_calculations'
          (REDCap has several names for the 'choices' field
          but they all begin with 'choices' and contain 'calc')
        - if the name begins with a digit, then prepend "id_"
        """
        x = RE_strip_outer_underbars.sub(
                r'\1',
                RE_non_alphanumeric.sub('_', name.strip().lower()))
        if x.startswith('choices') and 'calc' in x:
            x = 'choices_or_calculations'
        if x.startswith('branching_logic'):
            x = 'branching_logic'
        if x not in ('text_validation_min', 'text_validation_max') \
                and x.startswith('text_validation'):
            x = 'text_validation'
        if x and x[0].isdigit():
            x = 'id_' + x
        return x


class RedcapToRios(ToRios):

    def __init__(self):
        self.parser = argparse.ArgumentParser(
                formatter_class=argparse.RawTextHelpFormatter,
                description=__doc__)
        try:
            self_version = \
                pkg_resources.get_distribution('rios.conversion').version
        except pkg_resources.DistributionNotFound:    # pragma: no cover
            self_version = 'UNKNOWN'                  # pragma: no cover
        self.parser.add_argument(
                '-v',
                '--version',
                action='version',
                version='%(prog)s ' + self_version, )
        self.parser.add_argument(
                '--format',
                default='yaml',
                choices=['yaml', 'json'],
                help='The format and extension for the output files.  '
                        'The default is "yaml".')
        self.parser.add_argument(
                '--id',
                required=True,
                help='The instrument id to output.')
        self.parser.add_argument(
                '--infile',
                required=True,
                type=argparse.FileType('r'),
                help="The csv input file to process.  Use '-' for stdin.")
        self.parser.add_argument(
                '--instrument-version',
                required=True,
                help='The instrument version to output.')
        self.parser.add_argument(
                '--localization',
                default='en',
                metavar='',
                help='The default localization for the web form.  '
                        'The default is "en"')
        self.parser.add_argument(
                '--outfile-prefix',
                required=True,
                help='The prefix for the output files')
        self.parser.add_argument(
                '--title',
                required=True,
                help='The instrument title to output.')

    def __call__(self, argv=None, stdout=None, stderr=None):
        """process the csv input, and create output files. """
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr

        try:
            args = self.parser.parse_args(argv)
        except SystemExit as exc:
            return exc

        self.outfile_prefix = args.outfile_prefix
        self.id = args.id
        self.instrument_version = args.instrument_version
        self.title = args.title
        self.localization = args.localization
        self.format = args.format

        self.instrument = Rios.Instrument(
                id=self.id,
                version=self.instrument_version,
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
        self.reader = Csv2OrderedDict(args.infile)
        self.reader.load_attributes()
        first_field = self.reader.attributes[0]
        if first_field == 'variable_field_name':
            process = self.process_od
        elif first_field == 'fieldid':
            process = self.process_od2
        else:
            raise ValueError(
                    "Input has unknown format",
                    self.reader.attributes)
        for od in self.reader:
            process(od)
        self.validate_results()
        self.create_instrument_file()
        self.create_calculation_file()
        self.create_form_file()
        return 0

    def convert_calc(self, calc):
        """convert RedCap expression into Python

        - convert database reference:  [a][b] => a["b"]
        - convert assessment variable reference: [a] => assessment["a"]
        - convert calculation variable reference: [c] => calculations["c"]
        - convert redcap function names to python
        - convert caret to pow
        - convert operators
        """
        s = RE_database_ref.sub(r'\1["\2"]', calc)
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
        s = self.convert_carat_function(s)
        for pattern, replacement in RE_ops:
            s = pattern.sub(replacement, s)
        return s

    def convert_carat_function(self, string):
        answer = ''
        position = 0
        carat_pos = string.find(')^(', position)
        while carat_pos != -1:
            begin, end = balanced_match.balanced_match(string, carat_pos)
            answer += string[position: begin]
            answer += 'math.pow(' + string[begin + 1: end - 1]
            begin, end = balanced_match.balanced_match(string, carat_pos + 2)
            answer += ', ' + string[begin + 1: end - 1] + ')'
            position = end
            carat_pos = string.find(')^(', position)
        answer += string[position:]
        return answer

    def convert_text_type(self, text_type):
        if text_type.startswith('date'):
            return 'dateTime'
        elif text_type == 'integer':
            return 'integer'
        elif text_type in ('number', 'numeric'):
            return 'float'
        else:
            return 'text'

    def convert_trigger(self, trigger):
        s = self.convert_calc(trigger)
        return '!(%s)' % s

    def convert_value(self, value, text_type):
        if text_type == 'integer':
            return int(value)
        elif text_type == 'float':
            return float(value)
        else:
            return value    # pragma: no cover

    def get_choices_form(self, od):
        """ returns array of DescriptorObject

        Expecting: choices_or_calculations to be pipe separated list
        of (comma delimited) tuples: internal, external
        """
        return [
                Rios.DescriptorObject(
                        id=self.reader.get_name(x.strip().split(',')[0]),
                        text=self.localized_string_object(
                                ','.join(x.strip().split(',')[1:]).strip()),)
                for x in od['choices_or_calculations'].split('|') ]

    def get_choices_instrument(self, od):
        """ returns EnumerationCollectionObject

        Expecting: choices_or_calculations to be pipe separated list
        of (comma delimited) tuples: internal, external
        """
        choices_instrument = Rios.EnumerationCollectionObject()
        for x in od['choices_or_calculations'].split('|'):
            choices_instrument.add(
                    self.reader.get_name(x.strip().split(',')[0]))
        return choices_instrument

    def get_type(self, od, side_effects=True):
        """returns the computed instrument field type.

        Also has side effects when side_effects is True.
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
                raise ValueError(
                        'unexpected text type',
                        text_type,
                        od)   # pragma: no cover

        def process_calculation():
            if side_effects:
                field_name = self.reader.get_name(od['variable_field_name'])
                calc = self.convert_calc(od['choices_or_calculations'])
                self.calculations.add(Rios.CalculationObject(
                        id=field_name,
                        description=od['field_label'],
                        type='float',
                        method='python',
                        options={'expression': calc}, ))
                assert field_name not in self.calculation_variables
                self.calculation_variables.add(field_name)
            return None     # not an instrument field

        def process_checkbox():
            if side_effects:
                self.question.set_widget(get_widget(type='checkGroup'))
                self.question['enumerations'] = self.get_choices_form(od)
            return Rios.TypeObject(
                    base='enumerationSet',
                    enumerations=self.get_choices_instrument(od), )

        def process_dropdown():
            if side_effects:
                self.question.set_widget(get_widget(type='dropDown'))
                self.question['enumerations'] = self.get_choices_form(od)
            return Rios.TypeObject(
                    base='enumeration',
                    enumerations=self.get_choices_instrument(od), )

        def process_notes():
            if side_effects:
                self.question.set_widget(get_widget(type='textArea'))
            return 'text'

        def process_radio():
            if side_effects:
                self.question.set_widget(get_widget(type='radioGroup'))
                self.question['enumerations'] = self.get_choices_form(od)
            return Rios.TypeObject(
                    base='enumeration',
                    enumerations=self.get_choices_instrument(od), )

        def process_slider():
            if side_effects:
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
                    od['text_validation'])
            if side_effects:
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
            if side_effects:
                self.question.set_widget(get_widget(type='radioGroup'))
                self.question.add_enumeration(Rios.DescriptorObject(
                        id="true",
                        text=self.localized_string_object("True"),))
                self.question.add_enumeration(Rios.DescriptorObject(
                        id="false",
                        text=self.localized_string_object("False"),))
            type_object = Rios.TypeObject(base='enumeration', )
            type_object.add_enumeration('true', description='True')
            type_object.add_enumeration('false', description='False')
            return type_object

        def process_yesno():
            if side_effects:
                self.question.set_widget(get_widget(type='radioGroup'))
                self.question.add_enumeration(Rios.DescriptorObject(
                        id="yes",
                        text=self.localized_string_object("Yes"),))
                self.question.add_enumeration(Rios.DescriptorObject(
                        id="no",
                        text=self.localized_string_object("No"),))
            type_object = Rios.TypeObject(base='enumeration', )
            type_object.add_enumeration('yes', description='Yes')
            type_object.add_enumeration('no', description='No')
            return type_object

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
            raise ValueError('Unknown field_type', od)

    def get_type2(self, od):
        data_type = od['data_type']
        if data_type == 'instruction':
            return None
        if self.choices:
            # self.choices is an array of single key dicts.
            # The values in these dicts are
            # only used in the form - not the instrument
            type_object = Rios.TypeObject(base=od['enumeration_type'], )
            for choice in self.choices:
                type_object.add_enumeration(choice.keys()[0])
            return type_object
        else:
            # So far we've seen data_type in ['date', 'text', 'instruction']
            # So 'date' and 'text' need no translation:
            return data_type

    def make_elements(self, od):
        element = Rios.ElementObject()
        elements = [element]
        section_header = od['section_header']
        if section_header:
            element['type'] = 'header'
            element['options'] = {
                    'text': self.localized_string_object(section_header)}
            element = Rios.ElementObject()
            elements.append(element)
        if od['field_type'] == 'calc':
            del elements[-1]    # not a form field.
        else:
            element['type'] = 'question'
            field_name = self.reader.get_name(od['variable_field_name'])
            if section_header:
                field_name = '%s_%s' % (
                    field_name,
                    self.reader.get_name(section_header),
                )
            element['options'] = Rios.QuestionObject(
                    fieldId=field_name,
                    text=self.localized_string_object(od['field_label']),
                    help=self.localized_string_object(od['field_note']), )
        return elements

    def make_element2(self, od):
        element = Rios.ElementObject()
        if od['data_type'] == 'instruction':
            element['type'] = 'text'
            element['options'] = {
                    'text': self.localized_string_object(od['text']), }
        else:
            element['type'] = 'question'
            element['options'] = Rios.QuestionObject(
                    fieldId=self.reader.get_name(od['fieldid']),
                    text=self.localized_string_object(od['text']),
                    help=self.localized_string_object(od['help']), )
            if self.choices:
                question = element['options']
                for choice in self.choices:
                    key, value = choice.items()[0]
                    question.add_enumeration(Rios.DescriptorObject(
                            id=self.reader.get_name(key),
                            text=self.localized_string_object(value), ))
                question.set_widget(Rios.WidgetConfigurationObject(
                        type='checkGroup'
                        if od['enumeration_type'] == 'enumerationSet'
                        else 'radioGroup'))
        return element

    def make_field2(self, od):
        field = Rios.FieldObject()
        field_type = self.get_type2(od)
        if field_type:
            field['id'] = self.reader.get_name(od['fieldid'])
            field['description'] = od['text']
            field['type'] = field_type
        return field

    def make_field(self, od):
        field = Rios.FieldObject()
        field_type = self.get_type(od)
        if field_type:
            field_name = self.reader.get_name(od['variable_field_name'])
            if od['section_header']:
                field_name = '%s_%s' % (
                    field_name,
                    self.reader.get_name(od['section_header']),
                )
            field['id'] = field_name
            field['description'] = od['field_label']
            field['type'] = field_type
            field['required'] = bool(od['required_field'])
            field['identifiable'] = bool(od['identifier'])
        return field

    def make_matrix_field(self, od):
        field = Rios.FieldObject()
        field['id'] = self.reader.get_name(od['matrix_group_name'])
        field['description'] = od.get('section_header', '')
        field['type'] = Rios.TypeObject(base='matrix', )
        return field

    def process_od(self, od):
        page_name = self.reader.get_name(od['form_name'])
        if self.page_name != page_name:
            self.page_name = page_name
            self.page = Rios.PageObject(id=page_name)
            self.form.add_page(self.page)

        elements = self.make_elements(od)
        # Add any non-questions to form
        self.page.add_element(elements[:-1])

        # last element should be question
        if elements and elements[-1]['type'] == 'question':
            self.question = elements[-1]['options']

        if od['branching_logic']:
            self.question.add_event(Rios.EventObject(
                    trigger=self.convert_trigger(
                            od['branching_logic']),
                    action='disable', ))

        """ assessment[m][r][c]
        m = matrix_group_name
        r = variable_field_name
        c = field_type
        """
        matrix_group_name = self.reader.get_name(
                od.get('matrix_group_name', ''))
        if matrix_group_name:
            if self.matrix_group_name != matrix_group_name:
                # Add the matrix question to form
                self.page.add_element(elements[-1])
                # Start a new matrix.
                self.matrix_group_name = matrix_group_name
                self.matrix = self.question
                self.matrix['fieldId'] = matrix_group_name
                field = self.make_matrix_field(od)
                self.field_type = field['type']
                # Append the only column(to instrument).
                # Use the field_type (checkbox or radiobutton) as the id.
                self.field_type.add_column(Rios.ColumnObject(
                        id=self.reader.get_name(od['field_type']),
                        description=od['field_type'],
                        type=self.get_type(od, side_effects=False),
                        required=bool(od['required_field']),
                        identifiable=bool(od['identifier']), ))
                # add the column to the form
                self.matrix.add_question(Rios.QuestionObject(
                        fieldId=self.reader.get_name(od['field_type']),
                        text=self.localized_string_object(od['field_label']),
                        enumerations=self.get_choices_form(od), ))
                # Append the first row (to instrument).
                self.field_type.add_row(Rios.RowObject(
                        id=self.reader.get_name(od['variable_field_name']),
                        description=od['field_label'],
                        required=bool(od['required_field']), ))
                # add the row to the form.
                self.matrix.add_row(Rios.DescriptorObject(
                        id=self.reader.get_name(od['variable_field_name']),
                        text=self.localized_string_object(od['field_label']),
                        ))
            else:
                # Append row to existing matrix (to instrument).
                self.field_type.add_row(Rios.RowObject(
                        id=self.reader.get_name(od['variable_field_name']),
                        description=od['field_label'],
                        required=bool(od['required_field']), ))
                field = Rios.FieldObject()
                # add the row to the form
                self.matrix.add_row(Rios.DescriptorObject(
                        id=self.reader.get_name(od['variable_field_name']),
                        text=self.localized_string_object(od['field_label']),
                        ))
        else:
            self.matrix_group_name = ''
            self.matrix = None
            self.field_type = None
            # Add the question to the form
            if elements:
                self.page.add_element(elements[-1])
            field = self.make_field(od)

        if field['id']:
            self.instrument.add_field(field)

    def process_od2(self, od):
        page_name = (
                self.reader.get_name(od['page'])
                if od['page']
                else 'page_0')
        if self.page_name != page_name:
            self.page_name = page_name
            self.page = Rios.PageObject(id=page_name)
            self.form.add_page(self.page)

        if od['enumeration_type'] in ['enumeration', 'enumerationSet']:
            # data_type might be a JSON string of a dict which contains
            # 'Choices' or 'choices', an array of single key dicts.
            try:
                data_type = json.loads(od['data_type'])
                self.choices = (
                        data_type.get('Choices', False)
                        or data_type.get('choices', False)
                        or None )
                # What a world.  Now we sort the array
                # because we want key order not array order.  go figure.
                if self.choices:
                    self.choices = [
                            {self.reader.get_name(k): v}
                            for c in self.choices
                            for k, v in c.items() ]
                    self.choices.sort()
            except (ValueError):
                raise ValueError('unable to load data_type as JSON: %s' % od)
        else:
            self.choices = None

        element = self.make_element2(od)
        self.page.add_element(element)
        field = self.make_field2(od)
        if field['id']:
            self.instrument.add_field(field)


def main(argv=None, stdout=None, stderr=None):
    sys.exit(RedcapToRios()(argv, stdout, stderr))    # pragma: no cover
