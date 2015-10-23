"""
Converts RIOS form (and calculationset) files into a REDCap csv file.
"""

import argparse
import json
import pkg_resources
import rios.conversion.classes as Rios
import sys
import yaml

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
        self.load_input_files(args.form, args.calculationset)

        if self.calculationset:
            if self.calculationset['instrument'] != self.form['instrument']:
                self.stderr.write(
                        'FATAL: The form and calculationset '
                        'must reference the same Instrument.\n')
                sys.exit(1)

        for page in self.form['pages']:
            self.start_page(page)
            for element in self.page['elements']:
                self.process_element(element)
        self.create_csv_file()
        sys.exit(0)

    def create_csv_file(self):
        self.outfile.write('%s\n' % self.calculationset)

    def load_input_files(self, form, calculationset):
        loader = {'yaml': yaml, 'json': json}[self.format]
        self.form = loader.load(form)
        if calculationset:
            self.calculationset = loader.load(calculationset)

    def process_element(self, element):
        print(element['type'], element['options'])

    def start_page(self, page):
        self.page = page
        
main = FromRios()
