import codes
from connection import Connection
from run import Run
import time

def main():
# Create a serial port connection and start listening on it
    with Connection("COM5", 115200) as serial_conn:
        serial_conn.listen()

        # Create a script sequence
        script = Run(writer=serial_conn, with_checksum=True)
        script.execute(codes.Code("M105"))

        script.execute([
            codes.set_lineno(1),
            codes.get_temp()
        ])

    time.sleep(2)


if __name__ == "__main__":
    main()

