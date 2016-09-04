..
  To build this documentation from the project base::
  $ cd docs
  $ make html
  Results are in ./build/html/

============================================
Welcome to the RIOS.CONVERSION documentation
============================================

`RIOS.CONVERSION`_ is a `Python`_ package that supports 
converting research instruments in various formats 
to and from `RIOS`_ data structures.

Supported formats:

- REDCap_ 
- Qualtrics_
- `RexDB-based Applications`_ (already in RIOS format)

.. _`Python`: https://www.python.org
.. _`Qualtrics`: http://www.qualtrics.com
.. _`RexDB-based Applications`: http://www.prometheusresearch.com
.. _`REDCap`: http://project-redcap.org
.. _`RIOS`: https://rios.readthedocs.org
.. _`RIOS.CONVERSION`: https://bitbucket.org/prometheus/rios.conversion

Examples
========

Convert to RIOS

::

  >>> from rios.conversion import (
  >>>     rios_to_redcap,
  >>>     rios_to_qualtrics,
  >>> )
  >>>
  >>> ...open instrument, form, calculationset files into streams/buffers...
  >>>
  >>> instrument = rios_to_redcap(
  >>>     instrument=instrument,
  >>>     form=form,
  >>>     calculationset=calculationset,
  >>>     localization='en',
  >>>     suppress=False
  >>> )
  >>>
  >>> ...use instrument object...

Convert from RIOS

::

  >>> from rios.conversion import (
  >>>     redcap_to_rios,
  >>>     qualtrics_to_rios,
  >>> )
  >>>
  >>> ...open data dictionary into a stream/buffer...
  >>> ...generate instrument id, title, description...
  >>>
  >>> rios_definition = rios_to_redcap(
  >>>     id=id,
  >>>     title=title,
  >>>     description=description,
  >>>     stream=stream,
  >>>     localization='en',
  >>>     instrument_version='1.0',
  >>>     suppress=False
  >>> )
  >>>
  >>> ...use rios definition...

Overview
========

.. toctree::
   :maxdepth: 1

   overview
   redcap
   qualtrics


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

This project is licensed under the Apache Software License, 
Version 2.0. 

.. toctree::
   :maxdepth: 1

   license


Change History
==============

.. toctree::

   changes


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _nose: https://nose.readthedocs.org/en/latest/
.. _pbbt: https://pypi.python.org/pypi/pbbt
.. _prospector: https://prospector.readthedocs.org/en/master/
.. _tests/: https://bitbucket.org/prometheus/rios.conversion/src/tip/tests/
