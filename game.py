
import time
from datetime import timedelta, datetime
from random import randint
from typing import List

from pyA20.gpio import gpio, port

from lcd16x2 import LCD


PIN_BUTTON = port.PA3
PIN_AUTOPLAY = port.PA1

SPRITE_RUN1 = 1
SPRITE_RUN2 = 2
SPRITE_JUMP = 3
SPRITE_JUMP_UPPER = ord('.')  # Use the '.' character for the head
SPRITE_JUMP_LOWER = 4
SPRITE_TERRAIN_EMPTY = ord(' ')  # User the ' ' character
SPRITE_TERRAIN_SOLID = 5
SPRITE_TERRAIN_SOLID_RIGHT = 6
SPRITE_TERRAIN_SOLID_LEFT = 7

HERO_HORIZONTAL_POSITION  = 1  # Horizontal position of hero on screen

TERRAIN_WIDTH = 16
TERRAIN_EMPTY = 0
TERRAIN_LOWER_BLOCK = 1
TERRAIN_UPPER_BLOCK = 2

HERO_POSITION_OFF = 0          # Hero is invisible
HERO_POSITION_RUN_LOWER_1 = 1  # Hero is running on lower row (pose 1)
HERO_POSITION_RUN_LOWER_2 = 2  #                              (pose 2)

HERO_POSITION_JUMP_1 = 3   # Starting a jump
HERO_POSITION_JUMP_2 = 4   # Half-way up
HERO_POSITION_JUMP_3 = 5   # Jump is on upper row
HERO_POSITION_JUMP_4 = 6   # Jump is on upper row
HERO_POSITION_JUMP_5 = 7   # Jump is on upper row
HERO_POSITION_JUMP_6 = 8   # Jump is on upper row
HERO_POSITION_JUMP_7 = 9   # Half-way down
HERO_POSITION_JUMP_8 = 10  # About to land

HERO_POSITION_RUN_UPPER_1 = 11  # Hero is running on upper row (pose 1)
HERO_POSITION_RUN_UPPER_2 = 12  #                              (pose 2)


lcd = LCD(rs=port.PA11, e=port.PA12, d_pins=[
    port.PA10, port.PA13, port.PA2, port.PA18, port.PA19, port.PA7, port.PG7, port.PG6
])

terrain_upper: List[int] = [SPRITE_TERRAIN_EMPTY for _ in range(TERRAIN_WIDTH + 1)]
terrain_lower: List[int] = [SPRITE_TERRAIN_EMPTY for _ in range(TERRAIN_WIDTH + 1)]


def initialize_graphics():
    graphics = [
        [   # Run position 1
            0b01100,
            0b01100,
            0b00000,
            0b01110,
            0b11100,
            0b01100,
            0b11010,
            0b10011,
        ],
        [   # Run position 2
            0b01100,
            0b01100,
            0b00000,
            0b01100,
            0b01100,
            0b01100,
            0b01100,
            0b01110,
        ],
        [   # Jump
            0b01100,
            0b01100,
            0b00000,
            0b11110,
            0b01101,
            0b11111,
            0b10000,
            0b00000,
        ],
        [   # Jump lower
            0b11110,
            0b01101,
            0b11111,
            0b10000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
        ],
        [   # Ground
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
        ],
        [   # Ground right
            0b00011,
            0b00011,
            0b00011,
            0b00011,
            0b00011,
            0b00011,
            0b00011,
            0b00011,
        ],
        [   # Ground left
            0b11000,
            0b11000,
            0b11000,
            0b11000,
            0b11000,
            0b11000,
            0b11000,
            0b11000,
        ],
    ]
    for i in range(7):
        lcd.create_char(i + 1, graphics[i])

    global terrain_upper, terrain_lower
    terrain_upper = [SPRITE_TERRAIN_EMPTY for _ in range(TERRAIN_WIDTH + 1)]
    terrain_lower = [SPRITE_TERRAIN_EMPTY for _ in range(TERRAIN_WIDTH + 1)]


