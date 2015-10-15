"""
Converts a Qualtrics qsf file into a series of output files

    - <prefix>_c.<format> RIOS calculation
    - <prefix>_i.<format> RIOS instrument
    - <prefix>_f.<format> RIOS web form

The RIOS calculation file is only created when there are 
calculation fields in the input.
"""

import argparse
import json
import re
import rios.conversion.classes as Rios
import sys
import os
import yaml

class Converter(object):
    def __init__(self):
        args = self._get_args()
        self.prefix = args.prefix
        self.version = args.version
        self.format = args.format
        self.page_name = PageName()
        self(args.infile)
        
    def _get_args(self):
        parser = argparse.ArgumentParser(
                prog=os.path.basename(sys.argv[0]),
                formatter_class=argparse.RawTextHelpFormatter,
                description=__doc__)
        parser.add_argument(
                '--format',
                default='yaml',
                choices=['yaml', 'json'],
                help='The format and extension for the output files.  '
                        'The default is "yaml".')
        parser.add_argument(
                '--infile',
                required=True,
                type=argparse.FileType('r'),            
                help="The qsf input file to process.  Use '-' for stdin.")
        parser.add_argument(
                '--prefix',
                required=True,
                help='The prefix for the output files')
        parser.add_argument(
                '--version',
                required=True,
                help='The instrument version to output.')
        return parser.parse_args()
    
    def __call__(self, fname):
        """process the qsf input, and create output files.
        ``fname`` is an open file object.
        """
        self.qualtrics = self.get_qualtrics(json.load(fname))
        self.localization = self.qualtrics['localization']
        self.instrument = Rios.Instrument(
                id='urn:' + self.qualtrics['id'],
                version=self.version,
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
            if element['Type'] == 'Page Break':
                self.start_page()
            elif element['Type'] == 'Question':
                self.process_question(questions[element['QuestionID']])
        self.create_instrument_file()
        self.create_calculation_file()
        self.create_form_file()

    def create__file(self, kind, obj):
        if obj:
            obj.clean()
            with open(self.filename(kind), 'w') as fo:
                if self.format == 'json':
                    json.dump(obj, fo, indent=1)
                elif self.format == 'yaml':
                    yaml.safe_dump(
                            json.loads(json.dumps(obj)), 
                            fo, 
                            default_flow_style=False)

    def create_calculation_file(self):
        if self.calculations.get('calculations', False):
            self.create__file('c', self.calculations)

    def create_instrument_file(self):
        self.create__file('i', self.instrument)
        
    def create_form_file(self):
        self.create__file('f', self.form)

    def filename(self, kind):
        return '%(prefix)s_%(kind)s.%(extension)s' % {
                'prefix':self.prefix,
                'kind': kind, 
                'extension': self.format, }

    def get_choices(self, question):
        """ Returns an array of tuples: (id, choice)
        """
        choices = question.get('Choices', [])
        order = question.get('ChoiceOrder', [])
        if choices:
            if isinstance(choices, dict):
                if order:
                    choices = [(x, choices[str(x)]) for x in order]
                else:
                    choices = [i for i in enumerate(choices.values())]
            elif isinstance(choices, list):
                choices = [i for i in enumerate(choices)]
            else:
                raise ValueError, ('not dict or list', choices, question)
            choices = [(str(i).lower(), c['Display']) for i, c in choices]
        return choices
            
    def get_qualtrics(self, raw):
        """ Extract all the useful info from the raw qualtrics object
        into a dict and return it.
        """
        survey_entry = raw['SurveyEntry']
        qualtrics = {
                'description':    survey_entry['SurveyDescription'],
                'id':             survey_entry['SurveyID'],
                'localization':   survey_entry['SurveyLanguage'].lower(),
                'title':          survey_entry['SurveyName'],
                'block_elements': [],
                'questions':      {}, # QuestionID: payload (dict)
                }
        questions = qualtrics['questions']
        block_elements = qualtrics['block_elements']
        for survey_element in raw['SurveyElements']:
            element = survey_element['Element']
            if element == 'BL':
                """ Element: BL
                Payload is either a list of Block or a dict of Block.
                Sets ``block_elements`` to the first non-empty BlockElements.
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
        
    def get_type(self, question):
        if self.choices:
            return Rios.TypeObject(
                    base='enumeration',
                    enumerations=Rios.EnumerationCollectionObject(**{
                            str(i): None
                            for i, c in self.choices}), )
        else:
            return 'text'

    def localized_string_object(self, string):
        return Rios.LocalizedStringObject({self.localization: string})

    def make_element(self, question):
        element = Rios.ElementObject()
        element['type'] = 'question'
        element['options'] = Rios.QuestionObject(
                fieldId=question['DataExportTag'].lower(),
                text=self.localized_string_object(question['QuestionText']),)
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
        self.choices = self.get_choices(question)
        #add to instrument
        field = self.make_field(question)
        self.instrument.add_field(field) 
         
        #add to form
        element = self.make_element(question)
        self.page.add_element(element)
        
    def start_page(self):
        self.page = Rios.PageObject(id=self.page_name.next())
        self.form.add_page(self.page)
    
class PageName(object):
    def __init__(self, start=0):
        self.page_id = start
    
    def next(self):
        self.page_id += 1 
        return 'page_%02d' % self.page_id

def main():
    Converter()
    sys.exit(0)

