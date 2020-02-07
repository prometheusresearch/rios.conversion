#
# Copyright (c) 2016, Prometheus Research, LLC
#


from . import structures


from rios.conversion.utils import InMemoryLogger


__all__ = (
    'ConversionBase',
    'localized_string_object',
    'DEFAULT_VERSION',
    'DEFAULT_LOCALIZATION',
    'SUCCESS_MESSAGE',
)


DEFAULT_LOCALIZATION = 'en'
DEFAULT_VERSION = '1.0'
SUCCESS_MESSAGE = 'Conversion process was successful'


def localized_string_object(localization, string):
    return structures.LocalizedStringObject({localization: string})


class ConversionBase(object):
    """ Base class for building conversion objects """

    def __init__(self, *args, **kwargs):
        """
        Initializes a conversion tool for converting from one instrument
        definition to another.

        Implementations must override this method and specify necessary
        function parameters.
        """

        raise NotImplementedError(
            '{}.__call__'.format(self.__class__.__name__)
        )

    def __call__(self):
        """
        Converts the given instrument definition into a another instrument
        definition.

        Implementations must override this method.
        """

        raise NotImplementedError(
            '{}.__call__'.format(self.__class__.__name__)
        )

    @property
    def logger(self):
        """
        Logger interface. Builds a new logging instance if one doesn't
        already exist. It is up to implementations to use this logging feature
        within a subclass implementation's __call__ method.
        """

        try:
            return self._logger
        except AttributeError:
            self._logger = InMemoryLogger()
            return self._logger

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
        """
        Returns the instrument definition output as a dictionary or a list.

        Implementations must override this method.
        """

        raise NotImplementedError(
            "{}.instrument".format(self.__class__.__name__)
        )

    @property
    def package(self):
        """
        Returns a dictionary with an ``instrument`` key containing the
        converted definitions. May also add a ``logger`` key if logs exist.

        Implementations must override this method.
        """

        raise NotImplementedError(
            "{}.package".format(self.__class__.__name__)
        )
