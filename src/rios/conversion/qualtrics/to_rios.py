#
# Copyright (c) 2016, Prometheus Research, LLC
#


import json
import sys
import rios.conversion.structures as Rios


from rios.conversion.base import ToRios
from rios.conversion.exception import (
    Error,
    ConversionValidationError,
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

class JsonReaderWithProcessor(JsonReader):
    """ Process Qualtrics JSON data """

    def processor(self, data):
        """ Extract info from the raw qualtrics object and return a dict. """
        try:
            survey_entry = data['SurveyEntry']
            qualtrics = {
                'description':    survey_entry['SurveyDescription'],
                'id':             survey_entry['SurveyID'],
                'localization':   survey_entry['SurveyLanguage'].lower(),
                'title':          survey_entry['SurveyName'],
                'block_elements': [],
                'questions':      {},   # QuestionID: payload (dict)
            }
            for survey_element in data['SurveyElements']:
                element = survey_element['Element']
                payload = survey_element['Payload']
                if element == 'BL':
                    # Element: BL
                    # Payload is either a list of Block or a dict of Block.
                    # Sets qualtrics['block_element'] to the first non-empty
                    # BlockElements.
                    if isinstance(payload, dict):
                        payload = payload.values()
                    for block in payload:
                        if block['BlockElements']:
                            qualtrics['block_elements'].extend(
                                block['BlockElements']
                            )
                            break
                elif element == 'SQ':
                    qualtrics['questions'][payload['QuestionID']] = payload
            return qualtrics
        except Exception as exc:
            error = QualtricsFormatError(
                'Unable to parse Qualtrics object. Error:',
                str(exc)
            )


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

        self.reader = JsonReaderWithProcessor(self.stream)
        self.reader.process()

        self.page = Rios.PageObject(id=self.page_name.next())
        self.form.add_page(self.page)

        questions = self.reader.json['questions']
        for element in self.reader.json['block_elements']:
            element_type = element.get('Type', False)
            if element_type is False:
                raise ValueError(
                    "Block element has no Type: %s" % element
                )
            if element_type == 'Page Break':
                self.page = Rios.PageObject(id=self.page_name.next())
                self.form.add_page(self.page)
            elif element_type == 'Question':
                question_id = questions.get(element['QuestionID'], False)
                if question is False:
                    raise ValueError(
                            "Block element QuestionID not found: %s" % element)
                self.process_question(question_id)
            else:
                raise ValueError(
                        "Block element has unknown Type: %s" % element)
        self.validate()

    def process_question(self, question):
        try:
            self.choices = self.get_choices(question)
            element = self.make_element(question)
            question = Rios.ElementObject()
            question_type = question['QuestionType']
            question_text = self.localized_string_object(
                self.clean_question(question['QuestionText'])
            )
            if question_type == 'DB':
                question['type'] = 'text'
                question['options'] = {'text': question_text}
            else:
                question['type'] = 'question'
                question['options'] = Rios.QuestionObject(
                    fieldId=question['DataExportTag'].lower(),
                    text=self.localized_string_object(
                        self.clean_question(
                            question['QuestionText']
                        )
                    ), 
                )
            if self.choices:
                question_object = question['options']
                for _id, choice in self.choices:
                    question_object.add_enumeration(
                        Rios.DescriptorObject(
                            id=_id,
                            text=self.localized_string_object(choice),
                        )
                    )
            self.page.add_element(question)
            if question['type'] == 'question':
                # add to instrument
                field = Rios.FieldObject()
                field['id'] = question['DataExportTag'].lower()
                field['description'] = question['QuestionDescription']
                field['type'] = self.get_type(question)
                field['required'] = False
                field['identifiable'] = False
                self._instrument.add_field(field)
        except Exception as exc:
            error = ConversionValueError(
                "Unable to process question: " + str(question) + ". Error:",
                str(exc)
            )

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

    def get_type(self, question):
        if self.choices:
            type_object = Rios.TypeObject(base='enumeration', )
            for id_, choice in self.choices:
                type_object.add_enumeration(str(id_))
            return type_object
        else:
            return 'text'


class PageName(object):
    """ Provides easy naming for pages """

    def __init__(self, start=0):
        self.page_id = start

    def next(self):
        self.page_id += 1
        return "{0:0=2d}".format(self.page_id)
