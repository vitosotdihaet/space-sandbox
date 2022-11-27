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
        self.zoom_level = INIT_SCALING
        self.delta_zoom = 0.1

        self.shift = INIT_SHIFT
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

        if has_trail and type(self) != PlanetStatic:
            self.has_trail = True
            self.trail = deque([VIEWPORT.scale(self.coordinates), VIEWPORT.scale(self.coordinates)], maxlen=TRAILSIZE)
            self.trail_real = deque([self.position * SCALE, self.position * SCALE], maxlen=TRAILSIZE)
        else:
            self.has_trail = False

    def update(self):
        global current_acceleration
        if type(self) == PlanetStatic:
            self.coordinates = VIEWPORT.scale(self.position * SCALE)
            return

        for e in entities:  # Iterate over all the entities to calculate physics
            if e == self:
                continue

            d = self.position - e.position
            if d.length() < self.radius + e.radius + EPS:
                calculate_collision(self, e, d)
            else:
                self.acceleration = calculate_gravitational_force(self, e, d)

        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt  # type: ignore
        current_acceleration += self.acceleration
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
    def __init__(self, name, coordinates, init_velocity, radius, color, stage_masses, stage_fuel, stage_engine_thrust, has_trail=True):
        super().__init__(name, coordinates, init_velocity, radius, stage_masses[0], color, has_trail)
        self.stage_masses = stage_masses
        self.stage_fuel = stage_fuel
        self.stage_engine_thrust = stage_engine_thrust
        self.stage = 0

    def move(self, directions):
        # TODO fix
        if self.velocity.length() > MAX_VELOCITY:
            return

        self.acceleration = pg.Vector2(0, 0)
        
        if self.stage_fuel[self.stage] > 0:
            for e in directions:
                self.acceleration += e
        
            dx = self.acceleration.x
            dy = self.acceleration.y
            if abs(dx) == abs(dy) == 1:  # Check for diagonal movement
                self.acceleration.x = 1/2**0.5 * dx
                self.acceleration.y = 1/2**0.5 * dy
        
            self.acceleration *= (self.stage_engine_thrust[self.stage] - self.mass) / 50000
        
        if self.acceleration != pg.Vector2(0, 0):
            temp = min(1000, self.stage_fuel[self.stage] + 1) * dt
            self.mass = max(0, self.mass - temp)
            self.stage_fuel[self.stage] = max(0, self.stage_fuel[self.stage] - temp)
            self.stage_masses[self.stage] = max(0, self.stage_masses[self.stage] - temp)
            # Uncomment to change stages when fuel is 0
            # if self.stage_fuel[self.stage] <= 0:
            #     self.change_stage()

    def change_stage(self):
        self.stage = min(self.stage + 1, len(self.stage_masses) - 1)
        self.mass = self.stage_masses[self.stage]


class Planet(Entity):
    def __init__(self, name, coordinates, init_velocity, radius, mass, color, has_trail=True):
        super().__init__(name, coordinates, init_velocity, radius, mass, color, has_trail)


class PlanetStatic(Planet):
    def __init__(self, name, coordinates, radius, mass, color, has_trail=True):
        super().__init__(name, coordinates, pg.Vector2(0, 0), radius, mass, color, has_trail)


class OnScreenText:
    # constants for anchoring onscreentext
    TL = (-1, -1)
    TC = (0, -1)
    TR = (1, -1)

    ML = (-1, 0)
    MC = (0, 0)
    MR = (1, 0)

    BL = (-1, 1)
    BC = (0, 1)
    BR = (1, 1)

    def __init__(self, text, fontsize, coords, antial=True, anchor=MC, color=(0, 0, 0)):
        self.text = text
        self.fontsize = fontsize
        self.color = color
        self.antial = antial
        self.coords = coords
        self.anchor = anchor

        self.rendered_text = self.fontsize.render(self.text, self.antial, self.color)
        self.rect = self.rendered_text.get_rect(center=self.coords)
        self.rect.x -= self.anchor[0] * self.rect.width//2
        self.rect.y -= self.anchor[1] * self.rect.height//2

    def blit(self):
        SCREEN.blit(self.rendered_text, self.rect)

    def update(self, text):
        self.text = text
        self.rendered_text = self.fontsize.render(self.text, self.antial, self.color)
        self.rect = self.rendered_text.get_rect(center=self.coords)
        self.rect.x -= self.anchor[0] * self.rect.width//2
        self.rect.y -= self.anchor[1] * self.rect.height//2


