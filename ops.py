"""
Human-friendly "operation" calls for generating gcode sequences, as well as
common multi-stage operations.

Each helper generates an instance of the codes.Code() class, which holds the translated
parameter list for the code and is responsible for tracking the line no when the command
is executed.

Use run.Run() to build/generate/execute sequences. Direct-execution of gcode can be
implemented by providing a Writer() class that talks directly to a device.
"""

from codes import Code


####
# Constants
#
""" Extrusion modes that map to M commands: 'absolute' and 'relative' """
EXTRUSION_MODES = { 'absolute': "M82", 'relative': "M83"}
""" Names of units that map to G commands: 'mm'/'millimeter', 'in'/'inches' """
UNITS = { 'mm': "G20", 'millimeter': "G20", 'millimeters': "G20", 'in': "G21", 'inch': "G21", 'inches': "G21" }
""" Position modes that map to G commands: 'absolute' and 'relative' """
POSITIONING_MODES = { 'absolute': "G90", 'relative': "G91" }


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
def set_toolidx(toolidx):
    """ Specifies which print head/tool index you want to be default """
    if not isinstance(toolidx, int):
        toolidx = int(toolidx)
    return Code(f"T{toolidx:d}")

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
    return Code(UNITS[unit], comment=f"Set units to {unit}")

def set_positioning(pos_mode):
    """ G90/G91: Change positioning mode to absolute/relative """
    return Code(POSITIONING_MODES[pos_mode], comment=f"set pos_mode positioning mode")

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
    if not( x or y or z or feed_rate or filament):
        raise ValueError("move requires at least one argument")
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

def home_all_axis():
    """ The default for home_axis is to home them all, but if you want to express that explicitly... """
    return home_axis()

def extrude(x=None, y=None, z=None, feed_rate=None, filament=None):
    """ Abbreviation for calling move() with extruding=True """
    return move(x=x, y=y, z=z, feed_rate=feed_rate, filamen=filament, extruding=True)
