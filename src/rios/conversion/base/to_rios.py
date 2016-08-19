"""
Converts a foreign instrument file into a series of RIOS output files

    <OUTFILE_PREFIX>_c.<format> RIOS calculation
    <OUTFILE_PREFIX>_i.<format> RIOS instrument
    <OUTFILE_PREFIX>_f.<format> RIOS web form

The RIOS calculation file is only created when there are
calculation fields in the input.
However if there are no calculation fields
and the calculation file already exists,
it will be deleted.
"""

import json
import os
import rios.conversion.classes as Rios
import yaml

from rios.core import validation


class ToRios(object):
    def create__file(self, kind, obj):
        with open(self.filename(kind), 'w') as fo:
            if obj:
                obj.clean()
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
        else:
            filename = self.filename('c')
            if os.access(filename, os.F_OK):
                os.remove(filename)   # pragma: no cover

    def create_instrument_file(self):
        self.create__file('i', self.instrument)

    def create_form_file(self):
        self.create__file('f', self.form)

    def validate_results(self):
        self.instrument.clean()
        validation.validate_instrument(self.instrument.as_dict())

        self.form.clean()
        validation.validate_form(
            self.form.as_dict(),
            instrument=self.instrument.as_dict(),
        )

        if self.calculations.get('calculations', False):
            self.calculations.clean()
            validation.validate_calculationset(
                self.calculations.as_dict(),
                instrument=self.instrument.as_dict(),
            )

    def filename(self, kind):
        return '%(outfile_prefix)s_%(kind)s.%(extension)s' % {
                'outfile_prefix': self.outfile_prefix,
                'kind': kind,
                'extension': self.format, }

    def localized_string_object(self, string):
        return Rios.LocalizedStringObject({self.localization: string})
