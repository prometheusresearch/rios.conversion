"""
Converts a Qualtrics qsf file into a series of output files

    <OUTFILE_PREFIX> _c.<format> RIOS calculation
    <OUTFILE_PREFIX>_i.<format> RIOS instrument
    <OUTFILE_PREFIX>_f.<format> RIOS web form

The RIOS calculation file is only created when there are
calculation fields in the input.
"""

import argparse
import json
import pkg_resources
import rios.conversion.classes as Rios
from rios.conversion.to_rios import ToRios
import sys


class QualtricsToRios(ToRios):

    def __init__(self):
        self.page_name = PageName()
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
                '--infile',
                required=True,
                type=argparse.FileType('r'),
                help="The qsf input file to process.  Use '-' for stdin.")
        self.parser.add_argument(
                '--instrument-version',
                required=True,
                help='The instrument version to output.')
        self.parser.add_argument(
                '--outfile-prefix',
                required=True,
                help='The prefix for the output files')

    def __call__(self, argv=None, stdout=None, stderr=None):
        """process the qsf input, and create output files. """
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr

        try:
            args = self.parser.parse_args(argv)
        except SystemExit as exc:
            return exc

        self.outfile_prefix = args.outfile_prefix
        self.instrument_version = args.instrument_version
        self.format = args.format

        self.qualtrics = self.get_qualtrics(self.load_infile(args.infile))
        self.localization = self.qualtrics['localization']
        self.instrument = Rios.Instrument(
                id='urn:' + self.qualtrics['id'],
                version=self.instrument_version,
                title=self.qualtrics['title'],
                description=self.qualtrics['description'])
        self.calculations = Rios.CalculationSetObject(
                instrument=Rios.InstrumentReferenceObject(self.instrument),
                )
        self.form = Rios.WebForm(
                instrument=Rios.InstrumentReferenceObject(self.instrument),
                defaultLocalization=self.localization,
                title=self.localized_string_object(self.instrument['title']),
                )

        self.start_page()
        questions = self.qualtrics['questions']
        for element in self.qualtrics['block_elements']:
            element_type = element.get('Type', False)
            if element_type is False:
                raise ValueError(
                        "Block element has no Type: %s" % element)
            if element_type == 'Page Break':
                self.start_page()
            elif element_type == 'Question':
                question = questions.get(element['QuestionID'], False)
                if question is False:
                    raise ValueError(
                            "Block element QuestionID not found: %s" % element)
                self.process_question(question)
            else:
                raise ValueError(
                        "Block element has unknown Type: %s" % element)
        self.validate_results()
        self.create_instrument_file()
        self.create_calculation_file()
        self.create_form_file()
        return 0

    def clean_question(self, text):
        return text.replace('<br>', '')

    def get_choices(self, question):
        """ Returns an array of tuples: (id, choice)
        """
        choices = question.get('Choices', [])
        order = question.get('ChoiceOrder', [])
        if choices:
            if isinstance(choices, dict):
                if not order:
                    keys = choices.keys()
                    if all([k.isdigit() for k in keys]):
                        keys = [int(k) for k in keys]
                    order = sorted(keys)
                choices = [(x, choices[str(x)]) for x in order]

            elif isinstance(choices, list):
                choices = [i for i in enumerate(choices)]
            else:
                raise ValueError(
                        'not dict or list',
                        choices,
                        question)   # pragma: no cover
            choices = [(str(i).lower(), c['Display']) for i, c in choices]
        return choices

    def get_qualtrics(self, raw):
        """ Extract info from the raw qualtrics object and return a dict. """
        try:
            survey_entry = raw['SurveyEntry']
            qualtrics = {
                    'description':    survey_entry['SurveyDescription'],
                    'id':             survey_entry['SurveyID'],
                    'localization':   survey_entry['SurveyLanguage'].lower(),
                    'title':          survey_entry['SurveyName'],
                    'block_elements': [],
                    'questions':      {},   # QuestionID: payload (dict)
                    }
            questions = qualtrics['questions']
            block_elements = qualtrics['block_elements']
            for survey_element in raw['SurveyElements']:
                element = survey_element['Element']
                if element == 'BL':
                    """ Element: BL
                    Payload is either a list of Block or a dict of Block.
                    Sets block_elements to the first non-empty BlockElements.
                    """
                    payload = survey_element['Payload']
                    if isinstance(payload, dict):
                        payload = payload.values()
                    for block in payload:
                        if block['BlockElements']:
                            block_elements.extend(block['BlockElements'])
                            break
                elif element == 'SQ':
                    payload = survey_element['Payload']
                    questions[payload['QuestionID']] = payload
            return qualtrics
        except Exception, e:
            raise ValueError('Unable to parse raw qualtrics object', e)

    def get_type(self, question):
        if self.choices:
            type_object = Rios.TypeObject(base='enumeration', )
            for id_, choice in self.choices:
                type_object.add_enumeration(str(id_))
            return type_object
        else:
            return 'text'

    def load_infile(self, infile):
        try:
            return json.load(infile)
        except Exception, e:
            raise ValueError('Unable to load input file as JSON', e)

    def make_element(self, question):
        element = Rios.ElementObject()
        question_type = question['QuestionType']
        question_text = self.localized_string_object(
                self.clean_question(
                        question['QuestionText']))
        if question_type == 'DB':
            element['type'] = 'text'
            element['options'] = {'text': question_text}
        else:
            element['type'] = 'question'
            element['options'] = Rios.QuestionObject(
                    fieldId=question['DataExportTag'].lower(),
                    text=self.localized_string_object(
                            self.clean_question(
                                    question['QuestionText'])), )
        if self.choices:
            question_object = element['options']
            for id_, choice in self.choices:
                question_object.add_enumeration(Rios.DescriptorObject(
                    id=id_,
                    text=self.localized_string_object(choice),))
        return element

    def make_field(self, question):
        field = Rios.FieldObject()
        field['id'] = question['DataExportTag'].lower()
        field['description'] = question['QuestionDescription']
        field['type'] = self.get_type(question)
        field['required'] = False
        field['identifiable'] = False
        return field

    def process_question(self, question):
        try:
            self.choices = self.get_choices(question)
            # add to form
            element = self.make_element(question)
            self.page.add_element(element)
            if element['type'] == 'question':
                # add to instrument
                field = self.make_field(question)
                self.instrument.add_field(field)
        except Exception, e:
            raise ValueError(
                    "Unable to process question",
                    question,
                    e)

    def start_page(self):
        self.page = Rios.PageObject(id=self.page_name.next())
        self.form.add_page(self.page)


class PageName(object):
    def __init__(self, start=0):
        self.page_id = start

    def next(self):
        self.page_id += 1
        return 'page_%02d' % self.page_id


def main(argv=None, stdout=None, stderr=None):
    sys.exit(QualtricsToRios()(argv, stdout, stderr))    # pragma: no cover
