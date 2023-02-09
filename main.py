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
    def __init__(self, init_scaling=1, init_shift=pg.Vector2(0), delta_zoom=0.1):
        self.scaling = 1
        self.zoom_level = init_scaling
        self.delta_zoom = 0.1

        self.shift = init_shift
        self.shifting = False

    def scale(self, coord):
        center = pg.Vector2(W/2, H/2) - self.shift
        return (coord - center) / self.scaling + center + self.shift

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


# *                                    (m, kg, secs)
class Entity:  # * all the input parameters are real, except coordinates
    def __init__(self, name, coordinates, init_velocity, radius, mass, color, has_trail=True):
        self.name = name

        self.coordinates = pg.math.Vector2(coordinates)
        self.position = self.coordinates / SCALE
        self.radius = radius

        self.velocity = pg.Vector2(init_velocity)
        self.acceleration = pg.Vector2(0, 0)
        self.mass = mass

        self.color = color

        if has_trail and not isinstance(self, PlanetStatic):
            self.has_trail = True
            self.trail = deque([VIEWPORT.scale(self.coordinates), VIEWPORT.scale(self.coordinates)], maxlen=TRAILSIZE)
            self.trail_real = deque([self.position * SCALE, self.position * SCALE], maxlen=TRAILSIZE)
        else:
            self.has_trail = False

    def update(self):
        if isinstance(self, PlanetStatic):
            self.coordinates = VIEWPORT.scale(self.position * SCALE)
            return

        for e in entities:  # Iterate over all the entities to calculate physics
            if e == self:
                continue

            d = self.position - e.position
            if d.length() < self.radius + e.radius + INTERFERENCE_EPS:
                calculate_collision(self, e, d)
            else:
                self.acceleration = calculate_gravitational_force(self, e, d)

        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt  # type: ignore
        self.acceleration = pg.Vector2(0, 0)

        temp = self.position * SCALE
        self.coordinates = VIEWPORT.scale(temp)
        if self.has_trail:
            self.trail.append(self.coordinates)
            self.trail_real.append(temp)

    def draw(self):
        self.coordinates = VIEWPORT.scale(self.position * SCALE)
        if self.has_trail:
            pg.draw.lines(SCREEN, self.color, False, self.trail)
        pg.draw.circle(SCREEN, self.color, self.coordinates, max(
            MINIMAL_DRAWING_RADIUS, self.radius / VIEWPORT.scaling * SCALE))


class Rocket(Entity):
    def __init__(self, name, coordinates, init_velocity, radius, mass, color, thrust, has_trail=True):
        super().__init__(name, coordinates, init_velocity, radius, mass, color, has_trail)
        self.thrust = thrust

    def move(self, directions):
        # TODO fix
        if self.velocity.length() > MAX_VELOCITY:
            return

        self.acceleration = pg.Vector2(0, 0)

        for e in directions:
            self.acceleration += e

        dx = self.acceleration.x
        dy = self.acceleration.y
        if abs(dx) == abs(dy) == 1:  # Check for diagonal movement
            self.acceleration.x = 1/2**0.5 * dx
            self.acceleration.y = 1/2**0.5 * dy

        self.acceleration *= self.thrust


class Planet(Entity):
    def __init__(self, name, coordinates, init_velocity, radius, mass, color, has_trail=True):
        super().__init__(name, coordinates, init_velocity, radius, mass, color, has_trail)


class PlanetStatic(Planet):
    def __init__(self, name, coordinates, radius, mass, color, has_trail=True):
        super().__init__(name, coordinates, pg.Vector2(0, 0), radius, mass, color, has_trail)


class PlanetDynamic(Planet):
    def __init__(self, name, coordinates, init_velocity, radius, mass, color, has_trail=True):
        super().__init__(name, coordinates, init_velocity, radius, mass, color, has_trail)


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


