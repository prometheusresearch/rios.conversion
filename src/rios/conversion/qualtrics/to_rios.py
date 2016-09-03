#
# Copyright (c) 2016, Prometheus Research, LLC
#


import collections
import six


from rios.conversion.base import ToRios, localized_string_object, structures
from rios.conversion.utils import JsonReader
from rios.conversion.exception import (
    Error,
    ConversionValueError,
    QualtricsFormatError,
)


__all__ = (
    'QualtricsToRios',
)


class PageName(object):
    """ Provides easy naming for pages """

    def __init__(self, start=0):
        self.page_id = start

    def next(self):
        self.page_id += 1
        return "page_{0:0=2d}".format(self.page_id)


class JsonReaderMainProcessor(JsonReader):
    """ Process Qualtrics JSON data """

    def processor(self, data):
        """ Extract instrument data into a dict. """
        try:
            qualtrics = {
                'block_elements': [],
                'questions':      {},   # QuestionID: payload (dict)
            }
            for survey_element in data['SurveyElements']:
                element = (
                    survey_element.get('Element', None)
                    if isinstance(survey_element, dict)
                    else None
                )
                # Payload may be a "null" value in *.qsf files
                payload = (
                    survey_element.get('Payload', None)
                    if isinstance(survey_element, dict)
                    else None
                )
                if not element:
                    raise QualtricsFormatError(
                        'Missing \"Element\" field in \"SurveyElements\":',
                        repr(survey_element)
                    )
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
                    if not payload:
                        raise QualtricsFormatError(
                            'Missing \"Payload\" field in \"SurveyElements\":',
                            repr(survey_element)
                        )
                    qualtrics['questions'][payload['QuestionID']] = payload
        except Exception as exc:
            if isinstance(exc, QualtricsFormatError):
                error = QualtricsFormatError(
                    'Processor read error:',
                    str(exc)
                )
            else:
                error = QualtricsFormatError(
                    'Processor read error:',
                    repr(exc)
                )
            raise error
        else:
            return qualtrics


class QualtricsToRios(ToRios):
    """ Converts a Qualtrics *.qsf file to the RIOS specification format """

    def __init__(self, filemetadata=False, *args, **kwargs):
        super(QualtricsToRios, self).__init__(*args, **kwargs)
        self.page_name = PageName()

    def __call__(self):
        """ Process the qsf input, and create output files """

        # Preprocessing
        try:
            self.reader = JsonReaderMainProcessor(self.stream)
            self.reader.process()
        except Exception as exc:
            error = Error(
                "Unable to parse Qualtrics data dictionary:",
                "Invalid JSON formatted text"
            )
            error.wrap(
                "Parse error:",
                str(exc)
            )
            self.logger.error(str(error))
            raise error

        # Initialize processor
        process = Processor(self.reader, self.localization)

        # MAIN PROCESSING
        # Occures in two steps:
        #   1) Process data and page names into containers
        #   2) Iterate over containers to construct RIOS definitions
        # NOTE:
        #   1) Each CSV row is an ordered dict (see CsvReader in utils/)
        #   2) Start=2, because spread sheet programs set header row to 1
        #       and first data row to 2 (for user friendly errors)
        question_data = self.reader.data['questions']

        page_question_map = collections.OrderedDict()
        page_names = set()

        page_name = self.page_name.next()
        page_names.add(page_name)
        for form_element in self.reader.data['block_elements']:
            element_type = form_element.get('Type', None)
            if element_type == 'Page Break':
                page_name = self.page_name.next()
                page_names.add(page_name)
            elif element_type == 'Question':
                question_id = form_element.get('QuestionID', None)
                if question_id is None:
                    error = QualtricsFormatError(
                        "Block element QuestionID value not found in:",
                        str(form_element)
                    )
                    self.logger.error(str(error))
                    raise error
                elif question_id not in question_data:
                    error = QualtricsFormatError(
                        "QuestionID value not found in question data. Got ID:",
                        str(question_id)
                    )
                    self.logger.error(str(error))
                    raise error
                elif page_name not in page_question_map:
                    page_question_map[page_name] = {
                        question_id: question_data[question_id],
                    }
                else:
                    page_question_map[page_name].update(
                        {question_id: question_data[question_id]}
                    )
            else:
                error = QualtricsFormatError(
                    "Invalid type for block element. Expected types:",
                    "\"Page Break\" or \"Question\""
                )
                if element_type:
                    error.wrap("But got invalid type value:",
                               str(element_type))
                else:
                    error.wrap("Missing type value")
                self.logger.error(str(error))
                raise error

        for page_name in page_names:
            self.page_container.update(
                {page_name: structures.PageObject(id=page_name), }
            )

        for page_name, page in six.iteritems(self.page_container):
            mapping_data = page_question_map[page_name]
            for question_id, question_data in six.iteritems(mapping_data):
                try:
                    # WHERE THE MAGIC HAPPENS
                    fields = process(page, question_data)

                    # Clear processor's internal storage for next question
                    process.clear_storage()

                    for field in fields:
                        self.field_container.append(field)

                except Exception as exc:
                    if isinstance(exc, ConversionValueError):
                        error = Error(
                            "Skipping question: " + str(question_id)
                            + ". Error:",
                            str(exc)
                        )
                        self.logger.warning(str(error))
                    else:
                        error = Error(
                            "An unknown error occured:",
                            repr(exc)
                        )
                        error.wrap(
                            "REDCap data dictionary conversion failure:",
                            "Unable to parse REDCap data dictionary CSV"
                        )
                        self.logger.error(str(error))
                        raise exc

        # Construct insrument objects
        for field in self.field_container:
            self._instrument.add_field(field)
        # Page container is a dict instead of a list, so iterate over vals
        for page in six.itervalues(self.page_container):
            self._form.add_page(page)

        # Post-processing/validation
        self.validate()


