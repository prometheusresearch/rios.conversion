#
# Copyright (c) 2016, Prometheus Reserach, LLC
#


import textwrap


class Paragraph(object):
    """
     Represents error context as a text message with an optional payload.
     Rendered as:
       <message>
           <payload>
    """

    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload

    def __str__(self):
        if self.payload is None:
            return self.message
        block = "\n".join("    "+line if line else ""
                          for line in str(self.payload).splitlines())
        return "%s\n%s" % (self.message, block)

    def __repr__(self):
        if self.payload is None:
            return "%s(%r)" % (self.__class__.__name__, self.message)
        else:
            return "%s(%r, %r)" % (self.__class__.__name__,
                                   self.message, self.payload)


class Error(Exception):
    """
    Exception with a context trace.

    `message`
        Error description.
    `payload`
        Optional data related to the error.

    :class:`Error` objects provide a plain text traceback output,
    the exception is rendered as::

        {message}
            {payload}

    Use :meth:`wrap()` to add more paragraphs.
    """

    # Template for rendering the error in plain text.
    text_template = textwrap.dedent("""%s""")

    def __init__(self, message, payload=None):
        paragraph = Paragraph(message, payload)
        self.paragraphs = [paragraph]

    def wrap(self, message, payload=None):
        """
        Adds a paragraph to the context trace.
        """
        paragraph = Paragraph(message, payload)
        self.paragraphs.append(paragraph)
        return self

    def __call__(self, environ, start_response):
        output = self.text_template % self
        return [output]

    def __str__(self):
        return "\n".join(str(paragraph) for paragraph in self.paragraphs)

    def __repr__(self):
        # Emit:
        #   Error(...).wrap(...).wrap(...)
        output = ""
        for paragraph in self.paragraphs:
            if not output:
                output = self.__class__.__name__
            else:
                output += ".wrap"
            if paragraph.payload is None:
                output += "(%r)" % paragraph.message
            else:
                output += "(%r, %r)" % (paragraph.message, paragraph.payload)
        return output


class guard(object):
    """
    Adds a paragraph to exceptions leaving the wrapped ``with`` block.
    """

    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if isinstance(exc_value, Error):
            exc_value.wrap(self.message, self.payload)


class BaseConversionError(Error):
    """ Base class for rios.conversion exceptions """

    pass


class ConversionValueError(BaseConversionError):
    """ Thrown for ValueError exceptions in a conversion implementation """

    pass


class ConversionValidationError(BaseConversionError):
    """ Thrown for ValidationError exceptions in a conversion implementation """

    pass


class ConversionFailureError(Error):
    """
    Thrown for complete failure of instrument conversion process.

    Use when a foreign instrument/data dictionary cannot be converted at all.
    """

    pass


class RedcapFormatError(ConversionFailureError):
    """ Thrown for malformed REDCap data dictionary instrument """

    pass


class QualtricsFormatError(ConversionFailureError):
    """ Thrown for a malformed REDCap data dictionary instrument """

    pass
