#
# Copyright (c) 2016, Prometheus Research, LLC
#


import logging
import logging.config
import six


__all__ = (
    'get_conversion_logger',
)


__CONFIG = {
    'version': 1,
    'incremental': False,
    'disable_existing_loggers': True,
    'propogate': False,
    'formatters': {
        'brief': {
            'format': '%(message)s'
        },
        'basic': {
            'format': '%(levelname)s: %(message)s'
        },
    },
    'filters': {},
    'handlers': {
        'memory': {
            'class': 'rios.conversion.utils.log.InternalLoggingHandler',
            'formatter': 'basic',
            'logger': None,
        },
    },
    'loggers': {},
    'root': {
        'level': 'INFO',
        'handlers': [
            'memory',
        ]
    },
}


def get_conversion_logger(name=None, clearall=False, logger=None):
    """
    A convenience wrapper around the ``logging.getLogger()`` function. This
    function may take a string as the name for the logging instance, and a
    boolean requesting whether or not to clear cached loggers.

    :param name: the name of the logger
    :type name: str
    :param clearall: should logging cache be cleared
    :type clearall: bool
    :rtype: logging.Logger
    """

    if clearall:
        # Clear cached loggers
        logging.Logger.manager.loggerDict = {}
        pass

    # Load logging config
    __CONFIG['handlers']['memory']['logger'] = logger
    logging.config.dictConfig(__CONFIG)

    if name and not isinstance(name, six.string_types):
        raise TypeError('Name parameter must be a string')
    else:
        name = str(name)

    return logging.getLogger(name)


class InternalLoggingHandler(logging.Handler):
    """ Custom logging handler to allow retrieval of internal log state """

    def __init__(self, logger=None, *args, **kwargs):
        if not isinstance(logger, list):
            raise TypeError('Logger object must be of type list')
        super(InternalLoggingHandler, self).__init__(*args, **kwargs)
        self._logger = logger

    def emit(self, record):
        msg = self.format(record)
        self._logger.append(msg)
