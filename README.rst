************************
RIOS.CONVERSION Overview
************************

RIOS.CONVERSION is a `Python`_ package that supports 
converting instruments in various formats 
into `RIOS`_ data structures.

.. _`Python`: https://www.python.org
.. _`RIOS`: https://rios.readthedocs.org

The following command line programs have been implemented.

- redcap-rios

  Converts a REDCap Data Dictionary in csv format to 
  a RIOS Instrument, Form, and CalculationSet 
  in JSON or YAML format.

  The instrument id, version, and title must be provided as 
  arguments on the command line as they are not in the csv file.
  
- qualtrics-rios

  Converts a Qualtrics qsf file to a RIOS Instrument and Form
  in JSON or YAML format.

  The instrument version must be provided on the command line
  as it is not in the qsf file.
  
Run each program's help to see its 
required arguments and available options::

  <program> --help

Installation
============

::

    pip install rios.conversion


Contributing
============

Contributions and/or fixes to this package are more than welcome. Please submit
them by forking this repository and creating a Pull Request that includes your
changes. We ask that you please include unit tests and any appropriate
documentation updates along with your code changes.

This project will adhere to the `Semantic Versioning`_ methodology as much as
possible, so when building dependent projects, please use appropriate version
restrictions.

.. _`Semantic Versioning`: http://semver.org


License/Copyright
=================

This project is licensed under the GNU Affero General Public License, version
3. See the accompanying ``LICENSE.rst`` file for details.

Copyright (c) 2015, Prometheus Research, LLC
