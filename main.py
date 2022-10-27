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
from collections import deque


class Viewport:
    def __init__(self):
        self.scaling = 1
        self.zoom_level = 1
        self.delta_zoom = 0.1

        self.shift = pg.Vector2(0, 0)
        self.shifting = False

    # TODO make scaling work to the center of screen or to a mouse
    def scale(self, coord, mouse_pos=pg.Vector2(0, 0)):
        return pg.Vector2((coord[0] - W/2 + mouse_pos.x) / self.scaling + W/2, (coord[1] - H/2 + mouse_pos.y) / self.scaling + H/2) + self.shift

    def unscale(self, coord):
        coord = coord - self.shift
        return pg.Vector2((coord[0] - W/2) * self.scaling + W/2, (coord[1] - H/2) * self.scaling + H/2)

    def update(self, zoom):
        self.zoom_level += zoom * self.delta_zoom

        if self.zoom_level < 1:
            self.scaling = 1 / (1 + math.exp(-self.zoom_level))
        else:
            self.scaling = self.zoom_level * self.zoom_level

        for e in entities:
            if e.has_trail:
                for i in range(len(e.trail)):
                    e.trail[i] = self.scale(e.trail_real[i])


# *                                    (m, kg, secs)                      (rocket, planet dynamic, planet static)
class Entity:  # * all the input parameters are real, except coordinates; valid types are: "R", "PD", "PS"
    def __init__(self, coordinates, init_velocity, radius, mass, entity_type, color, has_trail=True):
        self.coordinates = pg.math.Vector2(coordinates)
        self.position = self.coordinates / SCALE
        self.radius = radius

        self.velocity = pg.Vector2(init_velocity)
        self.acceleration = pg.Vector2(0, 0)
        self.mass = mass

        self.type = entity_type

        self.color = color

        if has_trail and entity_type != "PS":
            self.has_trail = True
            self.trail = deque([VIEWPORT.scale(self.coordinates), VIEWPORT.scale(self.coordinates)], maxlen=TRAILSIZE)
            self.trail_real = deque([self.position * SCALE, self.position * SCALE], maxlen=TRAILSIZE)
        else:
            self.has_trail = False

    def move(self, directions):
        self.acceleration = pg.Vector2(0, 0)
        for e in directions:
            self.acceleration += e

        dx = self.acceleration.x
        dy = self.acceleration.y
        if abs(dx) == abs(dy) == 1:  # Check for diagonal movement
            self.acceleration.x = 1/2**0.5 * dx
            self.acceleration.y = 1/2**0.5 * dy

        self.acceleration *= MAX_ROCKET_ACCEL
        self.update()

    def update(self):
        if self.type == "PS":
            self.coordinates = VIEWPORT.scale(self.position * SCALE)
            return

        for e in entities:  # Iterate over all the entities to calculate physics
            if e == self:
                continue

            d = self.position - e.position
            r = d.length()

            # TODO? change biggest planet mass, radius, etc. if two collided
            if r <= self.radius + e.radius:
                if self.type == 'R' or e.type == 'R':
                    self.velocity = pg.Vector2(0, 0)
                    self.position = e.position + d
                else:
                    if self.mass < e.mass:
                        self.velocity = pg.Vector2(0, 0)
                        self.position = e.position
                    else:
                        e.velocity = pg.Vector2(0, 0)
                        e.position = self.position
            else:
                f = d * (-G * e.mass / (r * r * r))
                self.acceleration += f

        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt
        self.acceleration = pg.Vector2(0, 0)

        self.coordinates = VIEWPORT.scale(self.position * SCALE)
        if self.has_trail:
            self.trail.append(self.coordinates)
            self.trail_real.append(self.position * SCALE)

    def draw(self):
        if self.has_trail:
            pg.draw.lines(SCREEN, self.color, False, self.trail)
        pg.draw.circle(SCREEN, self.color, self.coordinates, self.radius / VIEWPORT.scaling * SCALE)


class OnScreenText:
    def __init__(self, text, fontsize, coords, antial=True, center=True, color=(0, 0, 0)):
        self.text = text
        self.fontsize = fontsize
        self.color = color
        self.antial = antial
        self.coords = coords
        self.center = center

        self.rendered_text = self.fontsize.render(self.text, self.antial, self.color)
        if self.center == True:
            self.rect = self.rendered_text.get_rect(center=self.coords)
        else:
            self.rect = coords

    def blit(self):
        SCREEN.blit(self.rendered_text, self.rect)

    def update(self, text):
        self.text = text
        self.rendered_text = self.fontsize.render(self.text, self.antial, self.color)
        if self.center == True:
            self.rect = self.rendered_text.get_rect(center=self.coords)
        else:
            self.rect = self.coords


class Button:
    def __init__(self, color, x, y, width, height, text=""):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self, outline=None):
        if outline:
            pg.draw.rect(SCREEN, outline, (self.x + 5, self.y + 5, self.width, self.height), 0)
        pg.draw.rect(SCREEN, self.color, (self.x, self.y, self.width, self.height), 0)

        if self.text != "":
            lines = self.text.split("\n")
            for i, line in enumerate(lines, start=1):
                text = FONTS.render(line, True, (255, 255, 255))

                SCREEN.blit(
                    text,
                    (self.x + (self.width/2 - text.get_width()/2),
                     self.y + (self.height/(len(lines) + 1) * i - text.get_height()/2))
                )

    def is_over(self, pos):
        if self.x < pos[0] < self.x + self.width:
            if self.y < pos[1] < self.y + self.height:
                return True
        return False


