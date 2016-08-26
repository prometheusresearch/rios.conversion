#
# Copyright (c) 2016, Prometheus Research, LLC
#


import re
import six
import rios.conversion.structures as Rios


from rios.core import ValidationError
from rios.conversion.utils import (
    InstrumentCalcStorage,
    CsvReader,
    balanced_match,
)
from rios.conversion.base import ToRios, localized_string_object
from rios.conversion.exception import (
    RedcapFormatError,
    ConversionValidationError,
    ConversionValueError,
    Error,
    guard,
)


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
        'mean': 'rios.conversion.redcap.functions.mean',
        'median': 'rios.conversion.redcap.function.median',
        'sum': 'rios.conversion.redcap.functions.sum_',
        'stdev': 'rios.conversion.redcap.functions.stdev',
        'round': 'rios.conversion.redcap.functions.round_',
        'roundup': 'rios.conversion.redcap.functions.roundup',
        'rounddown': 'rios.conversion.redcap.functions.rounddown',
        'sqrt': 'math.sqrt',
        'abs': 'abs',
        'datediff': 'rios.conversion.redcap.functions.datediff',
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


class CsvReaderWithGetName(CsvReader):
    """
    RIOS imposes restrictions on the range of strings which can be used for
    IDs. This program quietly converts input IDs using
    Csv2OrderedDict.get_name() in the hopes of obtaining a valid RIOS ID.
    """

    def get_name(self, name):
        """
        Return canonical name, a valid RIOS Identifier.

        - replace (one or more) non-alphanumeric with underbar.
        - strip leading and trailing underbars.
        - convert to lowercase.
        - ensure 'choices' field is 'choices_or_calculations'
          (REDCap has several names for the 'choices' field
          but they all begin with 'choices' and contain 'calc')
        - if the name begins with a digit, then prepend "id_"
        """
        if name is None:
            raise ValueError("Name cannot be None")
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
    """ Converts a REDCap CSV file to the RIOS specification format """

    def __call__(self):
        with guard("REDCap instrument conversion failure:",
                    "Unable to parse CSV"):
            # Pre-processing
            self.reader = CsvReaderWithGetName(self.stream)  # noqa: F821
            self.reader.load_attributes()

            # Determine processor
            first_field = self.reader.attributes[0]
            if first_field == 'variable_field_name':
                # Process new CSV format
                process = Processor(self.reader, self.localization)
            elif first_field == 'fieldid':
                # Process legacy CSV format
                # process = LegacyProcessor(self.reader, self.localization)
                # TODO: Implement LegacyProcessor
                pass
            else:
                error = RedcapFormatError(
                    "Unknown input CSV header format. Got:",
                    ", ".join(self.reader.attributes)
                )
                self.critical_error = True
                raise error

            # MAIN PROCESSING
            # Occures in two steps:
            #   1) Process data and page names into containers
            #   2) Iterate over containers to construct RIOS definitions
            # NOTE:
            #   1) Each row is an ordered dict
            #   2) Start=2, because spread sheet programs set header row to 1
            #       and first data row to 2 (strictly for user friendly errors)
            for line, row in enumerate(self.reader, start=2):
                if 'page' in row:
                    # Page name for legacy REDCap data dictionary format
                    if row['page']:
                        page_name = self.reader.get_name(row['page'])
                    else:
                        page_name = 'page_0'
                elif 'form_name' in row:
                    # Page name for current REDCap data dictionary format
                    page_name = self.reader.get_name(row['form_name'])
                else:
                    raise RedcapFormatError(
                        'REDCap data dictionaries must contain'
                        ' the Form Name column'
                    )

                # Need unique list of page names to create one page instance
                # per page name
                self.page_names.add(page_name)

                # Insert into data container
                self.data[line] = {'page_name': page_name, 'row': row}

            # Created pages for the data dictionary instrument
            for page_name in self.page_names:
                self.page_container.update(
                    {page_name: Rios.PageObject(id=page_name)}
                )

            # Process the row
            for line, row_pkg in six.iteritems(self.data):
                page = self.page_container[row_pkg['page_name']]
                row = row_pkg['row']
                try:
                    # WHERE THE MAGIC HAPPENS
                    fields, calcs = process(page, row)

                    # Clear processor's internal storage for next line
                    process.clear_storage()

                    for field in fields:
                        self.field_container.append(field)
                    for calc in calcs:
                        self.calc_container.update(calc)

                except Exception as exc:
                    if isinstance(exc, ConversionValueError):
                        # TODO: Log line failures
                        error = Error(
                            "Warning on line: " + str(line) + ". Got:",
                            str(exc)
                        )
                        error.wrap('Skipping line...')
                        print error
                    elif isinstance(exc, RedcapFormatError):
                        error = Error(
                            "Error on line: " + str(line) + ". Got:",
                            str(exc)
                        )
                        raise error
                    else:
                        raise exc

            # Construct insrument and calculationset objects
            for field in self.field_container:
                self._instrument.add_field(field)
            for calc in self.calc_container:
                self._calculationset.add(calc)
            # Page container is a dict instead of a list, so iterate over vals
            for page in six.itervalues(self.page_container):
                self._form.add_page(page)

            # Post-processing
            try:
                self.validate()
            except ValidationError as exc:
                error = ConversionValidationError(
                    'Validation error. Got:',
                    str(exc)
                )
                raise error
            else:
                # TODO: Log validation success
                print "Validation successful"


