"""
Converts RIOS form (and calculationset) files into a REDCap csv file.
"""

import argparse
import json
import pkg_resources
import rios.conversion.classes as Rios
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
                '--calculationset',
                type=argparse.FileType('r'),
                help="The calculationset file to process.  Use '-' for stdin.")
        self.parser.add_argument(
                '--instrument',
                required=True,
                type=argparse.FileType('r'),
                help="The instrument file to process.  Use '-' for stdin.")
        self.parser.add_argument(
                '--form',
                required=True,
                type=argparse.FileType('r'),
                help="The form file to process.  Use '-' for stdin.")
        self.parser.add_argument(
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

        if self.calculationset:
            instrument = Rios.InstrumentReferenceObject(self.instrument)
            if (self.calculationset['instrument'] != instrument
                    or self.form['instrument'] != instrument):
                self.stderr.write(
                        'FATAL: The form and calculationset '
                        'must reference the same Instrument.\n')
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
        self.outfile.write('%s\n' % self.calculationset)
        for row in self.rows:
            self.outfile.write('%s\n' % row)

    def get_field_type(self, field):
        non_text = {
                'float': 'number',
                'integer': 'integer', }
        typ = field['type']
        obj = None
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
        if calculationset:
            self.calculationset = loader.load(calculationset)

    def process_element(self, element):
        print(element['type'], element['options'])
        type_ = element['type']
        if type_ == 'header':
            self.section_header = self.get_local_text(
                    element['options']['text'])
        elif type_ == 'question':
            question = element['options']
            field_id = question['fieldId']
            field = self.fields[field_id]
            field_type, field_object = self.get_field_type(field)
            if field_object:
                if 'range' in field_object:
                    min_ = field_object['range'].get('min', '')
                    max_ = field_object['range'].get('max', '')
                    min_ = str(min_) if min_ is not '' else ''
                    max_ = str(max_) if max_ is not '' else ''
            if 'rows' in question and 'questions' in question:
                self.rows.extend(self.process_matrix(question))
            else:
                self.rows.append([
                        field_id,
                        self.form_name,
                        self.section_header,
                        field_type,
                        self.get_local_text(question['text']),
                        'CHOICES',
                        question.get('help', {}),
                        "value_type",
                        "Min",
                        "Max",
                        'y' if field['identifiable'] else '',
                        "Branching",
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
