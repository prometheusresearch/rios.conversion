#
# Copyright (c) 2016, Prometheus Research, LLC
#


import argparse
import pkg_resources
import sys

from six import iteritems

from .redcap import RedcapToRios, RedcapFromRios 
from .qualtrics import QualtricsToRios, QualtricsFromRios


__all__ = (
    'ConversionScript',
    'convert'
)


# TODO: Add FromRios conversions
CONVERTERS = {
    'redcap': RedcapToRios,
    'qualtrics': QualtricsToRios
}


class ConversionScript(object):
    """ Conversion tool endpoint """

    def __init__(self):
        self._stdout = None

        self.parser = argparse.ArgumentParser(
            description='A tool for converting to or from the RIOS definition.',
        )

        try:
            version = pkg_resources.get_distribution('rios.conversion').version
        except pg_resources.DistributionNotFound:
            version = 'UNKNOWN'
        self.parser.add_argument(
            '-v',
            '--version',
            action='version',
            version='%(prog)s ' + version,
        )

        self.parser.add_argument(
            '-s',
            '--spectype',
            required=True,
            choices=[
                'redcap',
                'qualtrics',
            ],
            help='The type of instrument specification to convert.',
        )

        self.parser.add_argument(
            '-f',
            '--filename',
            required=True,
            type=argparse.FileType('r'),
            help='The instrument definition file to convert.'
            ' Use "-" for stdin.',
        )

        self.parser.add_argument(
            '--format',
            default='yaml',
            choices=['yaml', 'json'],
            help='The format and extension for the output files.'
            ' The default is "yaml".'
        )


        ### TODO: Can we get rid of these following arguments (auto generate these)?
        self.parser.add_argument(
            '--id',
            required=True,
            help='The instrument id to output.',
        )
        self.parser.add_argument(
            '--infile',
            required=True,
            type=argparse.FileType('r'),
            help='The csv input file to process.'
        )
        self.parser.add_argument(
            '--instrument-version',
            required=True,
            help='The instrument version to output.',
        )
        self.parser.add_argument(
            '--localization',
            default='en',
            metavar='',
            help='The default localization for the web form.'
            ' The default is "en"',
        )
        # TODO: Outfile prefix should be variation of title input
        #self.parser.add_argument(
        #    '--outfile-prefix',
        #    required=True,
        #    help='The prefix for the output files.',
        #)
        self.parser.add_argument(
            '--title',
            required=True,
            help='The instrument title to output.',
        )

    def __call__(self, argv=None, stdout=sys.stdout):
        args = self.parser.parse_args(argv)
        self._stdout = stdout

        try:
            CONVERTERS[args.spectype](
                args.filename,
                instrument=args.instrument,
            )
        #except ConversionError as exc:
        except Exception as exc:
            self.out('FAILED conversion.')
            for source, message in iteritems(exc.asdict()):
                self.out('%s: %s' % (
                    source,
                    message,
                ))
            return 1
        else:
            self.out('Successful conversion.')
            return 0

    def out(self, message):
        self._stdout.write('%s\n' % (message,))

convert = ConversionScript()

