#! *python3-tests:doctest-modules*

import unittest
from mock import MagicMock

import ops

class TestCase(unittest.TestCase):

    def expect_gcode(self, got, expected_code, expected_parameters, expect_line_no=None):
        self.assertEqual(got.code, expected_code)
        if expect_line_no is None:
            self.assertIsNone(got.line_no)
        else:
            self.assertEqual(got.line_no, expect_line_no)
        self.assertEqual(got.parameters, expected_parameters)

    def test_setline(self):
        self.expect_gcode(ops.set_lineno(1), "M110", {"N": 1}, expect_line_no=0)
        self.expect_gcode(ops.set_lineno(33), "M110", {"N": 33}, expect_line_no=32)

    def test_set_toolidx(self):
        self.expect_gcode(ops.set_toolidx(0), "T0", {})
        self.expect_gcode(ops.set_toolidx(3), "T3", {})

    def test_home_axis(self):
        # Home axis optionally takes a list of axes to be changed
        self.expect_gcode(ops.home_axis(), "G28", {})
        self.expect_gcode(ops.home_axis(x=False, y=None, z=False, optional=None), "G28", {})

        self.expect_gcode(ops.home_axis(x=True, y=True, optional=False), "G28", {'X': '', 'Y': ''})

        self.expect_gcode(ops.home_axis(z=True, optional=True), "G28", {'Z': '', 'O': ''})

    def test_home_all_axis(self):
        self.expect_gcode(ops.home_all_axis(), "G28", {})

    def test_move(self):
        self.expect_gcode(ops.move(x=1, y=2, z=5, feed_rate=None, extruding=False),
                            "G0", {'X': 1, 'Y': 2, 'Z': 5})
        self.expect_gcode(ops.move(x=2, y=3, z=6, feed_rate=40, extruding=True),
                            "G1", {'X': 2, 'Y': 3, 'Z': 6, 'F':40*60})

    def test_set_modes(self):
        self.expect_gcode(ops.set_extrudemode("absolute"), "M82", {})
        self.expect_gcode(ops.set_extrudemode("relative"), "M83", {})

        self.expect_gcode(ops.set_units("mm"), "G20", {})
        self.expect_gcode(ops.set_units("millimeter"), "G20", {})
        self.expect_gcode(ops.set_units("in"), "G21", {})
        self.expect_gcode(ops.set_units("inch"), "G21", {})

        self.expect_gcode(ops.set_positioning("absolute"), "G90", {})
        self.expect_gcode(ops.set_positioning("absolute"), "G90", {})

