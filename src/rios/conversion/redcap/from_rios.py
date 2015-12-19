"""
Converts RIOS form (and calculationset) files into a REDCap csv file.
"""

import csv
import re
import rios.core.validation.instrument as RI
import sys

from rios.conversion.from_rios import FromRios
from rios.conversion.redcap.to_rios import FUNCTION_TO_PYTHON
from rios.conversion.redcap.to_rios import OPERATOR_TO_REXL

COLUMNS = [
        "Variable / Field Name",
        "Form Name",
        "Section Header",
        "Field Type",
        "Field Label",
        "Choices, Calculations, OR Slider Labels",
        "Field Note",
        "Text Validation Type OR Show Slider Number",
        "Text Validation Min",
        "Text Validation Max",
        "Identifier?",
        "Branching Logic (Show field only if...)",
        "Required Field?",
        "Custom Alignment",
        "Question Number (surveys only)",
        "Matrix Group Name",
        "Matrix Ranking?",
        "Field Annotation",
        ]

# dict: each item => rios.conversion name: REDCap name
FUNCTION_TO_REDCAP = {rios: red for red, rios in FUNCTION_TO_PYTHON.items()}

# dict of function name: pattern which finds "name("
RE_funcs = {
        k: re.compile(r'\b%s\(' % k)
        for k in FUNCTION_TO_REDCAP.keys()}

# array of (regex pattern, replacement)
RE_ops = [(re.compile(rexl), redcap) for redcap, rexl in OPERATOR_TO_REXL]

# Find math.pow function: math.pow(base, exponent)
# \1 => base, \2 => exponent
RE_pow_function = re.compile(r'\bmath.pow\(\s*(.+)\s*,\s*(.+)\s*\)')

# Find variable reference: table["field"] or table['field']
# \1 => table, \2 => quote \3 => field
RE_variable_reference = re.compile(
        r'''\b([a-zA-Z][\w_]*)'''
        r'''\[\s*(["'])'''
        r'''([^\2\]]*)'''
        r'''\2\s*\]''')


