"""
Convert from RIOS.
"""
import argparse
import json
import pkg_resources
import sys
import yaml

import rios.conversion.classes as Rios


class FromRios(object):
    description = __doc__

    def __init__(self):
        self.parser = argparse.ArgumentParser(
                formatter_class=argparse.RawTextHelpFormatter,
                description=self.description)
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
                '--verbose',
                action='store_true',
                help='Display warning messages.')
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
        self.verbose = args.verbose
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
        return self.call()

    def call(self):
        """ must implement in the subclass.
        return 0 for success, > 0 for error.
        """
        raise NotImplementedError   # pragma: no cover

    def get_loader(self, file_object):
        name = file_object.name
        if name.endswith('.json'):
            loader = json
        elif name.endswith('.yaml') or name.endswith('.yml'):
            loader = yaml
        else:
            loader = {'yaml': yaml, 'json': json}[self.format]
        return loader

    def get_local_text(self, localized_string_object):
        return localized_string_object.get(self.localization, '')

    def load_file(self, file_obj):
        loader = self.get_loader(file_obj)
        return loader.load(file_obj)

    def load_input_files(self, form, instrument, calculationset):
        self.form = self.load_file(form)
        self.instrument = self.load_file(instrument)
        self.fields = {f['id']: f for f in self.instrument['record']}
        self.calculationset = (
                self.load_file(calculationset)
                if calculationset
                else {})

    def warning(self, message):
        if self.verbose:
            self.stderr.write('WARNING: %s\n' % message)
