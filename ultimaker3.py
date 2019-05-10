#! /usr/bin/env python3

"""
Ultimaker3 remote gcode helper.

Requirements:
    - Ultimaker 3,
    - Python 3,
    - Jupyter / iPython,
    - Developer mode access to the Ultimaker 3,
    - Passwordless access to the printer (via identity file etc)

This is a wrapper around iPython that establishes an SSH session to the 'ultimaker' user login on your printer
to provide as a writer to a "Run" instance so that you can generate gcommands using the iPython repl that are
then sent directly to your printer.

Example: (note: verbose commands used, abbreviate per your own level of experience)

    > python ultimaker3.py --printer pickles.my.net
    [ ... ipython blurb ... ]
    ---
    The Run instance is now available as 'um3': use um3.queue/um3.execute to queue/run commands
    ---
    > um3.queue(op.set_fanspeed(0))           # QUEUED: 1: turn the fan on
    > um3.queue(op.move(x=10, y=10, z=1))     # QUEUED: 2: move the print head without extruding
    > um3.execute()                           # EXECUTE: 1, 2
    > um3.queue(op.set_fanspeed(100))         # QUEUED: 3: set fan to full
    > um3.execute_immediate(op.set_fanspeed(20))  # sends this command right away
    > um3.execute(op.home_all_axis())         # queues a home-all-axis command and then executes the queue
"""

import code, ops, run

import IPython
import argparse
import logging
import re
import subprocess
import sys
import time

from inspect import cleandoc, signature
from threading import Thread
from queue import Queue, Empty

IS_POSIX = 'posix' in sys.builtin_module_names

# Since we can't do non-blocking io with select etc, use a thread to forward reads vi a queue.
def ssh_reader(stream, to_queue):
    """ Helper that consumes output from the printer and forwards it to queue, so the
    main thread has a non-blocking source for reads. """
    for read in iter(stream.read1, b''):
        for line in read.split(b'\n'):
            to_queue.put(line.decode())


class Ultimaker3(run.GriffinWriter):
    def __init__(self, host_addr, user, identity=None, ssh_cmd="ssh", connect_timeout=20):
        super().__init__(self)
        self.host_addr = host_addr
        self.user = user
        self.identity = f"-i {identity}" if identity else ""
        self.ssh_cmd = ssh_cmd
        self.connect_timeout = connect_timeout
        self.connected = False
        self.ssh_client = None
        self.client_responses = None
        self.response_queue = Queue()
        self.response_reader = None

    def await_cmd(self, timeout=300):
        """ Wait for a '(Cmd)' in the output from the printer """
        timeout = time.time() + timeout
        input_src = self.response_queue
        while timeout > time.time():
            try:
                line = input_src.get(timeout=0.01)
            except Empty:
                time.sleep(0.1)
                continue
            if line.startswith("(Cmd)"):
                    return True
            if line:
                print(line)
        return False

    def connect(self):
        """ Open the connection to the printer and wait for the initial (Cmd) """
        # Don't flash up an empty console window on windows
        if sys.platform == 'win32':
            si = subprocess.STARTUPINFO()
            si.wShowWindow = False
        else:
            si = None

        self.ssh_client = subprocess.Popen(f"{self.ssh_cmd} {self.user}@{self.host_addr} {self.identity}",
                                            bufsize=1,
                                            stdout=subprocess.PIPE, stderr=sys.stderr, stdin=subprocess.PIPE,
                                            startupinfo=si, close_fds=IS_POSIX)

        try:
            self.response_reader = Thread(target=ssh_reader, args=(self.ssh_client.stdout, self.response_queue))
            self.response_reader.start()

            # Give the SSH session upto 90s to connect_timeout to connect
            self.connected = False
            timeout = time.time() + self.connect_timeout
            if not self.await_cmd():
                raise RuntimeError("ssh timed out connecting")
            self.connected = True
        finally:
            if not self.connected:
                self.ssh_client.kill()

    def __call__(self, line):
        """ Implement the Writer protocol """
        pstdin, pstdout = self.ssh_client.stdin, self.ssh_client.stdout
        line = self.cmd_format.format(line=line)
        print(">> " + line)
        pstdin.write((line + "\n").encode())
        pstdin.flush()
        self.await_cmd()

    def close(self):
        """ Shutdown """
        if self.ssh_client and self.ssh_client.connected():
            self.ssh_client.kill()
        self.connected = False
        self.ssh_client = None

    def __enter__(self):
        """ context manager protocol: open """
        self.connect()
        return self

    def __exit__(self, *args):
        """ context manager protocol: close """
        if self.ssh_client:
            self.ssh_client.kill()


