'''
Libraries:
pygame - graphics
pymunk - physics (though gravity is calculated in a method of Planet and Rocket)
queue  - Planets' and Rocket's trails tracking
time   - timer on screen
os     - resources for graphics 
'''


import pygame as pg
import pymunk as pm
import queue
import time
import sys
import os


class Planet:
    def __init__(self, position, radius, mass, velocity, color, body_type=pm.Body.DYNAMIC, trail=True):
        self.body = pm.Body(mass * MASS_SCALE, 0, body_type=body_type)
        self.body.position = position
        self.body.velocity = (velocity[0] * SCALE * TIMESTEP, velocity[1] * SCALE * TIMESTEP)
        self.acceleration = (0, 0)
        self.color = color

        if trail and body_type == pm.Body.DYNAMIC:
            self.toggled_trail = True
            self.trail = queue.Queue(TRAIL_LENGTH + 10)
            self.trail.put(position)
            self.trail.put(position)
        else: self.toggled_trail = False

        self.shape = pm.Circle(self.body, radius * SCALE)
        self.shape.mass = mass * MASS_SCALE

        SPACE.add(self.body, self.shape)

    def draw(self):
        if self.toggled_trail: pg.draw.lines(SCREEN, self.color, False, self.trail.queue)
        pg.draw.circle(SCREEN, self.color, self.body.position, self.shape.radius)

    def update(self):
        if self.toggled_trail:
            self.trail.put(self.body.position)
            if self.trail.qsize() >= TRAIL_LENGTH: self.trail.get()

        if self.body.body_type == pm.Body.DYNAMIC:
            self.acceleration = (0, 0)
            for p in planets:
                r = self.body.position.get_distance(p.body.position)
                # skip if division by zero or iterated planet is itself
                if r == 0 or self == p: continue

                # i don't understand shit
                v = -(self.shape.mass * p.shape.mass) / (r * r) * 1e6
                print(f'{v}')
                mg = v / self.shape.mass
                sm = set_magnitude((self.body.position - p.body.position), mg)
                self.acceleration = ((self.acceleration[0] + sm[0]) * 100 , (self.acceleration[1] + sm[1]) * 100)

            # update velocity
            self.body.velocity = (self.body.velocity[0] + self.acceleration[0] * dt, self.body.velocity[1] + self.acceleration[1] * dt)


class Rocket:
    def __init__(self, position, velocity , mass, color, angle, trail=True):
        self.body = pm.Body(mass * MASS_SCALE, 0, body_type=pm.Body.DYNAMIC)
        self.body.position = position
        self.body.velocity = (velocity[0] * TIMESTEP, velocity[1] * TIMESTEP) 
        self.acceleration = (0, 0)
        self.color = color

        if trail:
            self.toggled_trail = True
            self.trail = queue.Queue(TRAIL_LENGTH + 10)
            self.trail.put(position)
            self.trail.put(position)

        self.angle = angle # in pi

        self.shape = pm.Segment(self.body, (-1, 0), (1, 0), radius=2)
        self.shape.mass = mass * MASS_SCALE

        SPACE.add(self.body, self.shape)

    def draw(self):
        if self.toggled_trail: pg.draw.lines(SCREEN, self.color, False, self.trail.queue)
        pg.draw.circle(SCREEN, self.color, self.body.position, self.shape.radius)

    def update(self):
        if self.toggled_trail:
            self.trail.put(self.body.position)
            if self.trail.qsize() >= TRAIL_LENGTH: self.trail.get()

        self.acceleration = (0, 0)
        for p in planets:
            r = self.body.position.get_distance(p.body.position)
            if r == 0: continue

            v = -(self.shape.mass * p.shape.mass) / (r * r) * 1e6
            mg = v / self.shape.mass
            sm = set_magnitude((self.body.position - p.body.position), mg)
            self.acceleration = ((self.acceleration[0] + sm[0]) * 100, (self.acceleration[1] + sm[1]) * 100)

        self.body.velocity = (self.body.velocity[0] + self.acceleration[0] * dt, self.body.velocity[1] + self.acceleration[1] * dt)
        # print(f'{self.acceleration}, {self.body.velocity}')


