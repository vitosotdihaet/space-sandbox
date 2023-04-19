class OnScreenText:
    def __init__(self, text, fontsize, coords, pg_screen, antial=True, center=True, color=(0, 0, 0)):
        self.text = text
        self.fontsize = fontsize
        self.color = color
        self.antial = antial
        self.coords = coords
        self.pg_screen = pg_screen
        self.center = center

        self.rendered_text = self.fontsize.render(self.text, self.antial, self.color)
        if self.center == True:
            self.rect = self.rendered_text.get_rect(center=self.coords)
        else:
            self.rect = coords

    def blit(self):
        self.pg_screen.blit(self.rendered_text, self.rect)

    def update(self, text):
        self.text = text
        self.rendered_text = self.fontsize.render(self.text, self.antial, self.color)
        if self.center == True:
            self.rect = self.rendered_text.get_rect(center=self.coords)
        else:
            self.rect = self.coords
