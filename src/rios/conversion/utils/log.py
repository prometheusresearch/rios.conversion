#
# Copyright (c) 2016, Prometheus Research, LLC
#


import six


__all__ = (
    'InMemoryLogger',
)


ERROR_PREFIX = 'ERROR: '
WARNING_PREFIX = 'WARNING: '
INFO_PREFIX = 'INFO: '


class InMemoryLogger(object):
    """
    Simple logging container for logging messages.

    This class allows logging of messages in an internal list. The messages
    are available for output. Output may be a string with newline characters
    separating each log. All messages may be cleared.

    Make sure logs are cleared in each logging instance when the logging
    instance is no longer needed or needs to be reset. There is no automatic
    dumping of logs if the internal list becomes huge, so plan accordingly or
    use the logging module instead.
    """

    __slots__ = ('_logs',)

    def __init__(self):
        self._logs = []

    def clear(self):
        del(self._logs[:])

    @property
    def pplogs(self):
        return "\n".join(self._logs)

    @property
    def logs(self):
        return self._logs

    def info(self, msg):
        self.log(msg, INFO_PREFIX)

    def error(self, msg):
        self.log(msg, ERROR_PREFIX)

    def warning(self, msg):
        self.log(msg, WARNING_PREFIX)

    def log(self, msg, pfx=None):
        if not isinstance(msg, six.string_types):
            raise ValueError('Loggable objects must be of type string')
        if pfx:
            self._logs.append(pfx + msg)
        else:
            self._logs.append(msg)

    @property
    def check(self):
        """ Checks if any logs have been registered. """
        if len(self._logs) == 0:
            return False
        else:
            return True
