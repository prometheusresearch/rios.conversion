#
# Copyright (c) 2016, Prometheus Research, LLC
#


import simplejson
import sys
import yaml


from rios.core import ValidationError
from rios.conversion.base import ConversionBase, DEFAULT_LOCALIZATION
from rios.conversion import structures
from rios.conversion.utils import InMemoryLogger
from rios.conversion.exception import ConversionValidationError
from rios.core.validation import (
    validate_instrument,
    validate_form,
    validate_calculationset,
)


class FromRios(ConversionBase):
    """ Converts a valid RIOS specification into a foreign instrument """

    def __init__(self, form, instrument,
                    calculationset=None, localization=None):
        """
        Expects `form`, `instrument`, and `calculationset` to be dictionary
        objects. Implementations must process the data dictionary first before
        passing to this class.
        """

        self.localization = localization or DEFAULT_LOCALIZATION
        self._form = form
        self._instrument = instrument
        self._calculationset = (calculationset if calculationset else {})

        self._definition = list()

        self.fields = {f['id']: f for f in self._instrument['record']}

    def get_local_text(localization, localized_str_obj):
        return localized_str_obj.get(localization, '')

    @property
    def instrument(self):
        return self._definition

    @property
    def payload(self):
        """
        Returns a dictionary with an ``instrument`` key matched to a value
        that is a list of lines of the foriegn instrument file. May also add
        a ``logger`` key if logs exist.
        """

        payload = {'instrument': self.instrument}
        if self.logger.check:
            payload.update({'logs': self.logs})
        return payload
