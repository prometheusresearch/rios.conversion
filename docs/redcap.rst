****************
REDCap Converter
****************

redcap-rios
===========

Converts a REDCap Data Dictionary in csv format to 
a RIOS Instrument, Form, and CalculationSet 
in JSON or YAML format.

The instrument id, version, and title must be provided as 
arguments on the command line as they are not in the csv file.

The program creates or overwrites its output files.
As for CalculationSet, if there are no calculations in the input, 
no CalculationSet file will be created, 
and if it already existed it will be deleted.
 
Since there are restrictions on `RIOS Identifiers`_,
the program converts all internal values to valid identifiers.
See ``help(rios.conversion.redcap.to_rios.Csv2OrderedDict.get_name)``
for details.  
This mangling of the input identifiers may break expressions 
or cause other errors so it is **strongly** recommended 
to begin with valid RIOS identifiers for all page, form, matrix, and 
field names, as well as all internal enumeration values.

Sliders are converted to a simple float input field 
with min=0.0 and max=100.0.  Any slider labels are ignored.

Two input formats are accepted.  The first uses these input fields::

    Variable / Field Name
    Form Name
    Section Header
    Field Type
    Field Label
    Choices, Calculations, OR Slider Labels
    Field Note
    Text Validation Type OR Show Slider Number
    Text Validation Min
    Text Validation Max
    Identifier?
    Branching Logic (Show field only if...)
    Required Field?
    Custom Alignment
    Question Number (surveys only)
    Matrix Group Name
    Matrix Ranking?
    Field Annotation

- **Variable / Field Name** is mapped to Field Object id.
- **Form Name** is mapped to the RIOS page ID.
- When **Section Header** is present, an additional "text" element is included
  in the form.
- **Field Type** and **Text Validation Type ...** determine the RIOS type.
  "dropdown" and "radio" map to an enumeration, 
  and "checkbox" maps to an enumeration set.
- **Field Label** is mapped to Question Object text.  
- Various spellings for the Choices / Calculations field have been 
  encountered, so any field name starting with "Choices" 
  and containing "Calc" is taken to be this field.

  When this field contains choices it is a pipe delimited string 
  of comma seperated tuples:  id, value.  
  The value is what is displayed to the user, 
  and the id is what is stored in the database 
  when the user selects the value.
   
- **Field Note** is mapped to Question Object help.
- **Text Validation Max and Min** 
  are mapped to a suitable Bound Constraint Object 
  as the "range" of an appropriate RIOS Type Object.
- **Identifier?** is mapped to Field Object identifiable.
- REDCap displays a field if its "Branching Logic" expression is True.
  In RIOS, the field is disabled if the expression is False.
  Arbitrarily, this converter outputs "disable" instead of "hide" 
  as the action for this event. 
- **Required Field** is mapped to Field Object required.
- **Matrix Group Name** is mapped to the Field Object id of a matrix field.
- The following fields: 
  **Custom Alignment**, 
  **Question Number (Show field only if...)**, 
  **Matrix Ranking?**, 
  and **Field Annotation** 
  are completely ignored.

Entries with the same **Form Name** or **Matrix Group Name** 
must appear consecutively. 

The second format uses these input fields::

    fieldID
    text
    help
    error
    enumeration_type
    data_type
    repeating_group_name
    page

- **fieldID** is mapped to Field Object id.
- **text** is mapped to Question Object text.
- **help** is mapped to Question Object help.
- **enumeration_type** selects "enumeration" or "enumerationSet".
- **data_type** determines the RIOS type.
  When enumeration_type is set, this field contains a JSON string 
  which encodes an object whose "Choices" attribute 
  is an array of single item dictionaries.  For each (key, value) item,
  the key is the identifier and the value is displayed to the user.

  The array of choices will be presented to the user 
  in order of dictionary key.
- **repeating_group_name** is ignored.
- **page** is mapped to the RIOS page id.  
  As a convenience, 
  "page_0" is assigned if this field is left blank.

Entries with the same **page** must appear consecutively.
  
..
  During development, numerous forms in this format were encountered 
  which had enumerations of a single entry.  
  RIOS rejects such enumerations because 
  they do not make much sense for a dropdown menu or radio button.  
  However, instead of rejecting these forms outright, as a convenience,
  the converter appends the following "default" choice to the enumeration::

      {'c999': 'N/A'}

 
rios-redcap
===========

Converts a RIOS Instrument, Form, and optional CalculationSet 
to a REDCap Data Dictionary in csv format.

The first format is used for output because it supports calculations,
branching logic, and matrices, as well as the "required" and "identifiable"
field attributes.

Cavaets
-------

* Function names, variable references, and operators in REXL expressions
  are converted to REDCap; however the truth value of the REXL expression 
  used for "Branching Logic" has NOT been negated. 
  This must be done manually.
 
* RIOS calculations are associated with an assessment and are not 
  directly connected to a form.  Consequently all of the calculations 
  are appended to the last page of the REDCap Data Dictionary.

* The only RIOS matrices which can be converted to REDCap have exactly
  one question column.  This column must be an enumeration or enumerationSet.

Expressions
===========

Expressions are converted to lowercase and to `PEXL`_.

So for example in REDCap 
suppose A and B are form fields 
and C is a calculation field::

    SUM([A], [B], [C]) <> 1

is converted to RIOS as::

    rios.conversion.math.sum_(assessment["a"], assessment["b"], calculations["c"]) != 1

REDCap expressions support a collection of math and date functions.

``min``, ``max``, and ``abs`` are available directly in Python, 
``sqrt`` is in the Python math library, 
and the following have implementations in rios.conversion::

    datediff
    mean
    median
    round
    rounddown
    roundup
    stdev
    sum
    
If your expressions reference any of these functions then include 
rios.conversion as a dependency for your project.

Matrices
========

REDCap matrices of R rows by C columns 
become a RIOS matrix of R rows by 1 column.
The single column is an enumeration (or enumeration set) of C values.

.. _PEXL: https://bitbucket.org/rexdb/rex.expression-provisional#rst-header-features-supported
.. _RIOS Identifiers: https://rios.readthedocs.org/en/latest/instrument_specification.html#identifier

