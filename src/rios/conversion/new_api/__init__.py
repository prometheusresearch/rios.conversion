#
# Copyright (c) 2016, Prometheus Research, LLC
#


from rios.conversion.redcap import RedcapToRios, RedcapFromRios
from rios.conversion.qualtrics import QualtricsToRios, QualtricsFromRios


__all__ = (
    'redcap_to_rios',
    'qualtrics_to_rios',
    'rios_to_redcap',
    'rios_to_qualtrics',
)


def redcap_to_rios(instrument, **kwargs):
    """
    Converts a REDCap configuration into a RIOS configuration.

    :param instrument: The REDCap instrument definition
    :type instrument: File-like object
    :param kwargs:
        Extra keyword arguments are passed to the underlying
        converter class instantiation.
    :returns: The RIOS instrument, form, and calculationset configuration.
    :rtype: dictionary
    """

    converter = RedcapToRios(instrument, **kwargs)
    converter.convert()
    return converter.export()


def qualtrics_to_rios(instrument, **kwargs):
    """
    Converts a Qualtrics configuration into a RIOS configuration.

    :param instrument: The Qualtrics instrument definition
    :type instrument: File-like object
    :param kwargs:
        Extra keyword arguments are passed to the underlying
        converter class instantiation.
    :returns: The RIOS instrument, form, and calculationset configuration.
    :rtype: dictionary
    """

    converter = QualtricsToRios(instrument, **kwargs)
    converter.convert()
    return converter.export()


def rios_to_redcap(instrument, form, calculationset, **kwargs):
    """
    Converts a RIOS configuration into a REDCap configuration.

    :param instrument: The RIOS instrument definition
    :type instrument: Dictionary
    :param form: The RIOS form definition
    :type form: Dictionary
    :param calculationset: The RIOS calculationset instrument definition
    :type calculationset: Dictionary
    :param kwargs:
        Extra keyword arguments are passed to the underlying
        converter class instantiation.
    :returns: The RIOS instrument, form, and calculationset configuration.
    :rtype: dictionary
    """

    converter = RedcapFromRios(instrument, form, calculationset, **kwargs)
    converter.convert()
    return converter.export()


def rios_to_qualtrics(instrument, form, calculationset, **kwargs):
    """
    Converts a RIOS configuration into a Qualtrics configuration.

    :param instrument: The Qualtrics instrument definition
    :type instrument: File-like object
    :param kwargs:
        Extra keyword arguments are passed to the underlying
        converter class instantiation.
    :returns: The RIOS instrument, form, and calculationset configuration.
    :rtype: dictionary
    """

    converter = QualtricsFromRios(instrument, form, calculationset, **kwargs)
    converter.convert()
    return converter.export()
