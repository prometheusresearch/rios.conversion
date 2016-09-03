#
# Copyright (c) 2016, Prometheus Research, LLC
#


from rios.core.validation.instrument import get_full_type_definition
from rios.conversion.base import FromRios
from rios.conversion.exception import (
    ConversionValueError,
    QualtricsFormatError,
    Error,
)


__all__ = (
    'QualtricsFromRios',
)


class QuestionNumber:
    def __init__(self):
        self.number = 0

    def next(self):
        self.number += 1
        return self.number


class QualtricsFromRios(FromRios):
    """
    Converts RIOS instrument and form definitions into a Qualtrics data
    dictionary.
    """

    def __call__(self):
        self.lines = []
        self.question_number = QuestionNumber()
        for page in self._form['pages']:
            try:
                self.page_processor(page)
            except Exception as exc:
                if isinstance(exc, ConversionValueError):
                    # Don't need to specify what's being skipped here, because
                    # deeper level exceptions access that data.
                    self.logger.warning(str(exc))
                elif isinstance(exc, QualtricsFormatError):
                    error = Error(
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
                    self.logger.error(str(error))
                    raise error

        # Skip the first line ([[PageBreak]]) and the last 2 lines (blank)
        def rmv_extra_strings(lst):
            if len(lst) > 0:
                if lst[0] == '[[PageBreak]]':
                    rmv_extra_strings(lst[1:])
                elif lst[-1] == "":
                    rmv_extra_strings(lst[:-1])
            return lst[:]

        for line in rmv_extra_strings(self.lines):
            self._definition.append(line)

    def page_processor(self, page):
        # Start the page
        self.lines.append('[[PageBreak]]')
        elements = page['elements']
        # Process question elements
        for question in elements:
            question_options = question['options']
            # Get question ID for exception/error messages
            # Get question/form element ID value for error messages
            try:
                identifier = question['options']['fieldId']
            except:
                identifier = question['options']['text'].get(
                    self.localization,
                    None
                )
            if not identifier:
                raise ConversionValueError(
                    'Form element has no identifier.'
                    ' Invalid element data:',
                    str(question)
                )
            # Handle form element if a question
            if question['type'] == 'question':
                try:
                    self.question_processor(question_options)
                except Exception as exc:
                    error = ConversionValueError(
                        ("Skipping form field with ID: " + str(identifier)
                                + ". Error:"),
                        (str(exc) if isinstance(exc, Error) else repr(exc))
                    )
                    raise error
            else:
                # Qualtrics only handles form questions
                error = ConversionValueError(
                    'Skipping form field with ID:',
                    str(identifier)
                )
                error.wrap(
                    'Form element type is not \"question\". Got:',
                    str(question['type'])
                )
                raise error

    def question_processor(self, question_options):
        field_id = question_options['fieldId']
        field = self.fields[field_id]
        type_object = get_full_type_definition(
            self._instrument,
            field['type']
        )
        base = type_object['base']
        if base not in ('enumeration', 'enumerationSet',):
            error = ConversionValueError(
                "Invalid question type:",
                "Type is not \"enumeration\" or \"enumerationSet\""
            )
            error.wrap("Got invalid value for type:", str(base))
            raise error
        self.lines.append(
            '%d. %s' % (
                self.question_number.next(),
                self.get_local_text(question_options['text']),
            )
        )
        if base == 'enumerationSet':
            self.lines.append('[[MultipleAnswer]]')
        # Blank line separates question from choices.
        self.lines.append('')
        for enumeration in question_options['enumerations']:
            self.lines.append(
                self.get_local_text(enumeration['text'])
            )
        # Two blank lines between questions
        self.lines.append('')
        self.lines.append('')
