**************
Change History
**************


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