class RedcapFromRios(FromRios):
    description = __doc__

    def call(self):
        """process the csv input, and create output files. """
        self.rows = [COLUMNS]
        self.section_header = ''
        for page in self.form['pages']:
            self.start_page(page)
            for element in self.elements:
                self.process_element(element)
        if self.calculationset:
            for calculation in self.calculationset['calculations']:
                self.process_calculation(calculation)
        self.create_csv_file()
        return 0

    def convert_rexl_expression(self, rexl):
        """convert REXL expression into REDCap

        - convert operators
        - convert caret to pow
        - convert redcap function names to python
        - convert database reference:  a["b"] => [a][b]
        - convert assessment variable reference: assessment["a"] => [a]
        - convert calculation variable reference: calculations["c"] => [c]
        """
        s = rexl
        for pattern, replacement in RE_ops:
            s = pattern.sub(replacement, s)
        s = RE_pow_function.sub(r'(\1)^(\2)', s)
        for name, pattern in RE_funcs.items():
            # the matched pattern includes the '('
            s = pattern.sub('%s(' % FUNCTION_TO_REDCAP[name], s)
        s = self.convert_variables(s)
        return s

    @staticmethod
    def convert_variables(s):
        start = 0
        answer = ''
        while 1:
            match = RE_variable_reference.search(s[start:])
            if match:
                table, quote, field = match.groups()
                if table in ['assessment', 'calculations']:
                    replacement = '[%s]' % field
                else:
                    replacement = '[%s][%s]' % (table, field)
                answer += s[start: start + match.start()] + replacement
                start += match.end()
            else:
                break
        answer += s[start:]
        return answer

    def create_csv_file(self):
        csv_writer = csv.writer(self.outfile)
        csv_writer.writerows(self.rows)

    def get_choices(self, array):
        return ' | '.join(['%s, %s' % (
                d['id'],
                self.get_local_text(d['text'])) for d in array])

    def get_type_tuple(self, base, question):
        widget_type = question.get('widget', {}).get('type', '')
        if base == 'float':
            return 'text', 'number'
        elif base == 'integer':
            return 'text', 'integer'
        elif base == 'text':
            return {'textArea': 'notes'}.get(widget_type, 'text'), ''
        elif base == 'enumeration':
            enums = {'radioGroup': 'radio', 'dropDown': 'dropdown'}
            return enums.get(widget_type, 'dropdown'), ''
        elif base == 'enumerationSet':
            return 'checkbox', ''
        elif base == 'matrix':
            return 'radio', ''
        else:
            return 'text', ''

    def process_calculation(self, calculation):
        def get_expression():
            expression = calculation['options']['expression']
            if calculation['method'] == 'python':
                expression = self.convert_rexl_expression(expression)
            return expression

        self.rows.append([
                calculation['id'],
                'calculations',
                '',
                'calc',
                calculation['description'],
                get_expression(),
                '', '', '', '', '', '', '', '', '', '', '', '', ])

    def process_element(self, element):
        type_ = element['type']
        options = element['options']
        if type_ in ['header', 'text']:
            self.process_header(options)
        elif type_ == 'question':
            self.process_question(options)

    def process_header(self, header):
        self.section_header = self.get_local_text(header['text'])

    def process_matrix(self, question):
        questions = question['questions']
        if isinstance(questions, list):
            if len(questions) > 1:
                self.warning(
                        'REDCap matrices support only one question.'
                        ' Question ignored: %s' % question['fieldId'])
                return
            column = questions[0]
        else:
            column = questions
        if 'enumerations' not in column:
            self.warning(
                    'REDCap matrix column must be an enumeration.'
                    '  Question ignored: %s' % question['fieldId'])
            return
        choices = self.get_choices(column['enumerations'])
        section_header = self.section_header
        matrix_group_name = question['fieldId']
        field = self.fields[matrix_group_name]
        type_object = RI.get_full_type_definition(
                self.instrument,
                field['type'])
        base = type_object['base']
        field_type, valid_type = self.get_type_tuple(base, question)
        for row in question['rows']:
            self.rows.append([
                    row['id'],
                    self.form_name,
                    section_header,
                    field_type,
                    self.get_local_text(row['text']),
                    choices,
                    self.get_local_text(row.get('help', {})),
                    valid_type,
                    '',
                    '',
                    'y' if field.get('identifiable', False) else '',
                    '',
                    'y' if field.get('required', False) else '',
                    '',
                    '',
                    matrix_group_name,
                    'y',
                    '', ])
            section_header = ''

    def process_question(self, question):
        def get_choices():
            return (
                    self.get_choices(question['enumerations'])
                    if 'enumerations' in question
                    else '')

        def get_range(type_object):
            r = type_object.get('range', {})
            min_value = str(r.get('min', ''))
            max_value = str(r.get('max', ''))
            return min_value, max_value

        def get_trigger():
            return (
                    question['events'][0]['trigger']
                    if 'events' in question and question['events']
                    else '' )

        branching = self.convert_rexl_expression(get_trigger())
        if 'rows' in question and 'questions' in question:
            self.process_matrix(question)
        else:
            field_id = question['fieldId']
            field = self.fields[field_id]
            type_object = RI.get_full_type_definition(
                    self.instrument,
                    field['type'])
            base = type_object['base']
            field_type, valid_type = self.get_type_tuple(base, question)
            min_value, max_value = get_range(type_object)
            self.rows.append([
                    field_id,
                    self.form_name,
                    self.section_header,
                    field_type,
                    self.get_local_text(question['text']),
                    get_choices(),
                    self.get_local_text(question.get('help', {})),
                    valid_type,
                    min_value,
                    max_value,
                    'y' if field.get('identifiable', False) else '',
                    branching,
                    'y' if field.get('required', False) else '',
                    '',
                    '',
                    '',
                    '',
                    '', ])
        self.section_header = ''

    def start_page(self, page):
        self.form_name = page['id']
        self.elements = page['elements']


def main(argv=None, stdout=None, stderr=None):
    sys.exit(RedcapFromRios()(argv, stdout, stderr))    # pragma: no cover
