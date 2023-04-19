import pygame as pg

import math


class Viewport:
    def __init__(self, h, w, init_scaling=1, init_shift=pg.Vector2(0), delta_zoom=0.1):
        self.scaling = 1
        self.zoom_level = init_scaling
        self.delta_zoom = 0.1

        self.h = h
        self.w = w

        self.shift = init_shift
        self.shifting = False

    def scale(self, coord):
        center = pg.Vector2(self.w/2, self.h/2) - self.shift
        return (coord - center) / self.scaling + center + self.shift

    def unscale(self, coord):
        coord = coord - self.shift
        return pg.Vector2((coord[0] - self.w/2) * self.scaling + self.w/2, (coord[1] - self.h/2) * self.scaling + self.h/2)

    def update(self, zoom, entities):
        self.zoom_level += zoom * self.delta_zoom

        if self.zoom_level < 1:
            self.scaling = 1 / (1 + math.exp(-self.zoom_level))
        else:
            self.scaling = self.zoom_level * self.zoom_level

        for e in entities:
            if e.has_trail:
                for i in range(len(e.trail)):
                    e.trail[i] = self.scale(e.trail_real[i])


RESOLUTION = W, H = (1500, 900)
SCREEN = pg.display.set_mode(RESOLUTION)
SCREEN_SURF = pg.Surface(RESOLUTION)

INIT_SCALING = 1
INIT_SHIFT = pg.Vector2(0, 0)

VIEWPORT = Viewport(H, W, init_scaling=INIT_SCALING, init_shift=INIT_SHIFT)