def advance_terrain(terrain: List[int], new_terrain: int):
    for i in range(TERRAIN_WIDTH):
        current = terrain[i]
        next = new_terrain if (i == TERRAIN_WIDTH - 1) else terrain[i + 1]
        if current == SPRITE_TERRAIN_EMPTY:
            terrain[i] = SPRITE_TERRAIN_SOLID_RIGHT if (next == SPRITE_TERRAIN_SOLID) else SPRITE_TERRAIN_EMPTY
        elif current == SPRITE_TERRAIN_SOLID:
            terrain[i] = SPRITE_TERRAIN_SOLID_LEFT if (next == SPRITE_TERRAIN_EMPTY) else SPRITE_TERRAIN_SOLID
        elif current == SPRITE_TERRAIN_SOLID_RIGHT:
            terrain[i] = SPRITE_TERRAIN_SOLID
        elif current == SPRITE_TERRAIN_SOLID_LEFT:
            terrain[i] = SPRITE_TERRAIN_EMPTY


def draw_hero(position: int, terrain_upper: List[int], terrainLower: List[int], score: int) -> bool:
    collide = False
    upper_save = terrain_upper[HERO_HORIZONTAL_POSITION]
    lower_save = terrain_lower[HERO_HORIZONTAL_POSITION]
    if position == HERO_POSITION_OFF:
        upper = SPRITE_TERRAIN_EMPTY
        lower = SPRITE_TERRAIN_EMPTY
    elif position == HERO_POSITION_RUN_LOWER_1:
        upper = SPRITE_TERRAIN_EMPTY
        lower = SPRITE_RUN1
    elif position == HERO_POSITION_RUN_LOWER_2:
        upper = SPRITE_TERRAIN_EMPTY
        lower = SPRITE_RUN2
    elif position in {HERO_POSITION_JUMP_1,
                      HERO_POSITION_JUMP_8}:
        upper = SPRITE_TERRAIN_EMPTY
        lower = SPRITE_JUMP
    elif position in {HERO_POSITION_JUMP_2,
                      HERO_POSITION_JUMP_7}:
        upper = SPRITE_JUMP_UPPER
        lower = SPRITE_JUMP_LOWER
    elif position in {HERO_POSITION_JUMP_3,
                      HERO_POSITION_JUMP_4,
                      HERO_POSITION_JUMP_5,
                      HERO_POSITION_JUMP_6}:
        upper = SPRITE_JUMP
        lower = SPRITE_TERRAIN_EMPTY
    elif position == HERO_POSITION_RUN_UPPER_1:
        upper = SPRITE_RUN1
        lower = SPRITE_TERRAIN_EMPTY
    elif position == HERO_POSITION_RUN_UPPER_2:
        upper = SPRITE_RUN2
        lower = SPRITE_TERRAIN_EMPTY

    if (upper != ord(' ')):
        terrain_upper[HERO_HORIZONTAL_POSITION] = upper
        collide = not (upper_save == SPRITE_TERRAIN_EMPTY)
    if (lower != ord(' ')):
        terrain_lower[HERO_HORIZONTAL_POSITION] = lower
        collide |= not (lower_save == SPRITE_TERRAIN_EMPTY)

    digits = len(str(score))

    # Draw the scene
    # import pdb
    # pdb.set_trace()
    terrain_upper[TERRAIN_WIDTH] = 0
    terrain_lower[TERRAIN_WIDTH] = 0
    temp = terrain_upper[16 - digits]
    terrain_upper[16 - digits] = 0
    lcd.set_cursor(0, 0)
    lcd.print(terrain_upper)
    terrain_upper[16 - digits] = temp
    lcd.set_cursor(0, 1)
    lcd.print(terrain_lower)

    lcd.set_cursor(16 - digits, 0)
    lcd.prints(str(score))

    terrain_upper[HERO_HORIZONTAL_POSITION] = upper_save
    terrain_lower[HERO_HORIZONTAL_POSITION] = lower_save

    return collide