class Processor(object):
    """ Processor class for Qualtrics data dictionaries """

    def __init__(self, reader, localization):
        self.reader = reader
        self.localization = localization

        # For storing fields
        self._field_storage = []

        # Object to store pointer to instrument field object
        self._field = None
        self._field_type = None

        # Object to store pointers to question choices
        self._choices = None

    def __call__(self, page, question_data):
        """ Processes a Qualtrics data dictionary question per form page """

        # Generate question element object
        question = structures.ElementObject()

        try:
            self.question_field_processor(question_data, question)
        except Exception as exc:
            # Reset storage if conversion of current page/question fails
            self.clear_storage()
            error = ConversionValueError(
                "Invalid questions data. Got error:",
                repr(exc)
            )
            raise error

        # Add the configured question to the page
        page.add_element(question)

        fields = self._field_storage

        return fields

    @staticmethod
    def clean_question(text):
        return text.replace('<br>', '')

    def clear_storage(self):
        self._field_storage = []

    def question_field_processor(self, question_data, question):
        """ Processe questions and fields """
        question_type = question_data['QuestionType']
        question_text = localized_string_object(
            self.localization,
            self.clean_question(question_data['QuestionText'])
        )
        if question_type == 'DB':
            # Question is only display text
            question['type'] = 'text'
            question['options'] = {'text': question_text}
        else:
            # Question is an interactive form element
            question['type'] = 'question'
            question['options'] = structures.QuestionObject(
                fieldId=question_data['DataExportTag'].lower(),
                text=localized_string_object(
                    self.localization,
                    self.clean_question(
                        question_data['QuestionText']
                    )
                ),
            )

            # Choices are generated, where "choices" is an array of
            # tuples: (id, choice)
            self._choices = question_data.get('Choices', [])
            order = question_data.get('ChoiceOrder', [])
            if self._choices:
                if isinstance(self._choices, dict):
                    if not order:
                        keys = self._choices.keys()
                        if all([k.isdigit() for k in keys]):
                            keys = [int(k) for k in keys]
                        order = sorted(keys)
                    self._choices = [(x, self._choices[str(x)]) for x in order]
                elif isinstance(self._choices, list):
                    self._choices = [i for i in enumerate(self._choices)]
                else:
                    error = ConversionValueError(
                        "Choices are not formatted correctly. Got choices:",
                        str(self._choices)
                    )
                    error.wrap("With question data:", str(question))
                    raise error
                self._choices = [
                    (str(i).lower(), c['Display'])
                    for i, c in self._choices
                ]
                # Process question object and field type object
                question_obj = question['options']
                field_type = structures.TypeObject(base='enumeration', )
                for _id, choice in self._choices:
                    question_obj.add_enumeration(
                        structures.DescriptorObject(
                            id=_id,
                            text=localized_string_object(
                                self.localization,
                                choice
                            ),
                        )
                    )
                    field_type.add_enumeration(str(_id))
            else:
                field_type = 'text'

            # Consruct field for instrument definition
            field = structures.FieldObject(
                id=question_data['DataExportTag'].lower(),
                description=question_data['QuestionDescription'],
                type=field_type,
                required=False,
                identifiable=False,
            )
            self._field_storage.append(field)
