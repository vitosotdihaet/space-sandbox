'''
Libraries:
pygame + pygame_widgets - graphics
deque  - Planets' and Rocket's trails tracking
math   - smoothing function for zooming
time   - timer on screen
sys    - stopping the application
os     - resources for graphics 
'''


import pygame as pg
import pygame_widgets as pw

import math
import time
import sys
import os

from pygame_widgets.slider import Slider

from viewport import *
from on_screen_text import OnScreenText
from button import Button
from entities import *


# Show planet info on LMB
def change_showing_info(pos):
    global SHOWING_INFO
    to_show = None
    max_distance = INFO_DISTANCE
    for e in entities:
        if not isinstance(e, Rocket):
            current_distance = e.coordinates.distance_to(pos) - e.radius * SCALE / VIEWPORT.scaling
            if current_distance < max_distance:
                max_distance = current_distance
                to_show = e

    if to_show == None:
        return

    SHOWING_INFO = to_show


# Basically handles any input, related to pygame events (except Rocket controls)
def event_handler(event):
    global VIEWPORT
    global LAUNCH_FROM
    global LMB_MODE

    match event.type:
        case pg.QUIT:
            sys.exit()
        case pg.KEYDOWN:
            match event.key:
                case pg.K_ESCAPE:
                    sys.exit()
                case pg.K_SPACE:
                    if SPEED_SLIDER.value != 0:
                        SPEED_SLIDER.value = 0
                    else:
                        SPEED_SLIDER.value = BASE_SPEED
                case pg.K_RIGHTBRACKET:
                    SPEED_SLIDER.value = min(SPEED_SLIDER.value + SPEED_SLIDER.step, SPEED_SLIDER.max)
                case pg.K_LEFTBRACKET:
                    SPEED_SLIDER.value = max(SPEED_SLIDER.value - SPEED_SLIDER.step, SPEED_SLIDER.min)
                case pg.K_s:
                    VIEWPORT.shift = pg.Vector2(0, 0)
                    VIEWPORT.update(0, entities)
                case pg.K_l:
                    LMB_MODE = "l"
                case pg.K_i:
                    LMB_MODE = "i"
        case pg.MOUSEBUTTONDOWN:
            match event.button:
                case 1:  # LMB to start launching planet
                    match LMB_MODE:
                        case "l":
                            if event.pos[0] > 40:  # Check if mouse.pos is not near SPEED_SLIDER
                                LAUNCH_FROM = event.pos
                        case "i":
                            change_showing_info(event.pos)
                case 3:  # RMB to move view
                    VIEWPORT.shifting = True
                case 4:  # Scroll up to get closer to the Earth
                    VIEWPORT.update(-1, entities)
                case 5:  # Scroll down to get further from the Earth
                    VIEWPORT.update(1, entities)
        case pg.MOUSEBUTTONUP:
            match event.button:
                case 1:  # Release LMB to launch a planet
                    match LMB_MODE:
                        case "l":
                            if LAUNCH_FROM != None:
                                velocity_vector = (LAUNCH_FROM - pg.Vector2(event.pos)) * LAUNCH_VELOCITY
                                spawn_point = VIEWPORT.unscale(LAUNCH_FROM)
                                entities.append(PlanetDynamic(f'Spawned Planet №{len(entities) - 3}', spawn_point, velocity_vector,
                                                1500 * 1000, 4e22, (0, 230, 230), SCALE, SCREEN))
                                LAUNCH_FROM = None
                        case "i":
                            pass
                case 3:  # Release RMB to stop moving
                    VIEWPORT.shifting = False
        case pg.MOUSEMOTION:
            if VIEWPORT.shifting:
                VIEWPORT.shift += pg.Vector2(event.rel) * VIEWPORT.scaling
                VIEWPORT.update(0, entities)


pg.init()

# * Application options
CWD = os.path.dirname(__file__)
RES_PATH = os.path.join(CWD, "resources")
FONT_PATH = os.path.join(RES_PATH, "fonts")
IMG_PATH = os.path.join(RES_PATH, "images")

hp = "HPSimplified_Rg.ttf"
microgramma = "microgramma.ttf"

font = microgramma

FONTS = pg.font.Font((os.path.join(FONT_PATH, font)), 18)
FONTM = pg.font.Font((os.path.join(FONT_PATH, font)), 25)
FONTL = pg.font.Font((os.path.join(FONT_PATH, font)), 45)

ICON = pg.image.load(os.path.join(IMG_PATH, "icon.png"))
pg.display.set_icon(ICON)