last_pressed = datetime.now()

def button_pushed(with_delay=False) -> bool:
    global last_pressed
    btn_pressed = gpio.input(PIN_BUTTON)
    if with_delay and btn_pressed:
        last_pressed = datetime.now()
        return btn_pressed
    if (datetime.now() - last_pressed).seconds < 1:
        return False
    return btn_pressed
    


def setup():
    gpio.setcfg(PIN_BUTTON, gpio.INPUT)
    gpio.pullup(PIN_BUTTON, gpio.PULLDOWN)
    gpio.setcfg(PIN_AUTOPLAY, gpio.OUTPUT)

    initialize_graphics()


hero_pos = HERO_POSITION_RUN_LOWER_1
new_terrain_type = TERRAIN_EMPTY
new_terrain_duration = 1
playing = False
blink = False
distance = 0

def loop():
    global hero_pos, new_terrain_type, new_terrain_duration, playing, blink, distance

    if not playing:
        draw_hero(HERO_POSITION_OFF if blink else hero_pos,
                  terrain_upper, terrain_lower, distance >> 3)
        if blink:
            lcd.set_cursor(0, 0)
            lcd.prints("Press Start")
        time.sleep(0.25)
        blink = not blink
        if button_pushed(with_delay=True):
            initialize_graphics()
            hero_pos = HERO_POSITION_RUN_LOWER_1
            playing = True
            distance = 0
        return None

    advance_terrain(terrain_lower, SPRITE_TERRAIN_SOLID if new_terrain_type == TERRAIN_LOWER_BLOCK else SPRITE_TERRAIN_EMPTY)
    advance_terrain(terrain_upper, SPRITE_TERRAIN_SOLID if new_terrain_type == TERRAIN_UPPER_BLOCK else SPRITE_TERRAIN_EMPTY)

    new_terrain_duration -= 1
    if new_terrain_duration == 0:
        if new_terrain_type == TERRAIN_EMPTY:
            new_terrain_type = TERRAIN_UPPER_BLOCK if randint(0, 3) == 0 else TERRAIN_LOWER_BLOCK
            new_terrain_duration = 2 + randint(0, 10)
        else:
            new_terrain_type = TERRAIN_EMPTY
            new_terrain_duration = 10 + randint(0, 10)

    if button_pushed():
        if (hero_pos <= HERO_POSITION_RUN_LOWER_2):
            hero_pos = HERO_POSITION_JUMP_1

    if draw_hero(hero_pos, terrain_upper, terrain_lower, distance >> 3):
        playing = False
    else:
        if hero_pos == HERO_POSITION_RUN_LOWER_2 or hero_pos == HERO_POSITION_JUMP_8:
            hero_pos = HERO_POSITION_RUN_LOWER_1
        elif (hero_pos >= HERO_POSITION_JUMP_3 and hero_pos <= HERO_POSITION_JUMP_5) and \
                terrain_lower[HERO_HORIZONTAL_POSITION] != SPRITE_TERRAIN_EMPTY:
            hero_pos = HERO_POSITION_RUN_UPPER_1
        elif (hero_pos >= HERO_POSITION_RUN_UPPER_1 and terrain_lower[HERO_HORIZONTAL_POSITION] == SPRITE_TERRAIN_EMPTY):
            hero_pos = HERO_POSITION_JUMP_5
        elif hero_pos == HERO_POSITION_RUN_UPPER_2:
            hero_pos = HERO_POSITION_RUN_UPPER_1
        else:
            hero_pos += 1
        distance += 1

        gpio.output(PIN_AUTOPLAY, not terrain_lower[HERO_HORIZONTAL_POSITION + 2] == SPRITE_TERRAIN_EMPTY)
    time.sleep(0.1)


if __name__ == '__main__':
    setup()
    while True:
        loop()
