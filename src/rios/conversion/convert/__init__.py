#
# Copyright (c) 2016, Prometheus Research, LLC
#


from rios.conversion.redcap import RedcapToRios, RedcapFromRios
from rios.conversion.qualtrics import QualtricsToRios, QualtricsFromRios
from rios.conversion.exception import QualtricsFormatError
from rios.conversion.utils import JsonReader


__all__ = (
    'redcap_to_rios',
    'qualtrics_to_rios',
    'rios_to_redcap',
    'rios_to_qualtrics',

    'RedcapToRios',
    'RedcapFromRios',
    'QualtricsToRios',
    'QualtricsFromRios',
)


class JsonReaderMetaDataProcessor(JsonReader):
    """ Process Qualtrics data dictionary/instrument metadata """

    def processor(self, data):
        """ Extract metadata into a dict """
        try:
            survey_entry = data['SurveyEntry']
            metadata = {
                'id':             survey_entry['SurveyID'],
                'title':          survey_entry['SurveyName'],
                'localization':   survey_entry['SurveyLanguage'].lower(),
                'description':    survey_entry['SurveyDescription'],
            }
        except Exception as exc:
            error = QualtricsFormatError(
                'Processor read error:',
                str(exc)
            )
            raise error
        else:
            return metadata


def redcap_to_rios(id, title, description, stream, localization=None,
                    instrument_version=None, logger=None):
    """
    Converts a REDCap configuration into a RIOS configuration.

    :param id: The RIOS specification formatted instrument ID.
    :type id: str
    :param title: The RIOS specification formatted instrument title.
    :type title: str
    :param description: The instrument description.
    :type description: str
    :param stream:
        A file stream containing a foriegn data dictionary to convert to the
        RIOS specification.
    :type stream: File-like object
    :param localization:
        Localization must be in the form of an RFC5646 Language Tag. Defaults
        to 'en' if not supplied.
    :type localization: str or None
    :param instrument_version:
        Version of the instrument. Defaults to '1.0' if none supplied. Must be
        in a decimal format with precision to one decimal place.
    :type instrument_version: str or None
    :param logger: Logging instance to store logs.
    :type logger: list
    :returns:
        The RIOS instrument, form, and calculationset configuration. Includes
        logging data if a logger is suplied.
    :rtype: dictionary
    """

    converter = RedcapToRios(
        id=id,
        instrument_version=instrument_version,
        title=title,
        localization=localization,
        description=description,
        stream=stream,
        logger=None
    )
    converter()
    if logger:
        return dict(converter.package, **{'logs': logger})
    else:
        return converter.package


def qualtrics_to_rios(stream, instrument_version=None, title=None,
                        localization=None, description=None, id=None,
                            logger=None, filemetadata=False):
    """
    Converts a Qualtrics configuration into a RIOS configuration.

    :param id: The RIOS specification formatted instrument ID.
    :type id: str
    :param title: The RIOS specification formatted instrument title.
    :type title: str
    :param description: The instrument description.
    :type description: str
    :param stream:
        A file stream containing a foriegn data dictionary to convert to the
        RIOS specification.
    :type stream: File-like object
    :param localization:
        Localization must be in the form of an RFC5646 Language Tag. Defaults
        to 'en' if not supplied.
    :type localization: str or None
    :param instrument_version:
        Version of the instrument. Defaults to '1.0' if none supplied. Must be
        in a decimal format with precision to one decimal place.
    :type instrument_version: str or None
    :param logger: Logging instance to store logs.
    :type logger: list
    :param filemetadata:
        Flag to tell converter API to pull meta data from the stream file.
    :type filemetadata: bool
    :returns:
        The RIOS instrument, form, and calculationset configuration. Includes
        logging data if a logger is suplied.
    :rtype: dictionary
    """

    if filemetadata:
        kwargs = dict()
        kwargs['stream'] = stream
        kwargs['instrument_version'] = instrument_version
        # Process properties from the stream
        reader = JsonReaderMetaDataProcessor(stream).process()
        kwargs['id'] = reader.data['id']
        kwargs['description'] = reader.data['description']
        kwargs['title'] = reader.data['title']
        kwargs['localization'] = reader.data['localization']
    converter = QualtricsToRios(**kwargs)()
    if logger:
        return dict(converter.package, **{'logs': logger})
    else:
        return converter.package


def rios_to_redcap(instrument, **kwargs):
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

    converter = RedcapFromRios(instrument, **kwargs)
    converter()


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

    converter = QualtricsFromRios(instrument, **kwargs)
    converter()
