#
# Copyright (c) 2016, Prometheus Reserach, LLC
#


from rios.core import ValidationError
from rios.conversion import structures
from rios.conversion.utils import InMemoryLogger
from rios.conversion.exception import ConversionValidationError
from rios.core.validation import (
    validate_instrument,
    validate_form,
    validate_calculationset,
)


__all__ = (
    'ToRios',
    'DEFAULT_LOCALIZATION',
    'DEFAULT_VERSION',
    'SUCCESS_MESSAGE',
)


DEFAULT_LOCALIZATION = 'en'
DEFAULT_VERSION = '1.0'
SUCCESS_MESSAGE = 'Conversion process was successful'


class ToRios(object):
    """ Converts a foreign instrument file into a valid RIOS specification """

    def __init__(self, id, title, description, stream,
                    localization=None, instrument_version=None):

        # Initialize logging
        self.logger = InMemoryLogger()

        # Set attributes
        self.id = id
        self.instrument_version = instrument_version or DEFAULT_VERSION
        self.title = title
        self.localization = localization or DEFAULT_LOCALIZATION
        self.description = description
        self.stream = stream

        # Inserted into self._form
        self.page_container = dict()
        # Inserted into self._instrument
        self.field_container = list()
        # Inserted into self._calculationset
        self.calc_container = dict()

        # Generate yet-to-be-configured RIOS definitions
        self._instrument = structures.Instrument(
            id=self.id,
            version=self.instrument_version,
            title=self.title,
            description=self.description
        )
        self._calculationset = structures.CalculationSetObject(
            instrument=structures.InstrumentReferenceObject(self._instrument),
        )
        self._form = structures.WebForm(
            instrument=structures.InstrumentReferenceObject(self._instrument),
            defaultLocalization=self.localization,
            title=localized_string_object(self.localization, self.title),
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
    def pplogs(self):
        """
        Pretty print logs by joining into a single, formatted string for use
        in displaying informative error messages to users.
        """
        return self.logger.pplogs

    @property
    def logs(self):
        return self.logger.logs

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
        if self._calculationset.get('calculations', False):
            self._calculationset.clean()
            return self._calculationset.as_dict()
        else:
            return dict()

    def validate(self):
        try:
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
        except ValidationError as exc:
            error = ConversionValidationError(
                'Validation error:',
                str(exc)
            )
            self.logger.error(str(error))
            raise error
        else: 
            if SUCCESS_MESSAGE:
                self.logger.info(SUCCESS_MESSAGE)

    @property
    def package(self):
        payload = {
            'instrument': self.instrument,
            'form': self.form,
        }
        if self._calculationset.get('calculations', False):
            payload.update(
                {'calculationset': self.calculations}
            )
        if self.logger.check:
            payload.update(
                {'logs': self.logs}
            )
        return payload


def localized_string_object(localization, string):
    return structures.LocalizedStringObject({localization: string})
