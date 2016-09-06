#
# Copyright (c) 2016, Prometheus Reserach, LLC
#


from rios.core import ValidationError
from rios.conversion.exception import (
    ConversionValidationError,
)
from rios.conversion.base import structures
from rios.conversion.base import (
    ConversionBase,
    localized_string_object,
    DEFAULT_VERSION,
    DEFAULT_LOCALIZATION,
    SUCCESS_MESSAGE,
)
from rios.core.validation import (
    validate_instrument,
    validate_form,
    validate_calculationset,
)


__all__ = (
    'ToRios',
)


class ToRios(ConversionBase):
    """ Converts a foreign instrument into a valid RIOS specification """

    def __init__(self, id, title, description, stream, localization=None,
                                    instrument_version=None, *args, **kwargs):
        """
        Expects `stream` to be a file-like object. Implementations must process
        the data dictionary first before passing to this class.
        """

        # Set attributes
        self.id = (id if 'urn:' in str(id) else ('urn:' + str(id)))
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
        """
        Validation interface. Must be called at the end of all subclass
        implementations of the __call__ method.
        """

        try:
            val_type = "Instrument"
            validate_instrument(self.instrument)
            val_type = "Form"
            validate_form(
                self.form,
                instrument=self.instrument,
            )
            if self.calculationset.get('calculations', False):
                val_type = "Calculationset"
                validate_calculationset(
                    self.calculationset,
                    instrument=self.instrument
                )
        except ValidationError as exc:
            error = ConversionValidationError(
                (val_type + ' validation error:'),
                str(exc)
            )
            self.logger.error(str(error))
            raise error
        else:
            if SUCCESS_MESSAGE:
                self.logger.info(SUCCESS_MESSAGE)

    @property
    def package(self):
        """
        Returns a dictionary with ``instrument``, ``form``, and possibly
        ``calculationset`` keys containing their corresponding, converted
        definitions. May also add a ``logger`` key if logs exist.
        """

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