# Checks if e1 collides with e2 and changes its parameters
def calculate_collision(e1, e2, d):
    if type(e1) == Rocket:
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
def change_showing_info():
    global SHOWING_INFO
    to_show = None
    max_distance = INFO_DISTANCE
    for e in entities:
        if type(e) != Rocket:
            current_distance = e.coordinates.distance_to(event.pos) - e.radius * SCALE / VIEWPORT.scaling
            if current_distance < max_distance:
                max_distance = current_distance
                to_show = e

    if to_show == None:
        return
    elif to_show == SHOWING_INFO:
        to_show = None

    SHOWING_INFO = to_show


# Basically handles any input, related to pygame events (except Rocket controls)
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
                case pg.K_RIGHTBRACKET:
                    SPEED_SLIDER.value = min(SPEED_SLIDER.value + SPEED_SLIDER.step * 2, SPEED_SLIDER.max)
                case pg.K_LEFTBRACKET:
                    SPEED_SLIDER.value = max(SPEED_SLIDER.value - SPEED_SLIDER.step * 2, SPEED_SLIDER.min)
                case pg.K_s:
                    VIEWPORT.shift = pg.Vector2(0, 0)
                    VIEWPORT.update(0)
                case pg.K_n:
                    if SAVE_MOVES:
                        save_to.write(f'{real_elapsed_time:.4f} N_\n{real_elapsed_time:.4f} []_\n')
                    ROCKET.change_stage()
        case pg.MOUSEBUTTONDOWN:
            match event.button:
                case 1:  # LMB to view info of the nearest entity
                    change_showing_info()
                case 3:  # RMB to move view
                    VIEWPORT.shifting = True
                case 4:  # Scroll up to get closer to the Earth
                    VIEWPORT.update(-1)
                case 5:  # Scroll down to get further from the Earth
                    VIEWPORT.update(1)
        case pg.MOUSEBUTTONUP:
            match event.button:
                case 3:  # Release RMB to stop moving
                    VIEWPORT.shifting = False
        case pg.MOUSEMOTION:
            if VIEWPORT.shifting:
                VIEWPORT.shift += pg.Vector2(event.rel) * VIEWPORT.scaling
                VIEWPORT.update(0)


def draw_arrow(pos, vec, length, color=(255, 255, 255), width=5):
    l = vec.length()
    if l > VELOCITY_SHOW_EPS:
        end = pos + (vec / vec.length()) * length
    else:
        end = pos
    seq = [pos, end]
    pg.draw.polygon(SCREEN, color, seq, width)


def draw_that_thing(rect, vec, bg_color=(240, 240, 240), fg_color=(20, 20, 20), arrow_color=(255, 255, 255)):
    nr = pg.Rect(rect.left + 5, rect.top + 5, rect.width - 10, rect.height - 10)
    pg.draw.rect(SCREEN, bg_color, rect, border_radius=50)
    pg.draw.rect(SCREEN, fg_color, nr, border_radius=45)

    center = pg.Vector2(rect.x + rect.width / 2, rect.y + rect.height / 2)
    arrow_length = (nr.width / 2) * 9 / 10
    
    draw_arrow(center, vec, arrow_length, arrow_color, ARROW_WIDTH)


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

RESOLUTION = W, H = (1600, 900)
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

INFO_DISTANCE = 50
SHOWING_INFO = None
info_ost = OnScreenText('', FONTS, (W/2, 25), color=(240, 240, 250))

stage_ost = OnScreenText('', FONTS, (W - 15, 25), anchor=OnScreenText.MR, color=(240, 240, 30))