def event_handler(event):
    global VIEWPORT
    global LAUNCH_FROM

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
        case pg.MOUSEBUTTONDOWN:
            match event.button:
                case 1:  # LMB to start launching planet
                    if event.pos[0] > 40:  # Check if mouse.pos is not near SPEED_SLIDER
                        LAUNCH_FROM = event.pos
                case 3:  # RMB to move view
                    VIEWPORT.shifting = True
                case 4:  # Scroll up to get closer to the Earth
                    VIEWPORT.update(-1)
                case 5:  # Scroll down to get further from the Earth
                    VIEWPORT.update(1)
        case pg.MOUSEBUTTONUP:
            match event.button:
                case 1:  # Release LMB to launch a planet
                    if LAUNCH_FROM != None:
                        velocity_vector = (LAUNCH_FROM - pg.Vector2(event.pos)) * LAUNCH_VELOCITY
                        spawn_point = VIEWPORT.unscale(LAUNCH_FROM)
                        entities.append(Entity(spawn_point, velocity_vector, 1500 * 1000, 4e22, "PD", (0, 230, 230)))
                        LAUNCH_FROM = None
                case 3:  # Release RMB to stop moving
                    VIEWPORT.shifting = False
        case pg.MOUSEMOTION:
            if VIEWPORT.shifting:
                VIEWPORT.shift += event.rel
                VIEWPORT.update(0)


pg.init()

CWD = os.path.dirname(__file__)
RES_PATH = os.path.join(CWD, "resources")
FONT_PATH = os.path.join(RES_PATH, "fonts")
IMG_PATH = os.path.join(RES_PATH, "images")

hp = "HPSimplified_Rg.ttf"
microgramma = "microgramma.ttf"

font = microgramma

FONTS = pg.font.Font((os.path.join(FONT_PATH, font)), 40)
FONTM = pg.font.Font((os.path.join(FONT_PATH, font)), 90)
FONTL = pg.font.Font((os.path.join(FONT_PATH, font)), 120)

RESOLUTION = W, H = (1500, 900)
SCREEN = pg.display.set_mode(RESOLUTION)
SCREEN_SURF = pg.Surface(RESOLUTION)
ICON = pg.image.load(os.path.join(IMG_PATH, "icon.png"))
pg.display.set_icon(ICON)

VIEWPORT = Viewport()

LAUNCH_COLOR = (200, 200, 200)
LAUNCH_WIDTH = 1
LAUNCH_FROM = None
LAUNCH_VELOCITY = 15

CLOCK = pg.time.Clock()
TIMER = time.time()
elapsed_time = time.time() - TIMER
etime_ost = OnScreenText(str(elapsed_time), FONTS, (W/2, H - 25), color=(240, 240, 250))

# whole earth orbit in 156 seconds by moon if SPEED = 36
# to have real life time speed, you need to set BASE_SPEED to 7.395e-7 => 27d 7h 43m (5,859,780 seconds)
# the lower the speed, the more accurate is result, speed change, how often calculations happen
BASE_SPEED = 7.395e-7
SPEED = BASE_SPEED
SPEED_SLIDER = Slider(SCREEN, 20, 50, 8, H - 100, min=1, max=400, step=0.1, initial=BASE_SPEED,
                      vertical=True, colour=(255, 255, 255), handleColour=(255, 150, 30))

SCALE = 1/1000000
G = 6.67e-11
MAX_ROCKET_ACCEL = 39240 / 3600 / 100

TRAILSIZE = 100
BG_COLOR = (0, 10, 25)

EARTH = Entity((W/2, H/2), (0, 0), 6371 * 1000, 5.972e24, "PD", (100, 100, 255))
MOON = Entity((W/2 - 405, H/2), (0, -1023), 1737 * 1000, 7.347e22, "PD", (200, 200, 200))

STARTING_POSITION = (EARTH.coordinates[0] + EARTH.radius * SCALE + 100, EARTH.coordinates[1])
ROCKET = Entity(STARTING_POSITION, (0, 0), 100 * 1000, 2000, "R", (255, 100, 255))

MOVE_MAP = {pg.K_UP:    pg.Vector2(0, -1),
            pg.K_DOWN:  pg.Vector2(0,  1),
            pg.K_LEFT:  pg.Vector2(-1,  0),
            pg.K_RIGHT: pg.Vector2(1,  0)}

entities = [EARTH, MOON, ROCKET]

while True:
    CLOCK.tick(60)

    dt = CLOCK.tick(60) * SPEED_SLIDER.value

    events = pg.event.get()
    for event in events:
        event_handler(event)

    pressed = pg.key.get_pressed()
    ROCKET.move([MOVE_MAP[key] for key in MOVE_MAP if pressed[key]])

    SCREEN.fill(BG_COLOR)
    SCREEN.blit(SCREEN_SURF, (0, 0))

    for e in entities:
        e.update()
        e.draw()
    # so rocket stays on top all the time
    ROCKET.draw()

    elapsed_time = time.time() - TIMER
    etime_ost.update(f'{str(elapsed_time).split(".")[0]}.{str(elapsed_time).split(".")[1][:3]}')
    etime_ost.blit()

    if LAUNCH_FROM is not None:
        pg.draw.line(SCREEN, LAUNCH_COLOR, LAUNCH_FROM, pg.mouse.get_pos(), LAUNCH_WIDTH)

    pw.update(events)
    pg.display.update()
