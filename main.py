'''
Libraries:
pygame - graphics
deque  - Planets' and Rocket's trails tracking
time   - timer on screen
sys    - stopping the application
os     - resources for graphics 
'''


from collections import deque
import pygame as pg
import time
import sys
import os


#*                                        (km, kg); (rocket, planet dynamic, planet static)
class Entity: #* all the input parameters are real; valid types are: "R", "PD", "PS"
    def __init__(self, coordinates, init_velocity, radius, mass, entity_type, color, has_trail=True):
        self.coordinates = pg.math.Vector2(coordinates)
        self.position = self.coordinates / SCALE
        self.radius  = radius

        self.velocity = pg.Vector2(init_velocity)
        self.acceleration = pg.Vector2(0, 0)
        self.mass = mass

        self.type = entity_type

        self.color = color

        if has_trail and entity_type != "PS":
            self.has_trail = True
            self.trail = deque([self.coordinates], maxlen=TRAILSIZE)
            self.trail.append(self.coordinates)
        else:
            self.has_trail = False

    def update(self):
        if self.type == "PS": return

        self.acceleration = pg.Vector2(0, 0)
        for e in entities:
            if e == self: continue

            d = self.position - e.position
            r = d.length()

            #TODO? change biggest planet mass and radius if two collided
            if r < self.radius + e.radius: continue

            f = d * (-G * e.mass / (r * r * r))

            self.acceleration += f

        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt

        tmp = self.position * SCALE
        self.coordinates = pg.Vector2((tmp[0] - W/2) / APP_SCALE + W/2, (tmp[1] - H/2) / APP_SCALE + H/2)
        if self.has_trail: self.trail.append(self.coordinates)


    def draw(self):
        if self.has_trail: pg.draw.lines(SCREEN, self.color, False, self.trail)
        pg.draw.circle(SCREEN, self.color, self.coordinates, self.radius * SCALE)


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
    global APP_SCALE
    match event.type:
        case pg.QUIT:
            sys.exit()
        case pg.KEYDOWN:
            match event.key:
                case pg.K_ESCAPE:
                    sys.exit()
        case pg.MOUSEBUTTONDOWN:
            match event.button:
                case 1: # LMB to spawn a planet at mouse position 
                    entities.append(Entity(event.pos, (0, 0), 1500 * 1000, 4e22, "PD", (0, 230, 230)))
                case 4: # SCROLL DOWN TO GET CLOSER FROM THE EARTH
                    APP_SCALE -= DELTA_SCALE
                    change_app_scale()
                    print(f'closer: {APP_SCALE}')
                case 5: # SCROLL UP TO GET FURTHER FROM THE EARTH
                    APP_SCALE += DELTA_SCALE
                    change_app_scale()
                    print(f'away: {APP_SCALE}')


#TODO fix scaling
def change_app_scale():
    for e in entities:
        if e.has_trail:
            for i in range(len(e.trail)):
                nx = (e.trail[i][0] - W/2) / APP_SCALE + W/2
                ny = (e.trail[i][1] - H/2) / APP_SCALE + H/2
                e.trail[i] = pg.Vector2(nx, ny)


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

APP_SCALE = 1
DELTA_SCALE = 0.1

CLOCK = pg.time.Clock()
TIMER = time.time()
elapsed_time = time.time() - TIMER
etime_ost = OnScreenText(str(elapsed_time), FONTS, (W/2, H - 25), color=(240, 240, 250))

SCALE = 1/1000000
SPEED = 36
# whole orbit flew in 160 seconds if SPEED = 36 

G = 6.67e-11

TRAILSIZE = 100
BG_COLOR = (0, 10, 25)

EARTH = Entity((W/2,       H/2), (0,     0), 6371 * 1000, 5.972e24, "PS", (100, 100, 255))
MOON  = Entity((W/2 - 405, H/2), (0, -1023), 1737 * 1000, 7.347e22, "PD", (200, 200, 200))

STARTING_POSITION = (EARTH.coordinates[0] + EARTH.radius * SCALE + 100, EARTH.coordinates[1])
ROCKET = Entity(STARTING_POSITION, (0, 1000), 1000, 2000, "R", (255, 100, 255))

entities = [EARTH, MOON, ROCKET]

while True:
    CLOCK.tick(60)

    dt = CLOCK.tick(60) * SPEED

    for event in pg.event.get():
        event_handler(event)

    SCREEN.fill(BG_COLOR)
    SCREEN.blit(SCREEN_SURF, (0, 0))

    for e in entities:
        e.update()
        e.draw()

    elapsed_time = time.time() - TIMER
    etime_ost.update(f'{str(elapsed_time).split(".")[0]}.{str(elapsed_time).split(".")[1][:3]}')
    etime_ost.blit()

    pg.display.update()