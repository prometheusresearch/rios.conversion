#
# Copyright (c) 2016, Prometheus Reserach, LLC
#


import json
import os
import yaml


from rios.conversion import structures
from rios.core.validation import (
    validate_instrument,
    validate_form,
    validate_calculationset,
    ValidationError,
)


DEFAULT_LOCALIZATION = 'en'
DEFAULT_VERSION = '1.0'


class ToRios(object):
    """
    Converts a foreign instrument file into a valid RIOS specifications.
    """

    def __init__(self, id, instrument_version, title,
                    localization, description, stream):
        self.id = id
        self.instrument_version = instrument_version or DEFAULT_VERSION
        self.title = title
        self.localization = localization or DEFAULT_LOCALIZATION
        self.description = description
        self.stream = stream

        self._instrument = structures.Instrument(
            id=self.id,
            version=self.instrument_version,
            title=self.title,
            description=self.description
        )
        self._calculations = structures.CalculationSetObject(
            instrument=structures.InstrumentReferenceObject(self._instrument),
        )
        self._form = structures.WebForm(
            instrument=structures.InstrumentReferenceObject(self._instrument),
            defaultLocalization=self.localization,
            title=self._localized_string_object(self.title),
        )

    def __call__(self):
        """
        Converts the given foreign instrument file into corresponding RIOS
        specfication formatted data objects.

        Implementations must override this method.
        """

        raise NotImplementedError(
            '{}.__call__'.format(self.__class__.__name__)
        )

    @property
    def instrument(self):
        self._instrument.clean()
        return self._instrument.as_dict()

    @property
    def form(self):
        self._form.clean()
        return self._form.as_dict()

    @property
    def calculationset(self):
        if self._calculations.get('calculations', False):
            self._calculations.clean()
            return self._calculations.as_dict()
        else:
            return dict()

    def validate(self):
        validate_instrument(self.instrument)
        validate_form(
            self.form,
            instrument=self.instrument,
        )
        if self.calculationset.get('calculations', False):
            validate_calculationset(
                self.calculationset,
                instrument=self.instrument
            )

    @property
    def package(self):
        payload = {
            'instrument': self.instrument.as_dict(),
            'form': self.form.as_dict(),
        }
        if self.calculations.get('calculations', False):
            calculations = self.calculations.as_dict()
            return dict(payload, **{'calculationset': calculations})
        else:
            return payload

    def _localized_string_object(self, string):
        return structures.LocalizedStringObject({self.localization: string})
