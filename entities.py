import pygame as pg

from collections import deque
from viewport import VIEWPORT


INTERFERENCE_EPS = 1e3
COLLISION_EPS = 1e-10

MINIMAL_DRAWING_RADIUS = 1

G = 6.67e-11

MAX_VELOCITY = 3e8


# *                                    (m, kg, secs)
class Entity: # * all the input parameters are real, except coordinates
    def __init__(self, name, coordinates, init_velocity, radius, mass, color, scale, screen, trail_size=100, has_trail=True):
        self.name = name

        self.coordinates = pg.math.Vector2(coordinates)
        self.position = self.coordinates / scale
        self.radius = radius

        self.velocity = pg.Vector2(init_velocity)
        self.acceleration = pg.Vector2(0, 0)
        self.mass = mass

        self.color = color

        self.scale = scale
        self.screen = screen

        if has_trail and not isinstance(self, PlanetStatic):
            self.has_trail = True
            self.trail = deque([VIEWPORT.scale(self.coordinates), VIEWPORT.scale(self.coordinates)], maxlen=trail_size)
            self.trail_real = deque([self.position * self.scale, self.position * self.scale], maxlen=trail_size)
        else:
            self.has_trail = False

    def update(self, dt, entities):
        if isinstance(self, PlanetStatic):
            self.coordinates = VIEWPORT.scale(self.position * self.scale)
            return

        for e in entities: # Iterate over all the entities to calculate physics
            if e == self:
                continue

            d = self.position - e.position
            if d.length() < self.radius + e.radius + INTERFERENCE_EPS:
                calculate_collision(self, e, d)
            else:
                self.acceleration = calculate_gravitational_force(self, e, d)

        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt # type: ignore
        self.acceleration = pg.Vector2(0, 0)

        temp = self.position * self.scale
        self.coordinates = VIEWPORT.scale(temp)
        if self.has_trail:
            self.trail.append(self.coordinates)
            self.trail_real.append(temp)

    def draw(self):
        self.coordinates = VIEWPORT.scale(self.position * self.scale)
        if self.has_trail:
            pg.draw.lines(self.screen, self.color, False, self.trail)
        pg.draw.circle(self.screen, self.color, self.coordinates, max(
            MINIMAL_DRAWING_RADIUS, self.radius / VIEWPORT.scaling * self.scale))


class Rocket(Entity):
    def __init__(self, name, coordinates, init_velocity, radius, mass, color, scale, screen, thrust, trail_size=100, has_trail=True):
        super().__init__(name, coordinates, init_velocity, radius, mass, color, scale, screen, trail_size, has_trail)
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
        if abs(dx) == abs(dy) == 1: # Check for diagonal movement
            self.acceleration.x = 1/2**0.5 * dx
            self.acceleration.y = 1/2**0.5 * dy

        self.acceleration *= self.thrust


class Planet(Entity):
    def __init__(self, name, coordinates, init_velocity, radius, mass, color, scale, screen, trail_size=100, has_trail=True):
        super().__init__(name, coordinates, init_velocity, radius, mass, color, scale, screen, trail_size, has_trail)


class PlanetStatic(Planet):
    def __init__(self, name, coordinates, radius, mass, color, scale, screen, has_trail=True):
        super().__init__(name, coordinates, pg.Vector2(0, 0), radius, mass, color, scale, screen, has_trail=has_trail)


class PlanetDynamic(Planet):
    def __init__(self, name, coordinates, init_velocity, radius, mass, color, scale, screen, trail_size=100, has_trail=True):
        super().__init__(name, coordinates, init_velocity, radius, mass, color, scale, screen, trail_size, has_trail)


# Changes the acceleration of entity1
def calculate_gravitational_force(e1, e2, d):
    r = d.length()
    a = e1.acceleration
    f = d * (-G * e2.mass / (r * r * r))
    a += f

    return a


# Checks if e1 collides with e2 and changes its parameters
def calculate_collision(e1, e2, d):
    if isinstance(e1, Rocket):
        e1.position = e2.position.copy() + d * (1 + COLLISION_EPS)
        if d.length() <= e1.radius + e2.radius:
            e1.velocity = e2.velocity.copy()
