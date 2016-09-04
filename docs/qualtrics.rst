*******************
Qualtrics Converter
*******************

qualtrics_to_rios
=================

Converts a Qualtrics qsf file to a RIOS Instrument and Form
in JSON or YAML format.

The instrument version must be provided as it is not in the qsf file.

Some questions in some qsf files contain the html markup "<br>". This
text is deleted.

rios_to_qualtrics
=================

Converts a RIOS instrument, form, (and optional calculationset)
in JSON or YAML to a data object.

Only 'Question' elements are converted, and of these only fields
whose base type is 'enumeration' or 'enumerationSet' are converted.
All other elements and questions produce warning messages and are ignored.
Calculations and "skip logic" are also ignored.

Conversion to the qsf format may be implemented in the future 
in support of calculations and "skip logic".
