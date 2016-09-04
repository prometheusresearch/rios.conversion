#
# Copyright (c) 2016, Prometheus Reserach, LLC
#


import textwrap


__all__ = (
    'Error',
    'guard',

    'ConversionFailureError',
    'ConversionValueError',
    'RedcapFormatError',
    'QualtricsFormatError',
    'RiosFormatError',
    'RiosRelationshipError',
)


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
        block = "\n".join("    " + line if line else ""
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


class guard(object):  # noqa:F401
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


class ConversionFailureError(Error):
    """ Thrown for complete conversion failures """

    pass


class ConversionValidationError(Error):
    """
    Thrown when a conversion fails validation.

    See :class:ValidationError in ``rios.core``.
    """

    pass


class ConversionValueError(Error):
    """ Thrown for ValueError exceptions in a conversion implementation """

    pass


class RedcapFormatError(Error):
    """ Thrown for malformed REDCap data dictionary instrument """

    pass


class QualtricsFormatError(Error):
    """ Thrown for a malformed REDCap data dictionary instrument """

    pass


class RiosFormatError(Error):
    """ Thrown for a malformed REDCap data dictionary instrument """

    pass


class RiosRelationshipError(Error):
    """ Thrown for non-matching instrument, form, and calculationsets """

    pass
