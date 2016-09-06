#
# Copyright (c) 2016, Prometheus Research, LLC
#


import re
import collections


from rios.core.validation.instrument import get_full_type_definition
from rios.conversion.base import FromRios
from rios.conversion.exception import (
    ConversionValueError,
    RiosFormatError,
    Error,
)
from rios.conversion.redcap.to_rios import (
    FUNCTION_TO_PYTHON,
    OPERATOR_TO_REXL,
)


__all__ = (
    'RedcapFromRios',
)


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
    """ Converts a RIOS configuration into a REDCap configuration """

    def __call__(self):
        self._rows = collections.deque()
        self._rows.append(COLUMNS)
        self.section_header = ''

        if 'pages' not in self._form or not self._form['pages']:
            raise RiosFormatError(
                "RIOS data dictionary conversion failure. Error:"
                "RIOS form configuration does not contain page data"
            )

        # Process form and instrument configurations
        for page in self._form['pages']:
            try:
                self.page_processor(page)
            except Exception as exc:
                if isinstance(exc, ConversionValueError):
                    # Don't need to create a new error instance, b/c
                    # ConversionValueErrors caught here already contain
                    # identifying information.
                    self.logger.warning(str(exc))
                elif isinstance(exc, RiosFormatError):
                    error = Error(
                        "Error parsing the data dictionary:",
                        str(exc)
                    )
                    error.wrap(
                        "RIOS data dictionary conversion failure:",
                        "Unable to parse the data dictionary"
                    )
                    self.logger.error(str(error))
                    raise error
                else:
                    error = Error(
                        "An unknown or unexpected error occured:",
                        repr(exc)
                    )
                    error.wrap(
                        "RIOS data dictionary conversion failure:",
                        "Unable to parse the data dictionary"
                    )
                    self.logger.error(repr(error))
                    raise exc

        # Process calculations
        if self._calculationset:
            for calculation in self._calculationset['calculations']:
                try:
                    calc_id = calculation.get('id', None)
                    calc_description = calculation.get('id', None)
                    if not calc_id or not calc_description:
                        raise RiosFormatError(
                            "Missing ID or description for a calculation:",
                            str(
                                calc_id
                                or calc_description
                                or "Calculation is not identifiable"
                            )
                        )
                    self.process_calculation(calculation)
                except Exception as exc:
                    if isinstance(exc, ConversionValueError):
                        error = Error(
                            "Skipping calculation element with ID:",
                            str(calc_id)
                        )
                        error.wrap("Error:", str(exc))
                        self.logger.warning(str(exc))
                    else:
                        raise exc

        self._definition.append(self._rows)

    def page_processor(self, page):
        self.form_name = page.get('id', None)
        self.elements = page.get('elements', None)
        if not self.form_name or not self.elements:
            raise RiosFormatError(
                "Error:",
                "RIOS form does not contain valid page data"
            )

        # Iterate over form elements and process them accordingly
        for element in self.elements:
            # Get question/form element ID value for error messages
            try:
                identifier = element['options']['fieldId']
            except:
                identifier = element['options']['text'].get(
                    self.localization,
                    None
                )
            if not identifier:
                raise ConversionValueError(
                    'Form element has no identifier.'
                    ' Invalid element data:',
                    str(element)
                )
            try:

                self.process_element(element)

            except Exception as exc:
                if isinstance(exc, ConversionValueError):
                    error = Error(
                        "Skipping form element with ID:",
                        str(identifier)
                    )
                    error.wrap('Error:', str(exc))
                else:
                    raise exc

    def convert_rexl_expression(self, rexl):
        """
        Convert REXL expression into REDCap expressions

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

    def get_choices(self, array):
        return ' | '.join(['%s, %s' % (
                str(d['id']),
                self.get_local_text(self.localization, d['text']))
                for d in array])

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

        self._rows.append(
            [
                calculation['id'],
                'calculations',
                '',
                'calc',
                calculation['description'],
                get_expression(),
                '', '', '', '', '', '', '', '', '', '', '', '',
            ]
        )

    def process_element(self, element):
        _type = element['type']
        options = element['options']
        if _type in ['header', 'text']:
            self.process_header(options)
        elif _type == 'question':
            self.process_question(options)
        else:
            error = ConversionValueError(
                "Invalid form element type. Got:",
                str(_type)
            )
            error.wrap("Expected values:", "header, text, question")
            raise error

    def process_header(self, header):
        self.section_header = self.get_local_text(
            self.localization,
            header['text']
        )

    def process_matrix(self, question):
        questions = question['questions']
        if isinstance(questions, list):
            if len(questions) > 1:
                error = ConversionValueError(
                    'REDCap matrices support only one question. Got:',
                    ", ".join([str(q) for q in questions])
                )
                raise error
            column = questions[0]
        else:
            column = questions
        if 'enumerations' not in column:
            error = ConversionValueError(
                'Form element skipped with ID:',
                str(question.get('fieldId', 'Unknown field ID'))
            )
            error.wrap(
                'REDCap matrix column must be an enumeration. Got column:',
                str(column)
            )
            raise error
        choices = self.get_choices(column['enumerations'])
        section_header = self.section_header
        matrix_group_name = question['fieldId']
        field = self.fields[matrix_group_name]
        type_object = get_full_type_definition(
            self._instrument,
            field['type']
        )
        base = type_object['base']
        field_type, valid_type = self.get_type_tuple(base, question)
        for row in question['rows']:
            self._rows.append(
                [
                    row['id'],
                    self.form_name,
                    section_header,
                    field_type,
                    self.get_local_text(self.localization, row['text']),
                    choices,
                    self.get_local_text(self.localization,
                                        row.get('help', {})),
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
                    '',
                ]
            )
            section_header = ''

    def process_question(self, question):
        def get_choices():
            return (
                self.get_choices(question['enumerations'])
                if 'enumerations' in question
                else ''
            )

        def get_range(type_object):
            r = type_object.get('range', {})
            min_value = str(r.get('min', ''))
            max_value = str(r.get('max', ''))
            return min_value, max_value

        def get_trigger():
            return (
                question['events'][0]['trigger']
                if 'events' in question and question['events']
                else ''
            )

        branching = self.convert_rexl_expression(get_trigger())
        if 'rows' in question and 'questions' in question:
            self.process_matrix(question)
        else:
            field_id = question['fieldId']
            field = self.fields[field_id]
            type_object = get_full_type_definition(
                    self._instrument,
                    field['type'])
            base = type_object['base']
            field_type, valid_type = self.get_type_tuple(base, question)
            min_value, max_value = get_range(type_object)
            self._rows.append(
                [
                    field_id,
                    self.form_name,
                    self.section_header,
                    field_type,
                    self.get_local_text(self.localization, question['text']),
                    get_choices(),
                    self.get_local_text(self.localization,
                                        question.get('help', {})),
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
                    '',
                ]
            )
        self.section_header = ''
