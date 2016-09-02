#
# Copyright (c) 2016, Prometheus Research, LLC
#


import sys


from rios.core.validation.instrument import get_full_type_definition
from rios.conversion.base import FromRios
from rios.core.exceptions import (
    ConversionValueError,
    RiosFormatError,
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
        if 'pages' not in self.form or not self.form['pages']:
            raise RiosFormatError(
                "RIOS data dictionary conversion failure. Error:"
                "RIOS form does not contain valid page data"
            )
        for page in self.form['pages']:
            try:
                # Start the page
                self.lines.append('[[PageBreak]]')
                elements = page['elements']
                # Process question elements
                for question in elements:
                    _type = question['type']
                    question_options = question['options']
                    # Handle form element if a question
                    if _type == 'question':
                        field_id = question['fieldId']
                        field = self.fields[field_id]
                        type_object = get_full_type_definition(
                            self.instrument,
                            field['type']
                        )
                        base = type_object['base']
                        if base == 'enumerationSet':
                            self.lines.append('[[MultipleAnswer]]')
                        if base not in ('enumeration', 'enumerationSet',):
                            error = ConversionValueError(
                                "Field skipped:"
                                str(field_id)
                            )
                            error.wrap(
                                "Base not \"enumeration\" or"
                                " \"enumerationSet\". Got:",
                                str(base)
                            )
                            self.logger.warning(str(error))
                            # Break to halt processing of question
                            break
                        self.lines.append('%d. %s' % (
                                self.question_number.next(),
                                self.get_local_text(question['text']), ))
                        # blank line separates question from choices.
                        self.lines.append('')
                        for enumeration in question['enumerations']:
                            self.lines.append(
                                self.get_local_text(enumeration['text'])
                            )
                        # Two blank lines between questions
                        self.lines.append('')
                        self.lines.append('')
                    else:
                        # Qualtrics only handles form questions
                        error = ConversionValueError(
                            'Form element skipped with ID:',
                            str(question_options.get('fieldId',
                                                     'Unknown field ID')
                            )
                        )
                        error.wrap(
                            'Form element type is not \"question\". Got:',
                            str(_type)
                        )
                        self.logger.warning(str(error))
                        # Break to halt processing of question
                        break
                else:
                    continue
                break
        except Exception as exc:
            error = RiosFormatError(
                "RIOS data dictionary conversion failure. Error:"
                str(exc)
            )
            self.logger.error(str(error))
            raise error
        else:
            # Skip the first line ([[PageBreak]]) and the last 2 lines (blank)
            for line in self.lines[1: -2]:
                self._defintion.append(line)
