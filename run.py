#! *python3:doctest-modules*

import codes

class Run(object):
    """ Encapsulation of a run of commands, with the ability to queue and run commands while tracking line numbers for checksums """

    def __init__(self, without_comments=False, with_checksum=False, writer=print):
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
        if isinstance(commands, codes.Code):
            commands = (commands,)
        if self.line_no is None and commands[0].code != "M110":
            self.line_no = 0
            self.execute_immediate(codes.set_lineno(1))

        checksum, without_comments, writer = self.with_checksum, self.without_comments, self.writer
        history = self.cmd_hist.append
        for command in commands:
            writer(command.emit(checksum=checksum, without_comments=without_comments, line_no=self.line_no))
            if command.line_no is not None:
                self.line_no = command.line_no + 1
            history(command)

    def execute(self, commands=None):
        """ Executes optional commands after first executing the queue. """
        queue, self.cmd_queue = self.cmd_queue, []
        if isinstance(commands, codes.Code):
            queue.append(commands)
        else:
            queue.extend(commands or [])
        if queue:
            self.execute_immediate(queue)
