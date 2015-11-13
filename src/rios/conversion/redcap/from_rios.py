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
            return 1

        if (self.calculationset
                    and self.calculationset['instrument'] != instrument):
            self.stderr.write(
                    'FATAL: Calculationset and Instrument do not match: '
                    '%s != %s.\n' % (
                            self.calculationset['instrument'],
                            instrument))
            return 1

        self.rows = [COLUMNS]
        self.section_header = ''
        for page in self.form['pages']:
            self.start_page(page)
            for element in self.elements:
                self.process_element(element)
        self.create_csv_file()
        return 0

    def convert_rexl_expression(self, rexl):
        converted = rexl.replace('!=', '<>')
        # finish this ...
        return converted
    
    def create_csv_file(self):
        csv_writer = csv.writer(self.outfile)
        csv_writer.writerows(self.rows)
        if self.calculationset:
            for calculation in self.calculationset['calculations']:
                self.process_calculation(calculation)

    def get_choices(self, array):
        return ' | '.join(['%s, %s' % (
                d['id'],
                self.get_local_text(d['text'])) for d in array])

    def get_local_text(self, localized_string_object):
        return localized_string_object.get(self.localization, '')

    def get_type_tuple(self, base, question):
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

    def load_input_files(self, form, instrument, calculationset):
        loader = {'yaml': yaml, 'json': json}[self.format]
        self.form = loader.load(form)
        self.instrument = loader.load(instrument)
        self.fields = {f['id']: f for f in self.instrument['record']}
        self.calculationset = (
                loader.load(calculationset)
                if calculationset
                else {})

    def process_calculation(self, calculation):
        def get_expression():
            expression = calculation['options']['expression']
            if calculation['method'] == 'python':
                expression = self.convert_python_expression(expression)
            return expression

        self.rows.append([
                calculation['id'],
                'calculations',
                '',
                'calc',
                calculation['description'],
                get_expression(),
                '', '', '', '', '', '', '', '', '', '', '', '', ])

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
        if len(question['questions']) > 1:
            self.warning(
                    'REDCap matrices support only one question.'
                    ' Question ignored: %s' % question['fieldId'])
            return
        column = question['questions'][0]
        if 'enumerations' not in column:
            self.warning(
                    'REDCap matrix column must be an enumeration.'
                    '  Question ignored: %s' % question['fieldId'])
            return
        choices = self.get_choices(column['enumerations'])
        section_header = self.section_header
        matrix_group_name = question['fieldId']
        field = self.fields[matrix_group_name]
        type_object = RI.get_full_type_definition(
                self.instrument,
                field['type'])
        base = type_object['base']
        field_type, valid_type = self.get_type_tuple(base, question)
        for row in question['rows']:
            self.rows.append([
                    row['id'],
                    self.form_name,
                    section_header,
                    field_type,
                    self.get_local_text(row['text']),
                    choices,
                    self.get_local_text(row.get('help', {})),
                    valid_type,
                    '',
                    '',
                    'y' if field['identifiable'] else '',
                    '',
                    'y' if field['required'] else ''
                    '',
                    '',
                    matrix_group_name,
                    'y',
                    '', ])
            section_header = ''

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

        def get_trigger():
            return (
                    question['events'][0]['trigger']
                    if 'events' in question and question['events']
                    else '' )
                           
        branching = self.convert_rexl_expression(get_trigger())
        if 'rows' in question and 'questions' in question:
            self.process_matrix(question)
        else:
            field_id = question['fieldId']
            field = self.fields[field_id]
            type_object = RI.get_full_type_definition(
                    self.instrument,
                    field['type'])
            base = type_object['base']
            field_type, valid_type = self.get_type_tuple(base, question)
            min_value, max_value = get_range(type_object)
            self.rows.append([
                    field_id,
                    self.form_name,
                    self.section_header,
                    field_type,
                    self.get_local_text(question['text']),
                    get_choices(),
                    self.get_local_text(question.get('help', {})),
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

    def warning(self, message):
        self.stderr.write('WARNING: %s\n' % message)
        
def main(argv=None, stdout=None, stderr=None):
    sys.exit(FromRios()(argv, stdout, stderr))
