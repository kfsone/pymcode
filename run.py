#! *python3:doctest-modules*

import codes
import ops
import sys


# -----------------------------------------------------------------------------
#
class Writer(object):
    """ Base class for the Writer interface which implements a __call__ method that takes a string
        and sends it to the output stream """
    def __call__(self, line):
        """ Run will forward executing lines to this function """
        print(line)


# -----------------------------------------------------------------------------
#
class GriffinWriter(Writer):
    """ Emits commands in a format suitable for use with griffin's utility that has a "sendgcode" command

    :param outstream: Specify the file/stream to write to, default stdout
    :param cmd_format: Optionally override the format ('sendgcode {line}\n')
    """
    def __init__(self, outstream=sys.stdout, cmd_format="sendgcode {line}\n"):
        self.stdout = outstream
        self.cmd_format = cmd_format

    def __call__(self, line):
        """ Output a line suitable for pasting into, e.g, an Ultimaker 3 command line
        >>> class MockStream:
        ...    def write(self, text): print(text, end='')
        >>> g = GriffinWriter(outstream=MockStream())
        >>> g("M110 N999")
        sendgcode M110 N999
        """
        self.stdout.write(self.cmd_format.format(line=line))


# -----------------------------------------------------------------------------
#
class Run(object):
    """ Encapsulation of a run of commands, with the ability to queue and run commands while tracking line numbers for checksums """

    def __init__(self, without_comments=False, with_checksum=False, writer=Writer()):
        self.with_checksum = with_checksum
        self.without_comments = without_comments
        self.writer = writer

        self.reset()

    def reset(self):
        """ Clear the queue and reset the line number. """
        self.cmd_hist = []
        self.cmd_queue = []
        self.line_no = None

    def queue(self, commands):
        """ Add a command to the queue.
        >>> r = Run()
        >>> r.queue(["a", "b"])
        >>> r.cmd_queue
        ['a', 'b']
        >>> r.queue(['x'])
        >>> r.cmd_queue
        ['a', 'b', 'x']
        """
        if isinstance(commands, codes.Code):
            self.cmd_queue.append(commands)
        else:
            self.cmd_queue.extend(commands)

    def execute_immediate(self, commands):
        """ Execute the given commands without consulting the queue. """
        if not commands:
            return
        # User passing us a text line, e.g. "G0 X0 Y1"
        if isinstance(commands, bytes):
            commands = commands.encode()
        if isinstance(commands, (codes.Code, str)):
            commands = (commands,)

        checksum, without_comments, writer = self.with_checksum, self.without_comments, self.writer
        history = self.cmd_hist.append
        for command in commands:
            if isinstance(command, str):
                command, _, comment = command.partition(';')
                command = command.strip()
                tokens = command.split('\s+')
                code, args = tokens[0], {arg[0]: arg[1:] for arg in tokens[1:]}
                command = codes.Code(code, **args)

            if self.line_no is None and command.code != "M110":
                self.line_no = 0
                self.execute_immediate(ops.set_lineno(1))

            writer(command.emit(checksum=checksum, without_comments=without_comments, line_no=self.line_no))
            if command.line_no is not None:
                self.line_no = command.line_no + 1
            history(command)

    def execute(self, commands=None):
        """ Executes optional commands after first executing the queue. """
        queue, self.cmd_queue = self.cmd_queue, []
        if isinstance(commands, (codes.Code, str, bytes)):
            queue.append(commands)
        else:
            queue.extend(commands or [])
        if queue:
            self.execute_immediate(queue)
