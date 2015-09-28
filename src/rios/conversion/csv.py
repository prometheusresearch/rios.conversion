__all__ = (
    "CsvConverter",
    )
    
class CsvConverter(object):
    """This object reads `fname`, a csv file, and can iterate over the rows.
     
    usage:
    
        for row in CsvConverter(fname):
            process(row)

    fname is either the filename, or an open file object, or any object 
    suitable for csv.reader.

    The first row is expected to be a list of column names. 
    These are converted to "canonical" form by get_name() 
    and stored in the self.attributes list.

    Subsequent rows are converted to "canonical" form by get_row().
    
    Overwrite these methods to implement "canonical":
    
    - get_name(name): returns the "canonical" name.
      The default returns name unchanged.
      
    - get_row(row): returns a "canonical" row.
      The default returns row unchanged.                
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
        return row

