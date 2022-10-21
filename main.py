import pygame as pg
import pymunk as pm
import math
import time
import sys
import os

def set_magnitude(vec, nm):
    nv = normalize(vec)
    return (nv[0] * nm, nv[1] * nm)

def get_magnitude(a):
    return math.sqrt(a.x * a.x + a.y * a.y)

def normalize(a):
    mg = get_magnitude(a)
    if mg == 0: return (0, 0)
    return (a.x / mg, a.y / mg)

class Planet:
    def __init__(self, position, radius, mass, velocity, color, body_type=pm.Body.DYNAMIC):
        self.body = pm.Body(mass, 0, body_type=body_type)
        self.body.position = position
        self.color = color

        self.velocity = (velocity[0] * SCALE * TIMESTEP, velocity[1] * SCALE * TIMESTEP)
        self.acceleration = (0, 0)

        self.shape = pm.Circle(self.body, radius * SCALE)
        self.shape.mass = mass * MASS_SCALE

        SPACE.add(self.body, self.shape)

    def draw(self):
        # pg.draw.circle(SCREEN, self.color, (self.body.position[0]/100 + W/2, self.body.position[1]/100 + H/2), self.shape.radius)
        pg.draw.circle(SCREEN, self.color, self.body.position, self.shape.radius)

    def update(self):
        if self.body.body_type == pm.Body.DYNAMIC:
            self.acceleration = (0, 0)
            for p in planets:
                r = self.body.position.get_distance(p.body.position)
                if r == 0 or self == p: continue
                # print(f'distance: {r}')

                v = -(self.shape.mass * p.shape.mass) / (r * r) * 10e5
                mg = v / self.shape.mass
                # print(f'{self.shape.mass} * {p.shape.mass} = {self.shape.mass * p.shape.mass}')
                sm = set_magnitude((self.body.position - p.body.position), mg)
                self.acceleration = ((self.acceleration[0] + sm[0]) * 100 , (self.acceleration[1] + sm[1]) * 100)
                # print(f'what\'s dis {self.body.position - p.body.position}, {mg}')
                # print(f'this is acceleration: {self.acceleration} and magnitude: {sm}')

            self.velocity = (self.velocity[0] + self.acceleration[0] * dt, self.velocity[1] + self.acceleration[1] * dt)
            self.body.position = (self.body.position.x + self.velocity[0] * dt, self.body.position.y + self.velocity[1] * dt)
            # print(f'velocity: {self.velocity} at planet: {self.body.position}')


class Rocket:
    def __init__(self, starting_position, velocity , mass, color, angle):
        self.body = pm.Body(mass, 0, body_type=pm.Body.DYNAMIC)
        self.body.position = starting_position
        self.color = color

        self.velocity = (velocity[0] * TIMESTEP, velocity[1] * TIMESTEP) 
        self.acceleration = (0, 0)
        self.angle = angle # in pi

        self.shape = pm.Segment(self.body, (-1, 0), (1, 0), radius=2)
        self.shape.mass = mass * MASS_SCALE

        SPACE.add(self.body, self.shape)

    def draw(self):
        pg.draw.circle(SCREEN, self.color, self.body.position, self.shape.radius)

    def update(self):
        self.acceleration = (0, 0)
        for p in planets:
            r = self.body.position.get_distance(p.body.position)
            if r == 0 or self == p: continue

            v = -(self.shape.mass * p.shape.mass) / (r * r) * 10e5
            mg = v / self.shape.mass
            sm = set_magnitude((self.body.position - p.body.position), mg)
            self.acceleration = ((self.acceleration[0] + sm[0]) * 100 , (self.acceleration[1] + sm[1]) * 100)

        self.velocity = (self.velocity[0] + self.acceleration[0] * dt, self.velocity[1] + self.acceleration[1] * dt)
        self.body.position = (self.body.position.x + self.velocity[0] * dt, self.body.position.y + self.velocity[1] * dt)

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
        if pos[0] > self.x and pos[0] < self.x + self.width:
            if pos[1] > self.y and pos[1] < self.y + self.height:
                return True
        return False


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

EARTH = Planet((W/2,                  H/2), 6371, 5.97 * 10**24, (0,    0), (100, 200, 255), body_type=pm.Body.STATIC)
MOON =  Planet((W/2 - 405400 * SCALE, H/2), 1737, 7.34 * 10**22, (0, -2500), (200, 200, 200)) # 405,400 km from earth
moon_tail = [MOON.body.position]
planets = [EARTH, MOON]

STARTING_POSITION = (EARTH.body.position[0] + EARTH.shape.radius + 10, EARTH.body.position[1])
R1 = Rocket(STARTING_POSITION, (0, 0), 200, (200, 180, 0), 0)
rocket_tail = [STARTING_POSITION]

last_ticks = 0
count_ticks = 0

while True:
    CLOCK.tick(60)

    dt = min(CLOCK.tick(60) / 1000, 0.02)

    for event in pg.event.get():
        if event.type == pg.QUIT:
            sys.exit()
        if event.type == pg.KEYDOWN:
            match event.key:
                case pg.K_ESCAPE:
                    sys.exit()

    # SPACE.step(1/50)

    SCREEN.fill((0, 0, 20))
    SCREEN.blit(SCREEN_SURF, (0, 0))

    R1.update()

    for p in planets:
        p.update()

    for p in planets:
        p.draw()


    moon_tail.append(MOON.body.position)
    pg.draw.lines(SCREEN, MOON.color, False, moon_tail)


    rocket_tail.append(R1.body.position)
    pg.draw.lines(SCREEN, R1.color, False, rocket_tail)
    R1.draw()

    elapsed_time = time.time() - TIMER
    etime_ost.update(f'{str(elapsed_time).split(".")[0]}.{str(elapsed_time).split(".")[1][:3]}')
    etime_ost.blit()

    pg.display.update()