def cmd_help(args):
    if not args or args == "all":
        print("Repl-Commands: exit/quit, go, queue, help.")
        print("To queue raw gcode, start with a ' or \" character.")
        print("G/MCode Commands:")
        helpCheck = re.compile("^[a-z]").match
        print(", ".join(cmd for cmd in dir(ops) if helpCheck(cmd)))
    else:
        print()
        for arg in args:
            if arg == "exit" or arg == "quit":
                print(f"{arg}: Returns to ipython")
            elif arg == "go":
                print("Send any queued commands")
            elif arg == "list":
                print("List queued commands")
            elif arg == "help":
                print("This.")
            else:
                fn = getattr(ops, arg, None)
                if not fn:
                    print("Unrecognized command:", arg)
                else:
                    print("Ok.")
                    print("===", arg, str(signature(fn))[1:-1])
                    print(re.sub(r'^', cleandoc(fn.__doc__), '    '), re.M)
            print()


def cmd_list():
    if not um3.cmd_queue:
        print("Nothing queued.")
        return

    print("Queued commands:")
    for code in um3.cmd_queue:
        print(code)

def main(arglist):
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", "-u",     type=str, help="Username [default: 'ultimaker']", default='ultimaker')
    parser.add_argument("--ssh",  "-S",     type=str, help="SSH Command [default: 'ssh']", default='ssh')
    parser.add_argument("--identity", "-i", type=str, help="Identity file to use [default: None]", default=None)
    parser.add_argument("--verbose", "-v",  action="count", help="Increased verbosity", default=0)
    parser.add_argument("printer",          type=str, help="Network name/address of the printer")

    args = parser.parse_args(arglist)

    log_levels = [logging.WARN, logging.INFO, logging.DEBUG]
    log_level = log_levels[min(args.verbose, len(log_levels)-1)]
    logging.basicConfig(level=log_level)

    with Ultimaker3(host_addr=args.printer, user=args.user, identity=args.identity) as writer:
        um3 = run.Run(with_checksum=False, writer=writer)
        globals()["um3"] = um3
        IPython.embed()


def repl():
    while True:
        line = input("Code: ").strip()
        atoms = line.split()
        if not atoms:
            continue
        cmd, args = atoms[0], atoms[1:]

        if cmd == "exit" or cmd == "quit":
            return
        elif cmd == "go":
            um3.execute()
        elif cmd == "list":
            cmd_list()
        elif cmd == "help":
            cmd_help(args)
        else:
            if cmd[0] == '"' or cmd[0] == "'":
                cmd = cmd.strip(cmd[0])
            else:
                atoms = cmd.split(r'\s+')
                function, args = atoms[0], atoms[1:]
                # lookup the command name
                func = getattr(ops, function, None)
                if not func:
                    print("XX Unknown command: %s" % function)
                    continue
                kwargs = {}
                for arg in args:
                    key, value = arg.split('=')
                    kwargs[key] = value
                print("kwargs =", kwargs)
                cmd = func(**kwargs)
            print("Queueing:", cmd)
            um3.queue(cmd)


if __name__ == "__main__":
    main(sys.argv[1:])
