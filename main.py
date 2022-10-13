import pygame as pg
import pymunk as pm
import time
import sys
import os


class Planet:
    def __init__(self, position, radius, mass):
        pass


class Rocket:
    def __init__(self, starting_position, velocity, mass, color):
        self.body = pm.Body(mass, velocity, body_type=pm.Body.DYNAMIC)
        self.body.position = starting_position
        self.shape = pm.Segment(self.body, (-1, 0), (1, 0), radius=2)
        SPACE.add(self.body, self.shape)
        self.color = color
        pass


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

    def update(self):
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
                    (self.x + (self.width/2 - text.get_width()/2), self.y + (self.height/(len(lines) + 1) * i - text.get_height()/2))
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

RESOLUTION = WIDTH, HEIGHT = (960, 540)
SCREEN = pg.display.set_mode(RESOLUTION)
ICON = pg.image.load(os.path.join(IMG_PATH, "icon.png"))
pg.display.set_icon(ICON)
SCREEN_SURF = pg.Surface(RESOLUTION)

CLOCK = pg.time.Clock()
TIMER = time.time()
elapsed_time = time.time() - TIMER
etime_ost = OnScreenText(str(elapsed_time), FONTS, (WIDTH - 80, HEIGHT - 35), color=(240, 240, 250))

SPACE = pm.Space()
SPACE.gravity = (-10, 10)
STARTING_POSITION = (100, 400)
R1 = Rocket(STARTING_POSITION, 200, 5, (200, 180, 0))
rocket_tail = [STARTING_POSITION]

while True:
    CLOCK.tick(60)

    '''
    print(elapsed_time)
    SCREEN.fill(pg.Color(int((elapsed_time * 50) % 255),
    int((elapsed_time * 50 + 50) % 255),
    int((elapsed_time * 50 + 100) % 255)))
    '''

    for event in pg.event.get():
        if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                sys.exit()


    SPACE.step(1/50)

    SCREEN.fill((0, 0, 20))
    SCREEN.blit(SCREEN_SURF, (0, 0))

    rocket_tail.append(R1.body.position)
    pg.draw.lines(SCREEN, R1.color, False, rocket_tail)

    pg.draw.circle(SCREEN, R1.color, R1.body.position, 2)

    elapsed_time = time.time() - TIMER
    etime_ost.text = f'{str(elapsed_time).split(".")[0]}.{str(elapsed_time).split(".")[1][:3]}'
    etime_ost.update()
    etime_ost.blit()

    pg.display.update()