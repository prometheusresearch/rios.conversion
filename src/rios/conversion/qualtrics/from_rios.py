"""
Converts RIOS instrument, form, and optional calculationset files
into a text file in Qualtrics Simple .TXT format.
"""

import rios.core.validation.instrument as RI
import sys

from rios.conversion.from_rios import FromRios


class QuestionNumber:
    def __init__(self):
        self.number = 0

    def next(self):
        self.number += 1
        return self.number


class QualtricsFromRios(FromRios):
    description = __doc__

    def call(self):
        self.lines = []
        self.question_number = QuestionNumber()
        for page in self.form['pages']:
            self.start_page(page)
            for element in self.elements:
                self.process_element(element)
        self.create_txt_file()
        return 0

    def create_txt_file(self):
        # skip the first line ([[PageBreak]])
        # skip the last 2 lines (blank)
        for line in self.lines[1: -2]:
            self.outfile.write(line + '\n')

    def process_element(self, element):
        type_ = element['type']
        options = element['options']
        if type_ == 'question':
            self.process_question(options)
        else:
            self.warning('element type is not "question": %s' % type_)

    def process_question(self, question):
        field_id = question['fieldId']
        field = self.fields[field_id]
        type_object = RI.get_full_type_definition(
                self.instrument,
                field['type'])
        base = type_object['base']
        if base == 'enumeration':
            multiple_answer = False
        elif base == 'enumerationSet':
            multiple_answer = True
        else:
            self.skip_field_warning(
                    field_id,
                    'base not "enumeration" or "enumerationSet": %s' % base, )
            return
        self.lines.append('%d. %s' % (
                self.question_number.next(),
                self.get_local_text(question['text']), ))
        if multiple_answer:
            self.lines.append('[[MultipleAnswer]]')
        self.lines.append('')   # blank line separates question from choices.
        for enumeration in question['enumerations']:
            self.lines.append(self.get_local_text(enumeration['text']))
        self.lines.append('')   # 2 blank lines between questions
        self.lines.append('')   # 2 blank lines between questions

    def skip_field_warning(self, field_id, message):
        self.warning('field skipped: %s, %s' % (field_id, message))

    def start_page(self, page):
        self.lines.append('[[PageBreak]]')
        self.elements = page['elements']


def main(argv=None, stdout=None, stderr=None):
    sys.exit(QualtricsFromRios()(argv, stdout, stderr))   # pragma: no cover