CLOCK = pg.time.Clock()
TIMER = time.time()
elapsed_time = time.time() - TIMER
etime_ost = OnScreenText(str(elapsed_time), FONTM, (W/2, H - 65), SCREEN, color=(220, 220, 230))

real_elapsed_time = 0
last_elapsed = elapsed_time
real_etime_ost = OnScreenText('', FONTL, (W/2, H - 25), SCREEN, color=(240, 240, 250))

BG_COLOR = (0, 3, 10)

# * Interaction with application options
MOVE_MAP = {pg.K_UP:    pg.Vector2(0, -1),
            pg.K_DOWN:  pg.Vector2(0,  1),
            pg.K_LEFT:  pg.Vector2(-1, 0),
            pg.K_RIGHT: pg.Vector2(1,  0)}

LMB_MODE = "i"

INFO_DISTANCE = 50
SHOWING_INFO = None
info_ost = OnScreenText('', FONTS, (W/2, 25), SCREEN, color=(240, 240, 250))

LAUNCH_COLOR = (200, 200, 200)
LAUNCH_WIDTH = 1
LAUNCH_FROM = None
LAUNCH_VELOCITY = 15

# Max amount of points trail has
TRAILSIZE = 100

# * Physics
# to have real life time speed, you need to set BASE_SPEED to 2.378e-3
# the lower the speed, the more accurate the result, speed changes how often calculations happen
SPEED_CONST = 2.378e-3
BASE_SPEED = SPEED_CONST
SPEED = BASE_SPEED
SPEED_SLIDER = Slider(SCREEN, 20, 50, 8, H - 100,
                      min=BASE_SPEED, max=100, step=0.1, initial=BASE_SPEED,
                      vertical=True, colour=(255, 255, 255), handleColour=(255, 150, 30))

CALC_PER_FRAME = 5

SCALE = 1/1000000

ROCKET_ACCEL = 5

EARTH = PlanetStatic('Earth', (W/2, H/2), 6371 * 1000, 5.972e24, (100, 100, 255), SCALE, SCREEN)
MOON = PlanetDynamic('Moon', (W/2 - 405, H/2), (0, -1023), 1737 * 1000, 7.347e22, (200, 200, 200), SCALE, SCREEN)

STARTING_POSITION = (EARTH.coordinates[0] + EARTH.radius * SCALE + 100, EARTH.coordinates[1])
ROCKET = Rocket('Rocket', STARTING_POSITION, (0, 0), 50, 241000, (255, 100, 255), SCALE, SCREEN, 1170)

entities = [EARTH, MOON, ROCKET]

while True:
    CLOCK.tick(60)

    dt = CLOCK.tick(60) * SPEED_SLIDER.value / CALC_PER_FRAME

    events = pg.event.get()
    for event in events:
        event_handler(event)

    SCREEN_SURF.fill(BG_COLOR)
    SCREEN.blit(SCREEN_SURF, (0, 0))

    if dt != 0:
        pressed = pg.key.get_pressed()
        ROCKET.move([MOVE_MAP[key] for key in MOVE_MAP if pressed[key]])

        for _ in range(CALC_PER_FRAME):
            for e in entities:
                e.update(dt, entities)

    for e in entities:
        e.draw()
    ROCKET.draw()

    elapsed_time = time.time() - TIMER
    etime_ost.update(f'({str(elapsed_time).split(".")[0]}.{str(elapsed_time).split(".")[1][:3]})')
    etime_ost.blit()

    real_elapsed_time += ((elapsed_time - last_elapsed) * (SPEED_SLIDER.value / SPEED_CONST)) * int(dt != 0)
    last_elapsed = elapsed_time

    days = math.floor(real_elapsed_time / 86400)
    hours = math.floor(real_elapsed_time / 3600) % 24
    minutes = math.floor(real_elapsed_time / 60) % 60
    seconds = math.floor(real_elapsed_time % 60)

    real_etime_ost.update(f'{days}d {hours:0>2}h {minutes:0>2}m {seconds:0>2}s')
    real_etime_ost.blit()

    # TODO Add more information about entity (maybe double click changes what exactly is showing)
    if SHOWING_INFO != None:
        dist = int(ROCKET.position.distance_to(SHOWING_INFO.position)) - SHOWING_INFO.radius
        info_ost.update(f'Distance from {ROCKET.name} to {SHOWING_INFO.name}: {dist/1000:.1f}km')
    else:
        info_ost.update('')
    info_ost.blit()

    if LAUNCH_FROM is not None:
        pg.draw.line(SCREEN, LAUNCH_COLOR, LAUNCH_FROM, pg.mouse.get_pos(), LAUNCH_WIDTH)

    pw.update(events)
    pg.display.update()
