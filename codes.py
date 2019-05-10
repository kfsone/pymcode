#! *python3:doctest-modules*

"""
Marlin g/mcode class.

Provides a class for wrapping Code in helpers that translate human-friendly
arguments into formal gcode sequences.

The text representation of the command can be produced by calling code.emit().
"""


####
# 'Code' class
#
class Code(object):
    """
    Base class for describing a g/m code.

    >>> def answer_the_question():
    ...     return Code("M999", comment="life, universe, alles", t=42)
    >>> answer_the_question()
    <Code(code=M999, comment="life, universe, alles", T=42)>
    """
    def __init__(self, code, comment="", checksum_exception=False, line_no=None, **kwargs):
        self.code = code
        self.comment = comment
        self.parameters = {k.upper(): v for k, v in kwargs.items() if v is not None}
        self.checksummable = not checksum_exception
        self.line_no = line_no

    def __eq__(self, rhs):
        """
        Test for comparison by matching the code and the parameters only, line number is not a factor.
        
        >>> Code("M189", '', False, None, A=1) == Code("M189", 'ignored', True, 192, A=1)
        True
        >>> Code("M189", A=1) != Code("M189", A=2)
        True
        >>> Code("M189", A=1) != Code("M189")
        True
        >>> Code("M189") == Code("M189", S=None)
        True
        >>> Code("M189") != Code("G189")
        True
        """
        return self.code == rhs.code and self.parameters == rhs.parameters

    def __repr__(self):
        """
        >>> Code(code="A123", comment='Foo', line_no=234)
        <Code(code=A123, comment="Foo", line_no=234)>
        >>> Code(code="A123", comment='Foo', line_no=234, A=1, B=2)
        <Code(code=A123, comment="Foo", line_no=234, A=1, B=2)>
        >>> Code('A1', checksum_exception=True)
        <Code(code=A1, checksum_exception=True)>
        """
        parts = [f"code={self.code}"]
        if not self.checksummable:
            parts.append(f"checksum_exception=True")
        if self.comment is None:
            parts.append("comment=None")
        elif self.comment is not '':
            parts.append(f"comment=\"{self.comment}\"")
        if self.line_no is not None:
            parts.append(f"line_no={self.line_no}")
        parts.extend(f'{k}={v}' for k, v in self.parameters.items())
        return f'<Code({", ".join(parts)})>'

    def override(self, **kwargs):
        """ Explicitly override various parameters by identifier.
        >>> Code("A123", T=1).override(T=2).parameters
        {'T': 2}
        """
        for param, value in kwargs.items():
            param = str(param).upper()
            if len(param) != 1 or ord(param[0]) < ord('A') or ord(param[0]) > ord('Z'):
                raise ValueError("Invalid 'param' - must be a single letter A-Z")
            self.parameters[param] = value
        return self

    def emit(self, line_no=None, checksum=False, without_comments=False):
        """ Assembles the text representation of the code, optionally with checksum.
        >>> Code("A101").emit()
        'A101'
        >>> Code("A101", comment='cmt').emit()
        'A101 ;cmt'
        >>> Code("A123", F=9, T='', S=None, comment='cmt').emit(line_no=7, checksum=True, without_comments=True)
        'N7 A123 F9 T*3'
        >>> Code("A1", checksum_exception=True).emit(line_no=7, checksum=True)
        'A1'
        """
        # Build the full list of atoms we're going to put on this line - code and parameters.
        atoms = []

        # If the line needs to be checksummed, it has to start with the line number.
        if checksum and self.checksummable:
            if not isinstance(line_no, int):
                raise ValueError("Can't checksum without a line number")
            atoms.append(f"N{line_no}")

        atoms.append(self.code)

        # Include all parameters: for each parameter, output the field name
        # followed by the value. E.g. N100, S75. Bool values have no value, which
        # I'm representing by the empty string, e.g. "O": '' -> "O".
        atoms.extend(k+str(v) for k, v in self.parameters.items() if v is not None)

        # Make it a text string so we can do the checksum if need be.
        text = " ".join(atoms)
        if checksum and self.checksummable:
            # The checksum is just an xor of all the characters upto this point
            cs = 0
            for c in text:
                cs ^= ord(c)
            cs &= 255               # just the lower 8 bits
            text = f"{text}*{cs}"
            self.line_no = line_no  # checksums only apply to lines with a number.

        # Optionally add comments
        text += f" ;{self.comment}" if self.comment and not without_comments else ""

        return text
