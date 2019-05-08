import serial   # pyserial
import threading
import time


class Connection:

    def __init__(self, comport, baudrate):
        self.conn = serial.Serial(comport, baudrate, timeout=0.1)
        self.thread = threading.Thread(target=reader, args=(self,))
        self.listening = False

    def listen(self):
        if not self.listening:
            self.listening = True
            self.thread.start()

    def __call__(self, text):
        print(">>", text)
        if not text.endswith("\n"):
            text += "\n"
        self.conn.write((text + "\n").encode())
        self.conn.flush()

    def close(self):
        if self.listening:
            self.conn.flush()
            self.conn.close()
            self.thread.join()

    def __enter__(self):
        self.listen()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()


def reader(conn: Connection):
    # Naive implementation for now:
    while conn.listening and conn.conn.readable():
        print("...")
        try:
            text = conn.conn.readline()
        except serial.serialutil.SerialException:
            return
        if text:
            print("<<", text)

