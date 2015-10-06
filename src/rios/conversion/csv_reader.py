import collections
import csv

__all__ = (
    "CsvReader",
    )
    
class CsvReader(object):
    """This object reads `fname`, a csv file, and can iterate over the rows.
     
    usage:
    
        for row in CsvConverter(fname):
            process(row)

    fname is either the filename, or an open file object, or any object 
    suitable for csv.reader.

    The first row is expected to be a list of column names. 
    These are converted to "canonical" form by get_name() 
    and stored in the self.attributes list.

    Subsequent rows are converted to OrderedDicts based on self.attributes
    by get_row().
    
    - get_name(name): returns the "canonical" name.
      The default returns name unchanged.
    """
    def __init__(self, fname):
        self.fname = fname
        self.attributes = []
        self.reader = None

    def __iter__(self):
        if not self.reader:
            self.reader = self.get_reader(self.fname)
        if not self.attributes:
            self.attributes = [self.get_name(c) for c in self.reader.next()]
        for row in self.reader:
            yield self.get_row(row)

    def get_name(self, name):
        return name
        
    @staticmethod
    def get_reader(fname):
        fi = open(fname, 'r') if isinstance(fname, str) else fname
        return csv.reader(fi)

    def get_row(self, row):
        return collections.OrderedDict(zip(self.attributes, row))