class ProcessorBase(object):
    """ Abstract base class for processor objects """

    def __init__(self, reader, localization):
        self.reader = reader
        self.localization = localization

        # Set to hold unique calc variables
        self.calculation_variables = set()

        # Objects to construct instruments, forms, and calcsets
        self._storage = InstrumentCalcStorage()

        # Object to store pointer to instrument field object
        self._field = None

        # Objects to store pointers to matrix construction objects
        self._current_matrix_group_name = None
        self._matrix = None
        self._field_type = None

    def __call__(self, *args, **kwargs):
        """
        Processes REDCap data dictionary rows into corresponding RIOS
        specfication formatted data objects.

        Must return a tuple containing: first, a list of instrument fields, and
        second, a list of dicts defining calcs. The key must be the field
        reference name, and the value must be the calc definition.

        Implementations must override this method.
        """

        raise NotImplementedError(
            '{}.__call__'.format(self.__class__.__name__)
        )

    def convert_calc(self, calc):
        """
        Convert RedCap expression into Python

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
            # The matched pattern includes the '('
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
            begin, end = balanced_match(string, carat_pos)
            answer += string[position: begin]
            answer += 'math.pow(' + string[begin + 1: end - 1]
            begin, end = balanced_match(string, carat_pos + 2)
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

    def get_choices_form(self, row):
        """
        Returns array of DescriptorObject

        Expecting: choices_or_calculations to be pipe separated list
        of (comma delimited) tuples: internal, external
        """
        return [
                Rios.DescriptorObject(
                    id=self.reader.get_name(x.strip().split(',')[0]),
                    text=localized_string_object(
                            self.localization,
                            ','.join(x.strip().split(',')[1:]).strip()
                    ),
                )
                for x in row['choices_or_calculations'].split('|') ]

    def get_choices_instrument(self, row):
        """
        Returns EnumerationCollectionObject

        Expecting: choices_or_calculations to be pipe separated list
        of (comma delimited) tuples: internal, external
        """
        choices_instrument = Rios.EnumerationCollectionObject()
        for x in row['choices_or_calculations'].split('|'):
            choices_instrument.add(
                    self.reader.get_name(x.strip().split(',')[0]))
        return choices_instrument


class Processor(ProcessorBase):
    """ Processor class for modern REDCap data dictionaries """

    def __call__(self, page, row):
        """ Processes a a REDCap data dictionary CSV row """

        try:
            self.page_processor(page, row)
        except ConversionValueError as exc:
            # Reset storage if conversion of current line fails
            self.clear_storage()
            raise exc

        fields = self._storage['i']
        calcs = self._storage['c']

        return (fields, calcs,)

    def clear_storage(self):
        self._storage.clear()

    def page_processor(self, page, row):

        section_header = row['section_header']
        if section_header:
            header = Rios.ElementObject()
            header['type'] = 'header'
            header['options'] = {
                'text': localized_string_object(
                    self.localization,
                    section_header
                )
            }
        else:
            header = None

        # Check if a calc, and if so, remove, b/c not a form field/question
        if row['field_type'] == 'calc':
            question = None
        else:
            question = Rios.ElementObject(type='question')
            field_name = self.reader.get_name(row['variable_field_name'])
            if section_header:
                field_name = '%s_%s' % (
                    field_name,
                    self.reader.get_name(section_header),
                )
            question['options'] = Rios.QuestionObject(
                fieldId=field_name,
                text=localized_string_object(
                    self.localization,
                    row['field_label']
                ),
                help=localized_string_object(
                    self.localization,
                    row['field_note']
                ),
            )

        # Now that we have a header only OR question and maybe a header, we
        # either add the header by itself as a section header, or we add a new
        # question containing a possible sub-header. If no header or question,
        # then we have a calculation, which is handled when instrument fields
        # are constructed in the qestion_processor function.
        if header and not question:
            # Add non-questions to form (e.g., headers)
            page.add_element(header)
        if question:
            # Process existing ques or process and add new ques to the form
            add_question_and_store_fields = self.question_processor(
                row,
                page,
                question
            )

            # This block MUST COME AFTER the question processor to prevent
            # adding questions and fields that caused errors, but allow the
            # conversion to proceed to the next line.
            if add_question_and_store_fields:
                # Add the new question to form
                page.add_element(question)
                # Store instrument question field
                if self._field and self._field['id']:
                    self._storage['i'] = self._field

    def question_processor(self, row, page, question):
        """
        Processes questions.

        Return True if a question should be added as a new element to the page,
        and if a form field should be added to the instrument definition. New
        matrix questions and regular questions are added to both definitions.
        However, existing matrix questions are not added.

        A pointer reference is store to allow for:
            1) modifying existing matrix questions
            2) storing the instrument field by the parent function scope
        """

        add_question_and_store_field = True

        # Use question object in question['options']
        question_obj = question['options']

        # If row involves branching logic, add to question
        if row['branching_logic']:
            question_obj.add_event(
                Rios.EventObject(
                    trigger=self.convert_trigger(
                            row['branching_logic']
                    ),
                    action='disable',
                )
            )

        # Check for a matrix question
        matrix_group_name = self.reader.get_name(
            row.get('matrix_group_name', '')
        )

        if matrix_group_name:
            # Question is a matrix question
            #
            # assessment[m][r][c]
            # m = matrix_group_name
            # r = variable_field_name
            # c = field_type

            # Ranme for code clarity
            matrix = question_obj

            if self._current_matrix_group_name != matrix_group_name:
                # New matrix question

                self._current_matrix_group_name = matrix_group_name

                # Start a new matrix question field for the form
                matrix['fieldId'] = matrix_group_name

                # Create a new matrix question field for the instrument
                field = Rios.FieldObject()
                field['id'] = self.reader.get_name(
                        row['matrix_group_name']
                )
                field['description'] = row.get('section_header', '')
                field['type'] = Rios.TypeObject(base='matrix', )

                field_type = field['type']

                # Process matrix
                # Append the only column(to instrument).
                # Use the field_type (checkbox or radiobutton) as the id.
                field_type.add_column(
                    Rios.ColumnObject(
                        id=self.reader.get_name(row['field_type']),
                        description=row['field_type'],
                        type=self.get_type(
                            matrix,
                            row,
                            side_effects=False
                        ),
                        required=bool(row['required_field']),
                        identifiable=bool(row['identifier']),
                    )
                )
                # add the column to the form
                matrix.add_question(
                    Rios.QuestionObject(
                        fieldId=self.reader.get_name(row['field_type']),
                        text=localized_string_object(
                            self.localization,
                            row['field_label']
                        ),
                        enumerations=self.get_choices_form(row),
                    )
                )
                # Append the first row (to instrument).
                field_type.add_row(
                    Rios.RowObject(
                        id=self.reader.get_name(
                            row['variable_field_name']
                        ),
                        description=row['field_label'],
                        required=bool(row['required_field']),
                    )
                )
                # add the row to the form.
                matrix.add_row(
                    Rios.DescriptorObject(
                        id=self.reader.get_name(
                            row['variable_field_name']
                        ),
                        text=localized_string_object(
                            self.localization,
                            row['field_label']
                        ),
                    )
                )

                # Assign pointers to matrix construction objects, so
                # matrix questions have modifiable instrument and form
                # definitions if next question is  an existing matrix
                # question
                self._matrix = matrix
                self._field = field
                self._field_type = field_type

            else:
                # Current matrix question
                # Modify existing matrix question for instrument definition
                self._field_type.add_row(
                    Rios.RowObject(
                        id=self.reader.get_name(
                            row['variable_field_name']
                        ),
                        description=row['field_label'],
                        required=bool(row['required_field']),
                    )
                )

                # Field already exists, so prevent adding it to form
                self._field = Rios.FieldObject()

                # Modify existing matrix question for form definition
                self._matrix.add_row(
                    Rios.DescriptorObject(
                        id=self.reader.get_name(
                            row['variable_field_name']
                        ),
                        text=localized_string_object(
                            self.localization,
                            row['field_label']
                        ),
                    )
                )
                self._field = None
                add_question_and_store_field = False
        else:
            # A non-matrix, regular question
            self._current_matrix_group_name = None
            self._matrix = None
            self._field_type = None

            # Make instrument field
            field = Rios.FieldObject()
            field_type = self.get_type(question_obj, row)
            if field_type:
                field_name = self.reader.get_name(row['variable_field_name'])
                if row['section_header']:
                    field_name = '%s_%s' % (
                        field_name,
                        self.reader.get_name(row['section_header']),
                    )
                field['id'] = field_name
                field['description'] = row['field_label']
                field['type'] = field_type
                field['required'] = bool(row['required_field'])
                field['identifiable'] = bool(row['identifier'])

            self._field = field

        return add_question_and_store_field

    def get_type(self, question_obj, row, side_effects=True):
        """
        Returns the computed instrument field type.

        Also has side effects when side_effects is True.
        - can initialize calculations.
        - can append a calculation.
        - updates question_obj (renamed to "question" for code clarity):
            enumerations, questions, rows, widget, events
        """

        # Rename for code clarity
        question = question_obj

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
                raise ConversionValueError(
                    'Unexpected text type. Got:', str(text_type)
                )

        def process_calculation():
            if side_effects:
                field_name = self.reader.get_name(row['variable_field_name'])
                calc = self.convert_calc(row['choices_or_calculations'])
                calculation = Rios.CalculationObject(
                    id=field_name,
                    description=row['field_label'],
                    type='float',
                    method='python',
                    options={'expression': calc},
                )
                self._storage['c'] = calculation
                assert field_name not in self.calculation_variables
                self.calculation_variables.add(field_name)
            return None     # not an instrument field

        def process_checkbox():
            if side_effects:
                question.set_widget(get_widget(type='checkGroup'))
                question['enumerations'] = self.get_choices_form(row)
            return Rios.TypeObject(
                    base='enumerationSet',
                    enumerations=self.get_choices_instrument(row), )

        def process_dropdown():
            if side_effects:
                question.set_widget(get_widget(type='dropDown'))
                question['enumerations'] = self.get_choices_form(row)
            return Rios.TypeObject(
                    base='enumeration',
                    enumerations=self.get_choices_instrument(row), )

        def process_notes():
            if side_effects:
                question.set_widget(get_widget(type='textArea'))
            return 'text'

        def process_radio():
            if side_effects:
                question.set_widget(get_widget(type='radioGroup'))
                question['enumerations'] = self.get_choices_form(row)
            return Rios.TypeObject(
                    base='enumeration',
                    enumerations=self.get_choices_instrument(row), )

        def process_slider():
            if side_effects:
                question.set_widget(get_widget(type='inputNumber'))
            return Rios.TypeObject(
                    base='float',
                    range=Rios.BoundConstraintObject(
                            min=0.0,
                            max=100.0), )

        def process_text():
            val_min = row['text_validation_min']
            val_max = row['text_validation_max']
            text_type = self.convert_text_type(
                    row['text_validation'])
            if side_effects:
                question.set_widget(get_widget(
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
                question.set_widget(get_widget(type='radioGroup'))
                question.add_enumeration(
                    Rios.DescriptorObject(
                        id="true",
                        text=localized_string_object(
                            self.localization,
                            "True"
                        ),
                    )
                )
                question.add_enumeration(
                    Rios.DescriptorObject(
                        id="false",
                        text=localized_string_object(
                            self.localization,
                            "False"
                        ),
                    )
                )
            type_object = Rios.TypeObject(base='enumeration', )
            type_object.add_enumeration('true', description='True')
            type_object.add_enumeration('false', description='False')
            return type_object

        def process_yesno():
            if side_effects:
                question.set_widget(get_widget(type='radioGroup'))
                question.add_enumeration(
                    Rios.DescriptorObject(
                        id="yes",
                        text=localized_string_object(
                            self.localization,
                            "Yes"
                        ),
                    )
                )
                question.add_enumeration(
                    Rios.DescriptorObject(
                        id="no",
                        text=localized_string_object(
                            self.localization,
                            "No"
                        ),
                    )
                )
            type_object = Rios.TypeObject(base='enumeration', )
            type_object.add_enumeration('yes', description='Yes')
            type_object.add_enumeration('no', description='No')
            return type_object

        # Process question according to its field type
        field_type = row['field_type']
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
            error = ConversionValueError(
                'Unknown Field Type value. Got:', str(field_type)
            )
            raise error


# TODO: Implement LegacyProcessor
# class LegacyProcessor(ProcessorBase):
#     """ Processor class for REDCap data dictionaries """
#
#     def __call__(self, od):
#         """ Processes a legacy CSV data row in a REDCap data dictionary """
#
#         page_name = (
#                 self.reader.get_name(od['page'])
#                 if od['page']
#                 else 'page_0')
#         if self.page_name != page_name:
#             self.page_name = page_name
#             self.page = Rios.PageObject(id=page_name)
#             self.pages.append(self.page)
#
#         if od['enumeration_type'] in ('enumeration', 'enumerationSet',):
#             # data_type might be a JSON string of a dict which contains
#             # 'Choices' or 'choices', an array of single key dicts.
#             try:
#                 data_type = json.loads(od['data_type'])
#                 self.choices = (
#                         data_type.get('Choices', False)
#                         or data_type.get('choices', False)
#                         or None )
#                 # What a world.  Now we sort the array
#                 # because we want key order not array order.  go figure.
#                 if self.choices:
#                     self.choices = [
#                             {self.reader.get_name(k): v}
#                             for c in self.choices
#                             for k, v in c.items() ]
#                     self.choices.sort()
#             except:
#                 error = RedcapFormatError(
#                     "Unable to parse \"data_type\" field",
#                     "Cannot read JSON formatted text"
#                 )
#                 raise error
#         else:
#             self.choices = None
#
#         element = self.make_element2(od)
#         self.page.add_element(element)
#         field = self.make_field2(od)
#         if field['id']:
#             self.fields.append(field)
#
#     def get_type2(self, od):
#         data_type = od['data_type']
#         if data_type == 'instruction':
#             return None
#         if self.choices:
#             # self.choices is an array of single key dicts.
#             # The values in these dicts are
#             # only used in the form - not the instrument
#             type_object = Rios.TypeObject(base=od['enumeration_type'], )
#             for choice in self.choices:
#                 type_object.add_enumeration(choice.keys()[0])
#             return type_object
#         else:
#             # So far we've seen data_type in ['date', 'text', 'instruction']
#             # So 'date' and 'text' need no translation:
#             return data_type
#
#     def make_element2(self, od):
#         element = Rios.ElementObject()
#         if od['data_type'] == 'instruction':
#             element['type'] = 'text'
#             element['options'] = {
#                 'text': localized_string_object(
#                     self.localization,
#                     od['text']
#                 ),
#             }
#         else:
#             element['type'] = 'question'
#             element['options'] = Rios.QuestionObject(
#                 fieldId=self.reader.get_name(od['fieldid']),
#                 text=localized_string_object(
#                     self.localization,
#                     od['text']
#                 ),
#                 help=localized_string_object(
#                     self.localization,
#                     od['help']
#                 ),
#             )
#             if self.choices:
#                 question = element['options']
#                 for choice in self.choices:
#                     key, value = choice.items()[0]
#                     question.add_enumeration(
#                         Rios.DescriptorObject(
#                             id=self.reader.get_name(key),
#                             text=localized_string_object(
#                                 self.localization,
#                                 value
#                             ),
#                         )
#                     )
#                 question.set_widget(Rios.WidgetConfigurationObject(
#                         type='checkGroup'
#                         if od['enumeration_type'] == 'enumerationSet'
#                         else 'radioGroup'))
#         return element
#
#     def make_field2(self, od):
#         field = Rios.FieldObject()
#         field_type = self.get_type2(od)
#         if field_type:
#             field['id'] = self.reader.get_name(od['fieldid'])
#             field['description'] = od['text']
#             field['type'] = field_type
#         return field
