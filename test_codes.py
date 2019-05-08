
#! *python3-tests:doctest-modules*

import unittest

from codes import Code


class TestCase(unittest.TestCase):
    def test_code_basic(self):
        code = Code("M1")
        self.assertEqual(code.code, "M1")
        self.assertEqual(code.comment, "")
        self.assertEqual(code.parameters, {})
        self.assertEqual(code.checksummable, True)
        self.assertEqual(code.line_no, None)

    def test_code_populous(self):
        code = Code(code="M999", checksum_exception=True, line_no=3,
                    comment="Test code",
                    S=1, T=2, U=111)
        self.assertEqual(code.code, "M999")
        self.assertEqual(code.comment, "Test code")
        self.assertEqual(code.parameters, {'S': 1, 'T': 2, 'U': 111})
        self.assertEqual(code.checksummable, False)
        self.assertEqual(code.line_no, 3)
