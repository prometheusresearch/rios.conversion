********
Overview
********

RIOS.CONVERSION is a `Python`_ package that supports 
converting research instruments in various formats 
to and from `RIOS`_ data structures.

The following command line programs have been implemented.

- redcap-rios

  Converts a REDCap Data Dictionary in csv format to 
  a RIOS Instrument, Form, and CalculationSet 
  in JSON or YAML format.

- rios-redcap

  Converts a RIOS Instrument, Form, and CalculationSet 
  to a REDCap Data Dictionary in csv format.
  
- qualtrics-rios

  Converts a Qualtrics qsf file to a RIOS Instrument and Form
  in JSON or YAML format.

- rios-qualtrics

  Converts a RIOS Instrument, Form, and CalculationSet 
  to a Qualtrics text file in Simple .TXT format.
  
Run each program's help to see its 
required arguments and available options::

  <program> --help

The question order, text, and associated enumerations, 
are all converted correctly; however the converted expressions
used for "calculated fields" and "skip logic", as well as the display
niceties of section breaks and separators will most likely require 
some "tweaking" because the various systems model pages, events and actions 
differently.

For example a RIOS calculation is an expression applied to an assessment,
independently of the data collection, while a REDCap "calculated field"
is a read-only field which evaluates its expression and displays the result
during data collection.


Installation
============

::

    pip install rios.conversion


Copyright (c) 2015, Prometheus Research, LLC

.. _Python: https://www.python.org
.. _RIOS: https://rios.readthedocs.org
.. _RIOS Identifiers: https://rios.readthedocs.org/en/latest/instrument_specification.html#identifier
.. _Semantic Versioning: http://semver.org
