#! *python3:doctest-modules*

"""
G/MCode module:

Provides a series of human-friendly helper functions for generating Marlin M/G codes.

Each helper generates an instance of the codes.Code() class, which holds the translated
parameter list for the code and is responsible for tracking the line no when the command
is executed.

>>> get_temp()
<Code(code=M105, comment="report bed temp")>

The actual text representation of the command can be produced by calling code.emit().
"""


####
# Constants
#
""" Extrusion modes that map to M commands: 'absolute' and 'relative' """
EXTRUSION_MODES = { 'absolute': "M82", 'relative': "M83"}

""" Names of units that map to G commands: 'mm'/'millimeter', 'in'/'inches' """
UNITS = { 'mm': "G20", 'millimeter': "G20", 'in': "G21", 'inches': "G21" }

""" Position modes that map to G commands: 'absolute' and 'relative' """
positioningModes = { 'absolute': "G90", 'relative': "G91" }


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
    

####
# Parameter-type helper classes
#
def Bool(value):
    """
    Store bools in the parameter dictionary as empty string for True and None for False
    
    >>> Bool(True) is ''
    True
    >>> Bool(False) is None
    True
    >>> Bool(None) is None
    True
    """
    if value not in (None, True, False):
        raise ValueError("Expected boolean parameter or None")
    return '' if value else None


####
# Code functions
#
def set_lineno(number):
    """ M110: to set the current line number
    >>> set_lineno(555)
    <Code(code=M110, comment="set line no", line_no=554, N=555)>
    """
    if number < 1:
        raise ValueError("Cannot set line number < 0")
    item = Code("M110", n=number, comment="set line no")
    # Because I'm setting the line number, I behave as though I come from
    # the line before this one.
    item.line_no = number - 1
    return item

def set_hotendtemp(celcius, toolidx=None, max_auto=None):
    """ M104: Set temp of a hot end and/or the max autotemp for it """
    b, f = (max_auto, '') if max_auto is not None else (None, None)
    return Code('M104', s=celcius, t=toolidx, b=b, f=f,
                comment="set hotend temp")

def get_temp(toolidx=None):
    """ M105: Request a temperatures report """
    return Code('M105', t=toolidx,
                comment="report bed temp")

def wait_hotendtemp(celcius, toolidx=None, heat_to=False, max_auto=None):
    """ M109: Wait for hotend to reach a temperature """
    b, f = (max_auto, '') if max_auto is not None else (None, None)
    s, r = (celcius, None) if not heat_to else (None, celcius)
    return Code('M109', s=s, r=r, b=b, f=f, t=toolidx, comment="wait on hotend temp")

def wait_bedtemp(celcius, heat_to=False):
    """ M190: Wait for the bed to heat/cool to a temp, or to to heat past a temp """
    s, r = (celcius, None) if not heat_to else (None, celcius)
    return Code('M190', s=s, r=r,
                comment="wait for bedtemp to heat")

def set_bedtemp(celcius):
    """ M140: Set the bed temperature """
    return Code('M140', comment="set bed temp")

def set_extrudemode(ext_mode):
    """ M82/M83: Set extrusion mode to absolute/relative """
    return Code(EXTRUSION_MODES[ext_mode], comment=f"set {ext_mode} e-mode")

def set_units(unit):
    """ G20/G21: Switch units: mm/millimeter or in/inches """
    return Code(units[unit], comment=f"Set units to {unit}")

def set_positioning(pos_mode):
    """ G90/G91: Change positioning mode to absolute/relative """
    return Code(positioningModes[pos_mode], comment=f"set pos_mode positioning mode")

def set_fanspeed(speed, fanidx=None, secondary=None):
    """ M106: Set the fan speed (-1 for off, 0-255)"""
    return Code("M106", p=fanidx, s=speed, t=secondary)

def set_fanoff(fanidx=None):
    """ M107: Turn off a fan """
    return Code("M107", p=fanidx)

def home_axis(x=None, y=None, z=None, optional=None):
    """ G28: Home one or more axis. """
    return Code("G28", x=Bool(x), y=Bool(y), z=Bool(z), o=Bool(optional))

def set_axisstepsperunit(steps=None, extruderidx=None, x_units=None, y_units=None, z_units=None):
    """ G92: Set the steps-per-unit for one or more axis """
    return Code("G92", e=steps, t=extruderidx, x=x_units, y=y_units, z=z_units)

def move(x=None, y=None, z=None, feed_rate=None, filament=None, extruding=False):
    """ G0/G1: Move the active print head """
    extruding = extruding or bool(filament)
    if feed_rate: feed_rate *= 60
    return Code("G0" if not extruding else "G1",
                x=x, y=y, z=z, f=feed_rate, e=filament,
                )

def get_position(detail=None):
    """ M114: Query the current position """
    if detail is not None:
        detail = "<" if not detail else ">"
    return Code("M114", d=detail, comment="get position")

####
# General helpers.
#
def zero_extruded_length():
    """ Helper: Clear extrusion """
    return set_axisstepsperunit(steps=0)

