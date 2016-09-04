#
# Copyright (c) 2016, Prometheus Research, LLC
#


import simplejson
import six


__all__ = ('JsonReader',)


class JsonReader(object):
    """
    This object reads `fname`, a JSON formatted text file, and can pre-process
    the data.

    Usage:

        reader = JsonReader(fname)
        reader.process()
        ... data ready for processing

    `fname` is either a filename, an open file object, or any object suitable
    for `json.load`.
    """

    def __init__(self, fname):
        self.fname = fname
        self.reader = None
        self.data = {}

    @staticmethod
    def get_reader(fname):
        fi = open(fname, 'rU') \
                if isinstance(fname, six.string_types) else fname
        if hasattr(fi, 'seek'):
            fi.seek(0)
        return simplejson.load(fi)

    def load_reader(self):
        self.reader = self.get_reader(self.fname)

    def process(self):
        if not self.reader:
            self.load_reader()
        self.data = self.processor(self.reader)

    def processor(self, data):
        """ Implementations may override this method """
        return data