class OnScreenText:
    def __init__(self, text, fontsize, coords, antial=True, center=True, color=(0, 0, 0)):
        self.text = text
        self.fontsize = fontsize
        self.color = color
        self.antial = antial
        self.coords = coords
        self.center = center

        self.rendered_text = self.fontsize.render(self.text, self.antial, self.color)
        if self.center == True: self.rect = self.rendered_text.get_rect(center=self.coords)
        else: self.rect = coords

    def blit(self):
        SCREEN.blit(self.rendered_text, self.rect)

    def update(self, text):
        self.text = text
        self.rendered_text = self.fontsize.render(self.text, self.antial, self.color)
        if self.center == True: self.rect = self.rendered_text.get_rect(center=self.coords)
        else: self.rect = self.coords


class Button:
    def __init__(self, color, x, y, width, height, text=""):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self, outline=None):
        if outline: pg.draw.rect(SCREEN, outline, (self.x + 5, self.y + 5, self.width, self.height), 0)
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
    if event.type == pg.QUIT:
        sys.exit()
    if event.type == pg.KEYDOWN:
        match event.key:
            case pg.K_ESCAPE:
                sys.exit()

def set_magnitude(vec, nm):
    nv = normalize(vec)
    return (nv[0] * nm, nv[1] * nm)

def normalize(a):
    mg = get_magnitude(a)
    if mg == 0: return (0, 0)
    return (a.x / mg, a.y / mg)

def get_magnitude(a):
    return (a.x * a.x + a.y * a.y)**0.5


pg.init()

CWD = os.path.dirname(__file__)
RES_PATH = os.path.join(CWD, "resources")
FONT_PATH = os.path.join(RES_PATH, "fonts")
IMG_PATH = os.path.join(RES_PATH, "images")

microgramma = "microgramma.ttf"
allison = "Allison-Regular.ttf"
hp = "HPSimplified_Rg.ttf"
lobster = "lobster.ttf"
rockwell = "RockwellNovaCond.ttf"
comic = "comic.ttf"
impact = "impact.ttf"
tabs = "AmpleSoundTab.ttf"
gestures = "holomdl2.ttf"

FONTS = pg.font.Font((os.path.join(FONT_PATH, hp)), 54)
FONTM = pg.font.Font((os.path.join(FONT_PATH, hp)), 90)
FONTL = pg.font.Font((os.path.join(FONT_PATH, hp)), 120)

RESOLUTION = W, H = (1500, 900)
SCREEN = pg.display.set_mode(RESOLUTION)
SCREEN_SURF = pg.Surface(RESOLUTION)
ICON = pg.image.load(os.path.join(IMG_PATH, "icon.png"))
pg.display.set_icon(ICON)

CLOCK = pg.time.Clock()
TIMER = time.time()
elapsed_time = time.time() - TIMER
etime_ost = OnScreenText(str(elapsed_time), FONTS, (W - 80, H - 35), color=(240, 240, 250))

SPACE = pm.Space()
SPACE.gravity = (0, 0)

SCALE = 1/1000
MASS_SCALE = 1e-25
TIMESTEP = 60 # 1 minute
SPEED = 1
G = 6.67e-11

TRAIL_LENGTH = 100

EARTH = Planet((W/2,                  H/2), 6371, 5.97 * 10**24, (0,     0), (100, 200, 255), body_type=pm.Body.STATIC, trail=False)
MOON =  Planet((W/2 - 405400 * SCALE, H/2), 1737, 7.34 * 10**22, (0, -5000), (200, 200, 200)) # 405,400 km from earth
planets = [EARTH, MOON]

STARTING_POSITION = (EARTH.body.position[0] + EARTH.shape.radius + 200, EARTH.body.position[1])
R1 = Rocket(STARTING_POSITION, (0, 100), 2000, (200, 180, 0), 0)

last_ticks = 0
count_ticks = 0

while True:
    CLOCK.tick(60)

    dt = min(CLOCK.tick(60) / 1000, 0.02)

    for event in pg.event.get():
        event_handler(event)

    SPACE.step(dt)

    SCREEN.fill((0, 0, 20))
    SCREEN.blit(SCREEN_SURF, (0, 0))

    for p in planets:
        p.update()
        p.draw()

    R1.update()
    R1.draw()

    elapsed_time = time.time() - TIMER
    etime_ost.update(f'{str(elapsed_time).split(".")[0]}.{str(elapsed_time).split(".")[1][:3]}')
    etime_ost.blit()

    pg.display.update()