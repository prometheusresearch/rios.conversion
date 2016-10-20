**************
Change History
**************


0.6.1 (2016-09-05)
==================

* Fixed bug where REDCap text fields with bounded/ranged value retrictions were
  generated as invalid RIOS text fields (RIOS text fields may not have bounded
  constraints, so these REDCap fields are now converted to RIOS ``integer`` or
  ``float`` fields corresponding to the type of their bounded values)
* Fixed bug where Qualtrics/REDCap to RIOS conversions were missing the ``urn:``
  string was missing from the instrument ID
* Fixed bug where REDCap to RIOS conversion data was nested an extra,
  unnecessary list deep


0.6.0 (2016-09-04)
==================

* New API implemented with corresponding documentation
* Top level API exposes four functions for conversion: redcap_to_rios, qualtrics_to_rios, rios_to_redcap, rios_to_qualtrics
* Complete code refactor and reorganization
* Completely stripped out CLI/argparse command-like interface to conversion classes
* Proper implementation of a complete test suite
* Test files reorganized into a proper directory structure
* Implemented user friendly error output messages that make sense
* Implemented logging system to log errors, warnings, and information
* JSON reader class implemented with subclasses for the Qualtrics to RIOS converter and API
* Package simplejson added as a dependency for better JSON error output
* Instrument and calculation storage mechanism implemented
* Exception class suite added to the package with specific, package-based exceptions
* Base Error class implemented for friendly error output
* TODO: Implement new command line interface with some sort of relevant output format


0.5.0 (2016-08-17)
==================

* Fixed handling of REDCap CSVs with unexpected newline characters.

0.4.0 (2016-07-21)
==================

* Generated RIOS configurations are now validated before writing the files.
* Fixes to address some variances in REDCap column names.
* Fixed an issue with field name uniqueness in REDCap->RIOS conversions.
* Fixed an issue with identifying some numeric types in REDCap->RIOS
  conversions.

0.3.1 (2015-12-21)
==================

* fix License in setup.py classifiers

0.3.0 (2015-12-21)
==================

* Switch to Apache Software License 2.0
  for compatibility with the Open Science Framework.

0.2.1 (2015-12-19)
==================

* rios-redcap: fix bug - "identifiable" and "required"
  are optional attributes.
* rios-qualtrics: catch json.load and other input errors
  for better error messages.

0.2.0 (2015-09-28)
==================

* Started from prismh.conversion.

