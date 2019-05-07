#! *python3-tests:doctest-modules*

import unittest
from mock import MagicMock

import codes

class TestCodes(unittest.TestCase):
    def test_run(self):
        setline_cmd = codes.set_lineno(1)
        self.assertEqual(setline_cmd.code, "M110")
        self.assertEqual(setline_cmd.parameters, {"N": 1})
        self.assertEqual(setline_cmd.line_no, 0)

        # Home axis optionally takes a list of axes to be changed
        home_cmd = codes.home_axis()
        self.assertEqual(home_cmd.code, "G28")
        self.assertEqual(home_cmd.parameters, {})
        self.assertEqual(home_cmd.line_no, None)
        self.assertEqual(home_cmd, codes.home_axis(x=False, y=None, z=False, optional=None))

        home_cmd = codes.home_axis(x=True, y=True, optional=False)
        self.assertEqual(home_cmd.parameters, {'X': '', 'Y': ''})

        home_cmd = codes.home_axis(z=True, optional=True)
        self.assertEqual(home_cmd.parameters, {'Z': '', 'O': ''})
