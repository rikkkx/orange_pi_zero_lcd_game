import time
from typing import Union, List

from pyA20.gpio import gpio
from pyA20.gpio import port
from bitstring import Bits


gpio.init()


class LCD:
    RS_DATA = 1
    RS_CMD = 0

    E_DELAY = 0.0005
    E_PULSE = 0.0005

    def __init__(self, rs, e, d_pins):
        self.RS = rs
        self.E = e
        self.D = tuple(d_pins)

        self._init_display()

    def _init_display(self):
        self._send_byte(0x33, self.RS_CMD)  # 110011 Initialise
        self._send_byte(0x32, self.RS_CMD)  # 110010 Initialise
        self._send_byte(0x06, self.RS_CMD)  # 000110 Cursor move direction
        self._send_byte(0x0C, self.RS_CMD)  # 001100 Display On,Cursor Off, Blink Off
        self._send_byte(0x28, self.RS_CMD)  # 101000 Data length, number of lines, font size
        self._send_byte(0x01, self.RS_CMD)  # 000001 Clear display
        time.sleep(E_DELAY)

    def _send_byte(self, data: Union[Bits, int], rs_mode):
        if isinstance(data, int):
            data = Bits(hex(data))

        gpio.output(self.RS, rs_mode)

        for idx in range(4, 8):
            gpio.output(self.D[idx], data[idx])
        self._togle_e()

        for idx in range(4):
            gpio.output(self.D[idx], data[idx])
        self._togle_e()

    def _togle_e(self):
        time.sleep(self.E_DELAY)
        gpio.output(self.E, True)
        time.sleep(self.E_PULSE)
        gpio.output(self.E, False)
        time.sleep(self.E_DELAY)

    def print(self, array: List[int]):
        for c in array:
            self._send_byte(c, self.RS_DATA)

    def prints(self, msg: str):
        self.print([ord(x) for x in str])

    def set_cursor(position: int, line: int):
        line_start_addr = 0x00 if line == 0 else 0x40
        cmd = 0x80 | (line_start_addr + position)
        self._send_byte(cmd, self.RS_CMD)

    def create_char(pos: int, char_mask: List[int]):
        pass