# x, y, width, height
COMPASS_COORDS = (W - 200, H - 200, 190, 190)

VELOCITY_COLOR = (255, 100, 255)
ACCELERATION_COLOR = (100, 230, 30)

fuel_ost = OnScreenText('FUEL:', FONTS, (W - 200, H - 330), anchor=OnScreenText.BL, color=(240, 240, 250))
fuel_at_stage_ost = OnScreenText('', FONTS, (W - 15, H - 310), anchor=OnScreenText.BR, color=(240, 240, 250))

acceleration_ost = OnScreenText('ACCELERATION:', FONTS, (W - 200, H - 280), anchor=OnScreenText.BL, color=ACCELERATION_COLOR)
rocket_acceleration_ost = OnScreenText('', FONTS, (W - 15, H - 260), anchor=OnScreenText.BR, color=ACCELERATION_COLOR)

velocity_ost = OnScreenText('VELOCITY:', FONTS, (W - 200, H - 230), anchor=OnScreenText.BL, color=VELOCITY_COLOR)
rocket_velocity_ost = OnScreenText('', FONTS, (W - 10, H - 210), anchor=OnScreenText.BR, color=VELOCITY_COLOR)

ARROW_WIDTH = 5
VELOCITY_SHOW_EPS = 0.001

INIT_SCALING = -7
INIT_SHIFT = pg.Vector2(6.43, 0)
VIEWPORT = Viewport()

MINIMAL_DRAWING_RADIUS = 1

# Max amount of points trail has
TRAILSIZE = 100

# True if you want to save your flight
SAVE_MOVES = True
save_to = open('main.py')
if SAVE_MOVES:
    save_to = open(f'flight_{time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())}.txt', 'w')
    save_to.write('0 []_\n')
last_moves = []

# True if you want to read a flight
READ_MOVES = False
read_from = open('main.py')
read_moves = []
read_off = 0
if READ_MOVES:  # Enter name of flight here
    read_from = open('flight_2022-11-27_15-06-27.txt')
    read_moves = read_from.readlines()

# * Physics
# to have real life time speed, you need to set BASE_SPEED to 2.378e-3
# the lower the speed, the more accurate the result, (speed determines how often calculations happen)
SPEED_CONST = 2.378e-3
BASE_SPEED = SPEED_CONST
SPEED_SLIDER = Slider(SCREEN, 20, 50, 8, H - 100,
                      min=BASE_SPEED, max=1 * 10, step=0.01 * 10, initial=BASE_SPEED,
                      vertical=True, colour=(255, 255, 255), handleColour=(255, 150, 30))

CALC_PER_FRAME = 5

SCALE = 1/1000000
G = 6.67e-11
EPS = 1e2
COLLISION_EPS = 1e-10

MAX_VELOCITY = 3e8

EARTH = PlanetStatic('Earth', (W/2, H/2), 6371 * 1000, 5.972e24, (80, 80, 230))
MOON = PlanetStatic('Moon', (W/2 + 405, H/2), 1737 * 1000, 7.347e22, (200, 200, 200))

ROCKET_RADIUS = 50
STARTING_POSITION = (EARTH.coordinates[0] - (EARTH.radius * SCALE + ROCKET_RADIUS * SCALE), EARTH.coordinates[1])
# masses including fuel, payload, etc.
STAGE_MASSES = [241_000, 65_000, 15_000]
# fuel mass in kg
STAGE_FUEL = [171_800, 32_600, 12_375]
# thrust performance in vacuum without additional mass in newtons
STAGE_ENGINES_SPEED = [2_961_600, 789_100, 161_170]

ROCKET = Rocket('Rocket', STARTING_POSITION, (0, 0), ROCKET_RADIUS,
                (255, 100, 255), STAGE_MASSES, STAGE_FUEL, STAGE_ENGINES_SPEED)

entities = [EARTH, MOON, ROCKET]

VIEWPORT.update(0)