# Checks if e1 collides with e2 and changes its parameters
def calculate_collision(e1, e2, d):
    if isinstance(e1, Rocket):
        e1.position = e2.position.copy() + d * (1 + COLLISION_EPS)
        if d.length() <= e1.radius + e2.radius:
            e1.velocity = e2.velocity.copy()


# Changes the acceleration of entity1
def calculate_gravitational_force(e1, e2, d):
    r = d.length()
    a = e1.acceleration
    f = d * (-G * e2.mass / (r * r * r))
    a += f

    return a


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
                    VIEWPORT.update(0)
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
                    VIEWPORT.update(-1)
                case 5:  # Scroll down to get further from the Earth
                    VIEWPORT.update(1)
        case pg.MOUSEBUTTONUP:
            match event.button:
                case 1:  # Release LMB to launch a planet
                    match LMB_MODE:
                        case "l":
                            if LAUNCH_FROM != None:
                                velocity_vector = (LAUNCH_FROM - pg.Vector2(event.pos)) * LAUNCH_VELOCITY
                                spawn_point = VIEWPORT.unscale(LAUNCH_FROM)
                                entities.append(PlanetDynamic(f'Spawned Planet №{len(entities) - 3}', spawn_point, velocity_vector,
                                                1500 * 1000, 4e22, (0, 230, 230)))
                                LAUNCH_FROM = None
                        case "i":
                            pass
                case 3:  # Release RMB to stop moving
                    VIEWPORT.shifting = False
        case pg.MOUSEMOTION:
            if VIEWPORT.shifting:
                VIEWPORT.shift += pg.Vector2(event.rel) * VIEWPORT.scaling
                VIEWPORT.update(0)


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

RESOLUTION = W, H = (1500, 900)
SCREEN = pg.display.set_mode(RESOLUTION)
SCREEN_SURF = pg.Surface(RESOLUTION)
ICON = pg.image.load(os.path.join(IMG_PATH, "icon.png"))
pg.display.set_icon(ICON)

CLOCK = pg.time.Clock()
TIMER = time.time()
elapsed_time = time.time() - TIMER
etime_ost = OnScreenText(str(elapsed_time), FONTM, (W/2, H - 65), color=(220, 220, 230))

real_elapsed_time = 0
last_elapsed = elapsed_time
real_etime_ost = OnScreenText('', FONTL, (W/2, H - 25), color=(240, 240, 250))

BG_COLOR = (0, 3, 10)

# * Interaction with application options
MOVE_MAP = {pg.K_UP:    pg.Vector2(0, -1),
            pg.K_DOWN:  pg.Vector2(0,  1),
            pg.K_LEFT:  pg.Vector2(-1, 0),
            pg.K_RIGHT: pg.Vector2(1,  0)}

LMB_MODE = "i"

INFO_DISTANCE = 50
SHOWING_INFO = None
info_ost = OnScreenText('', FONTS, (W/2, 25), color=(240, 240, 250))

INIT_SCALING = 1
INIT_SHIFT = pg.Vector2(0, 0)
VIEWPORT = Viewport(init_scaling=INIT_SCALING, init_shift=INIT_SHIFT)

MINIMAL_DRAWING_RADIUS = 1

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
G = 6.67e-11
INTERFERENCE_EPS = 1e3
COLLISION_EPS = 1e-10

ROCKET_ACCEL = 5
MAX_VELOCITY = 3e8

EARTH = PlanetStatic('Earth', (W/2, H/2), 6371 * 1000, 5.972e24, (100, 100, 255))
MOON = PlanetDynamic('Moon', (W/2 - 405, H/2), (0, -1023), 1737 * 1000, 7.347e22, (200, 200, 200))

STARTING_POSITION = (EARTH.coordinates[0] + EARTH.radius * SCALE + 100, EARTH.coordinates[1])
ROCKET = Rocket('Rocket', STARTING_POSITION, (0, 0), 50, 241000, (255, 100, 255), 1170)

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
                e.update()

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
