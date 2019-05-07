from codes import *


def test_script():
    preamble = [
        set_lineno(1),
        set_bedtemp(75),
        get_temp(),
        wait_bedtemp(75),
        set_hotendtemp(185),
        get_temp(),
        wait_hotendtemp(185),
        set_extrudemode('absolute'),
        set_units('mm'),
        set_positioning('absolute'),
        set_fanspeed(0),
        home_axis(),
        zero_extruded_length(),
    ]

    prep = [
        move(z=1),
        move(x=10, z=0, feed_rate=1000),
        move(x=300),
        zero_extruded_length(),
    ]

    finish = [
        zero_extruded_length(),
        set_hotendtemp(0),
        set_positioning('relative'),
        move(z=15),
        set_positioning('absolute'),
        home_axis(x=True, y=True, optional=True),
    ]

    r = Run(with_checksum=True)
    for script in (preamble, prep, finish):
        map(r.execute, script)

