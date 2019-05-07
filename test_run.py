#! *python3-tests:doctest-modules*

import unittest
from mock import MagicMock

import codes
import run


class TestRun(unittest.TestCase):
    def test_run(self):
        setline_cmd = codes.set_lineno(1)
        home_cmd = codes.home_axis()
        temp_cmd = codes.get_temp()

        with MagicMock() as writer:
            r = run.Run(writer=writer)
            writer.assert_not_called()
            self.assertIsNone(r.line_no)
            self.assertEqual(r.cmd_queue, [])
            self.assertEqual(r.cmd_hist, [])
            self.assertFalse(r.without_comments)
            self.assertFalse(r.with_checksum)

        with MagicMock() as writer:
            r.writer = writer
            r.queue(home_cmd)
            writer.assert_not_called()
            self.assertIsNone(r.line_no)
            self.assertEqual(r.cmd_queue, [home_cmd])
            self.assertEqual(r.cmd_hist, [])

        # Add a second command
        with MagicMock() as writer:
            r.writer = writer
            r.queue(temp_cmd)
            writer.assert_not_called()
            self.assertIsNone(r.line_no)
            self.assertEqual(r.cmd_queue, [home_cmd, temp_cmd])
            self.assertEqual(r.cmd_hist, [])

        # Now check multi-command execution
        with MagicMock() as writer:
            r.writer = writer
            r.execute()
            self.assertEqual(len(writer.mock_calls), 3)
            # Because we're not doing checksums, line no should not increment
            self.assertEqual(r.line_no, 1)
            self.assertEqual(r.cmd_queue, [])
            self.assertEqual(r.cmd_hist, [setline_cmd, home_cmd, temp_cmd])
