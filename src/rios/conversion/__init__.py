#
# Copyright (c) 2016, Prometheus Research, LLC
#


from rios.core import (
    ValidationError,
    validate_instrument,
    validate_form,
    validate_calculationset,
)
from rios.conversion.redcap import RedcapToRios, RedcapFromRios
from rios.conversion.base import structures
from rios.conversion.qualtrics import QualtricsToRios, QualtricsFromRios
from rios.conversion.exception import (
    Error,
    ConversionFailureError,
    QualtricsFormatError,
    ConversionValidationError,
    RiosRelationshipError,
)
from rios.conversion.utils import JsonReader


__all__ = (
    'redcap_to_rios',
    'qualtrics_to_rios',
    'rios_to_redcap',
    'rios_to_qualtrics',
)


class _JsonReaderMetaDataProcessor(JsonReader):
    """ Process Qualtrics data dictionary/instrument metadata """

    def processor(self, data):  # noqa:F821
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


def _check_rios_relationship(instrument, form, calculationset=None):
    instrument = structures.InstrumentReferenceObject(instrument)
    if form['instrument'] != instrument:
        raise RiosRelationshipError(
            'Form and Instrument do not match:',
            '{} is not {}'.format(form['instrument'], instrument)
        )
    if (calculationset and calculationset['instrument'] != instrument):
        raise RiosRelationshipError(
            'Calculationset and Instrument do not match:',
            '{} is not {}'.format(calculationset['instrument'], instrument)
        )


def _validate_rios(instrument, form, calculationset=None):
    try:
        exc_type = "instrument"
        validate_instrument(instrument)
        exc_type = "form"
        validate_form(form, instrument=instrument)
        exc_type = "calculationset"
        if calculationset and calculationset.get('calculations', False):
            validate_calculationset(calculationset, instrument=instrument)
    except ValidationError as exc:
        raise ConversionValidationError(
            'The supplied RIOS ' + exc_type + ' configuration'
            ' is invalid. Error:',
            str(exc)
        )


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
    :param suppress:
        Supress exceptions and log return as a dict with a single 'failure'
        key that contains the exception message. Implementations should check
        for this key to make sure a conversion completed sucessfully, because
        the returned dict will not contain key-value pairs with conversion
        data if exception suppression is set.
    :type suppress: bool
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
        error = ConversionFailureError(
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
    :param suppress:
        Supress exceptions and log return as a dict with a single 'failure'
        key that contains the exception message. Implementations should check
        for this key to make sure a conversion completed sucessfully, because
        the returned dict will not contain key-value pairs with conversion
        data if exception suppression is set.
    :type suppress: bool
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
            reader = _JsonReaderMetaDataProcessor(stream)
            reader.process()
        except Exception as exc:
            error = ConversionFailureError(
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
        error = ConversionFailureError(
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


def rios_to_redcap(instrument, form, calculationset=None,
                                    localization=None, suppress=False):
    """
    Converts a RIOS configuration into a REDCap configuration.

    :param instrument: The RIOS instrument definition
    :type instrument: dict
    :param form: The RIOS form definition
    :type form: dict
    :param calculationset: The RIOS calculationset instrument definition
    :type calculationset: dict
    :param localization:
        Localization must be in the form of an RFC5646 Language Tag. Defaults
        to 'en' if not supplied.
    :type localization: str or None
    :param suppress:
        Supress exceptions and log return as a dict with a single 'failure'
        key that contains the exception message. Implementations should check
        for this key to make sure a conversion completed sucessfully, because
        the returned dict will not contain key-value pairs with conversion
        data if exception suppression is set.
    :type suppress: bool
    :returns:
        A list where each element is a row. The first row is the header row.
    :rtype: list
    """

    payload = dict()

    try:
        _validate_rios(instrument, form, calculationset)
        _check_rios_relationship(instrument, form, calculationset)
    except Exception as exc:
        error = ConversionFailureError(
            'The supplied RIOS configurations are invalid:',
            str(exc)
        )
        if suppress:
            payload['failure'] = str(error)
            return payload
        else:
            raise error

    converter = RedcapFromRios(
        instrument=instrument,
        form=form,
        calculationset=calculationset,
        localization=localization,
    )

    try:
        converter()
    except Exception as exc:
        error = ConversionFailureError(
            'Unable to convert RIOS data dictionary. Error:',
            (str(exc) if isinstance(exc, Error) else repr(exc))
        )
        if suppress:
            payload['failure'] = str(error)
        else:
            raise error
    else:
        payload.update(converter.package)

    return payload


def rios_to_qualtrics(instrument, form, calculationset=None,
                                    localization=None, suppress=False):
    """
    Converts a RIOS configuration into a Qualtrics configuration.

    :param instrument: The RIOS instrument definition
    :type instrument: dict
    :param form: The RIOS form definition
    :type form: dict
    :param calculationset: The RIOS calculationset instrument definition
    :type calculationset: dict
    :param localization:
        Localization must be in the form of an RFC5646 Language Tag. Defaults
        to 'en' if not supplied.
    :type localization: str or None
    :param suppress:
        Supress exceptions and log return as a dict with a single 'failure'
        key that contains the exception message. Implementations should check
        for this key to make sure a conversion completed sucessfully, because
        the returned dict will not contain key-value pairs with conversion
        data if exception suppression is set.
    :type suppress: bool
    :returns: The RIOS instrument, form, and calculationset configuration.
    :rtype: dictionary
    """

    payload = dict()

    try:
        _validate_rios(instrument, form, calculationset)
        _check_rios_relationship(instrument, form, calculationset)
    except Exception as exc:
        error = ConversionFailureError(
            'The supplied RIOS configurations are invalid:',
            str(exc)
        )
        if suppress:
            payload['failure'] = str(error)
            return payload
        else:
            raise error

    converter = QualtricsFromRios(
        instrument=instrument,
        form=form,
        calculationset=calculationset,
        localization=localization,
    )

    try:
        converter()
    except Exception as exc:
        error = ConversionFailureError(
            'Unable to convert RIOS data dictionary. Error:',
            (str(exc) if isinstance(exc, Error) else repr(exc))
        )
        if suppress:
            payload['failure'] = str(error)
        else:
            raise error
    else:
        payload.update(converter.package)

    return payload