while True:
    CLOCK.tick(60)

    dt = CLOCK.tick(60) * SPEED_SLIDER.value / CALC_PER_FRAME

    events = pg.event.get()
    for event in events:
        event_handler(event)

    SCREEN_SURF.fill(BG_COLOR)
    SCREEN.blit(SCREEN_SURF, (0, 0))

    current_acceleration = pg.Vector2(0, 0)
    if dt != 0:
        for _ in range(CALC_PER_FRAME):
            ROCKET.update()
            pressed = []

            if READ_MOVES:
                curr_read = read_moves[read_off].replace('\n', '').split(maxsplit=1)

                next_read_off = min(read_off + 1, len(read_moves) - 1)
                next_t = float(read_moves[next_read_off].replace('\n', '').split(maxsplit=1)[0])

                if next_t < real_elapsed_time:
                    read_off = next_read_off
                list_of_coords = curr_read[1].split('_')[:-1]

                for s in list_of_coords:
                    s = s.replace('[', '').replace(']', '').replace(',', '')
                    if s == 'N':
                        ROCKET.change_stage()
                    elif s != '':
                        v = pg.Vector2(int(s[:2]), int(s[-2:]))
                        pressed.append(v)
                moves = pressed
            else:
                pressed = pg.key.get_pressed()
                moves = [MOVE_MAP[key] for key in MOVE_MAP if pressed[key]]

            if SAVE_MOVES:
                if last_moves != moves:
                    save_to.write(f'{real_elapsed_time:.4f} ')

                    if len(moves) == 0:
                        save_to.write('[]_')

                    for key in moves:
                        save_to.write(f'{key}_')

                    save_to.write('\n')
                last_moves = moves.copy()

            ROCKET.move(moves)

    current_acceleration /= CALC_PER_FRAME

    for e in entities:
        e.draw()

    elapsed_time = time.time() - TIMER
    etime_ost.update(f'({elapsed_time:.3f})')
    etime_ost.blit()

    real_elapsed_time += ((elapsed_time - last_elapsed) * (SPEED_SLIDER.value / SPEED_CONST)) * int(dt != 0)
    last_elapsed = elapsed_time

    days = math.floor(real_elapsed_time / 86400)
    hours = math.floor(real_elapsed_time / 3600) % 24
    minutes = math.floor(real_elapsed_time / 60) % 60
    seconds = math.floor(real_elapsed_time % 60)

    real_etime_ost.update(f'{days}d {hours:0>2}h {minutes:0>2}m {seconds:0>2}s')
    real_etime_ost.blit()

    #? TODO Add more information about entity (maybe double click changes what exactly is showing)
    if SHOWING_INFO != None:
        dist = int(ROCKET.position.distance_to(SHOWING_INFO.position)) - SHOWING_INFO.radius
        info_ost.update(f'Distance from {ROCKET.name} to {SHOWING_INFO.name}: {dist/1000:.1f}km')
    else:
        info_ost.update('')
    info_ost.blit()

    stage_ost.update(f'stage: {ROCKET.stage + 1}')
    stage_ost.blit()

    fuel_ost.blit()
    fuel_at_stage_ost.update(f'{ROCKET.stage_fuel[ROCKET.stage]:.1f} l')
    fuel_at_stage_ost.blit()

    acceleration_ost.blit()
    rocket_acceleration_ost.update(f'{current_acceleration.length():.1f} m/s^2')
    rocket_acceleration_ost.blit()

    velocity_ost.blit()
    rocket_velocity_ost.update(f'{ROCKET.velocity.length():.1f} m/s')
    rocket_velocity_ost.blit()

    draw_that_thing(pg.Rect(COMPASS_COORDS), ROCKET.velocity, arrow_color=VELOCITY_COLOR)
    c = pg.Vector2(COMPASS_COORDS[0] + COMPASS_COORDS[2] / 2, COMPASS_COORDS[1] + COMPASS_COORDS[3] / 2)
    draw_arrow(c, current_acceleration, COMPASS_COORDS[2] / 3, color=ACCELERATION_COLOR)

    pw.update(events)
    pg.display.update()
