********
Overview
********

RIOS.CONVERSION is a `Python`_ package that supports 
converting research instruments in various formats 
to and from `RIOS`_ data structures.

The following APIs have been implemented:

- redcap_to_rios

  Converts a REDCap Data Dictionary format to 
  the RIOS Instrument, Form, and CalculationSet 
  format.

- rios_to_redcap

  Converts a RIOS Instrument, Form, and CalculationSet 
  to the REDCap Data Dictionary format.
  
Import these functions for use::

  >>> from rios.conversion import (
  >>>     redcap_to_rios,
  >>>     qualtrics_to_rios,
  >>>     rios_to_redcap,
  >>>     rios_to_qualtrics,
  >>> )

Notes:

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
