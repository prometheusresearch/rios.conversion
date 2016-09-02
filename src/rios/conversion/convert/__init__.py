#
# Copyright (c) 2016, Prometheus Research, LLC
#


from rios.conversion.redcap import RedcapToRios, RedcapFromRios
from rios.conversion.qualtrics import QualtricsToRios, QualtricsFromRios
from rios.conversion.exception import Error, QualtricsFormatError
from rios.conversion.utils import JsonReader


__all__ = (
    'redcap_to_rios',
    'qualtrics_to_rios',
    'rios_to_redcap',
    'rios_to_qualtrics',
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
                        instrument_version=None, suppress=False):
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
        stream=stream
    )

    payload = dict()
    try:
        converter()
    except Exception as exc:
        error = Error(
            'Unable to convert REDCap data dictionary. Error:',
            (str(exc) if isinstance(exc, Error) else repr(exc))
        )
        if suppress:
            payload['failure'] = str(error)
        else:
            raise error
    else:
        payload.update(converter.package)

    return payload


def qualtrics_to_rios(stream, instrument_version=None, title=None,
                        localization=None, description=None, id=None,
                            filemetadata=False, suppress=False):
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
    :param filemetadata:
        Flag to tell converter API to pull meta data from the stream file.
    :type filemetadata: bool
    :returns:
        The RIOS instrument, form, and calculationset configuration. Includes
        logging data if a logger is suplied.
    :rtype: dictionary
    """

    # Make sure function parameters are passed proper values if not getting
    # metadata from the data dictionary file
    if filemetadata is False and (id is None or description is None
                                    or title is None):
        raise ValueError(
            'Missing id, description, and/or title attributes'
        )

    payload = dict()

    if filemetadata:
        # Process properties from the stream
        try:
            reader = JsonReaderMetaDataProcessor(stream)
            reader.process()
        except Exception as exc:
            error = Error(
                "Unable to parse Qualtrics data dictionary:",
                "Invalid JSON formatted text"
            )
            error.wrap(
                "Parse error:",
                str(exc)
            )
            if suppress:
                payload['failure'] = str(error)
                return payload
            else:
                raise error
        else:
            id = reader.data['id']
            description = reader.data['description']
            title = reader.data['title']
            localization = reader.data['localization']

    converter = QualtricsToRios(
        id=id,
        instrument_version=instrument_version,
        title=title,
        localization=localization,
        description=description,
        stream=stream
    )

    try:
        converter()
    except Exception as exc:
        error = Error(
            'Unable to convert Qualtrics data dictionary. Error:',
            (str(exc) if isinstance(exc, Error) else repr(exc))
        )
        if suppress:
            payload['failure'] = str(error)
        else:
            raise error
    else:
        payload.update(converter.package)

    return payload


#def check_relationship(self):
#    instrument = structures.InstrumentReferenceObject(self.instrument)
#    if self.form['instrument'] != instrument:
#                'FATAL: Form and Instrument do not match: '
#                '%s != %s.\n' % (self.form['instrument'], instrument))
#
#    if (self.calculationset
#                and self.calculationset['instrument'] != instrument):
#        self.stderr.write(
#                'FATAL: Calculationset and Instrument do not match: '
#                '%s != %s.\n' % (
#                        self.calculationset['instrument'],
#                        instrument))


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
