"""
Converts RIOS form (and calculationset) files into a REDCap csv file.
"""

import argparse
import csv
import json
import pkg_resources
import rios.conversion.classes as Rios
import rios.core.validation.instrument as RI
import sys
import yaml

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


class FromRios(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(
                formatter_class=argparse.RawTextHelpFormatter,
                description=__doc__)
        try:
            self_version = \
                pkg_resources.get_distribution('rios.conversion').version
        except pkg_resources.DistributionNotFound:
            self_version = 'UNKNOWN'
        self.parser.add_argument(
                '-v',
                '--version',
                action='version',
                version='%(prog)s ' + self_version, )
        self.parser.add_argument(
                '--format',
                default='yaml',
                choices=['yaml', 'json'],
                help='The format for the input files.  '
                        'The default is "yaml".')
        self.parser.add_argument(
                '--localization',
                default='en',
                metavar='',
                help='The language to extract from the RIOS form.  '
                        'The default is "en"')
        self.parser.add_argument(
                '-c',
                '--calculationset',
                type=argparse.FileType('r'),
                help="The calculationset file to process.  Use '-' for stdin.")
        self.parser.add_argument(
                '-i',
                '--instrument',
                required=True,
                type=argparse.FileType('r'),
                help="The instrument file to process.  Use '-' for stdin.")
        self.parser.add_argument(
                '-f',
                '--form',
                required=True,
                type=argparse.FileType('r'),
                help="The form file to process.  Use '-' for stdin.")
        self.parser.add_argument(
                '-o',
                '--outfile',
                required=True,
                type=argparse.FileType('w'),
                help="The name of the output file.  Use '-' for stdout.")

    def __call__(self, argv=None, stdout=None, stderr=None):
        """process the csv input, and create output files. """
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr

        try:
            args = self.parser.parse_args(argv)
        except SystemExit as exc:
            return exc

        self.outfile = args.outfile
        self.localization = args.localization
        self.format = args.format
        self.load_input_files(args.form, args.instrument, args.calculationset)
        self.types = self.instrument.get('types', {})

        instrument = Rios.InstrumentReferenceObject(self.instrument)
        if self.form['instrument'] != instrument:
            self.stderr.write(
                    'FATAL: Form and Instrument do not match: '
                    '%s != %s.\n' % (self.form['instrument'], instrument))
            sys.exit(1)

        if (self.calculationset
                    and self.calculationset['instrument'] != instrument):
            self.stderr.write(
                    'FATAL: Calculationset and Instrument do not match: '
                    '%s != %s.\n' % (
                            self.calculationset['instrument'], 
                            instrument))
            sys.exit(1)

        self.rows = [COLUMNS]
        self.section_header = ''
        for page in self.form['pages']:
            self.start_page(page)
            for element in self.elements:
                self.process_element(element)
        self.create_csv_file()
        sys.exit(0)

    def create_csv_file(self):
        csv_writer = csv.writer(self.outfile)
        csv_writer.writerows(self.rows)

#        if self.calculationset:
#            self.outfile.write('%s\n' % self.calculationset)

    def get_choices(self, ary):
        return ' | '.join(['%s, %s' % (
                d['id'], 
                self.get_local_text(d['text'])) for d in ary])
        
    def get_field_type(self, field):
        """ Returns field_type and valid_type given Field Object
        """
        non_text = {
                'float': 'number',
                'integer': 'integer', }
        typ = field['type']

        if isinstance(typ, str):
            if typ in self.types:
                typ = self.types[typ]
            else:
                return typ
        else:
            typ = typ['base']    
       
            
        if isinstance(typ, dict) and 'base' in typ:
            obj = typ
            typ = typ['base']
        if isinstance(typ, str):
            return non_text[typ], obj if typ in non_text else 'text', obj
        raise ValueError('field type not str or TypeObject', field)

    def get_local_text(self, localized_string_object):
        return localized_string_object.get(self.localization, '')

    def load_input_files(self, form, instrument, calculationset):
        loader = {'yaml': yaml, 'json': json}[self.format]
        self.form = loader.load(form)
        self.instrument = loader.load(instrument)
        self.fields = {f['id']: f for f in self.instrument['record']}
        self.calculationset = (
                loader.load(calculationset) 
                if calculationset 
                else {})

    def process_element(self, element):
        type_ = element['type']
        options = element['options']
        if type_ in ['header', 'text']:
            self.process_header(options)
        elif type_ == 'question':
            self.process_question(options)

    def process_header(self, header):
        self.section_header = self.get_local_text(header['text'])

    def process_matrix(self, question):
        raise NotImplementedError

    def process_question(self, question):
        def get_choices():
            return (
                    self.get_choices(question['enumerations'])
                    if 'enumerations' in question
                    else '')

        def get_range(type_object):
            r = type_object.get('range', {})
            min_value = str(r.get('min', ''))
            max_value = str(r.get('max', ''))
            return min_value, max_value
            
        def get_type_tuple(base):
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
            else:
                 return 'text', ''            
         
        branching = ''
        if 'rows' in question and 'questions' in question:
            self.rows.extend(self.process_matrix(question))
        else:
            field_id = question['fieldId']
            field = self.fields[field_id]
            type_object = RI.get_full_type_definition(
                    self.instrument, 
                    field['type'])
            base = type_object['base']
            field_type, valid_type = get_type_tuple(base)
            min_value, max_value = get_range(type_object)            
            self.rows.append([
                    field_id,
                    self.form_name,
                    self.section_header,
                    field_type,
                    self.get_local_text(question['text']),
                    get_choices(),
                    question.get('help', ''),
                    valid_type,
                    min_value,
                    max_value,
                    'y' if field['identifiable'] else '',
                    branching,
                    'y' if field['required'] else ''
                    '',
                    '',
                    '',
                    '',
                    '', ])
        self.section_header = ''

    def start_page(self, page):
        self.form_name = page['id']
        self.elements = page['elements']

main = FromRios()
