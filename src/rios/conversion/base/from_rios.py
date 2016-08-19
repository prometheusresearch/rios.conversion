#
# Copyright (c) 2016, Prometheus Research, LLC
#


import argparse
import json
import pkg_resources
import sys
import yaml
import rios.conversion.structures as Rios


class FromRios(object):

    description = __doc__

    def __init__(self, outfile, localization, format,
                 verbose, form, instrument, calculationset, **kwargs):

        self.outfile = outfile
        self.localization = localization
        self.format = format
        self.verbose = verbose
        self.form = form
        self.instrument = instrument
        self.calculationset = calculationset


    def __call__(self, argv=None, stdout=None, stderr=None):
        """ Process the csv input, and create output files """

        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr

        self.load_input_files(self.form, self._instrument, self.calculationset)
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
