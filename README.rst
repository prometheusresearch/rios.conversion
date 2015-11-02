************************
RIOS.CONVERSION Overview
************************

RIOS.CONVERSION is a `Python`_ package that supports 
converting instruments in various formats 
to and from `RIOS`_ data structures.

.. _`Python`: https://www.python.org
.. _`RIOS`: https://rios.readthedocs.org

The following command line programs have been implemented.

- redcap-rios

  Converts a REDCap Data Dictionary in csv format to 
  a RIOS Instrument, Form, and CalculationSet 
  in JSON or YAML format.

- rios-redcap

  Converts a RIOS Instrument and Form to a REDCap Data Dictionary 
  in csv format.
  
- qualtrics-rios

  Converts a Qualtrics qsf file to a RIOS Instrument and Form
  in JSON or YAML format.

Run each program's help to see its 
required arguments and available options::

  <program> --help

See `test/input.yaml`_ for examples of running these programs.

.. _`test/input.yaml`: https://bitbucket.org/prometheus/rios.conversion/src/tip/test/input.yaml

While the conversion of most questions is straight forward 
the conversion of actions and events is more complex because 
these systems model these things differently.

Expressions are used for "calculated fields" and "skip logic".  
A "calculated field" is a read-only field which evaluates its expression
and displays the result.  The expression may reference other input fields
or other calculated fields on the form.  
Furthermore a field may be disabled or hidden (i.e. skipped) 
if a given expression is true.

The expressions use field IDs to reference other fields and RIOS restricts the 
range of values for an `Identifier`_.

These programs attempt to convert input IDs to valid RIOS Identifiers by 
converting to lowercase, converting sequences of non-alphanumeric 
characters to underbar, and removing leading and trailing underbars.  
The input expressions are also converted to lowercase in a naive attempt 
to preserve the semantics.


.. _`Identifier`: https://rios.readthedocs.org/en/latest/instrument_specification.html#id15
 
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
