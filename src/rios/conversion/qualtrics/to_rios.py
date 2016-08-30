#
# Copyright (c) 2016, Prometheus Research, LLC
#


import json
import sys
import rios.conversion.structures as Rios


from rios.conversion.base import ToRios
from rios.conversion.exceptions import (
    Error,
    ConversionValueError,
    QualtricsFormatError,
)


__all__ = (
    'QualtricsToRios',
)


def json_reader(stream):
    try:
        return json.load(stream)
    except Exception as e:
        raise ValueError('Unable to load input file as JSON', e)


class QualtricsToRios(ToRios):
    """ Converts a Qualtrics *.qsf file to the RIOS specification format """

    def __init__(self, *args, **kwargs):
        """
        Required parameters should be generated BEFORE instantiating this class
        """

        super(QualtricsToRios, self).__init__(*args, **kwargs)
        self.page_name = PageName()

    def __call__(self):
        """ Process the qsf input, and create output files """

        self.reader = json_reader(self.stream)

        self.page = Rios.PageObject(id=self.page_name.next())
        self.form.add_page(self.page)

        questions = self.reader['questions']
        for element in self.reader['block_elements']:
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

    @staticmethod
    def clean_question(text):
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

    def make_element(self, question):
        element = Rios.ElementObject()
        question_type = question['QuestionType']
        question_text = self.localized_string_object(
                self.clean_question(question['QuestionText'])
        )
        if question_type == 'DB':
            element['type'] = 'text'
            element['options'] = {'text': question_text}
        else:
            element['type'] = 'question'
            element['options'] = Rios.QuestionObject(
                fieldId=question['DataExportTag'].lower(),
                text=self.localized_string_object(
                    self.clean_question(
                        question['QuestionText']
                    )
                ), 
            )
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


class PageName(object):
    def __init__(self, start=0):
        self.page_id = start

    def next(self):
        self.page_id += 1
        return 'page_%02d' % self.page_id
