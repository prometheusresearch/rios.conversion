import collections
import csv
import re

__all__ = (
    "CsvReader",
    )


class CsvReader(object):
    """This object reads `fname`, a csv file, and can iterate over the rows.

    usage:

        for row in CsvReader(fname):
            assert isinstance(row, OrderedDict)
            ... process the row

    fname is either the filename, or an open file object, or any object
    suitable for csv.reader.

    The first row is expected to be a list of column names.
    These are converted to "canonical" form by get_name()
    and stored in the self.attributes list.

    Subsequent rows are converted by get_row()
    into OrderedDicts based on the keys in self.attributes.

    - get_name(name): returns the "canonical" name.
      The default returns name unchanged.
    """
    def __init__(self, fname):
        self.fname = fname
        self.attributes = []
        self.reader = None

    def __iter__(self):
        if not self.attributes:
            self.load_attributes()
        for row in self.reader:
            yield self.get_row(row)

    def get_name(self, name):
        return name

    @staticmethod
    def get_reader(fname):
        fi = open(fname, 'rU') if isinstance(fname, str) else fname
        filtered = (re.sub(r'(\r\n)|(\r)', r'', line) for line in fi)
        return csv.reader(filtered)

    def get_row(self, row):
        return collections.OrderedDict(zip(
                self.attributes,
                [x.strip() for x in row]))

    def load_attributes(self):
        if not self.reader:
            self.load_reader()
        self.attributes = [self.get_name(c) for c in self.reader.next()]

    def load_reader(self):
        self.reader = self.get_reader(self.fname)
