from machine import UART
import time

class driver_serial:
    def __init__(self):
        self._uart = UART(5, baudrate=115200)

    def send(self, key, value):
        self._uart.write("{}={:.6f}\n".format(str(key), float(value)))

    def read(self):
        if self._uart.any():
            b = self._uart.read(1)
            if b is not None:
                return b.decode('utf-8')
        return None