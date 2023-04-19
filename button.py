import pygame as pg


class Button:
    def __init__(self, bg_color, text_color, x, y, width, height, pg_screen, font, text=""):
        self.bg_color = bg_color
        self.text_color = text_color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.pg_screen = pg_screen
        self.font = font

    def draw(self, outline=None):
        if outline:
            pg.draw.rect(self.pg_screen, outline, (self.x + 5, self.y + 5, self.width, self.height), 0)
        pg.draw.rect(self.pg_screen, self.bg_color, (self.x, self.y, self.width, self.height), 0)

        if self.text != "":
            lines = self.text.split("\n")
            for i, line in enumerate(lines, start=1):
                text = self.font.render(line, True, self.text_color)

                self.pg_screen.blit(
                    text,
                    (self.x + (self.width/2 - text.get_width()/2),
                     self.y + (self.height/(len(lines) + 1) * i - text.get_height()/2))
                )

    def is_over(self, pos):
        if self.x < pos[0] < self.x + self.width and self.y < pos[1] < self.y + self.height:
            return True
        return False
