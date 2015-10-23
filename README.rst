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

  WARNING:
  
  Since RIOS does not allow capital letters in ids,
  the program converts all expressions and internal values to lowercase.
  Expressions are used both in calculations and in skip logic.

- qualtrics-rios

  Converts a Qualtrics qsf file to a RIOS Instrument and Form
  in JSON or YAML format.

  The instrument version must be provided on the command line
  as it is not in the qsf file.
  
  WARNING:

  Some questions in some qsf files contain the html markup "<br>".
  This text is deleted.
     
Run each program's help to see its 
required arguments and available options::

  <program> --help

See `test/input.yaml`_ for examples of running these programs to convert forms.

.. _`test/input.yaml`: https://bitbucket.org/prometheus/rios.conversion/src/tip/test/input.yaml


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

The project uses `pbbt`_ for testing.  
Add new tests to `test/input.yaml`_.
Run tests::

    $ pbbt -T   # train (update output.yaml)
    $ pbbt      # test (compare output.yaml to results)   

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

.. _`Semantic Versioning`: http://semver.org
.. _`pbbt`: https://pypi.python.org/pypi/pbbt

License/Copyright
=================

This project is licensed under the GNU Affero General Public License, version
3. See the accompanying ``LICENSE.rst`` file for details.

Copyright (c) 2015, Prometheus Research, LLC
