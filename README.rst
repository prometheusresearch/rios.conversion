********
Overview
********

RIOS.CONVERSION is a `Python`_ package that supports 
converting instruments in various formats 
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


Contributing
============

Contributions and/or fixes to this package are more than welcome. 
Please submit them by forking this repository and 
creating a Pull Request that includes your changes. 
We ask that you please include unit tests and 
any appropriate documentation updates along with your code changes.

The project uses `pbbt`_, `prospector`_, and `nose`_ for testing.  
Add new tests to `tests/`_.

This project will adhere to the 
Semantic Versioning methodology as much as possible, 
so when building dependent projects, 
please use appropriate version restrictions.

A development environment can be set up to work on this package 
by doing the following::

    $ virtualenv rios.conversion
    $ cd rios.conversion
    $ . bin/activate
    $ pip install pbbt
    $ hg clone ssh://hg@bitbucket.org/prometheus/rios.conversion
    $ pip install -e ./rios.conversion[dev]


License/Copyright
=================

This project is licensed under the GNU Affero General Public License, version
3. See the accompanying ``LICENSE.rst`` file for details.

Copyright (c) 2015, Prometheus Research, LLC

.. _nose: https://nose.readthedocs.org/en/latest/
.. _pbbt: https://pypi.python.org/pypi/pbbt
.. _prospector: https://prospector.readthedocs.org/en/master/
.. _Python: https://www.python.org
.. _RIOS: https://rios.readthedocs.org
.. _RIOS Identifiers: https://rios.readthedocs.org/en/latest/instrument_specification.html#identifier
.. _Semantic Versioning: http://semver.org
.. _tests/: https://bitbucket.org/prometheus/rios.conversion/src/tip/tests/

