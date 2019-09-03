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
        self.clear()
        self.set_cursor(0, 0)

    def _send_byte2(self, bits, mode):
        """
        Send byte to data pins

        bits = data
        mode = True  for character
             False for command
        """
        gpio.output(self.RS, mode) # RS

        # High bits
        gpio.output(self.D[4], False)
        gpio.output(self.D[5], False)
        gpio.output(self.D[6], False)
        gpio.output(self.D[7], False)
        if bits&0x10==0x10:
            gpio.output(self.D[4], True)
        if bits&0x20==0x20:
            gpio.output(self.D[5], True)
        if bits&0x40==0x40:
            gpio.output(self.D[6], True)
        if bits&0x80==0x80:
            gpio.output(self.D[7], True)

        self._togle_e()

        # Low bits
        gpio.output(self.D[4], False)
        gpio.output(self.D[5], False)
        gpio.output(self.D[6], False)
        gpio.output(self.D[7], False)
        if bits&0x01==0x01:
            gpio.output(self.D[4], True)
        if bits&0x02==0x02:
            gpio.output(self.D[5], True)
        if bits&0x04==0x04:
            gpio.output(self.D[6], True)
        if bits&0x08==0x08:
            gpio.output(self.D[7], True)

        self._togle_e()

    def _send_byte(self, data: Union[Bits, int], rs_mode):
        if isinstance(data, int):
            data = Bits('0b' + bin(data)[2:].rjust(8, '0'))

        gpio.output(self.RS, rs_mode)

        for idx in range(4, 8):
            gpio.output(self.D[idx], data[7 - idx])
        self._togle_e()

        for idx in range(4):
            gpio.output(self.D[idx+4], data[7 - idx])
        self._togle_e()

    def _togle_e(self):
        time.sleep(self.E_DELAY)
        gpio.output(self.E, True)
        time.sleep(self.E_PULSE)
        gpio.output(self.E, False)
        time.sleep(self.E_DELAY)

    def clear(self):
        self._send_byte(0x01, self.RS_CMD)
        time.sleep(self.E_DELAY)

    def print(self, array: List[int]):
        for c in array:
            self._send_byte(c, self.RS_DATA)

    def prints(self, msg: str):
        self.print([ord(x) for x in msg])

    def set_cursor(self, position: int, line: int):
        line_start_addr = 0x00 if line == 0 else 0x40
        cmd = 0x80 | (line_start_addr + position)
        self._send_byte(cmd, self.RS_CMD)

    def create_char(pos: int, char_mask: List[int]):
        pass
