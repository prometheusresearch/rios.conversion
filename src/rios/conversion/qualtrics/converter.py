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
        self.id = args.id
        self.version = args.version
        self.title = args.title
        self.localization = args.localization
        self.format = args.format
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
                '--id',
                required=True,
                help='The instrument id to output.')
        parser.add_argument(
                '--infile',
                required=True,
                type=argparse.FileType('r'),            
                help="The qsf input file to process.  Use '-' for stdin.")
        parser.add_argument(
                '--localization',
                default='en',
                help='The default localization for the web form.  '
                        'The default is "en"')
        parser.add_argument(
                '--prefix',
                required=True,
                help='The prefix for the output files')
        parser.add_argument(
                '--title',
                required=True,
                help='The instrument title to output.')
        parser.add_argument(
                '--version',
                required=True,
                help='The instrument version to output.')
        return parser.parse_args()
    
    def __call__(self, fname):
        """process the qsf input, and create output files.
        ``fname`` is an open file object.
        """
        self.instrument = Rios.Instrument(
                id=self.id,
                version=self.version,
                title=self.title)
        self.calculations = Rios.CalculationSetObject(
                instrument=Rios.InstrumentReferenceObject(self.instrument),
                )
        self.form = Rios.WebForm(
                instrument=Rios.InstrumentReferenceObject(self.instrument),
                defaultLocalization=self.localization,
                title=self.localized_string_object(self.title),
                )
        self.calculation_variables = set()
        self.instrument = Rios.DefinitionSpecification()
        self.instrument.update(json.load(fname))
        self.create_instrument_file()
        self.create_calculation_file()
        self.create_form_file()

    def create__file(self, kind, obj):
        if obj:
            #obj.clean()
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

    def localized_string_object(self, string):
        return Rios.LocalizedStringObject({self.localization: string})

def main():
    Converter()
    sys.exit(0)

